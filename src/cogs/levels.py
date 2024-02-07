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
        #return 9999999999999
        # Exponential growth formula for level progression
        return 5 * (current_level ** 2) + 50

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
        rank = 0
        next_level_xp = self.xp_for_next_level(level)
        font_path = os.path.join(os.getcwd(), "src", "fonts", "GROBOLD.ttf")
        font_size = 12
        font = ImageFont.truetype(font_path, font_size)



        # Load the background image (customizable)
        background = Image.open('src\\background_images\\background.jpg').convert("RGBA")
        img = Image.new('RGBA', background.size)
        img.paste(background, (0, 0))
        draw = ImageDraw.Draw(img)

        # Define XP bar dimensions and position
        bar_width = 350  # Total width of the XP bar
        bar_height = 20  # Height of the XP bar
        bar_x = 25  # X position of the XP bar
        bar_y = 175  # Y position of the XP bar

        # Calculate the XP bar length proportionally to the XP
        xp_bar_length = int((xp / next_level_xp) * bar_width)

        # Draw the grey background XP bar
        draw.rounded_rectangle([(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)], 
                            radius=10, fill=(128, 128, 128))

        # Draw the green XP progress bar on top of the background bar
        draw.rounded_rectangle([(bar_x, bar_y), (bar_x + xp_bar_length, bar_y + bar_height)], 
                            radius=10, fill=(0, 255, 0))
        
        # Draw the XP text above the XP bar
        xp_text = f"{xp} / {next_level_xp} XP"
        xp_text_x = bar_width - 35 # Position the XP text at the end of the bar
        xp_text_y = bar_y - 15  # Position the XP text above the bar
        draw.text((xp_text_x, xp_text_y), xp_text, font=font, fill=(244, 244, 244))

        level_text = f"Level {level}"
        level_text_x = bar_x  # Position the XP text at the end of the bar
        level_text_y = bar_y - 15  # Position the XP text above the bar
        draw.text((level_text_x, level_text_y), level_text, font=font, fill=(244, 244, 244))


        #draw.text((0,0), "Powered by Nexus", font=ImageFont.truetype(font_path, 6), fill=(0,0,0))


        # Draw the border around the profile picture
        border_color = (255, 255, 255)  # White border
        border_size = 4  # Border thickness
        avatar_x = 50  # X position of the avatar
        avatar_y = 50  # Y position of the avatar
        avatar_size = 80  # Avatar size
        draw.rounded_rectangle([(avatar_x - border_size, avatar_y - border_size),
                                (avatar_x + avatar_size + border_size, avatar_y + avatar_size + border_size)],
                                radius=avatar_size + border_size, outline=border_color, width=border_size)

        # Draw the username at the bottom right of the profile picture
        username = interaction.user.display_name
        username_x = avatar_x + avatar_size + 10  # Position the username to the right of the avatar
        username_y = avatar_y + avatar_size - 20  # Position the username at the bottom of the avatar
        draw.text((username_x, username_y), username, font=font, fill=(255, 255, 255))

        # Add user profile picture
        avatar_url = interaction.user.display_avatar.url
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url) as response:
                if response.status == 200:
                    avatar_data = await response.read()
                    avatar = Image.open(io.BytesIO(avatar_data))
                    avatar_size = 80  # Size of the avatar
                    avatar = avatar.resize((avatar_size, avatar_size)).convert("RGBA")

                    # Create a circular mask for the avatar
                    mask = Image.new('L', (avatar_size, avatar_size), 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
                    
                    # Apply the mask to the avatar to make it circular
                    avatar.putalpha(mask)
                    
                    # Create the border around the circular avatar
                    border_size = 5  # Thickness of the border
                    border = Image.new('RGBA', (avatar_size + border_size * 2, avatar_size + border_size * 2), border_color)
                    border_draw = ImageDraw.Draw(border)
                    border_draw.ellipse((border_size, border_size, avatar_size + border_size, avatar_size + border_size), fill=border_color)
                    
                    # Mask the border to make it circular
                    border_mask = Image.new('L', (avatar_size + border_size * 2, avatar_size + border_size * 2), 0)
                    border_draw = ImageDraw.Draw(border_mask)
                    border_draw.ellipse((border_size, border_size, avatar_size + border_size, avatar_size + border_size), fill=255)
                    border.putalpha(border_mask)
                    
                    # Position of the border (considering the border size)
                    border_position = (avatar_x - border_size, avatar_y - border_size)
                    img.paste(border, border_position, border)

                    # Position of the avatar
                    avatar_position = (avatar_x, avatar_y)
                    img.paste(avatar, avatar_position, avatar)


        # Save to a BytesIO buffer
        final_buffer = io.BytesIO()
        img.save(final_buffer, 'PNG')
        final_buffer.seek(0)

        # Send image
        file = discord.File(final_buffer, filename='rank.png')
        await interaction.response.send_message(file=file)

async def setup(bot):
    cog = XPCog(bot)
    await bot.add_cog(cog)
    guild = discord.Object(id=1203047551813816380)  
    bot.tree.add_command(cog.rank, guild=guild)
    bot.tree.add_command(cog.set_level_up_channel, guild=guild)
