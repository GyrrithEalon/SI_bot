# -*- coding: utf-8 -*-
"""
Created on Mon Apr 10 14:10:43 2023

@author: timsargent
"""

import os
import discord
import json
from discord.ext import commands
from discord.commands import Option
from Game import Game
from Player import Player
from dotenv import load_dotenv

#async def some_command(ctx, file: discord.Attachment):

# =============================================================================
# Load Env
# =============================================================================
load_dotenv()
GUILD = os.getenv('DISCORD_GUILD')
GUILD_ID = os.getenv('DISCORD_GUILD_ID')
EALON_ID = os.getenv('EALON_ID')

# =============================================================================
# Make a shell bot class
# =============================================================================

class CommandsHandler(commands.Cog):
    
    def __init__(self, bot):
       self.bot = bot

    def format_card_for_chat(self, card):
        site = r"https://sick.oberien.de/imgs/powers/"
        filetype = ".webp"
        cardname = card['name'].replace(" ", "_").lower()
        cardname = cardname.replace("'", "")
        cardname = cardname.replace("-", "")
        cardname = cardname.replace(",", "")
        return f"{site}{cardname}{filetype} "
    
    def generate_card_imbeds(self, cards, this_color = 0x00ff00):
        embed_group = []
        embeds = []
        for i, card in enumerate(cards):
            k = i % 2
            embeds.append(discord.Embed(url="https://sick.oberien.de/", title=card["name"], color=this_color).set_image(url=self.format_card_for_chat(card)))
            if k == 1:
                embed_group.append(embeds)
                embeds = []
        if len(embeds) > 0:
            embed_group.append(embeds)
        return embed_group
    
    def check_player(self, game_id, player_id):
        """Check if player is in game, return player object"""
        try:
            dude = Player(game_id, player_id)
        except:
            return None 
        return dude
       
    @commands.Cog.listener()
    async def on_ready(self):
        #for multi Server access, will need to sort through connecte servers
        self.guild = self.bot.guilds[0]
        print(
            f'{self.bot.user.name} is connected to the following guild:\n'
            f'{self.guild.name}(id: {self.guild.id})'
        )
        
# =============================================================================
#     The Help Command
# =============================================================================

    @commands.slash_command(name='help', guild_ids=[GUILD_ID])
    async def help(self, ctx):
        """Help Command"""

        response = "The main commands are: \n\n"
        response += "`/join_game <spirt name>` - Spirt name is a search term (I.E. Lightning, River, Speaker, Trickster are valid)\n\n"

        response += "`/show_<hand/discard/play/draft>` - Display your cards from a certain zone\n\n"

        response += "Playing Cards, `all` is a valid input, otherwise your input is comma seperated and  search is done on valid card picks cards\n"
        response += "    `/play_cards <card names>`\n"
        response += "    `/discard_cards <card names>`\n"
        response += "    `/reclaim_cards <card names>`\n"
        response += "    `/forget_cards <card names>`\n"
        response += "    `/undo_card_action` - Undo the last of the above actions, you only get one undo!\n\n"
        response += "Example: `/play_cards shatter,boon,harb` will move Lightning's Shatter Homesteads, Lightning's Boon, and Harbingers of the Lightning to the Inplay zone\n"
        response += "Example: `/reclaim_cards all` will reclaim all discarded cards to hand\n\n"

        response += "Drafting new powers\n"
        response += "   `/draft_power_card <minor/major> <count = 4>` - Default is to pick from 4\n"
        response += "   `/choose_power_card <card name>`\n"
        response += "   `/undo_power_choice` - Undo the power card choice you made, can't work if you play interact with cards after choosing\n\n"

        await ctx.respond(response)

