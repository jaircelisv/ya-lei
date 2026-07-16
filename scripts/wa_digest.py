#!/usr/bin/env python3
"""ya-lei — WhatsApp Desktop (macOS) local database reader.

Reads the WhatsApp Desktop message store (ChatStorage.sqlite) PASSIVELY:
it copies the database to a temp dir and opens the copy read-only. It never
touches the WhatsApp app, never talks to any API, and never sends anything
anywhere. Output goes to stdout or --out, for Claude to summarize.

Privacy: this script runs on YOUR machine against YOUR data. Message content
is only written where you point it. Nothing is transmitted.

Requires: Python 3 stdlib only.
"""

import argparse
import datetime as dt
import json
import shutil
import sqlite3
import sys
import tempfile
import unicodedata
from pathlib import Path

# Apple Core Data timestamps count seconds from 2001-01-01 00:00:00 UTC.
CORE_DATA_EPOCH = 978307200

DEFAULT_DB = (
    Path.home()
    / "Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite"
)

# ZMESSAGETYPE → placeholder for non-text payloads (best-effort mapping,
# schema is undocumented; unknown types fall back to [adjunto]).
MEDIA_PLACEHOLDERS = {
    1: "[foto]",
    2: "[video]",
    3: "[nota de voz]",
    4: "[contacto]",
    5: "[ubicación]",
    7: "[enlace]",
    8: "[documento]",
    11: "[gif]",
    14: "[mensaje eliminado]",
    15: "[sticker]",
    38: "[foto (ver una vez)]",
    39: "[video (ver una vez)]",
}
GROUP_EVENT_TYPE = 6


def norm(s: str) -> str:
    """Casefold + strip accents so 'Familia López' matches 'familia lopez'."""
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).casefold().strip()


