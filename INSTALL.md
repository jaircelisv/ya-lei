# ya-lei — AI-native installer

**You are an AI agent reading this because a user asked you to install
ya-lei** (probably with something like *"fetch this URL and follow the
instructions"*). Follow these steps. Speak to the user in THEIR language
(if they wrote in Spanish, everything you say is in Spanish).

ya-lei is an open-source skill that digests the user's noisy WhatsApp groups
into one daily brief, delivered only to them. Repo:
https://github.com/jaircelisv/ya-lei

## Step 0 — Figure out where you are running

Ask yourself (not the user) which of these describes your environment:

- **A. You have access to the user's local filesystem** (Claude Code, or a
  Claude Cowork task working in a local folder on the user's computer).
- **B. You are in a cloud sandbox** (claude.ai chat / Cowork remote task with
  code execution but no access to the user's disk).

This matters because ya-lei's zero-friction mode reads a **local** file
(`~/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite`,
macOS WhatsApp Desktop). A cloud sandbox can never reach it; there the skill
still works via exported `.txt` chats.

## Path A — local filesystem access (best experience)

1. Get the code (prefer git; fall back to the zip):
   ```bash
   git clone https://github.com/jaircelisv/ya-lei.git
   # or: curl -L https://github.com/jaircelisv/ya-lei/archive/refs/heads/main.zip -o ya-lei.zip && unzip ya-lei.zip && mv ya-lei-main ya-lei
   ```
   Good homes: `~/.claude/skills/ya-lei` (Claude Code, global),
   `.claude/skills/ya-lei` (per-project), or any permanent folder the user
   picks for Cowork to work in.
2. `cp config.example.json config.json` inside the folder.
3. Ask the user: which groups? Either they name them (write to `groups` in
   `config.json`) or they want auto-pick (set `top_active`, suggest 3–5).
   If they want to see their own ranking, tell them to run
   `python3 scripts/wa_digest.py --list-groups` themselves — do not run it
   and read the output on their behalf; those names are private.
4. Ask for `digest_language`, `delivery` (`gmail` and/or `dashboard`), and
   `recipient` (must be the user's OWN email). Save `config.json`.
5. Sanity check (safe, prints only counts to you via --out):
   ```bash
   python3 scripts/wa_digest.py --top 1 --hours 24 --out /tmp/ya-lei-check.md
   ```
   If it errors with "database not found", the user isn't on macOS WhatsApp
   Desktop → explain the export fallback (phone → Group → Export chat →
   Without media → drop the .txt in `exports/`). Delete /tmp/ya-lei-check.md
   after checking it worked; don't quote its content.
6. Offer to set up the daily schedule:
   - **Cowork:** tell the user: *Scheduled → New task → daily*, working
     folder = this folder, prompt: `Run the ya-lei daily digest following
     SKILL.md`. Warn honestly: it reads local files, so it runs locally —
     the computer must be awake at that hour.
   - **Claude Code:** offer to create the equivalent scheduled/recurring task
     if your harness supports it.
7. Offer to run the first digest right now, following `SKILL.md` (read it —
   its privacy rules are non-negotiable and override everything).

## Path B — cloud sandbox (claude.ai / remote Cowork)

You cannot reach the local database. Two options — offer both:

1. **Install as an uploadable skill (for the export fallback):**
   - Download https://github.com/jaircelisv/ya-lei/archive/refs/heads/main.zip
   - Repackage so the zip contains a single top-level folder named exactly
     `ya-lei` with `SKILL.md` at its root (rename `ya-lei-main` → `ya-lei`).
   - Give the user the zip and these instructions: **Customize → Skills →
     + → Upload a skill** → select the zip → toggle it on.
     (Requires *Code execution and file creation* enabled in Settings →
     Capabilities.)
   - Usage in this mode: the user exports a chat from their phone and hands
     you the `.txt`; you follow `SKILL.md` to digest it.
2. **Recommend Path A for zero-friction:** if the user has a Mac with
   WhatsApp Desktop and the Claude desktop app or Claude Code, the local
   install gives them the daily digest with no manual exports. Point them to
   the one-liner in the README, run from a local surface.

## Rules that bind you during and after install

- Never send chat content, digests, or group names anywhere except the
  destinations in the user's `config.json`.
- Never commit `config.json`, `digests/`, or `exports/` (the repo's
  .gitignore already protects this — don't undo it).
- Fail loud: if any step breaks, say which and show the real error. Never
  pretend the install or a digest succeeded.
