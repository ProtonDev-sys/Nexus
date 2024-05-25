from discord.ext import commands
import discord
from discord import app_commands
from utils.guild_data_management import GuildDataManager
from random import randint, choice

class EconomyCOG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = GuildDataManager()

    #@commands.Cog.listener()
    #async def on_message(self, message):
    #    if message.author.bot or not message.guild:
    #        return
    #
    #    now = datetime.datetime.utcnow()
    #    user_id = str(message.author.id)
    #    last_award_time = self.last_xp_award.get(user_id, datetime.datetime.utcfromtimestamp(0))
    #
    #    if (now - last_award_time).total_seconds() > 60:  # 1 minute cooldown
    #        xp_gain = random.randint(3, 6)  # Random XP between 3 and 6
    #        await self.award_xp(message.guild.id, user_id, xp_gain, message.channel)
    #        self.last_xp_award[user_id] = now

    @app_commands.command(name='balance', description='Shows how much money you have.')
    @app_commands.describe(user='Users balance you want to see.')
    async def balance(self, interaction: discord.Interaction, user: discord.User=None):
        await interaction.response.defer()
        if not user:
            user = interaction.user
        guild_economy_data = self.data_manager.get_guild_setting(interaction.guild_id, 'economy_data', {})
        user_id = str(interaction.user.id)
        user_data = guild_economy_data.get(user_id, {'cash': 0, 'bank': 0})
        formatted_cash = "{:,}".format(user_data['cash'])
        formatted_bank = "{:,}".format(user_data['bank'])
        embed = discord.Embed(
            title=f"**{user.name}**'s balance",
            description=f"\nCash balance: {formatted_cash} :coin:\n\nBank balance: {formatted_bank} :coin:", # change emoji
            color=int('27d858', 16),
        )
        embed.set_footer(text="Powered by Nexus")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='work', description='You work and earn some money.',)
    async def work(self, interaction: discord.Interaction):
        work_scenarios =['You work as a dog walker and earn {x}','You bake cookies and sell them for {x}','You tutor students in math and get {x}','You perform as a street musician and receive {x}','You mow lawns and collect {x}','You paint houses and earn {x}','You babysit for your neighbors and get {x}','You design websites and charge {x}','You deliver pizzas and make {x}','You sell handmade jewelry and gain {x}','You work as a barista and earn {x}','You wash cars and get {x}','You create digital art and sell it for {x}','You take photographs and sell prints for {x}','You develop apps and earn {x}','You sell vintage clothes and make {x}','You perform magic tricks and receive {x}','You write articles and get {x}','You work as a gardener and earn {x}','You drive for a ride-sharing service and make {x}','You clean houses and get {x}','You work as a personal trainer and earn {x}','You tutor in English and get {x}','You sell lemonade and earn {x}','You knit scarves and sell them for {x}','You play video games and stream for {x}','You walk dogs and earn {x}','You groom pets and get {x}','You create YouTube videos and make {x}','You work as a freelance writer and earn {x}','You sell handmade candles and gain {x}','You teach music lessons and get {x}','You work as a photographer and earn {x}','You create online courses and sell them for {x}','You do voiceover work and earn {x}','You manage social media accounts and get {x}','You write a blog and make {x}','You sell plants and gain {x}','You design t-shirts and sell them for {x}','You work as a virtual assistant and earn {x}','You run errands for people and get {x}','You make soap and sell it for {x}','You work as a content creator and earn {x}','You make pottery and sell it for {x}','You do data entry and get {x}','You walk cats and earn {x}','You design graphics and make {x}','You sell your crafts at a market and gain {x}','You write code and earn {x}','You paint murals and get {x}','You create custom portraits and earn {x}','You work as a translator and make {x}','You sell baked goods and gain {x}','You run a blog and get {x}','You teach yoga classes and earn {x}','You make music and sell it for {x}','You work as a life coach and get {x}','You sell homemade jam and earn {x}','You provide tech support and make {x}','You craft wooden furniture and sell it for {x}','You teach online classes and earn {x}','You organize homes and get {x}','You work as an event planner and make {x}','You do freelance photography and earn {x}','You design logos and sell them for {x}','You work as a fitness coach and get {x}','You write and publish eBooks and earn {x}','You create memes and gain {x}','You work as a travel guide and earn {x}','You create animations and get {x}','You do voice acting and make {x}','You work as a brand influencer and earn {x}','You perform as a DJ and get {x}','You sell artwork online and gain {x}','You do freelance editing and earn {x}','You work as a chef and make {x}','You create podcasts and gain {x}','You tutor in science and get {x}','You make video tutorials and earn {x}','You craft leather goods and sell them for {x}','You work as an online consultant and get {x}','You perform as a clown at parties and earn {x}','You sell vintage toys and make {x}','You teach dance classes and gain {x}','You design book covers and earn {x}','You work as a car mechanic and get {x}','You create knitting patterns and sell them for {x}','You perform stand-up comedy and earn {x}','You sell antiques and gain {x}','You create sewing patterns and make {x}','You work as a tour guide and earn {x}','You make custom cakes and get {x}','You do yard work and gain {x}','You work as a makeup artist and earn {x}','You create and sell digital stickers for {x}','You perform as an actor and gain {x}','You work as a seamstress and earn {x}','You sell your poetry and make {x}','You run a food truck and earn {x}','You do freelance marketing and get {x}']
        await interaction.response.defer()
        guild_economy_data = self.data_manager.get_guild_setting(interaction.guild_id, 'economy_data', {})
        user_id = str(interaction.user.id)
        user_data = guild_economy_data.get(user_id, {'cash': 0, 'bank': 0})

        current_cash = user_data['cash']
        current_bank = user_data['bank']

        earned_money = randint(100,999)
        earned_money_string = "{:,}".format(earned_money)
        current_cash += earned_money
        user_data.update({'cash': current_cash, 'bank': current_bank})

        guild_economy_data[user_id] = user_data
        self.data_manager.set_guild_setting(interaction.guild_id, 'economy_data', guild_economy_data)

        new_money = "{:,}".format(user_data['cash'] + user_data['bank'])
        scenario = choice(work_scenarios).replace('{x}', f"${earned_money_string}")
        embed = discord.Embed(
            title=f"",
            description=f"{scenario}\nYou now have ${new_money}",
            color=int('27d858', 16),
        )
        embed.set_footer(text="Powered by Nexus")
        embed.set_author(name=interaction.user.name,icon_url=str(interaction.user.avatar.url))
        await interaction.followup.send(embed=embed)

async def setup(bot):
    cog = EconomyCOG(bot)
    await bot.add_cog(cog)
    guild = discord.Object(id=1243055680274042940)  
    bot.tree.add_command(cog.balance, guild=guild)
    bot.tree.add_command(cog.work, guild=guild)
