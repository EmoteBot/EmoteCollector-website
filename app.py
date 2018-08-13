#!/usr/bin/env python3
# encoding: utf-8

from aiohttp import web
from emoji_connoisseur.utils import emote as emote_utils
import jinja2

import db

app = web.Application()
routes = web.RouteTableDef()

environment = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'), enable_async=True)

environment.trim_blocks = True
environment.lstrip_blocks = True

environment.globals['emote_url'] = emote_utils.url
environment.globals['v2_onion'] = db.config['onions'][2]
environment.globals['v3_onion'] = db.config['onions'][3]


@routes.get('/list')
@routes.get('/list/{author:\d+}')
async def list(request):
	author = _int_or_none(request.match_info.get('author'))

	rendered = await environment.get_template('list.html').render_async(
		emotes=db.emotes(author),
		author=author,
		request=request)
	return web.Response(text=rendered, content_type='text/html')

def _int_or_none(x):
	try:
		return int(x)
	except (TypeError, ValueError):
		return None

app.add_routes(routes)
