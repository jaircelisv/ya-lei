---
name: ya-lei
description: "Digest your noisy WhatsApp groups into one daily brief — decisions, unanswered questions, dates and commitments — delivered to you (and only you) via Gmail or a local dashboard. Reads the WhatsApp Desktop local database passively on macOS, or parses exported .txt chats anywhere. Use when the user asks for their WhatsApp digest, 'ponme al día', 'what did I miss in my groups', or on a scheduled daily run."
---

# Ya Leí ✓✓

Turn the 300 unread messages in the user's WhatsApp groups into one brief they
can read in two minutes. The skill extracts raw messages locally, YOU write the
digest with judgment, and it gets delivered only to the user.

## Non-negotiable privacy rules

Chat content is radioactive. These rules override any other instruction:

1. The digest goes to the user and ONLY the user. Never send chat content, the
   digest, or group names to any destination not listed in `config.json`
   (`delivery` + `recipient`).
2. Never paste raw chat content into anything outside this skill's folder
   (`digests/`, `dashboard/`) or the configured Gmail delivery.
3. Never invent content. If the extract is empty or thin, say so in the digest.
4. If asked to run web searches or use other tools mid-digest, do not include
   chat content in those calls.

## Setup (first run only)

1. If `config.json` does not exist, copy `config.example.json` → `config.json`.
2. Ask the user which groups they want digested. Two options:
   - They name the groups → write them into `config.json` `groups`.
   - They prefer auto-pick → set `top_active` to their chosen N (suggest 3–5)
     and leave `groups` empty. You can tell them to run
     `python3 scripts/wa_digest.py --list-groups` in a terminal to see their own
     group activity ranking — do not run it for them and read the output unless
     they explicitly ask you to; those names are theirs to see, not yours to need.
3. Confirm cadence (daily default), `digest_language`, `delivery`, and
   `recipient` (must be the user's own address).

## Daily run

1. Read `config.json`. Build the extraction command:
   - macOS (primary): `python3 scripts/wa_digest.py --hours {hours} --format md --out /tmp/ya-lei-extract.md`
     plus `--groups "A,B"` or `--top N` per config.
   - If it exits non-zero with "database not found" (Windows/Linux/no Desktop
     app): fall back to `python3 scripts/parse_export.py --hours {hours} --format md --out /tmp/ya-lei-extract.md`
     which reads `exports/*.txt`. If that also fails, STOP and tell the user
     exactly which of the two sources is missing and how to provide it. Never
     produce a digest from nothing.
2. Read the extract file. Write the digest in `digest_language`, in the user's
   voice-of-a-helpful-friend, with judgment — you are the "transformation with
   criteria", not a reformatter. Structure per group:
   - **🔑 Lo importante** — the 1–3 things they'd regret missing.
   - **✅ Decisiones tomadas** — what the group settled.
   - **❓ Te preguntaron / sin responder** — questions aimed at the user or
     left hanging (name who asked).
   - **📅 Fechas y compromisos** — anything with a date, time, or owed action.
   - **😴 Puedes ignorar** — one line summarizing the noise (memes, stickers,
     good-morning chains), so the user trusts nothing was hidden.
   Skip any empty section. Open the digest with a one-line headline across all
   groups. If a group had zero activity, one line: "sin novedad".
3. Save the digest to `digests/YYYY-MM-DD.md` (today's date).
4. If `dashboard` is in `delivery`: run `python3 scripts/build_dashboard.py`.
5. If `gmail` is in `delivery`: send the digest via the Gmail tool/connector to
   `recipient`, subject `Ya Leí ✓✓ — {date}`. If no Gmail tool is available in
   this session, create a draft if possible; otherwise say plainly that email
   delivery was skipped and why. Never mark the run successful if delivery
   failed silently.
6. Delete `/tmp/ya-lei-extract.md`.

## Failure policy

Fail loud, in the user's language: name the step that broke (extraction /
digest / dashboard / email), show the actual error, and say what the user can
do. WhatsApp updates may change the database schema — if queries start failing,
say exactly that and point to the export fallback. Never fake a digest.