def fail(msg: str, code: int = 2):
    print(f"ya-lei ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def snapshot_db(db_path: Path, tmpdir: Path) -> Path:
    """Copy db + WAL/SHM sidecars so we read a consistent, untouched snapshot."""
    if not db_path.exists():
        fail(
            f"WhatsApp database not found at {db_path}.\n"
            "  - Is WhatsApp Desktop (from the App Store) installed and signed in?\n"
            "  - On Windows/Linux, this mode is unavailable: use the export "
            "fallback instead (scripts/parse_export.py)."
        )
    dest = tmpdir / db_path.name
    shutil.copy2(db_path, dest)
    for suffix in ("-wal", "-shm"):
        side = Path(str(db_path) + suffix)
        if side.exists():
            shutil.copy2(side, Path(str(dest) + suffix))
    return dest


def open_ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def list_groups(conn: sqlite3.Connection, hours: int):
    """All group sessions with activity counts inside the window."""
    since = dt.datetime.now(dt.timezone.utc).timestamp() - CORE_DATA_EPOCH - hours * 3600
    rows = conn.execute(
        """
        SELECT cs.Z_PK AS pk, cs.ZPARTNERNAME AS name,
               COUNT(m.Z_PK) AS msgs
        FROM ZWACHATSESSION cs
        LEFT JOIN ZWAMESSAGE m
               ON m.ZCHATSESSION = cs.Z_PK AND m.ZMESSAGEDATE > ?
        WHERE cs.ZSESSIONTYPE = 1
        GROUP BY cs.Z_PK
        ORDER BY msgs DESC, cs.ZLASTMESSAGEDATE DESC
        """,
        (since,),
    ).fetchall()
    return rows


def pick_sessions(conn, groups, top, hours):
    all_groups = list_groups(conn, hours)
    if groups:
        wanted = [norm(g) for g in groups]
        picked, missing = [], []
        for w, original in zip(wanted, groups):
            matches = [r for r in all_groups if w in norm(r["name"] or "")]
            if not matches:
                missing.append(original)
            else:
                # Most active match wins when a fragment is ambiguous.
                picked.append(matches[0])
        if missing:
            print(
                f"ya-lei WARNING: no group matched: {', '.join(missing)} "
                "(check config.json 'groups'; matching ignores case/accents)",
                file=sys.stderr,
            )
        if not picked:
            fail("none of the configured groups matched. Run with --list-groups.")
        return picked
    n = top or 3
    return [r for r in all_groups[:n] if r["msgs"] > 0]


def fetch_messages(conn, session_pk: int, hours: int, cap: int):
    since = dt.datetime.now(dt.timezone.utc).timestamp() - CORE_DATA_EPOCH - hours * 3600
    rows = conn.execute(
        """
        SELECT m.ZMESSAGEDATE AS ts, m.ZISFROMME AS fromme,
               m.ZMESSAGETYPE AS mtype, m.ZTEXT AS text,
               m.ZPUSHNAME AS pushname, m.ZFROMJID AS fromjid,
               gm.ZCONTACTNAME AS contactname, gm.ZFIRSTNAME AS firstname
        FROM ZWAMESSAGE m
        LEFT JOIN ZWAGROUPMEMBER gm ON m.ZGROUPMEMBER = gm.Z_PK
        WHERE m.ZCHATSESSION = ? AND m.ZMESSAGEDATE > ?
        ORDER BY m.ZMESSAGEDATE ASC
        """,
        (session_pk, since),
    ).fetchall()

    total = len(rows)
    truncated = 0
    if total > cap:
        truncated = total - cap
        rows = rows[-cap:]  # keep the most recent

    out = []
    for r in rows:
        if r["mtype"] == GROUP_EVENT_TYPE:
            continue
        if r["fromme"]:
            sender = "Yo"
        else:
            sender = (
                r["contactname"]
                or r["firstname"]
                or r["pushname"]
                or (r["fromjid"] or "?").split("@")[0]
            )
        text = (r["text"] or "").strip()
        placeholder = MEDIA_PLACEHOLDERS.get(r["mtype"])
        if r["mtype"] != 0:
            text = f"{placeholder or '[adjunto]'} {text}".strip()
        if not text:
            continue
        when = dt.datetime.fromtimestamp(
            r["ts"] + CORE_DATA_EPOCH, dt.timezone.utc
        ).astimezone()
        out.append(
            {
                "date": when.strftime("%Y-%m-%d"),
                "time": when.strftime("%H:%M"),
                "from": sender,
                "text": text,
            }
        )
    return out, truncated


def render_markdown(data: dict) -> str:
    lines = [
        f"# ya-lei raw extract — {data['generated_at']}",
        f"_Window: last {data['window_hours']}h — this is RAW material for the digest, not the digest._",
        "",
    ]
    for g in data["groups"]:
        lines.append(f"## {g['name']} ({g['message_count']} mensajes)")
        if g["truncated"]:
            lines.append(
                f"_NOTE: {g['truncated']} older messages in the window were dropped (cap)._"
            )
        day = None
        for m in g["messages"]:
            if m["date"] != day:
                day = m["date"]
                lines.append(f"\n**{day}**")
            lines.append(f"- {m['time']} — {m['from']}: {m['text']}")
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB, help="path to ChatStorage.sqlite")
    ap.add_argument("--groups", help="comma-separated group names/fragments")
    ap.add_argument("--top", type=int, default=0, help="pick the N most active groups instead")
    ap.add_argument("--hours", type=int, default=24, help="look-back window (default 24)")
    ap.add_argument("--max-per-group", type=int, default=500)
    ap.add_argument("--format", choices=["json", "md"], default="md")
    ap.add_argument("--out", type=Path, help="write here instead of stdout")
    ap.add_argument(
        "--list-groups", action="store_true",
        help="print your group names + activity and exit (run this yourself; it's your data)",
    )
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="ya-lei-") as tmp:
        conn = open_ro(snapshot_db(args.db, Path(tmp)))
        try:
            if args.list_groups:
                for r in list_groups(conn, args.hours):
                    if r["name"]:
                        print(f"{r['msgs']:5d}  {r['name']}")
                return

            groups_arg = [g.strip() for g in args.groups.split(",")] if args.groups else None
            sessions = pick_sessions(conn, groups_arg, args.top, args.hours)
            data = {
                "generated_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "window_hours": args.hours,
                "groups": [],
            }
            for s in sessions:
                msgs, truncated = fetch_messages(
                    conn, s["pk"], args.hours, args.max_per_group
                )
                data["groups"].append(
                    {
                        "name": s["name"],
                        "message_count": len(msgs),
                        "truncated": truncated,
                        "messages": msgs,
                    }
                )

            body = (
                json.dumps(data, ensure_ascii=False, indent=1)
                if args.format == "json"
                else render_markdown(data)
            )
            if args.out:
                args.out.write_text(body, encoding="utf-8")
                total = sum(g["message_count"] for g in data["groups"])
                print(
                    f"ya-lei: wrote {total} messages from "
                    f"{len(data['groups'])} group(s) to {args.out}",
                    file=sys.stderr,
                )
            else:
                print(body)
        finally:
            conn.close()


if __name__ == "__main__":
    main()
