import os
import discord
from discord.ext import commands
from discord.ext.commands.errors import NoEntryPointError, ExtensionAlreadyLoaded

async def load_cogs(bot: commands.Bot):
    for filename in os.listdir("./src/cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension("src.cogs." + filename.removesuffix(".py"))
                print(f"\u001b[34;1m[Discord] Cog cargado: \"{filename}\"")
            except ExtensionAlreadyLoaded:
                return
            except NoEntryPointError:
                print(f"\033[1;31m[Discord] Omitiendo \"{filename}\" ya que no tiene función de configuración")
            except Exception as e:
                print(f"\033[1;31m[Discord] Error en la carga de la extensión \"{filename}\":", e)