# =============================================================================
# GAME SETUP
# =============================================================================
    @commands.slash_command(name='join_game', guild_ids=[GUILD_ID])
    async def join_game(self, ctx, spirit: str):
        """Register for this Channel's game"""
        game_id = ctx.channel.id
        game = Game(game_id)
        game.add_player(ctx.author.id, ctx.author.name)
        t = game.assign_spirit(ctx.author.id, spirit)
        response = f"Added <@{ctx.author.id}> as {t[0]}"
        await ctx.respond(response)

    @commands.slash_command(name='expunge_me', guild_ids=[GUILD_ID])
    async def expunge_me(self, ctx):
        """Delete from a game"""
        game_id = ctx.channel.id
        game = Game(game_id)
        game.remove_player(ctx.author.id)
        response = f"Removed <@{ctx.author.id}> from the game"
        await ctx.respond(response)
        
    @commands.slash_command(name='init_game', guild_ids=[GUILD_ID])
    async def init_power_deck(self, ctx, excluded_sets: str = None):
        """set the power deck"""
        game_id = ctx.channel.id
        player_id = ctx.author.id
        game = Game(game_id)
        game.purge_game()
        del game
        game = Game(game_id)
        if excluded_sets is not None:
            excluded_sets = excluded_sets.split(",")
        game.host = player_id
        game.set_played_sets(excluded_sets=excluded_sets)
        game.init_power_decks()
        await ctx.respond("Ok")

    @commands.slash_command(name='purge_game', guild_ids=[GUILD_ID])
    async def purge_game(self, ctx):
        """Purge a game"""
        game_id = ctx.channel.id
        game = Game(game_id)
        game.purge_game()
        await ctx.respond("Game Purged")

# =============================================================================
# Player Actions, picking new powers
# =============================================================================
    @commands.slash_command(name='draft_power_card', guild_ids=[GUILD_ID])
    async def draft_power_card(self, ctx, type:str, count: int = 4):
        """Draw a power card"""
        game_id = ctx.channel.id
        player_id = ctx.author.id
        dude = self.check_player(game_id, player_id)
        if dude is None:
            await ctx.respond("You are not in this game")
            return
        if str(type).lower() == "minor":
            stat = dude.draft_powers(True, count)
        elif str(type).lower() == "major":
            stat = dude.draft_powers(False, count)
        else:
            await ctx.respond("Pick Major or Minor")
            return
        
        if stat:
            response = "Take your Pick! \n\n"
        elif stat is None:
            response = "Please Init the Power Deck"
            await ctx.respond(response)
            return
        else:
            response = "You have pending cards to choose from... \n\n"
        await ctx.respond(response)
        embed_group = self.generate_card_imbeds(dude.pending_card_choice)
        for embeds in embed_group:
            await ctx.respond(embeds=embeds)

    @commands.slash_command(name='choose_power_card', guild_ids=[GUILD_ID])
    async def choose_power_card(self, ctx, card_name: str):
        """Choose a power card"""
        game_id = ctx.channel.id
        player_id = ctx.author.id
        dude = self.check_player(game_id, player_id)
        if dude is None:
            await ctx.respond("You are not in this game")
            return
        stat = dude.choose_power(card_name)
        if stat is None:
            response = f"No Pending Card Choice, run `/draft_power_card` first"
        elif stat[2] < 25:
            card_name = stat[0]["name"]
            response = f"Added `{card_name}` to your hand, \n I'm not confindant in that pick, if that's the wrong card, \n run `/undo_power_choice` and be more clear next time"
        else:
            card_name = stat[0]["name"]
            response = f"Added `{card_name}` to your hand"
        await ctx.respond(response)

    @commands.slash_command(name='undo_power_choice', guild_ids=[GUILD_ID])
    async def undo_power_choice(self, ctx):
        """Undo a power card choice"""
        game_id = ctx.channel.id
        player_id = ctx.author.id
        dude = self.check_player(game_id, player_id)
        if dude is None:
            await ctx.respond("You are not in this game")
            return
        stat = dude.undo_power_choice()
        if stat:
            response = "Undo Successful"
        else:
            response = "Nothing to Undo"
        await ctx.respond(response)

