import discord
from discord.ext import commands, tasks
import random
import os
import asyncio
import logging

class VoiceTrolling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.task_started = False
        self.logger = logging.getLogger(__name__)

    def cog_unload(self):
        self.voice_troll.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.task_started:
            self.task_started = True
            self.voice_troll.start()

    @tasks.loop(seconds=30) 
    async def voice_troll(self):
        if random.randint(1, 100) != 2:
            return
        if 1 == 1:
            return
        
        for guild in self.bot.guilds:
            non_empty_channels = [vc for vc in guild.voice_channels if len(vc.members) > 0]

            if non_empty_channels:
                voice_channel = random.choice(non_empty_channels)
                try:
                    was_playing = False
                    if guild.voice_client and guild.voice_client.is_playing():
                        # Bot is already in a voice channel and playing
                        was_playing = True
                        guild.voice_client.pause()

                    vc = await voice_channel.connect()
                    sound_files = os.listdir('src/sounds')
                    sound_file = random.choice(sound_files)
                    self.logger.info(f"Joining {voice_channel.name} playing {sound_file}")
                    sound_path = os.path.join('src/sounds', sound_file)
                    vc.play(discord.FFmpegPCMAudio(source=sound_path))
                    while vc.is_playing():
                        await asyncio.sleep(1)
                    self.logger.info(f"Disconnecting from {voice_channel.name}")
                    
                    if was_playing:
                        guild.voice_client.resume()
                    else:
                        await vc.disconnect()

                except Exception as e:
                    self.logger.error(f"Error in voice trolling task {e}")
            else:
                self.logger.info("No non-empty voice channels found.")


async def setup(bot):
    await bot.add_cog(VoiceTrolling(bot))
    
