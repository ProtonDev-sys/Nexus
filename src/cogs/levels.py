from discord.ext import commands
import discord
from discord import app_commands
from utils.guild_data_management import GuildDataManager
import random
import datetime

class XPCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = GuildDataManager()
        self.last_xp_award = {}  # Store the last time a user was awarded XP

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        now = datetime.datetime.utcnow()
        user_id = str(message.author.id)
        last_award_time = self.last_xp_award.get(user_id, datetime.datetime.utcfromtimestamp(0))

        if (now - last_award_time).total_seconds() > 60:  # 1 minute cooldown
            xp_gain = random.randint(3, 6)  # Random XP between 3 and 6
            await self.award_xp(message.guild.id, user_id, xp_gain, message.channel)
            self.last_xp_award[user_id] = now

    async def award_xp(self, guild_id, user_id, xp_gain, message_channel):
        guild_xp_data = self.data_manager.get_guild_setting(guild_id, 'xp_data', {})
        user_data = guild_xp_data.get(user_id, {'xp': 0, 'level': 0})
        
        current_xp = user_data['xp'] + xp_gain
        current_level = user_data['level']
        next_level_xp = self.xp_for_next_level(current_level)

        if next_level_xp <= current_xp:
            current_level += 1  # Level up
            current_xp = 0  # Reset XP
            level_up_channel_id = self.data_manager.get_guild_setting(guild_id, 'level_up_channel', None)
            if level_up_channel_id:
                level_up_channel = self.bot.get_channel(int(level_up_channel_id))
                if level_up_channel:
                    await level_up_channel.send(f"Congratulations {message_channel.guild.get_member(int(user_id)).mention}! You've leveled up to level {current_level}!")
            else:
                await message_channel.send(f"Congratulations {message_channel.guild.get_member(int(user_id)).mention}! You've leveled up to level {current_level}!")

        user_data.update({'xp': current_xp, 'level': current_level})
        guild_xp_data[user_id] = user_data
        self.data_manager.set_guild_setting(guild_id, 'xp_data', guild_xp_data)

    def xp_for_next_level(self, current_level):
        # Exponential growth formula for level progression
        return 5 * (current_level ** 2) + 50

    @app_commands.command(name='setlevelupchannel', description='Set the channel for level-up announcements.')
    @app_commands.describe(channel='The channel where level-up messages will be sent')
    async def set_level_up_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.data_manager.set_guild_setting(interaction.guild_id, 'level_up_channel', str(channel.id))
        await interaction.response.send_message(f"Level-up announcements will be sent to: {channel.mention}")

    @app_commands.command(name='myxp', description='Check your XP and level.')
    async def myxp(self, interaction: discord.Interaction):
        guild_xp_data = self.data_manager.get_guild_setting(interaction.guild_id, 'xp_data', {})
        user_id = str(interaction.user.id)
        user_data = guild_xp_data.get(user_id, {'xp': 0, 'level': 0})

        xp = user_data.get('xp', 0)
        level = user_data.get('level', 0)

        await interaction.response.send_message(f"You have {xp} XP and are at level {level}.")


async def setup(bot):
    cog = XPCog(bot)
    await bot.add_cog(cog)
    guild = discord.Object(id=1203047551813816380)  
    bot.tree.add_command(cog.myxp, guild=guild)
    bot.tree.add_command(cog.set_level_up_channel, guild=guild)
