import discord
import wavelink

from typing import cast
from discord import app_commands
from discord.ext import commands

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener("on_voice_state_update")
    async def voice_client(self, member, before, after):
        if not self.bot.voice_clients:
            return

        for guild in self.bot.guilds:
            player: wavelink.Player
            player = cast(wavelink.Player, guild.voice_client)
            
            if player:
                if len(guild.voice_client.channel.members) == 1 and guild.voice_client.channel.members[0].id == self.bot.user.id:
                    await player.disconnect()

                    embed = discord.Embed(
                        description=(
                            f"No hay usuarios activos. Dejando el canal de voz."
                        ),
                        color=discord.Color.red()
                    )

                    await player.home.send(
                       embed=embed
                    )

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        player: wavelink.Player | None = payload.player

        if not player:
            return

        track: wavelink.Playable = payload.track

        embed = discord.Embed(
            description=f"[**{track.title}**]({track.uri}) de `{track.author}`",
            color=discord.Color.red()
        )

        embed.set_author(
            name="Ahora reproduciendo",
            icon_url=player.author.display_avatar
        )

        if track.artwork:
            embed.set_thumbnail(
                url=track.artwork
            )

        duration = format_duration(track.length)

        embed.add_field(
            name="Duración",
            value=f"`{duration}`"
        )  

        embed.add_field(
            name="En cola",
            value=f"`{player.queue.count} canciones`"
        )  

        await player.home.send(
            embed=embed
        )
    
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackStartEventPayload):
        player: wavelink.Player | None = payload.player

        if not player:
            return

        if payload.reason == "replaced":
            return

        if not player.queue.is_empty:
            next_song = await player.queue.get_wait()
            await player.play(next_song, volume=80)
        else:
            await player.disconnect()

            embed = discord.Embed(
                description=(
                    f"No hay más canciones en cola. Dejando el canal de voz."
                ),
                color=discord.Color.red()
            )

            await player.home.send(
                embed=embed
            )

    @commands.hybrid_command(
        name="play",
        description="Reproduce una canción en el canal de voz",
        with_app_command=True,
        aliases=["p"]
    )
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    @app_commands.describe(canción="El nombre de la canción")
    async def play(self, ctx, *, canción: str):
        player: wavelink.Player
        player = cast(wavelink.Player, ctx.voice_client)

        if player:
            if ctx.author.voice:
                if (ctx.author.voice.channel != ctx.voice_client.channel):
                    await ctx.send(
                        content="Debes estar en el mismo canal de voz del bot para hacer esto.",
                        ephemeral=True
                    )
                    return
            else:
                await ctx.send(
                    content="Debes estar en el mismo canal de voz del bot para hacer esto.",
                    ephemeral=True
                )
                return

        if not player:
            try:
                player = await ctx.author.voice.channel.connect(cls=wavelink.Player, self_deaf=True)
            except AttributeError:
                await ctx.send(
                    content="Debes estar en un canal de voz para reproducir música.",
                    ephemeral=True
                )
                return
            except discord.ClientException:
                await ctx.send(
                    content="No he podido unirme al canal de voz. Por favor intenta nuevamente.",
                    ephemeral=True
                )
                return

        if not hasattr(player, "author"):
            player.author = ctx.author

        if not hasattr(player, "home"):
            player.home = ctx.channel

        tracks: wavelink.Search = await wavelink.Playable.search(canción, source=wavelink.TrackSource.YouTubeMusic)
        if not tracks:
            await ctx.send(
                content=f"No he encontrado ninguna canción con ese nombre. Por favor intenta nuevamente.",
                ephemeral=True
            )
            return

        if isinstance(tracks, wavelink.Playlist):
            added: int = await player.queue.put_wait(tracks)

            embed = discord.Embed(
                description=(
                    f"Playlist [**{tracks.name}**]({canción}) ({added} canciones) añadida a la cola."
                ),
                color=discord.Color.red()
            )

            await ctx.send(
                embed=embed
            )
        else:
            track: wavelink.Playable = tracks[0]
            await player.queue.put_wait(track)

            embed = discord.Embed(
                description=(
                    f"Canción [**{track.title}**]({track.uri}) añadida a la cola."
                ),
                color=discord.Color.red()
            )

            await ctx.send(
                embed=embed
            )
        
        if not player.playing:
            await player.play(player.queue.get(), volume=80)

    @commands.hybrid_command(
        name="skip",
        description="Salta la canción actual",
        with_app_command=True
    )
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    async def skip(self, ctx):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)

        if player:
            if ctx.author.voice:
                if (ctx.author.voice.channel != ctx.voice_client.channel):
                    await ctx.send(
                        content="Debes estar en el mismo canal de voz del bot para hacer esto.",
                        ephemeral=True
                    )
                    return
            else:
                await ctx.send(
                    content="Debes estar en el mismo canal de voz del bot para hacer esto.",
                    ephemeral=True
                )
                return
        else:
            await ctx.send(
                content="Debes estar en un canal de voz para hacer esto.",
                ephemeral=True
            )
            return

        if not player.queue.is_empty:
            await player.skip(force=True)

            embed = discord.Embed(
                description=(
                    f"La canción actual ha sido **saltada**."
                ),
                color=discord.Color.red()
            )
        else:
            await player.disconnect()

            embed = discord.Embed(
                description=(
                    f"La cola está **vacía**. Dejando el canal de voz."
                ),
                color=discord.Color.red()
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="back",
        description="Vuelve a la canción anterior de la cola",
        with_app_command=True
    )
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    async def back(self, ctx):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)

        if player:
            if ctx.author.voice:
                if (ctx.author.voice.channel != ctx.voice_client.channel):
                    await ctx.send(
                        content="Debes estar en el mismo canal de voz del bot para hacer esto.",
                        ephemeral=True
                    )
                    return
            else:
                await ctx.send(
                    content="Debes estar en el mismo canal de voz del bot para hacer esto.",
                    ephemeral=True
                )
                return
        else:
            await ctx.send(
                content="Debo encontrarme en un canal de voz para hacer esto.",
                ephemeral=True
            )
            return

        if not player.queue.history or len(player.queue.history) < 2:
            await ctx.send(
                content="No hay canciones reproducidas antes de la actual.",
                ephemeral=True
            )
            return
        
        previous_song = player.queue.history[-2]
        current_song = player.current

        embed = discord.Embed(
            description=(
                f"Volviendo a la canción **anterior**."
            ),
            color=discord.Color.red()
        )

        await ctx.send(embed=embed)
        player.queue.put_at(0, previous_song) 
        
        if current_song:
            player.queue.put_at(1, current_song) 
        await player.skip(force=True)

    @commands.hybrid_command(
        name="pause",
        description="Pausa la canción actual",
        with_app_command=True
    )
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    async def pause(self, ctx):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        
        if player:
            if ctx.author.voice:
                if (ctx.author.voice.channel != ctx.voice_client.channel):
                    await ctx.send(
                        content="Debes estar en el mismo canal de voz del bot para hacer esto.",
                        ephemeral=True
                    )
                    return
            else:
                await ctx.send(
                    content="Debes estar en el mismo canal de voz del bot para hacer esto.",
                    ephemeral=True
                )
                return
        else:
            await ctx.send(
                content="Debo encontrarme en un canal de voz para hacer esto.",
                ephemeral=True
            )
            return

        if player.paused:
            embed = discord.Embed(
                description=(
                    f"La canción actual ya se encuentra **pausada**."
                ),
                color=discord.Color.red()
            )

            await ctx.send(
                embed=embed
            )
            return

        await player.pause(True)

        embed = discord.Embed(
            description=(
                f"La canción actual ha sido **pausada**."
            ),
            color=discord.Color.red()
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="resume",
        description="Resume la canción actual",
        with_app_command=True
    )
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    async def resume(self, ctx):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        
        if player:
            if ctx.author.voice:
                if (ctx.author.voice.channel != ctx.voice_client.channel):
                    await ctx.send(
                        content="Debes estar en el mismo canal de voz del bot para hacer esto.",
                        ephemeral=True
                    )
                    return
            else:
                await ctx.send(
                    content="Debes estar en el mismo canal de voz del bot para hacer esto.",
                    ephemeral=True
                )
                return
        else:
            await ctx.send(
                content="Debo encontrarme en un canal de voz para hacer esto.",
                ephemeral=True
            )
            return

        if not player.paused:
            embed = discord.Embed(
                description=(
                    f"La canción actual no se encuentra **pausada**."
                ),
                color=discord.Color.red()
            )

            await ctx.send(
                embed=embed
            )
            return

        await player.pause(False)

        embed = discord.Embed(
            description=(
                f"La canción actual ha sido **resumida**."
            ),
            color=discord.Color.red()
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="stop",
        description="Limpia la lista de reproducción y deja el canal de voz",
        with_app_command=True
    )
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    async def stop(self, ctx):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)

        if player:
            if ctx.author.voice:
                if (ctx.author.voice.channel != ctx.voice_client.channel):
                    await ctx.send(
                        content="Debes estar en el mismo canal de voz del bot para hacer esto.",
                        ephemeral=True
                    )
                    return
            else:
                await ctx.send(
                    content="Debes estar en el mismo canal de voz del bot para hacer esto.",
                    ephemeral=True
                )
                return
        else:
            await ctx.send(
                content="Debo encontrarme en un canal de voz para hacer esto.",
                ephemeral=True
            )
            return

        await player.disconnect()

        embed = discord.Embed(
            description=(
                f"Limpiando la cola y dejando el canal de voz."
            ),
            color=discord.Color.red()
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="volume",
        description="Establece el volumen del reproductor de música",
        with_app_command=True
    )
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    @app_commands.describe(nivel="Nivel de volumen a establecer (0-200)")
    async def volume(self, ctx, nivel: int = None):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        
        if player:
            if ctx.author.voice:
                if (ctx.author.voice.channel != ctx.voice_client.channel):
                    await ctx.send(
                        content="Debes estar en el mismo canal de voz del bot para hacer esto.",
                        ephemeral=True
                    )
                    return
            else:
                await ctx.send(
                    content="Debes estar en el mismo canal de voz del bot para hacer esto.",
                    ephemeral=True
                )
                return
        else:
            await ctx.send(
                content="Debo encontrarme en un canal de voz para hacer esto.",
                ephemeral=True
            )
            return

        if nivel:
            if nivel > 200:
                await ctx.send(
                    content="No puedes establecer un volumen mayor a un **200**.",
                    ephemeral=True
                )
                return
            elif nivel < 0:
                await ctx.send(
                    content="No puedes establecer un volumen menor a un **0**.",
                    ephemeral=True
                )
                return
        else:
            nivel = 100

        await player.set_volume(nivel)

        embed = discord.Embed(
            description=(
                f"El volumen del reproductor de música ha sido establecido en **{nivel}**."
            ),
            color=discord.Color.red()
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="queue",
        description="Muestra la cola de reproducción",
        with_app_command=True,
        aliases=["cola", "q"]
    )
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    async def queue(self, ctx):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)

        if not player:
            await ctx.send(
                content="Debo encontrarme en un canal de voz para hacer esto.",
                ephemeral=True
            )
            return

        track: wavelink.Playable = player.queue.loaded
        if not track:
            await ctx.send(
                content="No hay una canción reproduciéndose actualmente ni hay canciones en cola.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            description=(
                f"Reproduciendo actualmente: [**{track.title}**]({track.uri}) de `{track.author}`"
                f" ({format_duration(track.length)})"
            ),
            color=discord.Color.red()
        )

        embed.set_author(
            name="Cola de reproducción",
            icon_url=ctx.bot.user.display_avatar
        )

        if track.artwork:
            embed.set_thumbnail(url=track.artwork)

        queue_text = ""
        for index, t in enumerate(player.queue[:5], start=1):
            queue_text += f"**{index}.** [**{t.title}**]({t.uri}) de `{t.author}` ({format_duration(t.length)})\n"

        total_duration = sum(t.length for t in player.queue)

        if queue_text:
            embed.add_field(name="🔻 Siguientes en la cola:", value=queue_text, inline=False)

        embed.set_footer(text=f"Canciones: {len(player.queue)} | Duración Total: {format_duration(total_duration)}")

        await ctx.send(embed=embed)

    @play.error
    async def play_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                content="Debes escribir el nombre de la canción que deseas reproducir."
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))

def pad_time_unit(unit):
    return f"{unit:02d}"

def format_duration(milliseconds):
    seconds = milliseconds // 1000
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    if days > 0:
        return f"{pad_time_unit(days)}:{pad_time_unit(hours)}:{pad_time_unit(minutes)}:{pad_time_unit(seconds)}"
    elif hours > 0:
        return f"{pad_time_unit(hours)}:{pad_time_unit(minutes)}:{pad_time_unit(seconds)}"
    elif minutes > 0:
        return f"{pad_time_unit(minutes)}:{pad_time_unit(seconds)}"
    else:
        return f"0:{pad_time_unit(seconds)}"