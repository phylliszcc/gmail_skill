# Agent Integration Guide

This document explains how to use `gmail_skill` as an AI agent.

## Available tools

The MCP server exposes 7 tools. All return JSON.

### Mail

**`gmail_send`** — send a new email
```json
{ "to": "alice@example.com", "subject": "Hello", "body": "...", "cc": "", "bcc": "" }
```

**`gmail_reply`** — reply to an existing thread
```json
{ "thread_id": "18abc...", "body": "...", "reply_all": false }
```
Set `reply_all: true` to CC all original recipients.

### Calendar

**`calendar_list_events`** — upcoming events
```json
{ "days_ahead": 7 }
```
Returns a list of `{id, title, start, end, location, attendees, link}`.

**`calendar_create_event`** — create event + send invites
```json
{
  "title": "Sync call",
  "start": "2026-06-01T10:00:00+08:00",
  "end":   "2026-06-01T11:00:00+08:00",
  "attendees": ["bob@example.com"],
  "description": "Quarterly review",
  "location": "Zoom",
  "timezone": "Asia/Shanghai",
  "send_notifications": true
}
```
`start`/`end` must be ISO 8601 with timezone offset.

### Archive

**`gmail_archive_sync`** — bulk sync recent messages to local storage
```json
{ "days_back": 7, "max_messages": 200 }
```
Downloads metadata + raw `.eml` + Markdown for each message.

**`gmail_archive_message`** — archive a single message by ID
```json
{ "message_id": "18abc123..." }
```

**`gmail_search_local`** — search the local SQLite archive
```json
{ "query": "invoice", "limit": 20 }
```
Searches subject, sender, and snippet. Returns `[{id, thread_id, subject, sender, date, snippet}]`.

---

## Standard workflows

### Read and reply
1. Use `search_threads` (Chrome MCP plugin) or `gmail_search_local` to find the thread
2. Use `get_thread` to read the full content
3. Draft a reply and show it to the user
4. **Only call `gmail_reply` after explicit user confirmation**

### Check calendar + schedule a meeting
1. `calendar_list_events(days_ahead=14)` to check availability
2. Confirm title, time, attendees with the user
3. `calendar_create_event(...)` — this sends invitations immediately

### Build and search local archive
```
# Initial sync
gmail_archive_sync(days_back=90, max_messages=500)

# Daily refresh
gmail_archive_sync(days_back=1)

# Offline search
gmail_search_local(query="budget proposal")
```

---

## Safety rules

- **Never send without explicit confirmation.** Always show the draft first.
- **Read the full thread** before drafting a reply. Never guess missing context.
- **Calendar events send notifications immediately.** Confirm attendees before creating.
- Use `reply_all: false` by default; only set `true` when the user explicitly requests it.

---

## Local data paths

| Path | Contents |
|------|----------|
| `~/.config/gmail_skill/credentials.json` | Google OAuth client (user-provided) |
| `~/.config/gmail_skill/token.json` | OAuth token (auto-generated, auto-refreshed) |
| `~/data/gmail/messages/` | Raw `.eml` files |
| `~/data/gmail/markdowns/` | Markdown exports |
| `~/data/gmail/gmail.db` | SQLite database |
