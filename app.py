#!/usr/bin/env python3
# encoding: utf-8

import asyncio
from urllib.parse import parse_qsl

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
	if isinstance(query_dict, str):
		query_dict = dict(parse_qsl(query_dict.lstrip('?')))
	new = {**query_dict, **params}
	return urlencode(new)

def remove_query_param(query_dict, *params):
	if isinstance(query_dict, str):
		query_dict = parse_qsl(query_dict.lstrip('?'))
	d = dict(query_dict)
	for param in params:
		d.pop(param, None)
	return urlencode(d)

environment.globals['emote_url'] = emote_utils.url
environment.globals['v2_onion'] = config['onions'][2]
environment.globals['v3_onion'] = config['onions'][3]
environment.globals['add_query_param'] = add_query_param
environment.globals['remove_query_param'] = remove_query_param

@routes.get('/index')
async def index(request):
	return await render_template('index.html')

@routes.get('/list')
@routes.get('/list/{author:\d+}')
async def list(request):
	author = _int_or_none(request.match_info.get('author'))
	allow_nsfw = 'allow_nsfw' in request.query
	before = request.query.get('before')
	after = request.query.get('after')
	if before is not None and after is not None:
		raise web.HTTPBadRequest(reason='only one of before, after may be specified')

	return await render_template('list.html',
		emotes=await db_cog.all_emotes_keyset(author, allow_nsfw=allow_nsfw, before=before, after=after),
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
