import discord
from discord.ext import commands
from discord import app_commands
import ollama
import logging

class AIInteractionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @app_commands.command(name='talktoai', description='Talk to an AI')
    @app_commands.describe(user_input='Your message to the AI')
    async def talk_to_ai(self, interaction: discord.Interaction, user_input: str):
        """Interact with an AI using a user's input."""
        await interaction.response.defer()

        try:
            # AI Interaction
            stream = ollama.chat(
                model='wizard-vicuna-uncensored:latest',
                messages=[{'role': 'user', 'content': f"answer within 1024 characters: {user_input}"}],
                stream=True,
            )
            
            ai_response = ''
            for chunk in stream:
                ai_response += chunk['message']['content']
                if 'end_of_chat' in chunk or len(ai_response) > 1024:
                    ai_response = ai_response[0:1023]
                    break
            self.logger.info(f"{interaction.user.display_name} asked: {user_input}, got output {ai_response}")
            # Create an embed with user input and AI response
            embed = discord.Embed(title="AI Interaction", color=discord.Color.blue())
            embed.add_field(name="Your Input", value=user_input, inline=False)
            embed.add_field(name="AI Response", value=ai_response, inline=False)
            embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

            # Send the embed as a follow-up message
            
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

async def setup(bot):
    cog = AIInteractionCog(bot)
    await bot.add_cog(cog)
    guild = discord.Object(id=1203047551813816380)  
    bot.tree.add_command(cog.talk_to_ai, guild=guild)
