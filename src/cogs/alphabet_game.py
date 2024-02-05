from discord.ext import commands
import discord
from discord import app_commands
import logging
from utils.db_handler import DatabaseHandler

class GameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.max_length = 3
        self.channel_progress = {}
        self.game_channel_name = 'game-channel'  # Default game channel
        self.logger = logging.getLogger(__name__)

    @app_commands.command(name='setgamechannel', description='Set the channel for the alphabet game.')
    @app_commands.describe(channel='The channel to set for the game')
    async def set_game_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.game_channel_name = channel.name

        # Create an embed
        embed = discord.Embed(title="Game Channel Set",
                              description=f"The game channel has been set to: {channel.mention}",
                              color=discord.Color.blue())

        # Optionally add fields, footers, images, etc.
        # embed.add_field(name="Field Name", value="Field Value", inline=False)
        # embed.set_footer(text="Your Footer Here")
        # embed.set_image(url="Your Image URL Here")
        # embed.set_thumbnail(url="Your Thumbnail URL Here")

        await interaction.response.send_message(embed=embed)


    def next_sequence(self, s):
        # Initialize an empty list to store the ASCII values of the characters in the string
        mapped_sequence = []
        # Convert each character in the string to its ASCII value and append to mapped_sequence
        for i in s:
            mapped_sequence.append(ord(i))
        
        # If the length of the string is less than the maximum allowed length (max_length),
        # return the string with an additional 'a' at the end
        if len(mapped_sequence) < self.max_length:
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
        if message.author == self.bot.user or message.channel.name != self.game_channel_name:
            return

        user_input = message.content.strip().lower()
        channel_id = message.channel.id
        expected_sequence = self.next_sequence(self.channel_progress.get(channel_id, "")).lower()

        if user_input == expected_sequence:
            self.channel_progress[channel_id] = user_input
            response = "Correct! Next sequence."
            color = discord.Color.green()  # Green color for correct response
        else:
            self.channel_progress[channel_id] = ""
            response = f"Incorrect, start over. Next is '{self.next_sequence('')}'."
            color = discord.Color.red()  # Red color for incorrect response

        await message.delete()

        # Create an embed with the response
        embed = discord.Embed(title="Alphabet Game", description=response, color=color)
        embed.add_field(name="Your Input", value=user_input, inline=False)
        embed.add_field(name="Expected Sequence", value=expected_sequence, inline=False)
        embed.set_footer(text=f"Message by {message.author.display_name}", icon_url=message.author.avatar.url)

        await message.channel.send(embed=embed)



async def setup(bot):
    cog = GameCog(bot)
    await bot.add_cog(cog)
    
    # Register the command for a specific guild
    guild = discord.Object(id=1203047551813816380)  # Replace guild_id with the target guild's ID
    bot.tree.add_command(cog.set_game_channel, guild=guild)
    print("alphabet game loaded.")