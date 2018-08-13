#!/usr/bin/env python3
# encoding: utf-8

__all__ = ('bot', 'config', 'db_cog', 'emotes_cog', 'api_cog')

import asyncio

from emoji_connoisseur import EmojiConnoisseur
from emoji_connoisseur import utils

with open('config.py') as config_file:
	config = utils.load_json_compat(config_file.read())
del config_file

loop = asyncio.get_event_loop()
bot = EmojiConnoisseur(config=config, loop=loop)
loop.run_until_complete(bot._init_db())
bot.load_extension('emoji_connoisseur.extensions.db')
bot.load_extension('emoji_connoisseur.extensions.emote')
bot.load_extension('emoji_connoisseur.extensions.api')
db_cog = bot.get_cog('Database')
emotes_cog = bot.get_cog('Emotes')
api_cog = bot.get_cog('API')
loop.run_until_complete(bot.login(config['tokens'].pop('discord')))
