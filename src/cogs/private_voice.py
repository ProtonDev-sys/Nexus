import discord
from discord import app_commands
from discord.ext import commands
import logging

class PrivateVoice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel is not None and "private" in before.channel.name and before.channel.name != "create-private":
            if len(before.channel.members) == 0:
                await before.channel.delete()

    @app_commands.command(name='private-voice', description='Create a private voice channel.')
    async def private_voice(self, interaction: discord.Interaction, limit: int):
        if interaction.user.voice.channel is not None and interaction.user.voice.channel.name == "create-private":
            channel = await interaction.guild.create_voice_channel(f"private {interaction.user.name}", category=interaction.user.voice.channel.category, user_limit=limit)
            await interaction.response.send_message(f"Channel created, <#{channel.id}>")
            await channel.set_permissions(interaction.user, manage_channels=True, kick_members=True, manage_permissions=True)
            await interaction.user.move_to(channel)

async def setup(bot):
    cog = PrivateVoice(bot)
    await bot.add_cog(cog)
    guild = discord.Object(id=1203047551813816380)  
    bot.tree.add_command(cog.private_voice, guild=guild)
