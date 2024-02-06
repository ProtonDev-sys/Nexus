import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp 
import datetime
from collections import deque
import asyncio
from utils.guild_data_management import GuildDataManager
import json

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = GuildDataManager()

    async def get_song_queue(self, guild_id):
        serialized_queue = self.data_manager.get_guild_setting(guild_id, 'song_queue', "[]")
        if isinstance(serialized_queue, str):
            return deque(json.loads(serialized_queue))  # Deserialize JSON and convert back to deque
        else:
            return deque(serialized_queue)  # If it's already a list, convert directly to deque


    async def set_song_queue(self, guild_id, queue):
        serialized_queue = json.dumps(list(queue))  # Convert deque to list and serialize to JSON
        self.data_manager.set_guild_setting(guild_id, 'song_queue', serialized_queue)

    async def get_current_playing(self, guild_id):
        return self.data_manager.get_guild_setting(guild_id, 'current_playing', None)

    async def set_current_playing(self, guild_id, url):
        self.data_manager.set_guild_setting(guild_id, 'current_playing', url)

    @app_commands.command(name='join', description='Tells the bot to join the voice channel')
    async def join(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        if not ctx.message.author.voice:
            await ctx.send(f"{ctx.message.author.name} is not connected to a voice channel")
            return

        channel = ctx.author.voice.channel
        await channel.connect()

    @app_commands.command(name='play', description='Plays a song from a URL or search query')
    @app_commands.describe(query='The URL or search query of the song to play')
    async def play(self, interaction: discord.Interaction, query: str):
        guild_id = interaction.guild_id
        ctx = await commands.Context.from_interaction(interaction)
        
        # Check if query is a URL or search term
        if not query.startswith("http://") and not query.startswith("https://"):
            await interaction.response.send_message(f"Processing your request for: {query}")
            query = f"ytsearch:{query}"
        else:
            await interaction.response.send_message(f"Processing your request for: {query}")

        song_queue = await self.get_song_queue(guild_id)
        if not song_queue:
            await self.set_song_queue(guild_id, deque())

        # Fetch song details and send embed
        song_url = await self.search_youtube(query)
        if song_url:
            song_queue = await self.get_song_queue(guild_id)
            song_queue.append(song_url)
            await self.set_song_queue(guild_id, song_queue)
            await self.send_song_embed(ctx, song_url)

            vc = ctx.voice_client
            if not vc:
                channel = ctx.author.voice.channel
                await channel.connect()
            vc = ctx.voice_client
            if not vc.is_playing():
                await self.start_playing(ctx)
        else:
            await interaction.response.send_message("Could not find any song matching the query.")

    async def search_youtube(self, query):
        with yt_dlp.YoutubeDL({'quiet': True, 'format': 'bestaudio', 'noplaylist':'True'}) as ydl:
            try:
                info = ydl.extract_info(query, download=False)
                if 'entries' in info:
                    # Take the first search result
                    return info['entries'][0]['webpage_url']
                else:
                    return info['webpage_url']
            except Exception as e:
                self.logger.error(f"Error searching YouTube: {e}")
                return None

        

    async def send_song_embed(self, ctx, url):
        guild_id = ctx.guild.id
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title')
            duration = str(datetime.timedelta(seconds=info.get('duration')))
            uploader = info.get('uploader')
            uploader_url = info.get('channel_url')  # URL of the uploader's channel
            thumbnail_url = info.get('thumbnail')
            song_queue = await self.get_song_queue(guild_id)
            position_in_queue = len(song_queue)

        # Format the title and uploader as clickable hyperlinks
        title_link = f"[{title}]({url})"
        uploader_link = f"[{uploader}]({uploader_url})" if uploader_url else uploader

        embed = discord.Embed(title="Added to the Queue", description=title_link, color=discord.Color.blue())
        embed.add_field(name="Channel", value=uploader_link, inline=False)
        embed.add_field(name="Duration", value=duration, inline=False)
        embed.add_field(name="Position in Queue", value=position_in_queue, inline=False)
        embed.set_thumbnail(url=thumbnail_url)
        await ctx.send(embed=embed)


    async def start_playing(self, ctx):
        guild_id = ctx.guild.id
        song_queue = await self.get_song_queue(guild_id)
        vc = ctx.voice_client

        if song_queue:
            url = song_queue.pop()
            await self.set_song_queue(guild_id, song_queue)
            await self.set_current_playing(guild_id, url)
            YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
            FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
                url2 = info['url']
                source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
                vc.play(source, after=lambda e: self.pointer_next_song(ctx))

            # Optionally, send a message that the bot is starting to play the song
            await ctx.send(f"Now playing: {info['title']}")
        else:
            await ctx.send("The queue is empty.")

    async def play_next_song(self, ctx):
        guild_id = ctx.guild.id
        vc = ctx.voice_client
        await self.set_current_playing(guild_id, " ")
        # Play the next song in the queue, if available
        song_queue = await self.get_song_queue(guild_id)
        if song_queue:
            await self.start_playing(ctx)
    
    def pointer_next_song(self, ctx):
        asyncio.run_coroutine_threadsafe(self.play_next_song(ctx), self.bot.loop)

    @app_commands.command(name='pause', description='Pauses/resumes the currently playing song')
    async def pause(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        vc = ctx.voice_client

        if vc:
            if vc.is_playing():
                vc.pause()
                await ctx.send("Paused the currently playing song.")
            elif vc.is_paused():
                vc.resume()
                await ctx.send("Resumed the song.")
            else:
                await ctx.send("No song is currently playing or paused.")
        else:
            await ctx.send("Not connected to a voice channel.")

    @app_commands.command(name='seek', description='Seeks to a specific time in the currently playing song')
    @app_commands.describe(seconds='Number of seconds to seek')
    async def seek(self, interaction: discord.Interaction, seconds: int):
        ctx = await commands.Context.from_interaction(interaction)
        vc = ctx.voice_client

        if vc and vc.is_playing():
            
            url = self.current_playing_url[ctx.guild.id]  # URL of the currently playing song
            if not url:
                return
            vc.stop()
            # Format seconds into hh:mm:ss
            seek_time = str(datetime.timedelta(seconds=seconds))

            FFMPEG_OPTIONS = {
                'before_options': f'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss {seek_time}',
                'options': '-vn'
            }

            # Extract audio using yt-dlp
            YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
                url2 = info['url']
                source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
                vc.play(source)

            await ctx.send(f"Seeked to {seek_time} in the current song.")
        else:
            await ctx.send("No audio is currently playing.")

    @app_commands.command(name='stop', description='Stops the current song and clears the queue')
    async def stop(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        vc = ctx.voice_client
        if vc:
            vc.disconnect()
            self.set_song_queue(ctx.guild.id, deque())

    @app_commands.command(name='skip', description='Skips the currently playing song')
    async def skip(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        vc = interaction.guild.voice_client

        if vc and vc.is_playing():
            vc.stop()  # This will trigger the after callback to play the next song
            await interaction.response.send_message("Skipped the current song.")
        else:
            await interaction.response.send_message("No song is currently playing.")
    



async def setup(bot):
    cog = MusicCog(bot)
    await bot.add_cog(cog)

    # Register the commands for a specific guild
    guild = discord.Object(id=1203047551813816380)  
    bot.tree.add_command(cog.play, guild=guild)
    bot.tree.add_command(cog.seek, guild=guild)
    bot.tree.add_command(cog.skip, guild=guild)
    bot.tree.add_command(cog.stop, guild=guild)
    bot.tree.add_command(cog.join, guild=guild)