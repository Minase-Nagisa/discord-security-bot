# main.py
# Discord Security Bot with SQLite Logging and Auto Security Channel Creation

import discord
from discord.ext import commands
import sqlite3
import asyncio

# ---- CONFIG ----
SECURITY_CHANNEL_NAME = "security-log"
BAD_WORDS = ["nuke", "raid", "destroy", "@everyone", "荒らし", "荒らし予告"]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---- DATABASE SETUP ----
conn = sqlite3.connect("logs.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    user_name TEXT,
    event_type TEXT,
    details TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

def log_event(user_id, user_name, event_type, details=""):
    cursor.execute(
        "INSERT INTO logs (user_id, user_name, event_type, details) VALUES (?, ?, ?, ?)",
        (user_id, user_name, event_type, details)
    )
    conn.commit()

# ---- HELPER ----
async def ensure_security_channel(guild):
    channel = discord.utils.get(guild.channels, name=SECURITY_CHANNEL_NAME)
    if channel:
        return channel
    channel = await guild.create_text_channel(SECURITY_CHANNEL_NAME)
    return channel

# ---- EVENTS ----
@bot.event\async def on_ready():
    print(f"Bot logged in as {bot.user}")
    for guild in bot.guilds:
        channel = await ensure_security_channel(guild)
        await channel.send("Security Bot is now online.")
        log_event("SYSTEM", "BOT", "startup", f"Started in guild {guild.name}")

@bot.event\async def on_member_join(member):
    log_event(str(member.id), member.name, "join")
    channel = await ensure_security_channel(member.guild)
    await channel.send(f"🟢 User Joined: {member.name} ({member.id})")

@bot.event\async def on_member_remove(member):
    log_event(str(member.id), member.name, "leave")
    channel = await ensure_security_channel(member.guild)
    await channel.send(f"🔴 User Left: {member.name} ({member.id})")

@bot.event\async def on_guild_channel_delete(channel):
    if channel.name == SECURITY_CHANNEL_NAME:
        guild = channel.guild
        new_channel = await ensure_security_channel(guild)
        await new_channel.send("⚠ security-log was deleted. It has been restored.")
        log_event("SYSTEM", "BOT", "channel_restore", "security-log restored")

@bot.event\async def on_message(message):
    if message.author.bot:
        return
    content = message.content.lower()
    if any(w in content for w in BAD_WORDS):
        log_event(str(message.author.id), message.author.name, "bad_message", message.content)
        channel = await ensure_security_channel(message.guild)
        await channel.send(f"⚠ Suspicious Message by {message.author}: {message.content}")
    await bot.process_commands(message)

# ---- RUN ----
import os
TOKEN = os.getenv("BOT_TOKEN")
bot.run(TOKEN)
