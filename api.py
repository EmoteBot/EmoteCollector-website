#!/usr/bin/env python3
# encoding: utf-8

import asyncio

from emoji_connoisseur import EmojiConnoisseur
from emoji_connoisseur.extensions import api as api_extension

from db import config

loop = asyncio.get_event_loop()
bot = EmojiConnoisseur(config=config, loop=loop)
loop.run_until_complete(bot.login(config['tokens'].pop('discord')))
