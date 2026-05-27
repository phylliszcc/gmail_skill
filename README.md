# gmail_skill

A local MCP server that lets AI agents read, send, reply, manage calendar, and archive Gmail — without a browser.

Built for [Claude Code](https://claude.ai/code) and compatible with any MCP-aware agent framework.

---

## What it does

| Capability | Tools |
|------------|-------|
| Send email | `gmail_send` |
| Reply / Reply-all | `gmail_reply` |
| List upcoming events | `calendar_list_events` |
| Create meeting invites | `calendar_create_event` |
| Sync mail to local archive | `gmail_archive_sync` |
| Archive single message | `gmail_archive_message` |
| Search local archive | `gmail_search_local` |

All data stays local: `.eml` files, SQLite, and Markdown exports live in `~/data/gmail/`. No server sync.

> **Reading email?** The [Gmail MCP Chrome extension](https://chromewebstore.google.com) already handles `search_threads`, `get_thread`, and label management well. This project adds the missing write operations and local persistence.

---

## Requirements

- Python 3.11+
- A Google account
- [Claude Code](https://claude.ai/code) or any MCP-compatible agent

---

## Installation

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/gmail_skill.git
cd gmail_skill
python3 -m venv .venv
.venv/bin/pip install -e .
```

### 2. Create Google Cloud credentials

You need a Google Cloud project with OAuth 2.0 credentials. This is a one-time setup (~5 minutes):

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a project
2. **APIs & Services → Library** → enable **Gmail API** and **Google Calendar API**
3. **OAuth consent screen** → External → add your Gmail as a test user
4. **Credentials → Create → OAuth 2.0 Client ID → Desktop app** → download JSON
5. Place the file at `~/.config/gmail_skill/credentials.json`:

```bash
mkdir -p ~/.config/gmail_skill
mv ~/Downloads/client_secret_*.json ~/.config/gmail_skill/credentials.json
```

### 3. Authenticate (one-time)

```bash
.venv/bin/python -c "
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path

SCOPES = ['https://www.googleapis.com/auth/gmail.modify',
          'https://www.googleapis.com/auth/calendar']
CONFIG = Path.home() / '.config/gmail_skill'

flow = InstalledAppFlow.from_client_secrets_file(
    str(CONFIG / 'credentials.json'), SCOPES,
    redirect_uri='urn:ietf:wg:oauth:2.0:oob')
auth_url, _ = flow.authorization_url(prompt='consent')
print('\nOpen this URL:\n\n' + auth_url + '\n')
code = input('Paste the code: ').strip()
flow.fetch_token(code=code)
(CONFIG / 'token.json').write_text(flow.credentials.to_json())
print('Done — token saved.')
"
```

Token is saved to `~/.config/gmail_skill/token.json` and refreshes automatically.

### 4. Register with Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "gmail-skill": {
      "command": "/absolute/path/to/gmail_skill/.venv/bin/gmail-skill",
      "args": []
    }
  }
}
```

Restart Claude Code. The tools will be available in every conversation.

---

## Local archive

Synced data lives in `~/data/gmail/`:

```
~/data/gmail/
  messages/     raw .eml files (one per message)
  markdowns/    AI-readable Markdown exports
  gmail.db      SQLite (messages, threads, labels)
```

Initial sync:
```
gmail_archive_sync(days_back=90, max_messages=500)
```

Daily refresh:
```
gmail_archive_sync(days_back=1)
```

---

## Skills file

Copy `skills/skill_gmail.md` to your agent's skills directory to give Claude a complete workflow guide for using these tools.

For Claude Code, place it anywhere in your project or vault and reference it in `CLAUDE.md`.

---

## Acknowledgements

Inspired by [grapeot/outlook_skill](https://github.com/grapeot/outlook_skill) — the same local-first, agent-native philosophy, adapted for Gmail.
