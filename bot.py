#!/usr/bin/env python3
# encoding: utf-8

__all__ = ('bot', 'config', 'db_cog', 'emotes_cog', 'api_cog')

import asyncio

from emote_collector import EmoteCollector
from emote_collector import utils

config = utils.load_json_compat('config.py')

loop = asyncio.get_event_loop()
bot = EmoteCollector(config=config, loop=loop)
loop.run_until_complete(bot._init_db())
bot.load_extension('emote_collector.extensions.db')
bot.load_extension('emote_collector.extensions.emote')
bot.load_extension('emote_collector.extensions.api')
db_cog = bot.get_cog('Database')
emotes_cog = bot.get_cog('Emotes')
api_cog = bot.get_cog('API')
loop.run_until_complete(bot.login(config['tokens'].pop('discord')))
