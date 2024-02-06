import discord
from discord.ext import commands
from discord import app_commands
from utils.guild_data_management import GuildDataManager

class WelcomeGoodbyeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = GuildDataManager()

    @app_commands.command(name='setwelcomechannel', description='Set the welcome channel for the server.')
    @app_commands.describe(channel='The channel to set as the welcome channel')
    async def set_welcome_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.data_manager.set_guild_setting(interaction.guild_id, 'welcome_channel', channel.id)
        await interaction.response.send_message(f"Welcome channel set to: {channel.mention}")

    @app_commands.command(name='setleavechannel', description='Set the leave channel for the server.')
    @app_commands.describe(channel='The channel to set as the leave channel')
    async def set_leave_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.data_manager.set_guild_setting(interaction.guild_id, 'leave_channel', channel.id)
        await interaction.response.send_message(f"Leave channel set to: {channel.mention}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        welcome_channel_id = self.data_manager.get_guild_setting(member.guild.id, 'welcome_channel')
        if welcome_channel_id:
            channel = member.guild.get_channel(welcome_channel_id)
            if channel:
                await channel.send(f"Welcome to the server, {member.mention}! 🎉")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        leave_channel_id = self.data_manager.get_guild_setting(member.guild.id, 'leave_channel')
        if leave_channel_id:
            channel = member.guild.get_channel(leave_channel_id)
            if channel:
                await channel.send(f"Goodbye {member.display_name}, we will miss you! 👋")

async def setup(bot):
    welcome_cog = WelcomeGoodbyeCog(bot)
    await bot.add_cog(welcome_cog)
    guild = discord.Object(1203047551813816380)
    bot.tree.add_command(welcome_cog.set_welcome_channel, guild=guild)
    bot.tree.add_command(welcome_cog.set_leave_channel, guild=guild)
