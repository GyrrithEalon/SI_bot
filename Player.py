import json
import rapidfuzz
import os
from PowerDeck import PowerDeck


class Player:
    def __init__(self, game_id, discord_id):
        self.load_player(str(game_id), str(discord_id))

    def __str__(self) -> str:
        return f"active_games/{self.game_id}/player_{self.discord_id}.json"
    
    #prep the player utils
    def load_player(self, game_id, discord_id):
        file_path = f"active_games/{game_id}/player_{discord_id}.json"
        # Check if the player file exists
        try:
            with open(file_path, "r") as file:
                players_data = json.load(file)
            for key, value in players_data.items():
                setattr(self, key, value)
            return
        except FileNotFoundError:
            print("Player file not found, making new one")
            with open("data/player_template.json", "r") as file:
                players_data = json.load(file)
            for key, value in players_data.items():
                setattr(self, key, value)
            self.game_id = game_id
            self.discord_id = discord_id
            self.save_player()
            return

    def save_player(self):
        file_path = f"active_games/{self.game_id}/player_{self.discord_id}.json"
        with open(file_path, "w") as file:
            json.dump(self.list_attributes(), file, indent=4)

    def list_attributes(self):
        result = {}
        for key, value in self.__dict__.items():
            result[key] = value
        return result
    
    def set_cards_undo_save(self):
        self.cards_bk = self.cards.copy()
        self.save_player()
        return True
    
    def set_pending_action_undo_save(self):
        self.pending_action_bk = self.pending_action.copy()
        self.save_player()
        return True
    


#card functions
    def fuzzy_power_choice(self, card_name, list_of_cards, scorer=rapidfuzz.fuzz.partial_ratio):
        #make list of cad names
        choices = []
        if len(list_of_cards) == 0:
            return None
        for card in list_of_cards:
            choices.append(card["name"].lower())
        #fuzzy search
        result = rapidfuzz.process.extract(card_name.lower(), choices, scorer=scorer, limit=2)
        #return the card
        if result is None:
            return None
        elif len(result) == 1:
            return [list_of_cards[result[0][2]], result[0][1], 100]
        else:
            con_0 = result[0][1]
            con_1 = result[1][1]
            diff = con_0 - con_1
            return [list_of_cards[result[0][2]], con_0, diff]

    def add_card(self, card):
        """
        Add card object to card list
        """
        card["status"] = "hand"
        self.cards.append(card)
    
    def discard_cards(self, card_names: list):
        """
        Discard a list of cards, suply card names
        """
        found_cards = []
        lowest_score = 100
        for card_name in card_names:
            found_card = self.fuzzy_power_choice(card_name, self.cards)
            if found_card is not None:
                for card in self.cards:
                    if card["name"] == found_card[0]["name"]:
                        card["status"] = "discard"
                        found_cards.append(card["name"])
                if found_card[2] < lowest_score:
                    lowest_score = found_card[2]
        self.save_player()
        return [found_cards, lowest_score]
    
    def discard_played(self):
        """
        Discard all played cards
        """
        for card in self.cards:
            if card["status"] == "inplay":
                card["status"] = "discard"
        self.save_player()
            
    def play_cards(self, card_names):
        """
        Play a list of cards, suply card names
        """
        lowest_score = 100
        found_cards = []
        if card_names == ["all"]:
            for card in self.cards:
                if card["status"] == "hand":
                    card["status"] = "inplay"
                    found_cards.append(card["name"])
            self.save_player()
            return [found_cards, 100]
        for card_name in card_names:
            found_card = self.fuzzy_power_choice(card_name, self.cards)
            if found_card is not None:
                for card in self.cards:
                    if card["name"] == found_card[0]["name"] and card["status"] == "hand":
                        card["status"] = "inplay"
                        found_cards.append(card["name"])
                if found_card[2] < lowest_score:
                    lowest_score = found_card[2]
        self.save_player()
        return [found_cards, lowest_score]
            
    def reclaim_cards(self, card_names):
        """
        Replace named cards
        """
        lowest_score = 100
        found_cards = []
        if card_names == ["all"]:
            for card in self.cards:
                if card["status"] == "discard":
                    card["status"] = "hand"
                    found_cards.append(card["name"])
            self.save_player()
            return [found_cards, 100]
        for card_name in card_names:
            found_card = self.fuzzy_power_choice(card_name, self.cards)
            if found_card is not None:
                for card in self.cards:
                    if found_card[2] < lowest_score:
                        lowest_score = found_card[2]
                    if card["name"] == found_card[0]["name"] and card["status"] == "discard":
                        card["status"] = "hand"
                        found_cards.append(card["name"])
        self.save_player()
        return [found_cards, lowest_score]

    def forget_cards(self, card_names):
        """
        Forget named cards
        """
        #backup hand
        lowest_score = 100
        found_cards = []
        for card_name in card_names:
            found_card = self.fuzzy_power_choice(card_name, self.cards)
            if found_card is not None:
                for card in self.cards:
                    if card["name"] == found_card[0]["name"]:
                        if found_card[2] < lowest_score:
                            lowest_score = found_card[2]
                        card["status"] = "forget"
                        found_cards.append(card["name"])
        self.save_player()
        return [found_cards, lowest_score]

    def undo_card_action(self):
        if len(self.cards_bk) > 0:
            self.cards = self.cards_bk.copy()
            self.save_player()
        return True

