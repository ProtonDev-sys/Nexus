from discord.ext import commands
import discord
from discord import app_commands
from utils.guild_data_management import GuildDataManager
import random
import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps
import aiohttp
import io
import os

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
        a, b, c = 2.26429179576826, 2.0502665558951225, 321.05028974358945
        return int(a * (current_level ** b) + c)

    @app_commands.command(name='setlevelupchannel', description='Set the channel for level-up announcements.')
    @app_commands.describe(channel='The channel where level-up messages will be sent')
    async def set_level_up_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.data_manager.set_guild_setting(interaction.guild_id, 'level_up_channel', str(channel.id))
        await interaction.response.send_message(f"Level-up announcements will be sent to: {channel.mention}")

    @app_commands.command(name='rank', description='Displays your rank with a custom image.')
    async def rank(self, interaction: discord.Interaction):
        guild_xp_data = self.data_manager.get_guild_setting(interaction.guild_id, 'xp_data', {})
        user_id = str(interaction.user.id)
        user_data = guild_xp_data.get(user_id, {'xp': 0, 'level': 0})
        xp = user_data.get('xp', 0)
        level = user_data.get('level', 0)
        next_level_xp = self.xp_for_next_level(level)
        font_path = os.path.join(os.getcwd(), "src", "fonts", "GROBOLD.ttf")
        font_size = 36
        font = ImageFont.truetype(font_path, font_size)
        border_color = (255,255,255)
        # Load and resize background image
        background = Image.open('src\\background_images\\background.jpg').convert("RGBA")
        img = Image.new('RGBA', (1200, 300))
        img.paste(background.resize((1200, 300)), (0, 0))

        draw = ImageDraw.Draw(img)

        # Avatar setup
        avatar_size = 180
        avatar_x, avatar_y = 50, 75
        border_size = 8

        # XP bar setup
        bar_width, bar_height = 810, 20
        bar_x, bar_y = 315, 200
        xp_bar_length = int((xp / next_level_xp) * bar_width)

        # Draw XP bar
        draw.rounded_rectangle([(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)], radius=10, fill=(128, 128, 128))
        draw.rounded_rectangle([(bar_x, bar_y), (bar_x + xp_bar_length, bar_y + bar_height)], radius=10, fill=(0, 255, 0))

        # Draw XP text
        xp_text = f"{xp} / {next_level_xp} XP"
        draw.text((bar_x, bar_y - 40), xp_text, font=font, fill=(255, 255, 255))

        # Draw level text
        level_text = f"Level {level}"
        draw.text((bar_x + bar_width - 150, bar_y - 40), level_text, font=font, fill=(255, 255, 255))

        # Draw username
        username = interaction.user.display_name
        draw.text((avatar_x + (avatar_size/8), avatar_y - 60), username, font=font, fill=(255, 255, 255))

        # Add user profile picture
        avatar_url = interaction.user.display_avatar.url
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url) as response:
                if response.status == 200:
                    avatar_data = await response.read()
                    avatar = Image.open(io.BytesIO(avatar_data))
                    avatar = avatar.resize((avatar_size, avatar_size)).convert("RGBA")

                    # Create a circular mask for the avatar
                    mask = Image.new('L', (avatar_size, avatar_size), 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
                    avatar.putalpha(mask)

                    # Define the border size and color
                    border_color = (255, 255, 255)  # White border

                    # Create a larger circle for the border
                    border_circle = Image.new('RGBA', (avatar_size + border_size * 2, avatar_size + border_size * 2), (0, 0, 0, 0))
                    border_circle_draw = ImageDraw.Draw(border_circle)
                    border_circle_draw.ellipse((0, 0, avatar_size + border_size * 2, avatar_size + border_size * 2), fill=border_color)

                    # Position the border circle behind the avatar
                    border_position = (avatar_x - border_size, avatar_y - border_size)
                    img.paste(border_circle, border_position, border_circle)

                    # Position the avatar on top of the border
                    avatar_position = (avatar_x, avatar_y)
                    img.paste(avatar, avatar_position, avatar)

        # Resize image for display
        img = img.resize((400, 100), Image.Resampling.LANCZOS)

        # Save to buffer and send
        final_buffer = io.BytesIO()
        img.save(final_buffer, 'PNG')
        final_buffer.seek(0)
        file = discord.File(final_buffer, filename='rank.png')
        await interaction.response.send_message(file=file)

async def setup(bot):
    cog = XPCog(bot)
    await bot.add_cog(cog)
    guild = discord.Object(id=1203047551813816380)  
    bot.tree.add_command(cog.rank, guild=guild)
    bot.tree.add_command(cog.set_level_up_channel, guild=guild)
