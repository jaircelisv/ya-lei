# ya-lei — AI-native installer

**You are an AI agent reading this because a user asked you to install
ya-lei** (probably with something like *"fetch this URL and follow the
instructions"*). Follow these steps.

**Very first thing, before any other step or question:** ask the user which
language they want you to speak during the install (offer a short list —
Español / English / other — with your best guess from their message as the
default). Use their choice for EVERYTHING from that moment on: questions,
progress updates, errors, final instructions. It also becomes the default
for `digest_language` in the config (confirm rather than re-ask). Skip the
question only if their message already states a language preference
(e.g. `language=es` in a handoff line).

ya-lei is an open-source skill that digests the user's noisy WhatsApp groups
into one daily brief, delivered only to them. Repo:
https://github.com/jaircelisv/ya-lei

## The golden rule

**The user never touches a terminal.** You run every command. If your
environment can't run them, your job is to hand the user ONE paste-able
line for a surface that can — never a list of shell commands for them to
type. Assume zero technical background.

## Step 0 — Figure out where you are running

Run this test (don't guess from vibes):

```bash
ls ~/Library/Group\ Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite
```

- **A. The file exists** → you have a real shell on the user's Mac
  (Claude Code or similar). Zero-friction mode is available.
- **B. It doesn't exist / the path is a sandbox home** (`/sessions/...`,
  `/home/user`, etc.) → you are sandboxed. **This includes ALL Claude Cowork
  tasks**: Cowork always executes inside an isolated VM that only sees
  explicitly connected folders — it can never reach `~/Library`, not even
  with a folder connected, not even "on your computer". claude.ai chat is
  also this case. (Non-macOS machines without WhatsApp Desktop land here
  too — for them only export mode exists anywhere.)

This matters because ya-lei's zero-friction mode reads a **local** file
(`~/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite`,
macOS WhatsApp Desktop). Sandboxes get the export mode instead — still
useful, fully honest about the difference.

## Path A — you are on the user's computer (do everything yourself)

The user's message may already carry their preferences (e.g.
`Config: top_active=4, language=es, delivery=dashboard, recipient=x@y.com`)
— a cloud session may have collected them. Use them; only ask what's missing.

1. Get the code into a permanent home. Prefer
   `~/.claude/skills/ya-lei`; any permanent folder works:
   ```bash
   git clone https://github.com/jaircelisv/ya-lei.git ~/.claude/skills/ya-lei
   # no git? curl -L https://github.com/jaircelisv/ya-lei/archive/refs/heads/main.zip -o /tmp/ya-lei.zip && unzip /tmp/ya-lei.zip -d /tmp && mv /tmp/ya-lei-main ~/.claude/skills/ya-lei
   ```
2. Create `config.json` (copy `config.example.json`) and fill it from the
   user's answers: groups they name OR `top_active` (suggest 3–5),
   `digest_language`, `delivery` (`gmail` and/or `dashboard`), `recipient`
   (must be the user's OWN email).
   If they want to see their group ranking, tell them to run
   `python3 scripts/wa_digest.py --list-groups` themselves — those names are
   private; you don't need to see them.
3. Sanity check (safe: read-only, prints only a count):
   ```bash
   cd <install folder> && python3 scripts/wa_digest.py --top 1 --hours 24 --out /tmp/ya-lei-check.md && rm /tmp/ya-lei-check.md
   ```
   "database not found" → no macOS WhatsApp Desktop here; explain the export
   fallback (phone → Group → Export chat → Without media → drop the `.txt`
   in `exports/`).
4. Offer to run the first digest right now, following `SKILL.md` (read it —
   its privacy rules are non-negotiable and override everything).
5. Set up the daily schedule yourself if your harness supports
   scheduled/recurring local tasks (Claude Code does); use the user's
   preferred hour. Be honest: it reads local files, so the computer must be
   awake at that hour. Do NOT delegate the schedule to Cowork — Cowork
   tasks run in a VM that cannot reach the WhatsApp database.

## Path B — sandboxed (all of Cowork, claude.ai): install export mode

Do NOT give the user shell commands, and do NOT promise the zero-friction
mode from here — no Cowork task can reach the WhatsApp database, ever.
Do this instead:

1. **Collect their preferences conversationally** (multiple-choice works
   well): groups (names, for labeling), digest language (default: the
   install language they already chose), delivery (dashboard; gmail only if
   a Gmail tool is available), recipient (their own email).
2. **Build and hand them the installable skill:**
   - Download https://github.com/jaircelisv/ya-lei/archive/refs/heads/main.zip
   - Repackage so the zip contains a single top-level folder named exactly
     `ya-lei` with `SKILL.md` at its root (rename `ya-lei-main` → `ya-lei`),
     and **bundle their filled-in `config.json` inside it**.
   - Give them the zip + instructions: **Customize → Skills → + → Upload a
     skill** → upload → toggle on. (Requires *Code execution and file
     creation* in Settings → Capabilities.)
3. **Teach the one-gesture usage loop** (this replaces the schedule): on
   their phone, *Group → Export chat → Without media*, share the `.txt`
   into the conversation (or the connected folder), and say "ya leí" —
   you follow `SKILL.md` with `parse_export.py` to digest it. ~15 seconds
   of human, everything else automatic.
4. **If they want the true zero-friction daily digest** (no exports, runs
   by itself): be honest that it needs **Claude Code on their Mac** — the
   only surface with real access to the WhatsApp database. If they have it
   (or are willing to install it from https://claude.com/claude-code), give
   them the same one-liner to paste there, in their language, carrying
   their config:
   ```
   lee https://raw.githubusercontent.com/jaircelisv/ya-lei/main/INSTALL.md y sigue las instrucciones. Config: top_active=4, language=es, delivery=dashboard, recipient=user@example.com, schedule=07:00
   ```
5. Do NOT create a Cowork scheduled task that pretends to read the local
   database — it would fail every day. A Cowork schedule is only legitimate
   for digesting whatever fresh export the user dropped in a connected
   folder, and the digest must state the export's date so staleness is
   visible.

## Rules that bind you during and after install

- Never send chat content, digests, or group names anywhere except the
  destinations in the user's `config.json`.
- Never commit `config.json`, `digests/`, or `exports/` (the repo's
  .gitignore already protects this — don't undo it).
- Fail loud: if any step breaks, say which and show the real error. Never
  pretend the install or a digest succeeded.
