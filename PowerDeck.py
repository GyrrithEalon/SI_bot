import json
import os
import random

class PowerDeck:
    def __init__(self, game_id, empty=None):
        self.minor_file = "active_games/" + game_id + "/minors.json"
        self.major_file = "active_games/" + game_id + "/majors.json"
        self.minor_data = []
        self.major_data = []

        # Check if the JSON files exist
        if os.path.exists(self.minor_file):
            self.load_power_deck(self.minor_file, minor=True)

        if os.path.exists(self.major_file):
            self.load_power_deck(self.major_file, minor=False)
        
        self.save_power_decks()

    def generate_deck(self, minor, sets_list=None):
        if minor:
            card_type = "minor"
        else:
            card_type = "major"

        #read master power deck
        with open("data/power_cards.json", "r") as file:
            master_power_deck = json.load(file)
        
        # Make decks
        data = self.filter_data(master_power_deck, "type", [card_type])

        #filter based on sets
        if minor:
            if sets_list:
                data = self.filter_data(data, "set", sets_list)
                random.shuffle(data)
                self.minor_data = data
        else:
            if sets_list:
                data = self.filter_data(data, "set", sets_list)
                random.shuffle(data)
                self.major_data = data
        self.save_power_decks()
        return
    
    def filter_data(self, data, field, value_list):
        filtered_data = []
        lower_value_list = [value.lower() for value in value_list]
        for row in data:
            field_value = row.get(field)
            if field_value and field_value.lower() in lower_value_list:
                filtered_data.append(row)
        return filtered_data

    def load_power_deck(self, file_name, minor):
        with open(file_name, 'r') as file:
            data = json.load(file)
            if minor:
                self.minor_data = data
            else:
                self.major_data = data

    def save_power_decks(self):
            # Save the lists as JSON files
        with open(self.minor_file, 'w') as file:
            json.dump(self.minor_data, file, indent=4)
        with open(self.major_file, 'w') as file:
            json.dump(self.major_data, file, indent=4)

    def draw_card(self, minor):
        if minor:
            card = self.minor_data.pop()
        else:
            card = self.major_data.pop()
        self.save_power_decks()
        return card
    
    def draw_cards(self, minor, number):  
        cards = []
        for _ in range(number):
            cards.append(self.draw_card(minor))
        return cards
    
    def shuffle_deck(self, minor):
        if minor:
            random.shuffle(self.minor_data)
        else:
            random.shuffle(self.major_data)
        self.save_power_decks()

    def count_cards(self, minor):
        if minor:
            return len(self.minor_data)
        else:
            return len(self.major_data)

    def add_card_to_deck(self, card, minor, position=0):
        if isinstance(card, dict) and all(key in card for key in ['name', 'set', 'type', 'status']):
            if minor:
                if position is not None and isinstance(position, int) and 0 <= position < len(self.minor_data):
                    self.minor_data.insert(position, card)
                else:
                    self.minor_data.append(card)
            else:
                if position is not None and isinstance(position, int) and 0 <= position < len(self.major_data):
                    self.major_data.insert(position, card)
                else:
                    self.major_data.append(card)
            self.save_power_decks()