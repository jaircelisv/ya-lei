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

Ask yourself (not the user) which of these describes your environment:

- **A. You can read/write the user's local filesystem and run commands on
  their computer** (a Cowork task running "On your computer", or Claude Code).
- **B. You are in a cloud sandbox** (claude.ai chat, or a Cowork task running
  in the cloud — you may have code execution, but not the user's disk).

This matters because ya-lei's zero-friction mode reads a **local** file
(`~/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite`,
macOS WhatsApp Desktop). A cloud sandbox can never reach it.

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
5. Set up the daily schedule — again, you do it or you make it one click:
   - **Cowork:** tell the user: *Scheduled → New task → daily → "On your
     computer" → working folder = the install folder*, prompt:
     `Run the ya-lei daily digest following SKILL.md`. Be honest: it reads
     local files, so the computer must be awake at that hour.
   - **Claude Code:** create the recurring task yourself if your harness
     supports scheduled/cron tasks; otherwise give the Cowork instruction.

## Path B — cloud sandbox: your job is a clean handoff

Do NOT give the user shell commands. Do this instead:

1. **Collect their preferences conversationally** (multiple-choice works
   well): groups by name or auto-pick N, digest language (default: the
   install language they already chose), delivery (gmail/dashboard),
   recipient (their own email), preferred daily hour.
2. **Hand them ONE line to paste.** Tell them: open the Claude desktop app →
   **New Cowork task** → choose **"On your computer"** (this is the key —
   that's where their WhatsApp database lives) → paste:
   ```
   fetch https://raw.githubusercontent.com/jaircelisv/ya-lei/main/INSTALL.md and follow the instructions. Config: top_active=4, language=es, delivery=dashboard, recipient=user@example.com, schedule=07:00
   ```
   …with the config values replaced by THEIR answers, and the sentence
   written in THEIR language (e.g. Spanish: `lee <url> y sigue las
   instrucciones. Config: …`). The local agent will do the entire install
   without asking twice.
3. **No computer access at all?** (phone-only, claude.ai only, no WhatsApp
   Desktop): build the uploadable skill instead —
   - Download https://github.com/jaircelisv/ya-lei/archive/refs/heads/main.zip
   - Repackage so the zip contains a single top-level folder named exactly
     `ya-lei` with `SKILL.md` at its root (rename `ya-lei-main` → `ya-lei`).
   - Give them the zip + instructions: **Customize → Skills → + → Upload a
     skill** → upload → toggle on. (Requires *Code execution and file
     creation* in Settings → Capabilities.)
   - Usage in this mode: they export a chat from their phone (Group →
     Export chat → Without media) and hand you the `.txt`; you follow
     `SKILL.md` to digest it. Be clear this mode has no automatic schedule —
     it works on demand.
4. Do NOT create a cloud scheduled task for the local mode — it would fail
   silently every day. Say so if the user asks.

## Rules that bind you during and after install

- Never send chat content, digests, or group names anywhere except the
  destinations in the user's `config.json`.
- Never commit `config.json`, `digests/`, or `exports/` (the repo's
  .gitignore already protects this — don't undo it).
- Fail loud: if any step breaks, say which and show the real error. Never
  pretend the install or a digest succeeded.
