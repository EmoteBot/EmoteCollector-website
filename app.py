#!/usr/bin/env python3
# encoding: utf-8

import asyncio
from functools import partial

from aiohttp import web
from emote_collector import utils
from emote_collector.utils import emote as emote_utils
import jinja2

from bot import *
from utils import urlencode

app = web.Application()
routes = web.RouteTableDef()

environment = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'), enable_async=True)

environment.trim_blocks = True
environment.lstrip_blocks = True

def add_query_param(query_dict, **params):
	new = {**query_dict, **params}
	return urlencode(new)

def remove_query_param(query_dict, *params):
	d = dict(query_dict)
	for param in params:
		d.pop(param, None)
	return urlencode(d)

environment.globals['emote_url'] = emote_utils.url
environment.globals['v2_onion'] = config['onions'][2]
environment.globals['v3_onion'] = config['onions'][3]

@routes.get('/list')
@routes.get('/list/{author:\d+}')
async def list(request):
	author = _int_or_none(request.match_info.get('author'))
	allow_nsfw = 'allow_nsfw' in request.query
	after = request.query.get('after')

	return await render_template('list.html',
		emotes=await db_cog.all_emotes_keyset(author, allow_nsfw=allow_nsfw, after=after),
		add_query_param=partial(add_query_param, request.query),
		remove_query_param=partial(remove_query_param, request.query),
		author=author,
		request=request,
		allow_nsfw=allow_nsfw)

async def render_template(template, **kwargs):
	rendered = await environment.get_template(template).render_async(**kwargs)
	return web.Response(text=rendered, content_type='text/html')

def _int_or_none(x):
	try:
		return int(x)
	except (TypeError, ValueError):
		return None

app.add_routes(routes)
