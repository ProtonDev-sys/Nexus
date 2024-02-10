from discord.ext import commands
from discord import app_commands
import discord
from utils.guild_data_management import GuildDataManager

class AutoModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = GuildDataManager()

    async def get_banned_words(self, guild_id):
        return self.data_manager.get_guild_setting(guild_id, 'banned_words', [])

    async def add_banned_word(self, guild_id, word):
        banned_words = await self.get_banned_words(guild_id)
        banned_words.append(word)
        self.data_manager.set_guild_setting(guild_id, 'banned_words', banned_words)

    async def remove_banned_word(self, guild_id, word):
        banned_words = await self.get_banned_words(guild_id)
        banned_words.remove(word)
        self.data_manager.set_guild_setting(guild_id, 'banned_words', banned_words)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return

        banned_words = await self.get_banned_words(message.guild.id)
        if any(word in message.content.lower() for word in banned_words):
            await message.delete()
            warning_message = f"{message.author.mention}, your message contained a banned word and was removed."
            await message.channel.send(warning_message, delete_after=10)

    @app_commands.command(name='addbannedword', description='Add a word to the banned words list.')
    @app_commands.describe(word='Word to be banned')
    @app_commands.checks.has_permissions(manage_messages=True)
    async def add_banned_word_command(self, interaction: discord.Interaction, word: str):
        # Manually check if user has manage_messages permission
        if interaction.user.guild_permissions.manage_messages:
            await self.add_banned_word(interaction.guild_id, word.lower())
            await interaction.response.send_message(f"Added `{word}` to the banned words list.", ephemeral=True)
        else:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

    @app_commands.command(name='removebannedword', description='Remove a word from the banned words list.')
    @app_commands.describe(word='Word to be removed from the banned list')
    @app_commands.checks.has_permissions(manage_messages=True)
    async def remove_banned_word_command(self, interaction: discord.Interaction, word: str):
        # Manually check if user has manage_messages permission
        if interaction.user.guild_permissions.manage_messages:
            await self.remove_banned_word(interaction.guild_id, word.lower())
            await interaction.response.send_message(f"Removed `{word}` from the banned words list.", ephemeral=True)
        else:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)


async def setup(bot):
    cog = AutoModerationCog(bot)
    await bot.add_cog(cog)
    guild = discord.Object(id=1203047551813816380)  
    bot.tree.add_command(cog.add_banned_word_command, guild=guild)
    bot.tree.add_command(cog.remove_banned_word_command, guild=guild)
