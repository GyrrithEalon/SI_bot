# -*- coding: utf-8 -*-
"""
Created on Tue Apr 27 15:12:48 2024

@author: Ealon
"""

#Start Code
import os
from discord.ext import commands
from dotenv import load_dotenv
from bot import CommandsHandler


#insalls for miniconda env
#PYTHON 3.11

#pip install py-cord
#pip install nest_asyncio
#pip install python-dotenv
#pip install table2ascii
#pip install rapidfuzz



# =============================================================================
# Load Env
# =============================================================================
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# =============================================================================
# Start Bot
# =============================================================================
bot = commands.Bot()
bot.add_cog(CommandsHandler(bot))
bot.run(TOKEN)
