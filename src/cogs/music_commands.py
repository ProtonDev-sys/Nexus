import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
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

    async def add_to_queue(self, guild_id, song_info):
        # Retrieve the current queue for the guild
        song_queue = await self.get_song_queue(guild_id)

        # Append the new song details to the queue
        song_queue.append(song_info)

        # Save the updated queue
        await self.set_song_queue(guild_id, song_queue)

    async def fetch_song_details(self, song_url):
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(song_url, download=False)
                song_info = {
                    'title': info.get('title', 'Unknown Title'),
                    'url': info.get('webpage_url', '#'),
                    'duration': info.get('duration', 0),
                    'channel': info.get('channel', 'Unknown Channel'),
                    'channel_url': info.get('channel_url', 'Unknown Channel'),
                    'thumbnail': info.get('thumbnail', '')
                }
                return song_info
            except Exception as e:
                print(f"Error fetching song details: {e}")
                return None


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
        await interaction.response.defer()
        guild_id = interaction.guild_id
        ctx = await commands.Context.from_interaction(interaction)

        # Check if query is a URL or search term
        if not query.startswith("http://") and not query.startswith("https://"):
            query = f"ytsearch:{query}"

        # Fetch song details
        song_info = await self.search_youtube(query)
        if song_info:
            await self.add_to_queue(guild_id, song_info)
            await self.send_song_embed(ctx, song_info)

            vc = ctx.voice_client
            if not vc:
                channel = ctx.author.voice.channel
                await channel.connect()
            vc = ctx.voice_client
            if not vc.is_playing():
                await self.start_playing(ctx)
        else:
            await interaction.response.send_message("Error fetching song details.")



    async def search_youtube(self, query):
        ydl_opts = {'quiet': True, 'format': 'bestaudio', 'noplaylist': 'True', 'default_search': 'auto'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(query, download=False)
                if 'entries' in info:
                    # Take the first search result
                    info = info['entries'][0]
                return {
                    'title': info.get('title', 'Unknown Title'),
                    'url': info.get('webpage_url', '#'),
                    'duration': info.get('duration', 0),
                    'channel': info.get('channel', 'Unknown Channel'),
                    'channel_url': info.get('channel_url', 'Unknown Channel'),
                    'thumbnail': info.get('thumbnail', '')
                }
            except Exception as e:
                self.logger.error(f"Error searching YouTube: {e}")
                return None

    async def send_song_embed(self, ctx, song_info):
        guild_id = ctx.guild.id

        title = song_info.get('title', 'Unknown Title')
        duration = str(datetime.timedelta(seconds=song_info.get('duration', 0)))
        channel = song_info.get('channel', 'Unknown Channel')
        channel_url = song_info.get('channel_url', '')
        thumbnail_url = song_info.get('thumbnail', '')
        song_queue = await self.get_song_queue(guild_id)
        position_in_queue = len(song_queue)

        # Create clickable links
        title_link = f"[{title}]({song_info['url']})"
        channel_link = f"[{channel}]({channel_url})" if channel_url else channel

        embed = discord.Embed(title="Added to the Queue", description=title_link, color=discord.Color.blue())
        embed.add_field(name="Channel", value=channel_link, inline=False)
        embed.add_field(name="Duration", value=duration, inline=False)
        embed.add_field(name="Position in Queue", value=position_in_queue, inline=False)
        embed.set_thumbnail(url=thumbnail_url)
        await ctx.send(embed=embed)

    async def start_playing(self, ctx):
        
        guild_id = ctx.guild.id
        song_queue = await self.get_song_queue(guild_id)
        vc = ctx.voice_client
        self.data_manager.set_guild_setting(guild_id, 'vote_skips', {})
        if song_queue:
            song_info = song_queue.popleft()  # Remove the first song from the queue
            await self.set_song_queue(guild_id, song_queue)  # Update the queue in the database
            url = song_info['url']
            await self.set_current_playing(guild_id, url)

            YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
            FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
                url2 = info['url']
                source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
                vc.play(source, after=lambda e: self.pointer_next_song(ctx))

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

    @app_commands.command(name='skip', description='Vote to skip the current song.')
    async def skip(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        vote_skips = self.data_manager.get_guild_setting(guild_id, 'vote_skips', {})

        vc = interaction.guild.voice_client
        if vc is None or not vc.is_playing():
            await interaction.response.send_message("No song is currently playing.")
            return

        member_count = len([member for member in vc.channel.members if not member.bot])  # Count members, excluding bots
        vote_skips[str(interaction.user.id)] = True

        votes = len(vote_skips)
        required_votes = member_count // 2 + 1  # More than half of the members need to vote

        if votes >= required_votes:
            vc.stop()  # Stop the current song
            self.data_manager.set_guild_setting(guild_id, 'vote_skips', {})  # Reset the votes
            await interaction.response.send_message("Vote passed. Skipping the song.")
        else:
            self.data_manager.set_guild_setting(guild_id, 'vote_skips', vote_skips)  # Save the updated vote_skips data
            await interaction.response.send_message(f"Vote to skip added. {votes}/{required_votes} votes.")

    async def is_dj_or_staff(self, interaction: discord.Interaction):
        """Check if the user has the DJ role or required permission."""
        has_permission = interaction.user.guild_permissions.manage_guild
        dj_role = discord.utils.get(interaction.guild.roles, name="DJ")
        has_dj_role = dj_role in interaction.user.roles if dj_role else False
        
        return has_permission or has_dj_role

    @app_commands.command(name='forceskip', description='Force skip the current song.')
    async def forceskip(self, interaction: discord.Interaction):
        if not await self.is_dj_or_staff(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
        vc = interaction.guild.voice_client
        if vc is None or not vc.is_playing():
            await interaction.response.send_message("No song is currently playing.")
            return

        vc.stop()
        if interaction.guild_id in self.vote_skips:
            self.vote_skips[interaction.guild_id].clear()
        await interaction.response.send_message("Song skipped by staff member.")


    @app_commands.command(name='queue', description='Displays the current music queue.')
    async def queue(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        song_queue = await self.get_song_queue(guild_id)

        if not song_queue:
            await interaction.response.send_message("The queue is currently empty.")
            return

        # Preparing the queue embed
        embed = self.create_queue_embed(song_queue, page=1)
        view = QueueView(song_queue, self.create_queue_embed)
        await interaction.response.send_message(embed=embed, view=view)

    def create_queue_embed(self, queue, page=1):
        embed = discord.Embed(title="Music Queue", color=discord.Color.blue())
        items_per_page = 8
        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue_list = list(queue)[start:end]

        for i, song_info in enumerate(queue_list, start=start + 1):
            title = song_info.get('title', 'Unknown Title')
            url = song_info.get('url', '#')
            duration = str(datetime.timedelta(seconds=song_info.get('duration', 0)))

            # Truncate title if it's too long
            if len(title) > 40:
                title = title[:37]

            # Format the string to have the clickable title and duration
            song_display = f"[{title.replace("[","").replace("]","")}]({url}) duration: `{duration}`"

            embed.add_field(name=f"", value=song_display, inline=False)

        total_pages = ((len(queue) - 1) // items_per_page) + 1
        embed.set_footer(text=f"Page {page} of {total_pages}")
        return embed

class QueueView(discord.ui.View):
    def __init__(self, queue, embed_creator):
        super().__init__()
        self.queue = queue
        self.embed_creator = embed_creator
        self.current_page = 1
        self.max_page = ((len(queue) - 1) // 8) + 1
        # Adding buttons
        self.add_item(PreviousButton())
        self.add_item(NextButton())

    async def update_embed(self, interaction: discord.Interaction):
        embed = self.embed_creator(self.queue, self.current_page)
        await interaction.response.edit_message(embed=embed, view=self)

class PreviousButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Previous", style=discord.ButtonStyle.grey)

    async def callback(self, interaction: discord.Interaction):
        view: QueueView = self.view
        view.current_page = max(1, view.current_page - 1)
        await view.update_embed(interaction)

class NextButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Next", style=discord.ButtonStyle.grey)

    async def callback(self, interaction: discord.Interaction):
        view: QueueView = self.view
        view.current_page = min(1, view.max_page+ 1)
        await view.update_embed(interaction)

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
    bot.tree.add_command(cog.queue, guild=guild)
    bot.tree.add_command(cog.forceskip, guild=guild)