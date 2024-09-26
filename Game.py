import json
import rapidfuzz
import os
from PowerDeck import PowerDeck
from Player import Player


class Game:
    def __init__(self, game_id):
        self.game_id = str(game_id)
        self.load_game()

    def load_game(self):
        file_path = 'active_games/' + self.game_id + '/game.json'
        folder_path = 'active_games/' + self.game_id
        #check if the folder exists
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # Check if the game file exists
        try:
            with open(file_path, "r") as file:
                game_data = json.load(file)
            for key, value in game_data.items():
                setattr(self, key, value)
            return
        except FileNotFoundError:
            print("Player file not found, making new one")
            id = self.game_id
            with open("data/game_template.json", "r") as file:
                game_data = json.load(file)
            print(self.game_id)
            for key, value in game_data.items():
                setattr(self, key, value)
            self.game_id = id
            self.save_game()
            return

    def save_game(self):
        file_path = 'active_games/' + self.game_id + '/game.json'
        with open(file_path, "w") as file:
            json.dump(self.list_attributes(), file, indent=4)

    def list_attributes(self):
        result = {}
        for key, value in self.__dict__.items():
            result[key] = value
        return result
    
    def purge_game(self):
        #remove the game folder
        try:
            folder_path = 'active_games/' + self.game_id
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(folder_path)
        except FileNotFoundError:
            pass
    
    def add_player(self, discord_id, player_name):
        player_ids = [player["id"] for player in self.players]
        if discord_id in player_ids:
            return False
        player = Player(self.game_id, discord_id)
        player.name = player_name
        player.pending_action = []
        #Add a player to discord ID mapping
        self.players.append({"id":discord_id, "name" : player_name})
        player.save_player()

    def get_player_id(self, name):
        '''Returns the discord id of the player, the confidence of the match, 
        and the difference between the best and second best matches'''
        return self.fuzzy_choice(name, self.player_names)

    def get_players(self):
        ids = [player["id"] for player in self.players]
        return ids
    
    def get_player_names(self):
        names = [player["name"] for player in self.players]
        return names

    def remove_player(self, discord_id):
        player_ids = [player["id"] for player in self.players]
        if discord_id in player_ids:
            player = Player(self.game_id, discord_id)
            try:
                os.remove(str(player))
            except FileNotFoundError:
                pass
            for i, player in enumerate(self.players):
                if player["id"] == discord_id:
                    del self.players[i]
                    self.save_game()
                    break
            return True
        else:
            return False
    
    def fuzzy_choice(self, name : str, list_of_names : list, scorer=rapidfuzz.fuzz.partial_ratio):
        '''
        Returns a list:
        0 is the best match, 
        1 is the best match confidence, 
        2 is the difference between the best and second best matches
        '''
        #make list lowercase    
        choices = [lname.lower() for lname in list_of_names]
        #fuzzy search
        result = rapidfuzz.process.extract(name.lower(), choices, scorer=scorer, limit=2)
        #return the card
        if result is None:
            return None
        elif len(result) == 1:
            return [list_of_names[result[0][2]], result[0][1], 100]
        else:
            con_0 = result[0][1]
            con_1 = result[1][1]
            diff = con_0 - con_1
            return [list_of_names[result[0][2]], con_0, diff]
                           
    def time_passes(self):
        self.turn_number += 1
        for player in self.players:
            player = Player(self.game_id, player["id"])
            player.discard_played()
        self.set_undo_point()
        self.save_game()

    def set_undo_point(self):
        for player in self.players:
            player = Player(self.game_id, player["id"])
            player.set_cards_undo_save()
            player.set_pending_action_undo_save()
            player.save_player()

    def assign_spirit(self, player_id, spirit:str):
        with open("data/spirits.json", "r") as file:
            spirits_data = json.load(file)
        spirits_names = [spirit["name"] for spirit in spirits_data]
        tmp = self.fuzzy_choice(spirit, spirits_names)
        spirit_pick = tmp[0]
        del spirits_data
        with open("data/power_cards.json", "r") as file:
            powercards = json.load(file)
        player = Player(self.game_id, player_id)
        player.spirit = spirit_pick
        player.cards = []
        for card in powercards:
            if card["type"] == spirit_pick.replace(" ", "_"):
                player.add_card(card)
        player.set_cards_undo_save()
        player.save_player()
        self.save_game()
        #return confidence values
        return tmp
    
    def draw_power_card(self, minor:bool, count:int = 1):
        deck = PowerDeck(self.game_id)
        print(deck)
        if len(deck.minor_data) == 0 or len(deck.major_data) == 0:
            return None
        cards = deck.draw_cards(minor, count)
        self.card_bk = cards
        return cards
    
    def set_played_sets(self, wanted_sets : list = None, excluded_sets : list = None):
        with open("data/sets.json", "r") as file:
            valild_sets = json.load(file)
        
        if wanted_sets is not None:
            for i, name in enumerate(wanted_sets):
                if name.lower() == "base":
                    name = "Spirit_Island"
                wanted_sets[i] = self.fuzzy_choice(name, valild_sets)[0]
            self.sets = wanted_sets
        elif excluded_sets is not None:
            for i, name in enumerate(excluded_sets):
                excluded_sets[i] = self.fuzzy_choice(name, valild_sets)[0]
            for excluded_set in excluded_sets:
                valild_sets.remove(excluded_set)
            self.sets = valild_sets
        else:
            self.sets = valild_sets
        
        self.save_game()

    def init_power_decks(self):
        if len(self.sets) == 0:
            return False
        try:
            os.remove('active_games/' + self.game_id + '/minor_power_cards.json')
            os.remove('active_games/' + self.game_id + '/major_power_cards.json')
        except FileNotFoundError:
            pass
        deck = PowerDeck(self.game_id, self.sets)
        deck.generate_deck(True, self.sets)
        deck.generate_deck(False, self.sets)
        self.save_game()

    def check_player_ready(self):
        for player in self.players:
            player = Player(self.game_id, player["id"])
            if player.ready is False and str(player.discord_id) != str(self.host):
                return False
        return True
    
    def unreadied(self, name = True):
        list = []
        for player in self.players:
            player = Player(self.game_id, player["id"])
            if player.ready is False:
                if name:
                    list.append(player.name)
                else:
                    list.append(player.discord_id)
        return list