# =============================================================================
# Player Actions, playing cards
# =============================================================================

    @commands.slash_command(name='play_cards', guild_ids=[GUILD_ID])
    async def play_cards(self, ctx, card_names: str):
        """Play a card"""
        game_id = ctx.channel.id
        player_id = ctx.author.id
        dude = self.check_player(game_id, player_id)
        if dude is None:
            await ctx.respond("You are not in this game")
            return
        if card_names == "all":
            catch = dude.play_cards(["all"])
        else:
            catch = dude.play_cards(card_names.split(","))
        response = "Cards Played: \n\n"
        for card in catch[0]:
            response += f"`{card}` \n"
        await ctx.respond(response)


    @commands.slash_command(name='reclaim_cards', guild_ids=[GUILD_ID])
    async def reclaim_cards(self, ctx, card_names: str):
        """Reclaim cards"""
        game_id = ctx.channel.id
        player_id = ctx.author.id
        dude = self.check_player(game_id, player_id)
        if dude is None:
            await ctx.respond("You are not in this game")
            return
        if card_names == "all":
            catch = dude.reclaim_cards(["all"])
            response = "All Cards have been Reclaimed"
        else:
            catch = dude.reclaim_cards(card_names.split(","))
            response = "Cards Reclaimed: \n\n"
            for card in catch[0]:
                response += f"`{card}` \n"
        await ctx.respond(response)

    @commands.slash_command(name='forget_cards', guild_ids=[GUILD_ID])
    async def forget_cards(self, ctx, card_names: str):
        """Forget cards"""
        game_id = ctx.channel.id
        player_id = ctx.author.id
        dude = self.check_player(game_id, player_id)
        if dude is None:
            await ctx.respond("You are not in this game")
            return
        catch = dude.forget_cards(card_names.split(","))
        response = "Cards Forgotten: \n\n"
        for card in catch[0]:
            response += f"`{card}` \n"
        await ctx.respond(response)

    @commands.slash_command(name='discard_cards', guild_ids=[GUILD_ID])
    async def discard_cards(self, ctx, card_names: str):
        """Discard cards"""
        game_id = ctx.channel.id
        player_id = ctx.author.id
        dude = self.check_player(game_id, player_id)
        if dude is None:
            await ctx.respond("You are not in this game")
            return
        catch = dude.discard_cards(card_names.split(","))
        response = "Cards Discarded: \n\n"
        for card in catch[0]:
            response += f"`{card}` \n"
        await ctx.respond("Cards Discarded")

    @commands.slash_command(name='undo_card_action', guild_ids=[GUILD_ID])
    async def undo_card_action(self, ctx):
        """Undo a card action"""
        game_id = ctx.channel.id
        player_id = ctx.author.id
        dude = self.check_player(game_id, player_id)
        if dude is None:
            await ctx.respond("You are not in this game")
            return
        if dude.undo_card_action():
            await ctx.respond("Undo Successful")
        else:
            await ctx.respond("Nothing to Undo")

    @commands.slash_command(name='show_pending_actions', guild_ids=[GUILD_ID])
    async def show_pending_actions(self, ctx, action: str = None):
        """Show Pending Actions"""
        game_id = ctx.channel.id
        player_id = ctx.author.id
        dude = Player(game_id, player_id)
        if action is None:
            response = "Pending Actions: \n\n"
            for gogurt in dude.pending_action:
                tmp1 = gogurt["action"]
                tmp2 = gogurt["response"]
                response += f"`{tmp1}:{tmp2}` \n"
        else: 
            response = "Pending Action: \n\n"
            response += "`" + action["response"] + "` \n"
        await ctx.respond(response)

    @commands.slash_command(name='update_action', guild_ids=[GUILD_ID])
    async def update_action(self, ctx, action: str, response: str):
        """Update a pending action"""
        game_id = ctx.channel.id
        player_id = ctx.author.id
        dude = self.check_player(game_id, player_id)
        if dude is None:
            await ctx.respond("You are not in this game")
            return
        dude.update_action(action, response)
        await ctx.respond("Action Updated")


# =============================================================================
# Displaying Player Cards
# =============================================================================
    @commands.slash_command(name='show_inplay', guild_ids=[GUILD_ID])
    async def show_inplay(self, ctx):
        """Display Player inplay cards"""
        game_id = ctx.channel.id
        player_id = ctx.author.id
        dude = self.check_player(game_id, player_id)
        if dude is None:
            await ctx.respond("You are not in this game")
            return
        if dude.get_inplay() == []:
            await ctx.respond("No Cards in Play")
            return
        response = "Your Cards: \n\n"
        ctx.respond(response)
        embed_group = self.generate_card_imbeds(dude.get_inplay())
        for embed in embed_group:
            await ctx.respond(embeds=embed)

    @commands.slash_command(name='show_hand', guild_ids=[GUILD_ID])
    async def show_hand(self, ctx):
        """Display Player hand cards"""
        game_id = ctx.channel.id
        player_id = ctx.author.id
        dude = self.check_player(game_id, player_id)
        if dude is None:
            await ctx.respond("You are not in this game")
            return
        if dude.get_hand() == []:
            await ctx.respond("No Cards in Hand")
            return
        response = "Your Cards: \n\n"
        ctx.respond(response)
        embed_group = self.generate_card_imbeds(dude.get_hand())
        for embed in embed_group:
            await ctx.respond(embeds=embed)

    @commands.slash_command(name='show_discard', guild_ids=[GUILD_ID])
    async def show_discard(self, ctx):
        """Display Player discard cards"""
        game_id = ctx.channel.id
        player_id = ctx.author.id
        dude = self.check_player(game_id, player_id)
        if dude is None:
            await ctx.respond("You are not in this game")
            return
        if dude.get_discard() == []:
            await ctx.respond("No Cards in Discard")
            return
        response = "Your Cards: \n\n"
        ctx.respond(response)
        embed_group = self.generate_card_imbeds(dude.get_discard())
        for embed in embed_group:
            await ctx.respond(embeds=embed)

    @commands.slash_command(name='show_draft', guild_ids=[GUILD_ID])
    async def show_draft(self, ctx):
        """Display Player power draft cards"""
        game_id = ctx.channel.id
        player_id = ctx.author.id
        dude = self.check_player(game_id, player_id)
        if dude is None:
            await ctx.respond("You are not in this game")
            return
        if dude.pending_card_choice == []:
            await ctx.respond("No Cards to Draft")
            return
        response = "Your Cards Choices: \n\n"
        ctx.respond(response)
        embed_group = self.generate_card_imbeds(dude.pending_card_choice)
        for embed in embed_group:
            await ctx.respond(embeds=embed)


