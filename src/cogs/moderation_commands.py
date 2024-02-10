import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
from utils.guild_data_management import GuildDataManager

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = GuildDataManager()
        self.task_started = False

    def cog_unload(self):
        self.check_bans.cancel()

    async def unban_expired_users(self):
        current_time = datetime.datetime.utcnow()
        for guild_id in self.bot.guilds:
            guild_bans = self.data_manager.get_guild_setting(guild_id.id, 'temp_bans', {})
            for user_id, unban_time in list(guild_bans.items()):
                if datetime.datetime.fromisoformat(unban_time) <= current_time:
                    user = await self.bot.fetch_user(int(user_id))
                    await guild_id.unban(user)
                    del guild_bans[user_id]
            self.data_manager.set_guild_setting(guild_id.id, 'temp_bans', guild_bans)

    async def unmute_expired_users(self):
        current_time = datetime.datetime.utcnow()
        for guild in self.bot.guilds:
            temp_mutes = self.data_manager.get_guild_setting(guild.id, 'temp_mutes', '{}')
            temp_mutes_dict = temp_mutes

            # Accumulate member IDs to be unmuted
            members_to_unmute = []
            for member_id, unmute_time_str in temp_mutes_dict.items():
                unmute_time = datetime.datetime.fromisoformat(unmute_time_str)
                if current_time >= unmute_time:
                    members_to_unmute.append(member_id)

            # Process unmutes
            for member_id in members_to_unmute:
                member = guild.get_member(int(member_id))
                if member:
                    muted_role = discord.utils.get(guild.roles, name='Muted')
                    await member.remove_roles(muted_role, reason="Temporary mute duration ended")
                    del temp_mutes_dict[member_id]

            # Save updated mutes list
            self.data_manager.set_guild_setting(guild.id, 'temp_mutes', temp_mutes_dict)



    @commands.Cog.listener()
    async def on_ready(self):
        if not self.task_started:
            self.task_started = True
            self.check_bans_and_mutes.start()

    @tasks.loop(minutes=1)
    async def check_bans_and_mutes(self):
        await self.unban_expired_users()
        await self.unmute_expired_users()

    @app_commands.command(name="ban", description="Ban a user from the server.")
    @app_commands.describe(user="User to ban", duration="Duration in minutes (0 for permanent)", reason="Reason for banning")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.User, duration: int = 0, reason: str = "No reason provided"):
        member = interaction.guild.get_member(user.id)
        if member:
            try:
                await member.send(f"You have been banned from {interaction.guild.name} for: {reason}")
            except discord.HTTPException:
                pass  # User has DMs closed or has blocked the bot
        await interaction.guild.ban(user, reason=reason, delete_message_days=0)


        if duration > 0:
            unban_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=duration)
            guild_bans = self.data_manager.get_guild_setting(interaction.guild.id, 'temp_bans', {})
            guild_bans[str(user.id)] = unban_time.isoformat()
            self.data_manager.set_guild_setting(interaction.guild.id, 'temp_bans', guild_bans)

        await interaction.response.send_message(f'{user.mention} has been banned.')


    @app_commands.command(name="unban", description="Unban a user from the server.")
    @app_commands.describe(user_id="ID of the user to unban")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str):
        user = await self.bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        await interaction.response.send_message(f'Unbanned {user.mention}')


    @app_commands.command(name="kick", description="Kick a user from the server.")
    @app_commands.describe(member="Member to kick", reason="Reason for kicking")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        try:
            await member.send(f"You have been kicked from {interaction.guild.name} for: {reason}")
        except discord.HTTPException:
            pass  # User has DMs closed or has blocked the bot
        await member.kick(reason=reason)
        await interaction.response.send_message(f'{member.mention} has been kicked.')


    @app_commands.command(name='mute', description='Mute a member in the server.')
    @app_commands.describe(member='Member to mute', duration='Duration of the mute in minutes', reason='Reason for muting')
    @app_commands.checks.has_permissions(manage_roles=True)
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "No reason provided"):
        muted_role = discord.utils.get(interaction.guild.roles, name='Muted')
        if not muted_role:
            # Create Muted role if it doesn't exist (with no permissions)
            muted_role = await interaction.guild.create_role(name='Muted', reason="Automatic muted role creation")
            # Update channel overrides to mute the role
            for channel in interaction.guild.channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False, add_reactions=False)

        await member.add_roles(muted_role, reason="Muted by command")
        await interaction.response.send_message(f"{member.mention} has been muted.")
        try:
            await member.send(f"You have been muted in {interaction.guild.name} for {duration} minutes. Reason: {reason}")
        except discord.HTTPException:
            pass
        if duration:
            unmute_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=duration)
            self.add_temp_mute(interaction.guild.id, member.id, unmute_time)

    @app_commands.command(name='unmute', description='Unmute a member in the server.')
    @app_commands.describe(member='Member to unmute', reason='Reason for unmuting')
    @app_commands.checks.has_permissions(manage_roles=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        # Remove the mute role from the member
        muted_role = discord.utils.get(interaction.guild.roles, name='Muted')
        if muted_role in member.roles:
            await member.remove_roles(muted_role, reason="Manually unmuted")

            # Update the temp mutes in the database
            temp_mutes = self.data_manager.get_guild_setting(interaction.guild.id, 'temp_mutes', '{}')
            temp_mutes_dict = temp_mutes
            if str(member.id) in temp_mutes_dict:
                del temp_mutes_dict[str(member.id)]
                self.data_manager.set_guild_setting(interaction.guild.id, 'temp_mutes', temp_mutes_dict)

            await interaction.response.send_message(f"{member.display_name} has been unmuted.")
            try:
                await member.send(f"You have been unmuted in {interaction.guild.name}. Reason: {reason}")
            except discord.HTTPException:
                # User has DMs disabled
                pass
        else:
            await interaction.response.send_message(f"{member.display_name} is not muted.")


    def add_temp_mute(self, guild_id, member_id, unmute_time):
        temp_mutes = self.data_manager.get_guild_setting(guild_id, 'temp_mutes', '{}')
        temp_mutes_dict = temp_mutes
        temp_mutes_dict[member_id] = unmute_time.isoformat()
        self.data_manager.set_guild_setting(guild_id, 'temp_mutes', temp_mutes_dict)


async def setup(bot):
    cog = ModerationCog(bot)
    await bot.add_cog(cog)

    # Register the commands for a specific guild
    guild = discord.Object(id=1203047551813816380)  
    bot.tree.add_command(cog.ban, guild=guild)
    bot.tree.add_command(cog.unban, guild=guild)
    bot.tree.add_command(cog.kick, guild=guild)
    bot.tree.add_command(cog.mute, guild=guild)
    bot.tree.add_command(cog.unmute, guild=guild)
    
