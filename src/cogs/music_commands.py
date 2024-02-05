import discord
from discord.ext import commands
import yt_dlp 
import os

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = {}

    @commands.command(name='join', help='Tells the bot to join the voice channel')
    async def join(self, ctx):
        if not ctx.message.author.voice:
            await ctx.send(f"{ctx.message.author.name} is not connected to a voice channel")
            return

        channel = ctx.author.voice.channel
        await channel.connect()

    @commands.command(name='play', help='Plays a selected song from YouTube')
    async def play(self, ctx, url):
        vc = ctx.voice_client
        if not vc:
            if not ctx.message.author.voice:
                await ctx.send(f"{ctx.message.author.name} is not connected to a voice channel")
                return
            else:
                channel = ctx.author.voice.channel
        await channel.connect()

        try:
            # Setting download options
            YDL_OPTIONS = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': 'downloads/tempfile.%(ext)s',  # Controlled filename
                'restrictfilenames': True
            }
            vc = ctx.voice_client

            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                ydl.extract_info(url, download=True)
                filename = 'downloads/tempfile.mp3'  # Fixed filename

                source = discord.FFmpegPCMAudio(filename)
                vc.play(source, after=lambda e: os.remove(filename) if os.path.exists(filename) else None)


        except Exception as e:
            await ctx.send("There was an error processing your request.")
            print(f"Error: {e}")


    @commands.command(name='pause', help='Pauses/resumes the currently playing song')
    async def pause(self, ctx):
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


    # Add other music commands (pause, resume, stop, etc.) here




async def setup(bot):
    await bot.add_cog(MusicCog(bot))