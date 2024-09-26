# -*- coding: utf-8 -*-
"""
Created on Wed Jul 26 16:54:47 2023

@author: timsargent
"""

from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

import json

# Load the JSON data from the file
with open('data/power_cards.json', 'r') as file:
    data = json.load(file)

# Iterate through each entry and add the "status" key
for entry in data:
    entry["status"] = "InDeck"

# Save the modified JSON data back to the file
with open('power_cards.json', 'w') as file:
    json.dump(data, file, indent=4)