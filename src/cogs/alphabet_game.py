from discord.ext import commands
import discord
from discord import app_commands
import logging
from utils.guild_data_management import GuildDataManager

class GameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.data_manager = GuildDataManager()
        self.max_length = 3

    def get_game_setting(self, guild_id, setting, default=None):
        return self.data_manager.get_guild_setting(guild_id, f'alphabet_game_{setting}', default)

    def set_game_setting(self, guild_id, setting, value):
        self.data_manager.set_guild_setting(guild_id, f'alphabet_game_{setting}', value)

    @app_commands.command(name='setalphabetgamechannel', description='Set the channel for the alphabet game.')
    @app_commands.describe(channel='The channel to set for the game')
    async def set_game_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.set_game_setting(interaction.guild_id, 'channel', channel.id)
        embed = discord.Embed(title="Game Channel Set", description=f"The game channel has been set to: {channel.mention}", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='setmaxlength', description='Set the maximum length for the game sequence.')
    @app_commands.describe(max_length='The maximum length of the sequence')
    async def set_max_length(self, interaction: discord.Interaction, max_length: int):
        self.set_game_setting(interaction.guild_id, 'max_length', max_length)
        embed = discord.Embed(title="Max Length Set", description=f"The maximum length of the sequence has been set to: {max_length}", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

    def next_sequence(self, s, max_length):
        # Initialize an empty list to store the ASCII values of the characters in the string
        mapped_sequence = []
        # Convert each character in the string to its ASCII value and append to mapped_sequence
        for i in s:
            mapped_sequence.append(ord(i))
        
        # If the length of the string is less than the maximum allowed length (max_length),
        # return the string with an additional 'a' at the end
        if len(mapped_sequence) < max_length:
            return s + "a"

        # Initialize min_value to a high number and change_index to -1
        min_value = 999
        index = 0
        change_index = -1
        # Iterate through the ASCII values in mapped_sequence
        for i in mapped_sequence:
            # If the current value is less than min_value, update min_value and change_index
            if i < min_value:
                min_value = i
                change_index = index
            index += 1
        
        # Increment the ASCII value at change_index
        mapped_sequence[change_index] += 1
        index = 0 
        # Iterate through the ASCII values again
        for i in mapped_sequence:
            # If the current index is greater than change_index,
            # reset the ASCII value at this index to 97 (which corresponds to 'a')
            if index > change_index:
                mapped_sequence[index] = 97 
            index += 1
            
        # Convert the ASCII values back to characters and join them to form a string
        return "".join(chr(i) for i in mapped_sequence)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        guild_id = message.guild.id
        game_channel_id = self.get_game_setting(guild_id, 'channel')
        if not game_channel_id:
            return
        if message.channel.id != int(game_channel_id):
            return

        progress = self.get_game_setting(guild_id, 'progress', '')
        expected_sequence = self.next_sequence(progress, int(self.get_game_setting(guild_id, 'max_length') or 3)).lower()

        if message.content.strip().lower() == expected_sequence:
            self.set_game_setting(guild_id, 'progress', expected_sequence)
            response = "Correct! Next sequence."
            color = discord.Color.green()
        else:
            self.set_game_setting(guild_id, 'progress', '')
            response = f"Incorrect, start over. Next is '{self.next_sequence('', int(self.get_game_setting(guild_id, 'max_length') or 3))}'."
            color = discord.Color.red()

        await message.delete()
        embed = discord.Embed(title="Alphabet Game", description=response, color=color)
        embed.add_field(name="Your Input", value=message.content.strip(), inline=False)
        embed.add_field(name="Expected Sequence", value=expected_sequence, inline=False)
        embed.set_footer(text=f"Message by {message.author.display_name}", icon_url=message.author.avatar.url)
        await message.channel.send(embed=embed)

async def setup(bot):
    cog = GameCog(bot)
    await bot.add_cog(cog)
    guild = discord.Object(id=1203047551813816380)
    bot.tree.add_command(cog.set_game_channel, guild=guild)
    bot.tree.add_command(cog.set_max_length, guild=guild)