#getting powers
    def draft_powers(self, minor, number = 4):
        #load the power deck
        deck = PowerDeck(self.game_id)
        if len(deck.minor_data) == 0 or len(deck.major_data) == 0:
            return None
        if len(self.pending_card_choice):
            return False
        if minor:
            self.pending_card_choice = deck.draw_cards(True, number)
            del deck
        else:
            self.pending_card_choice = deck.draw_cards(False, number)
        self.save_player()
        return True

    def choose_power(self, card_name):
        #backup hand and power coices
        self.set_cards_undo_save()
        self.set_pending_action_undo_save()
        #choose the power
        card_pick = self.fuzzy_power_choice(card_name, self.pending_card_choice)
        #add the power to the cards
        if card_pick is not None:
            self.pending_card_choice = []
            self.add_card(card_pick[0])
            self.save_player()
            return card_pick
        else:
            return None
    
    def undo_power_choice(self):
        if len(self.pending_card_choice_bk) > 0:
            self.pending_card_choice = self.pending_card_choice_bk.copy()
            self.cards = self.cards_bk.copy()
            self.pending_card_choice_bk_ready = False
            self.save_player()
            return True
        else:
            return False

#power cards getter functions
    def get_hand(self):
        hand = []
        for card in self.cards:
            if card["status"] == "hand":
                hand.append(card)
        return hand
    def get_inplay(self):
        inplay = []
        for card in self.cards:
            if card["status"] == "inplay":
                inplay.append(card)
        return inplay
    def get_discard(self):      
        discard = []
        for card in self.cards:
            if card["status"] == "discard":
                discard.append(card)
        return discard
    def get_forget(self):       
        forget = []
        for card in self.cards:
            if card["status"] == "forget":
                forget.append(card)
        return forget
    def get_pending(self):    
        return self.pending_card_choice

    def get_all(self):
        return self.cards
    
#pending action functions

    def set_ready(self, ready = None):
        """toggle ready status, or set it to a specific value"""
        if ready is not None:
            self.ready = ready
        else:
            self.ready = not self.ready
        self.save_player()
        return self.ready
    
    def get_response(self):
        return self.response_tape[self.response_index]
        
    def set_response(self, response):
        if self.response_index < len(self.response_tape) - 1: #If index is not at the end of the tape
            for i in range(len(self.response_tape)-1, self.response_index, -1):
                self.response_tape.pop(i)
        self.response_tape.append(response)
        self.response_index += 1
        self.save_player()
        return True
    
    def undo_response(self):
        if self.response_index > 0:
            self.response_index -= 1
        self.save_player()
        return True

    def redo_response(self):
        if len(self.response_tape)-1 > self.response_index:
            self.response_index += 1
        self.save_player()
        return True

    def commit_response(self):
        self.response_log.append(self.response_tape[self.response_index])
        self.response_tape = []
        self.response_index = 0
        return True
        
    def set_required_action(self, action:str):
        self.pending_action = action
        self.save_player()
        return True
    
    def set_decision(self, decision):
        self.decision = decision
        self.save_player()
        return True
    
    def get_decision(self):
        return self.decision
    


