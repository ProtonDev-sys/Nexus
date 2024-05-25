from discord.ext import commands
import discord
from discord import app_commands
import logging
from utils.guild_data_management import GuildDataManager

class EmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.data_manager = GuildDataManager()
        self.max_length = 3

    def get_game_setting(self, guild_id, setting, default=None):
        return self.data_manager.get_guild_setting(guild_id, f'alphabet_game_{setting}', default)

    def set_game_setting(self, guild_id, setting, value):
        self.data_manager.set_guild_setting(guild_id, f'alphabet_game_{setting}', value)

    @app_commands.command(name='send_embed', description='Send an embed in the current channel.')
    @app_commands.describe(
        title='The title of the embed',
        description='The description of the embed',
        color='The color of the embed in hex',
        footer='The footer of the embed'
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def send_embed(self, interaction: discord.Interaction, title: str, color: str, footer: str, *, description: str):
        description = description.replace("\\n", "\n")

        # Convert hex color to int
        color_int = int(color.strip('#'), 16)
        
        # Create the embed
        embed = discord.Embed(
            title=title,
            description=description,
            color=color_int
        )
        
        # Add footer if provided
        if footer:
            embed.set_footer(text=footer)
        
        # Send the embed
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    cog = EmbedCog(bot)
    await bot.add_cog(cog)
    guild = discord.Object(id=1203047551813816380)
    bot.tree.add_command(cog.send_embed, guild=guild)
