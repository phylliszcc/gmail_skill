"""MCP server: Gmail + Calendar tools."""
import asyncio
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from .gmail import send_email, reply_email, archive_message, archive_sync
from .calendar_api import list_events, create_event
from .storage import search_local

app = Server("gmail-skill")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="gmail_send",
            description="Send a new email via Gmail",
            inputSchema={
                "type": "object",
                "properties": {
                    "to":      {"type": "string", "description": "Recipient(s), comma-separated"},
                    "subject": {"type": "string"},
                    "body":    {"type": "string", "description": "Plain text body"},
                    "cc":      {"type": "string"},
                    "bcc":     {"type": "string"},
                },
                "required": ["to", "subject", "body"],
            },
        ),
        types.Tool(
            name="gmail_reply",
            description="Reply to a Gmail thread (set reply_all=true for reply-all)",
            inputSchema={
                "type": "object",
                "properties": {
                    "thread_id": {"type": "string"},
                    "body":      {"type": "string"},
                    "reply_all": {"type": "boolean", "default": False},
                },
                "required": ["thread_id", "body"],
            },
        ),
        types.Tool(
            name="calendar_list_events",
            description="List upcoming Google Calendar events",
            inputSchema={
                "type": "object",
                "properties": {
                    "days_ahead": {"type": "integer", "default": 7},
                },
            },
        ),
        types.Tool(
            name="calendar_create_event",
            description="Create a Google Calendar event; optionally invite attendees",
            inputSchema={
                "type": "object",
                "properties": {
                    "title":       {"type": "string"},
                    "start":       {"type": "string", "description": "ISO 8601, e.g. 2026-05-27T14:00:00+08:00"},
                    "end":         {"type": "string"},
                    "attendees":   {"type": "array", "items": {"type": "string"}},
                    "description": {"type": "string"},
                    "location":    {"type": "string"},
                    "timezone":    {"type": "string", "default": "Asia/Shanghai"},
                    "send_notifications": {"type": "boolean", "default": True},
                },
                "required": ["title", "start", "end"],
            },
        ),
        types.Tool(
            name="gmail_archive_sync",
            description="Download recent Gmail messages into local SQLite + .eml + Markdown",
            inputSchema={
                "type": "object",
                "properties": {
                    "days_back":    {"type": "integer", "default": 7},
                    "max_messages": {"type": "integer", "default": 200},
                },
            },
        ),
        types.Tool(
            name="gmail_archive_message",
            description="Archive a single Gmail message by message ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {"type": "string"},
                },
                "required": ["message_id"],
            },
        ),
        types.Tool(
            name="gmail_search_local",
            description="Search the local Gmail archive (SQLite) by keyword",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                },
                "required": ["query"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "gmail_send":
            result = send_email(
                to=arguments["to"],
                subject=arguments["subject"],
                body=arguments["body"],
                cc=arguments.get("cc", ""),
                bcc=arguments.get("bcc", ""),
            )
        elif name == "gmail_reply":
            result = reply_email(
                thread_id=arguments["thread_id"],
                body=arguments["body"],
                reply_all=arguments.get("reply_all", False),
            )
        elif name == "calendar_list_events":
            result = list_events(days_ahead=arguments.get("days_ahead", 7))
        elif name == "calendar_create_event":
            result = create_event(
                title=arguments["title"],
                start=arguments["start"],
                end=arguments["end"],
                attendees=arguments.get("attendees"),
                description=arguments.get("description", ""),
                location=arguments.get("location", ""),
                timezone=arguments.get("timezone", "Asia/Shanghai"),
                send_notifications=arguments.get("send_notifications", True),
            )
        elif name == "gmail_archive_sync":
            result = archive_sync(
                days_back=arguments.get("days_back", 7),
                max_messages=arguments.get("max_messages", 200),
            )
        elif name == "gmail_archive_message":
            result = archive_message(arguments["message_id"])
        elif name == "gmail_search_local":
            result = search_local(
                query=arguments["query"],
                limit=arguments.get("limit", 20),
            )
        else:
            result = {"error": f"unknown tool: {name}"}
    except Exception as e:
        result = {"error": str(e)}

    return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


def main():
    async def _run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(_run())
