#!/usr/bin/env python3
"""ya-lei — universal fallback: parse WhatsApp "Export chat" .txt files.

For anyone NOT on macOS WhatsApp Desktop (Windows, phone-only users):
export a chat from the phone (Group → Export chat → Without media), drop the
.txt into exports/, and this script turns it into the same structure
wa_digest.py produces.

Handles both common export dialects:
  iOS:     [31/12/23, 21:15:03] Name: message
  Android: 31/12/23, 21:15 - Name: message
plus AM/PM variants, the invisible U+200E marks iOS sprinkles around,
and multi-line messages (continuation lines are appended).

Requires: Python 3 stdlib only.
"""

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

IOS = re.compile(
    r"^‎?\[(?P<date>[\d/.\-]+),?\s+(?P<time>[\d:]+(?:\s?[apAP]\.?\s?[mM]\.?)?)\]\s"
    r"(?P<sender>[^:]+):\s?(?P<text>.*)$"
)
ANDROID = re.compile(
    r"^‎?(?P<date>[\d/.\-]+),?\s+(?P<time>[\d:]+(?:\s?[apAP]\.?\s?[mM]\.?)?)\s[-–]\s"
    r"(?P<sender>[^:]+):\s?(?P<text>.*)$"
)
MEDIA_MARKERS = (
    "<Multimedia omitido>", "<Media omitted>", "imagen omitida", "image omitted",
    "video omitido", "video omitted", "audio omitido", "audio omitted",
    "sticker omitido", "sticker omitted", "GIF omitido", "GIF omitted",
    "documento omitido", "document omitted",
)


def parse_when(date_s: str, time_s: str, dayfirst: bool):
    parts = re.split(r"[/.\-]", date_s)
    if len(parts) != 3:
        return None
    a, b, y = (int(p) for p in parts)
    if len(str(y)) <= 2:
        y += 2000
    day, month = (a, b) if dayfirst else (b, a)
    if month > 12 and day <= 12:  # the heuristic that saves gringo exports
        day, month = month, day
    t = time_s.strip().lower().replace(".", "").replace(" ", "")
    ampm = None
    if t.endswith(("am", "pm")):
        ampm, t = t[-2:], t[:-2]
    hh, mm, *rest = (int(x) for x in t.split(":"))
    if ampm == "pm" and hh != 12:
        hh += 12
    if ampm == "am" and hh == 12:
        hh = 0
    try:
        return dt.datetime(y, month, day, hh, mm, rest[0] if rest else 0)
    except ValueError:
        return None


def clean(text: str) -> str:
    text = text.replace("‎", "").strip()
    for marker in MEDIA_MARKERS:
        if marker.lower() in text.lower():
            return "[adjunto]"
    return text


def group_name_from_file(path: Path) -> str:
    name = path.stem
    for prefix in ("Chat de WhatsApp con ", "WhatsApp Chat with ", "Chat de WhatsApp - ",
                   "WhatsApp Chat - "):
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def parse_file(path: Path, hours: int, dayfirst: bool, cap: int):
    since = dt.datetime.now() - dt.timedelta(hours=hours)
    messages = []
    with path.open(encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            m = IOS.match(line) or ANDROID.match(line)
            if not m:
                if messages and line.strip():  # continuation of previous message
                    messages[-1]["text"] += "\n" + line.strip()
                continue
            when = parse_when(m["date"], m["time"], dayfirst)
            if when is None or when < since:
                continue
            text = clean(m["text"])
            if not text:
                continue
            messages.append(
                {
                    "date": when.strftime("%Y-%m-%d"),
                    "time": when.strftime("%H:%M"),
                    "from": m["sender"].replace("‎", "").strip(),
                    "text": text,
                }
            )
    truncated = max(0, len(messages) - cap)
    return {
        "name": group_name_from_file(path),
        "message_count": min(len(messages), cap),
        "truncated": truncated,
        "messages": messages[-cap:],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", type=Path, default=Path("exports"),
                    help="folder with exported .txt chats (default: exports/)")
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--monthfirst", action="store_true",
                    help="dates in exports are MM/DD (US phones). Default is DD/MM.")
    ap.add_argument("--max-per-group", type=int, default=500)
    ap.add_argument("--format", choices=["json", "md"], default="md")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    files = sorted(args.dir.glob("*.txt")) if args.dir.exists() else []
    if not files:
        print(
            f"ya-lei ERROR: no .txt exports found in {args.dir}/. "
            "On your phone: Group → Export chat → Without media, then drop the "
            ".txt file there.",
            file=sys.stderr,
        )
        sys.exit(2)

    data = {
        "generated_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "window_hours": args.hours,
        "groups": [parse_file(f, args.hours, not args.monthfirst, args.max_per_group)
                   for f in files],
    }

    if args.format == "json":
        body = json.dumps(data, ensure_ascii=False, indent=1)
    else:  # same shape wa_digest.py emits
        from wa_digest import render_markdown  # noqa: E402  (same folder)
        body = render_markdown(data)

    if args.out:
        args.out.write_text(body, encoding="utf-8")
        total = sum(g["message_count"] for g in data["groups"])
        print(f"ya-lei: wrote {total} messages from {len(files)} export(s) to {args.out}",
              file=sys.stderr)
    else:
        print(body)


if __name__ == "__main__":
    main()
