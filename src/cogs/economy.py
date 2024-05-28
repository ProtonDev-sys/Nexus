from discord.ext import commands
import discord
from discord import app_commands
from utils.guild_data_management import GuildDataManager
from random import randint, choice
import logging
from utils.constants import RED,GREEN
from time import time
from math import floor

class EconomyCOG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = GuildDataManager()
        self.logger = logging.getLogger(__name__)
        self.cooldowns = {
            "Work":600,
            "Daily":3600
        }

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
            color=GREEN,
        )
        embed.set_footer(text="Powered by Nexus")
        await interaction.followup.send(embed=embed)

    def add_cash(self, guild_id, user_id, amount: int):
        guild_economy_data = self.data_manager.get_guild_setting(guild_id, 'economy_data', {})
        user_id = str(user_id)
        user_data = guild_economy_data.get(user_id, {'cash': 0, 'bank': 0})
        current_cash = user_data['cash']
        current_bank = user_data['bank']
        user_data.update({'cash': current_cash + amount, 'bank': current_bank})
        guild_economy_data[user_id] = user_data
        self.data_manager.set_guild_setting(guild_id, 'economy_data', guild_economy_data)
        return user_data
    
    def add_bank(self, guild_id, user_id, amount: int):
        guild_economy_data = self.data_manager.get_guild_setting(guild_id, 'economy_data', {})
        user_id = str(user_id)
        user_data = guild_economy_data.get(user_id, {'cash': 0, 'bank': 0})
        current_cash = user_data['cash']
        current_bank = user_data['bank']
        user_data.update({'cash': current_cash, 'bank': current_bank + amount})
        guild_economy_data[user_id] = user_data
        self.data_manager.set_guild_setting(guild_id, 'economy_data', guild_economy_data)
        return user_data

    @app_commands.command(name='daily', description='Claim your daily bonus.',)
    async def daily(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild_id
        guild_cooldown_data = self.data_manager.get_guild_setting(guild_id, 'daily_cooldown', {})
        user_data = guild_cooldown_data.get(str(user_id), {'cooldown':0})
        time_left = (time() - user_data['cooldown']) - self.cooldowns['Daily'] 

        if time_left < 0:
            time_left = -time_left
            minutes_left = int(time_left // 60)
            seconds_left = int(time_left % 60)
            message = ""
            if minutes_left > 0:
                message = f"{minutes_left} minutes and "
            message += f"{seconds_left} seconds."
            embed = discord.Embed(
                title="Error",
                description=f"You cannot use this command for {message}.",
                color=RED
            ) 
            await interaction.response.send_message(embed=embed,ephemeral=True)
            return
        
        user_data.update({'cooldown':floor(time())})
        guild_cooldown_data[user_id] = user_data
        self.data_manager.set_guild_setting(guild_id, 'daily_cooldown', guild_cooldown_data)
        await interaction.response.defer()
        earned_money = randint(1000,9999)
        earned_money_string = "{:,}".format(earned_money)
        user_data = self.add_cash(guild_id, user_id, earned_money)
        
        new_money = "{:,}".format(user_data['cash'] + user_data['bank'])
        embed = discord.Embed(
            title=f"",
            description=f"You claimed your daily bonus of ${earned_money_string}\nYou now have ${new_money}",
            color=GREEN,
        )
        embed.set_footer(text="Powered by Nexus")
        embed.set_author(name=interaction.user.name,icon_url=str(interaction.user.avatar.url))
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='work', description='You work and earn some money.',)
    async def work(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild_id
        guild_cooldown_data = self.data_manager.get_guild_setting(guild_id, 'work_cooldown', {})
        user_data = guild_cooldown_data.get(str(user_id), {'cooldown':0})
        time_left = (time() - user_data['cooldown']) - self.cooldowns['Work'] 

        if time_left < 0:
            time_left = -time_left
            minutes_left = int(time_left // 60)
            seconds_left = int(time_left % 60)
            message = ""
            if minutes_left > 0:
                message = f"{minutes_left} minutes and "
            message += f"{seconds_left} seconds."
            embed = discord.Embed(
                title="Error",
                description=f"You cannot use this command for {message}.",
                color=RED
            ) 
            await interaction.response.send_message(embed=embed,ephemeral=True)
            return

        user_data.update({'cooldown':floor(time())})
        guild_cooldown_data[user_id] = user_data
        self.data_manager.set_guild_setting(guild_id, 'work_cooldown', guild_cooldown_data)

        work_scenarios =['You work as a dog walker and earn {x}','You bake cookies and sell them for {x}','You tutor students in math and get {x}','You perform as a street musician and receive {x}','You mow lawns and collect {x}','You paint houses and earn {x}','You babysit for your neighbors and get {x}','You design websites and charge {x}','You deliver pizzas and make {x}','You sell handmade jewelry and gain {x}','You work as a barista and earn {x}','You wash cars and get {x}','You create digital art and sell it for {x}','You take photographs and sell prints for {x}','You develop apps and earn {x}','You sell vintage clothes and make {x}','You perform magic tricks and receive {x}','You write articles and get {x}','You work as a gardener and earn {x}','You drive for a ride-sharing service and make {x}','You clean houses and get {x}','You work as a personal trainer and earn {x}','You tutor in English and get {x}','You sell lemonade and earn {x}','You knit scarves and sell them for {x}','You play video games and stream for {x}','You walk dogs and earn {x}','You groom pets and get {x}','You create YouTube videos and make {x}','You work as a freelance writer and earn {x}','You sell handmade candles and gain {x}','You teach music lessons and get {x}','You work as a photographer and earn {x}','You create online courses and sell them for {x}','You do voiceover work and earn {x}','You manage social media accounts and get {x}','You write a blog and make {x}','You sell plants and gain {x}','You design t-shirts and sell them for {x}','You work as a virtual assistant and earn {x}','You run errands for people and get {x}','You make soap and sell it for {x}','You work as a content creator and earn {x}','You make pottery and sell it for {x}','You do data entry and get {x}','You walk cats and earn {x}','You design graphics and make {x}','You sell your crafts at a market and gain {x}','You write code and earn {x}','You paint murals and get {x}','You create custom portraits and earn {x}','You work as a translator and make {x}','You sell baked goods and gain {x}','You run a blog and get {x}','You teach yoga classes and earn {x}','You make music and sell it for {x}','You work as a life coach and get {x}','You sell homemade jam and earn {x}','You provide tech support and make {x}','You craft wooden furniture and sell it for {x}','You teach online classes and earn {x}','You organize homes and get {x}','You work as an event planner and make {x}','You do freelance photography and earn {x}','You design logos and sell them for {x}','You work as a fitness coach and get {x}','You write and publish eBooks and earn {x}','You create memes and gain {x}','You work as a travel guide and earn {x}','You create animations and get {x}','You do voice acting and make {x}','You work as a brand influencer and earn {x}','You perform as a DJ and get {x}','You sell artwork online and gain {x}','You do freelance editing and earn {x}','You work as a chef and make {x}','You create podcasts and gain {x}','You tutor in science and get {x}','You make video tutorials and earn {x}','You craft leather goods and sell them for {x}','You work as an online consultant and get {x}','You perform as a clown at parties and earn {x}','You sell vintage toys and make {x}','You teach dance classes and gain {x}','You design book covers and earn {x}','You work as a car mechanic and get {x}','You create knitting patterns and sell them for {x}','You perform stand-up comedy and earn {x}','You sell antiques and gain {x}','You create sewing patterns and make {x}','You work as a tour guide and earn {x}','You make custom cakes and get {x}','You do yard work and gain {x}','You work as a makeup artist and earn {x}','You create and sell digital stickers for {x}','You perform as an actor and gain {x}','You work as a seamstress and earn {x}','You sell your poetry and make {x}','You run a food truck and earn {x}','You do freelance marketing and get {x}']
        await interaction.response.defer()
        earned_money = randint(100,999)
        earned_money_string = "{:,}".format(earned_money)
        user_data = self.add_cash(guild_id, user_id, earned_money)

        new_money = "{:,}".format(user_data['cash'] + user_data['bank'])
        scenario = choice(work_scenarios).replace('{x}', f"${earned_money_string}")
        embed = discord.Embed(
            title=f"",
            description=f"{scenario}\nYou now have ${new_money}",
            color=GREEN,
        )
        embed.set_footer(text="Powered by Nexus")
        embed.set_author(name=interaction.user.name,icon_url=str(interaction.user.avatar.url))
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='blackjack', description='Play blackjakc')
    async def blackjack(self, interaction: discord.Interaction, bet: int):
        guild_economy_data = self.data_manager.get_guild_setting(interaction.guild_id, 'economy_data', {})
        user_id = str(interaction.user.id)
        user_data = guild_economy_data.get(user_id, {'cash': 0, 'bank': 0})

        current_cash = user_data['cash']
        current_bank = user_data['bank']
        if current_cash < bet:
            embed = discord.Embed(
                title=f"Error",
                description=f"You don't have enough money to place this bet, withdraw your money before playing.",
                color=RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        elif bet < 200:
            embed = discord.Embed(
                title=f"Error",
                description=f"Your bet must be greater than $200.",
                color=RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        elif bet > 10000:
            embed = discord.Embed(
                title=f"Error",
                description=f"Your bet must be less than $10,000.",
                color=RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        self.add_cash(interaction.guild_id, interaction.user.id, -bet)

        player_hand = [deal_card(), deal_card()]
        dealer_hand = [deal_card(), deal_card()]
        
        player_total = calculate_hand(player_hand)
        dealer_total = calculate_hand(dealer_hand)
        
        await interaction.channel.send(
            embed=BlackjackView.create_embed(BlackjackView, player_hand, dealer_hand, player_total, dealer_total, True),
            view=BlackjackView(interaction, self, bet, player_hand, dealer_hand)
        )

    @app_commands.command(name='deposit', description='Deposit money into your bank.')
    @app_commands.describe(amount='Amount to depsoit.')
    async def deposit(self, interaction: discord.Interaction, amount: int):
        try:
            if str(int(amount)) != str(amount):
                embed = discord.Embed(
                    title=f"Error",
                    description=f"You must pass an integer value.",
                    color=RED,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                guild_economy_data = self.data_manager.get_guild_setting(interaction.guild_id, 'economy_data', {})
                user_id = str(interaction.user.id)
                user_data = guild_economy_data.get(user_id, {'cash': 0, 'bank': 0})
                current_cash = user_data['cash']
                current_bank = user_data['bank']
                if current_cash >= amount:
                    current_bank += amount
                    current_cash -= amount
                    user_data.update({'cash': current_cash, 'bank': current_bank})
                    guild_economy_data[user_id] = user_data
                    self.data_manager.set_guild_setting(interaction.guild_id, 'economy_data', guild_economy_data)
                    embed = discord.Embed(
                        title=f"Success",
                        description=f"Succesfully deposited {amount}.",
                        color=GREEN,
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    embed = discord.Embed(
                        title=f"Error",
                        description=f"You don't have enough money to deposit.",
                        color=RED,
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title=f"Error",
                description=f"You must pass an integer value.",
                color=RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            self.logger.error(e)
    
    @app_commands.command(name='withdraw', description='Withdraw money from your bank.')
    @app_commands.describe(amount='Amount to withdraw.')
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        try:
            if str(int(amount)) != str(amount):
                embed = discord.Embed(
                    title=f"Error",
                    description=f"You must pass an integer value.",
                    color=RED,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                guild_economy_data = self.data_manager.get_guild_setting(interaction.guild_id, 'economy_data', {})
                user_id = str(interaction.user.id)
                user_data = guild_economy_data.get(user_id, {'cash': 0, 'bank': 0})
                current_cash = user_data['cash']
                current_bank = user_data['bank']
                
                if current_bank >= amount:
                    current_cash += amount
                    current_bank -= amount
                    user_data.update({'cash': current_cash, 'bank': current_bank})
                    guild_economy_data[user_id] = user_data
                    self.data_manager.set_guild_setting(interaction.guild_id, 'economy_data', guild_economy_data)
                    embed = discord.Embed(
                        title=f"Success",
                        description=f"Succesfully withdrawn {amount}.",
                        color=GREEN,
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    embed = discord.Embed(
                        title=f"Error",
                        description=f"You don't have enough money to withdraw.",
                        color=RED,
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title=f"Error",
                description=f"You must pass an integer value.",
                color=RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            self.logger.error(e)

suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
values = {'2': 2, '3': 3, '4': 4, '5':5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'Jack': 10, 'Queen': 10, 'King': 10, 'Ace': 11}
def deal_card():
    suit = choice(suits)
    rank = choice(ranks)
    return rank, suit

def calculate_hand(hand):
    total = sum(values[card[0]] for card in hand)
    aces = sum(1 for card in hand if card[0] == 'Ace')
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

class BlackjackView(discord.ui.View):
    def __init__(self, interaction: discord.Integration, EconomyCOG: EconomyCOG, bet: int, player_hand: [], dealer_hand: []):
        super().__init__()
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.player_total = calculate_hand(player_hand)
        self.dealer_total = calculate_hand(dealer_hand)
        self.interaction = interaction
        self.bet = bet
        self.EconomyCOG = EconomyCOG

    def win(self):
        EconomyCOG.add_cash(self.EconomyCOG, self.interaction.guild.id, self.interaction.user.id, self.bet * 2)
        
    def draw(self):
        EconomyCOG.add_cash(self.EconomyCOG, self.interaction.guild.id, self.interaction.user.id, self.bet)
    
    def create_embed(self, player_hand, dealer_hand, player_total, dealer_total, hide_dealer_card=True):
        player_hand_str = ', '.join([f"{card[0]} of {card[1]}" for card in player_hand])
        if hide_dealer_card:
            dealer_hand_str = f"{dealer_hand[0][0]} of {dealer_hand[0][1]}, [hidden]"
        else:
            dealer_hand_str = ', '.join([f"{card[0]} of {card[1]}" for card in dealer_hand])
        
        embed = discord.Embed(title="Blackjack Game")
        embed.add_field(name="Your Hand", value=f"{player_hand_str} (Total: {player_total})", inline=False)
        embed.add_field(name="Dealer's Hand", value=f"{dealer_hand_str} (Total: {'?' if hide_dealer_card else dealer_total})", inline=False)
        return embed

    @discord.ui.button(label='Hit', style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return
        
        card = deal_card()
        self.player_hand.append(card)
        self.player_total = calculate_hand(self.player_hand)
        embed = self.create_embed(self.player_hand, self.dealer_hand, self.player_total, self.dealer_total)

        if self.player_total > 21:
            self.disable_buttons()
            embed.add_field(name="Result", value=f"Bust!")
            embed.color = RED
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label='Stand', style=discord.ButtonStyle.secondary)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return
        
        self.disable_buttons()
        embed = self.create_embed(self.player_hand, self.dealer_hand, self.player_total, self.dealer_total, hide_dealer_card=False)
        
        while self.dealer_total < 17:
            card = deal_card()
            self.dealer_hand.append(card)
            self.dealer_total = calculate_hand(self.dealer_hand)
            embed = self.create_embed(self.player_hand, self.dealer_hand, self.player_total, self.dealer_total, hide_dealer_card=False)
        
        if self.dealer_total > 21 or self.player_total > self.dealer_total:
            embed.add_field(name="Result", value=f"You win ${self.bet * 2}!")
            embed.color = GREEN
            self.win()
        elif self.player_total < self.dealer_total:
            embed.add_field(name="Result", value=f"Dealer wins!")
            embed.color = RED
        else:
            embed.add_field(name="Result", value=f"It's a tie! Bet returned.")
            embed.color = RED
            self.draw()
        await interaction.response.edit_message(embed=embed)

    def disable_buttons(self):
        for item in self.children:
            item.disabled = True
        self.stop()

async def setup(bot):
    cog = EconomyCOG(bot)
    await bot.add_cog(cog)
    guild = discord.Object(id=1203047551813816380)  
    bot.tree.add_command(cog.balance, guild=guild)
    bot.tree.add_command(cog.work, guild=guild)
    bot.tree.add_command(cog.deposit, guild=guild)
    bot.tree.add_command(cog.withdraw, guild=guild)
    bot.tree.add_command(cog.daily, guild=guild)
    bot.tree.add_command(cog.blackjack, guild=guild)
    