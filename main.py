import discord
import wavelink

import os
import sys
import logging

from dotenv import load_dotenv
from discord.ext import commands
from src.utils.loader import load_cogs
from src.utils.wavelink import node_connect

load_dotenv()
token = os.getenv("TOKEN")

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None,
    chunk_guilds_at_startup=False,
    max_ratelimit_timeout=30.0,
    case_insensitive=True,
    strip_after_prefix=True
)

if not token:
    print("\033[1;31m[Dotenv] El token no está configurado como una variable de entorno")
    sys.exit(1)

@bot.event
async def on_ready():
    print(f"\u001b[34;1m[Discord] Iniciado como {bot.user}")
    await load_cogs(bot)
    await node_connect(bot)

@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f"\u001b[32;1m[Wavelink] Iniciado como: {node.session_id}")

if __name__ == "__main__":
    bot.run(token=token, log_handler=handler)