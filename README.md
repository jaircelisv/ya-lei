# Ya Leí ✓✓

**English** · [Español](README.es.md)

> Your WhatsApp groups, already read.

**⚡ One-line install** — paste this into Claude (Cowork, Claude Code, or claude.ai):

```
fetch https://raw.githubusercontent.com/jaircelisv/ya-lei/main/INSTALL.md and follow the instructions
```

Claude detects where it's running, installs the right way, and walks you through setup — you never touch a terminal. **In Cowork, paste it into a task running "On your computer"** (that's where your WhatsApp lives); if you paste it in the cloud, Claude will collect your preferences and hand you back one personalized line for the local task. Prefer doing it by hand? See [Install](#install) below.

**Ya Leí** ("already read") is an open-source [Agent Skill](https://claude.com/skills) for **Claude Cowork** (and Claude Code) that digests your noisiest WhatsApp groups into one daily brief — decisions made, questions you were asked, dates and commitments, and a one-line summary of the noise — delivered **to you and only you**, by Gmail or a local dashboard.

No bots joining your groups. No WhatsApp API. No messages leaving your machine. It reads what's already sitting on your own disk.

## The problem

Everyone has *that* group. 300 messages a day, and buried in there: the one decision, the question someone asked *you*, the date that got moved. Reading it all is a part-time job; not reading it is social debt.

## How it works

```
WhatsApp Desktop (macOS)                 Any phone (fallback)
ChatStorage.sqlite  ──┐                  exported .txt chats ──┐
                      ▼                                        ▼
        scripts/wa_digest.py                    scripts/parse_export.py
                      └──────────► raw extract ◄───────────────┘
                                       ▼
                     Claude (scheduled Cowork task, runs locally)
                     writes the digest WITH JUDGMENT: what matters,
                     what was decided, what's still unanswered
                                       ▼
                   digests/YYYY-MM-DD.md ──► Gmail (to you)
                                        └──► dashboard/index.html
```

- **Primary mode (macOS):** WhatsApp Desktop keeps its message store in a readable SQLite file (`~/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite`). The skill snapshots it to a temp folder and reads the copy **read-only, passively**. It never touches the app, never automates your account, never calls any API.
- **Universal fallback (everything else):** export a chat from your phone (*Group → Export chat → Without media*), drop the `.txt` into `exports/`, done.
- **The "transformation with criteria":** Claude doesn't reformat messages — it reads them and decides what you'd regret missing. A cron pipeline reports `messages: 300`; an agent tells you *"they moved the dinner to Saturday and Andrés is still waiting for your answer."*

## Install

1. Clone this repo (or download it) somewhere permanent:
   ```bash
   git clone https://github.com/jaircelisv/ya-lei.git
   ```
2. Add it as a skill:
   - **Claude Cowork:** add the `ya-lei` folder to your Cowork skills, or point a Cowork task at the folder and ask Claude to follow `SKILL.md`.
   - **Claude Code:** copy/symlink the folder into `.claude/skills/` (or `~/.claude/skills/`).
3. Copy `config.example.json` → `config.json` and set your groups (or `top_active`), language, and your own email.
4. Create the scheduled task in Cowork: *Scheduled → New task*, daily, prompt: **"Run the ya-lei skill daily digest."**

> **Important:** because the skill reads local files, the scheduled task runs **locally** — your computer needs to be awake at the scheduled time. That's the honest trade-off for never sending your chats to any server.

## Privacy principles (non-negotiable)

1. **Only you.** The digest is delivered to your own inbox/dashboard. The skill refuses to send chat content anywhere else.
2. **Local first.** Extraction happens on your machine. `digests/`, `exports/` and `config.json` are gitignored — your data can't accidentally end up in a commit.
3. **Passive.** Nothing automates or impersonates your WhatsApp account. Reading a file on your own disk breaks no API terms — there is no API call to break.
4. **No silent failures.** If extraction, delivery or anything else fails, the skill says so loudly instead of faking a digest.

## Compatibility

| Platform | Mode | Status |
|---|---|---|
| macOS + WhatsApp Desktop (App Store) | local database (zero friction) | ✅ verified |
| Windows / Linux | exported `.txt` fallback | ✅ works (15-second export ritual) |
| Phone-only | exported `.txt` fallback | ✅ works |

The WhatsApp database schema is undocumented and may change with app updates. If it does, the skill fails loudly and the export fallback keeps working.

## 🏆 Vibecoders League — Platzi (Reto 6)

This project was built for **Proyecto 6: "El reporte que se arma y se envía solo"** of Platzi's Vibecoders League.

- **Real data source:** my own WhatsApp groups — 6,000+ real messages a week on this very machine.
- **Transformation with criteria:** the digest is written by Claude with judgment (decisions / unanswered questions / commitments / ignorable noise), not a raw forward.
- **Automatic scheduled delivery:** a Claude Cowork scheduled task runs it daily and delivers by Gmail + local dashboard.
- **What's different:** it's not a workflow — it's an **installable, open-source skill**. Anyone can clone this repo and wake up tomorrow with their own groups already read. And it treats privacy as the product: the report only ever reaches its owner.

Built live in a BMad "party mode" session — an adversarial roundtable of AI personas that killed two ideas (RIP the WhatsApp API route, which Meta's Groups API can't do for personal groups) before this one survived.

## License

[MIT](LICENSE) — do whatever you want, just don't blame us.