# =============================================================================
#     Player Actions, responses
# =============================================================================

    @commands.slash_command(name='ready', guild_ids=[GUILD_ID])
    async def ready(self, ctx):
        """Ready up"""
        game_id = ctx.channel.id
        player_id = ctx.author.id
        game = Game(game_id)
        dude = self.check_player(game_id, player_id)
        if dude is None:
            await ctx.respond("You are not in this game")
            return
        dude.set_ready()
        if dude.ready:
            await ctx.respond("Readied, run again to unready")
        else:
            await ctx.respond("Unreadied, run again to ready")
        if game.check_player_ready():
            await ctx.respond(f"<@{str(game.host)}>: All Players Ready!")
            return
        
    @commands.slash_command(name='my_decision', guild_ids=[GUILD_ID])
    async def my_decision(self, ctx):
        """Display Player decision"""
        game_id = ctx.channel.id
        player_id = ctx.author.id
        dude = self.check_player(game_id, player_id)
        if dude is None:
            await ctx.respond("You are not in this game")
            return
        response = "Your Decision: \n\n"
        response += dude.get_decision()
        await ctx.respond(response)
        
    @commands.slash_command(name='my_response', guild_ids=[GUILD_ID])
    async def respond(self, ctx):
        """Respond to a prompt"""
        game_id = ctx.channel.id
        player_id = ctx.author.id
        dude = self.check_player(game_id, player_id)
        if dude is None:
            await ctx.respond("You are not in this game")
            return
        await ctx.respond(dude.get_response())

    @commands.slash_command(name='set_response', guild_ids=[GUILD_ID])
    async def set_response(self, ctx, response: str):
        """Set a response"""
        game_id = ctx.channel.id
        player_id = ctx.author.id
        game = Game(game_id)
        dude = self.check_player(game_id, player_id)
        if dude is None:
            await ctx.respond("You are not in this game")
            return
        dude.set_response(response)
        await ctx.respond("Remember to Ready if you are done deciding")
        

