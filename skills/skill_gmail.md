# Gmail Skill

Use this skill to manage Gmail via AI agents. It covers reading, sending, replying, calendar, and local archiving.

## Setup

1. Install [gmail_skill](https://github.com/YOUR_USERNAME/gmail_skill) and register the MCP server
2. Optionally install the [Gmail MCP Chrome extension](https://chromewebstore.google.com) for read operations

## Tools

### Read (Chrome MCP plugin — if installed)

| Tool | Usage |
|------|-------|
| `search_threads(query, pageSize?)` | Search Gmail |
| `get_thread(thread_id)` | Read full thread |
| `create_draft(to, subject, body, cc?)` | Save a draft |
| `list_labels()` / `label_thread()` | Manage labels |

### Write + Calendar (gmail_skill MCP server)

| Tool | Usage |
|------|-------|
| `gmail_send(to, subject, body, cc?, bcc?)` | Send new email |
| `gmail_reply(thread_id, body, reply_all?)` | Reply to thread |
| `calendar_list_events(days_ahead?)` | View schedule |
| `calendar_create_event(title, start, end, attendees?, description?, location?)` | Create event + invite |
| `gmail_archive_sync(days_back?, max_messages?)` | Sync to local archive |
| `gmail_archive_message(message_id)` | Archive one message |
| `gmail_search_local(query, limit?)` | Search local SQLite |

## Workflows

### Read and reply
1. `search_threads` to find the thread
2. `get_thread` to read it fully
3. Draft the reply and **show the user before sending**
4. Send only after explicit confirmation via `gmail_reply`

### Calendar
1. `calendar_list_events(days_ahead=14)` — check availability
2. `calendar_create_event` — confirm attendees first; invites go out immediately

### Local archive
```
gmail_archive_sync(days_back=90)   # initial setup
gmail_archive_sync(days_back=1)    # daily refresh
gmail_search_local("keyword")      # offline search
```

## Safety

- Always show the draft before sending. Never send without explicit confirmation.
- Read the full thread before drafting. Never guess missing context.
- `reply_all` defaults to `false` — only enable when explicitly requested.
- Calendar events send notifications immediately; confirm attendees before creating.