# =============================================================================
# Host Actions
# =============================================================================

    @commands.slash_command(name='host_time_passes', guild_ids=[GUILD_ID])
    async def host_time_passes(self, ctx):
        """Host Time Passes"""
        game_id = ctx.channel.id
        game = Game(game_id)
        game.time_passes()
        await ctx.respond("Time Passes")

    @commands.slash_command(name='host_upload_board', guild_ids=[GUILD_ID])    
    async def host_upload_board(self, ctx, island_board: discord.Attachment, invader_board: discord.Attachment = None):
        """Host Upload Board"""
        game_id = ctx.channel.id
        game = Game(game_id)
        game.island_board = island_board.url
        if invader_board is not None:
            game.invader_board = invader_board.url
        game.save_game()
        await ctx.respond("Boards Uploaded")

    @commands.slash_command(name='host_spirt_board', guild_ids=[GUILD_ID])
    async def host_spirt_board(self, ctx,
                               player0: discord.Member = None, board0: discord.Attachment = None,
                               player1: discord.Member = None, board1: discord.Attachment = None,
                               player2: discord.Member = None, board2: discord.Attachment = None,
                               player3: discord.Member = None, board3: discord.Attachment = None):
        """Host Spirt Board"""
        game_id = ctx.channel.id
        game = Game(game_id)
        values = [(player0, board0), (player1, board1), (player2, board2), (player3, board3)]
        valid_ids = game.get_players()
        players = game.get_player_names()
        await ctx.respond("Players: \n" + "\n".join(players))
        for value in values:
            if value[0] is None or value[0].id not in valid_ids:
                continue
            dude = Player(game_id, value[0].id)
            dude.board = value[1].url
            dude.save_player()
        await ctx.respond("Board(s) Uploaded")

    @commands.slash_command(name='override_give_card', guild_ids=[GUILD_ID])
    async def override_give_card(self, ctx, player: discord.Member, card_name: str):
        """Give Card to player from outside of deck"""
        game_id = ctx.channel.id
        dude = Player(game_id, player.id)
        with open("data/power_cards.json", "r") as file:
            power_cards = json.load(file)
        card = dude.fuzzy_power_choice(card_name, power_cards)
        dude.add_card(card[0])
        dude.save_player()
        await ctx.respond(f"Card Given \n\n `{card[0]['name']}`\n confidence: `{card[1]}`\n diff: `{card[2]}`")

    @commands.slash_command(name='host_draw_card', guild_ids=[GUILD_ID])
    async def host_draw_card(self, ctx, type:str, count:int = 1):
        """Draw a card for a player"""
        game_id = ctx.channel.id
        game = Game(game_id)
        if type.lower == "major":
            card = game.draw_power_card(False, count)
        elif type.lower == "minor":
            card = game.draw_power_card(True, count)
        else:
            await ctx.respond("Pick Major or Minor")
            return
        if card is None:
            await ctx.respond("Please Init the Power Deck")
            return
        response = "Cards Drawn: \n\n"
        await ctx.respond(response)
        embed_group = self.generate_card_imbeds(card)
        for embeds in embed_group:
            await ctx.respond(embeds=embeds)

    @commands.slash_command(name='host_list_unready', guild_ids=[GUILD_ID])
    async def host_ping_unready(self, ctx):
        """Ping Unready Players"""
        game_id = ctx.channel.id
        game = Game(game_id)
        players = game.unreadied(True)
        response = "Unreadied Players: \n\n"
        for player in players:
            response + "--" + str(player) + "\n"
        await ctx.respond(response)

    @commands.slash_command(name='host_set_decision', guild_ids=[GUILD_ID])
    async def host_set_decision(self, ctx, action: str, all = False,
                                player0: discord.Member = None,
                                player1: discord.Member = None,
                                player2: discord.Member = None,
                                player3: discord.Member = None):
        """Set a decision for a player"""
        game_id = ctx.channel.id
        game = Game(game_id)
        game_players = game.get_players()
        these_players = []
        if all:
            these_players = game_players
        else:
            tmp = [player0, player1, player2, player3]
            for player in tmp:
                if player is None or player.id not in game_players:
                    continue
                these_players.append(player.id)
        response = "Decision time: \n\n"
        for player in these_players:
            dude = Player(game_id, player.id)
            dude.set_decision(action)
            dude.set_ready(False)
            response += f"<@{dude.id}> \n"
        await ctx.respond(response)

# =============================================================================
#Board Actions
# =============================================================================


    @commands.slash_command(name='show_board', guild_ids=[GUILD_ID])
    async def show_board(self, ctx):
        """Show Board"""
        game_id = ctx.channel.id
        game = Game(game_id)
        embeds = []
        embeds.append(discord.Embed(url="https://sick.oberien.de/", title="The Island").set_image(url=game.island_board))
        embeds.append(discord.Embed(url="https://sick.oberien.de/", title="The Island").set_image(url=game.invader_board))
        await ctx.respond(embeds=embeds)

    @commands.slash_command(name='my_board', guild_ids=[GUILD_ID])
    async def my_board(self, ctx):
        """Show Player Board"""
        game_id = ctx.channel.id
        player_id = ctx.author.id
        dude = Player(game_id, player_id)
        embeds = []
        embeds.append(discord.Embed(url="https://sick.oberien.de/", title="Spirit Board").set_image(url=dude.board))
        await ctx.respond(embeds=embeds)


# =============================================================================
#     Admin Section
# =============================================================================    
        
    @commands.slash_command(name='admin', guild_ids=[GUILD_ID])
    async def purge_table(self, ctx, cmd: str, option1:str = "", option2:str = ""):
        discord_id = ctx.author.id
        if str(discord_id) != str(EALON_ID):
            await ctx.respond("Only <@" + str(EALON_ID) + "> can run that commnand.")
            return
           
        if cmd == "purge_db":
            """Purge a table"""
            try:
                self.sql.truncate_table(option1)
                await ctx.respond("Truncate Table " + option1) 
            except:
                await ctx.respond("FAILED to Truncate Table " + option1)