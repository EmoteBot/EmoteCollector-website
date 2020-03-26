#!/usr/bin/env python3
# encoding: utf-8

import asyncio
from functools import partial
from urllib.parse import parse_qsl

import jinja2
from aiohttp import web
from emote_collector import utils
from emote_collector.utils import emote as emote_utils
from yarl import URL

from bot import *
from utils import is_safe_url, urlencode, url, render_template, parse_keyset_params

app = web.Application()
routes = web.RouteTableDef()

environment = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'), enable_async=True)

environment.trim_blocks = True
environment.lstrip_blocks = True

render_template = partial(render_template, environment=environment)

def _add_query_param(query_dict, **params):
	return {**query_dict, **params}

def add_query_param(request, **params):
	return request.path + urlencode(_add_query_param(request.query, **params))

def _remove_query_param(query_dict, *params):
	d = query_dict.copy()
	for param in params:
		d.pop(param, None)
	return d

def remove_query_param(request, *params):
	return request.path + urlencode(_remove_query_param(request.query, *params))

def update_query_param(request, *remove, **add,):
	return request.path + urlencode(_add_query_param(_remove_query_param(request.query, *remove), **add))

environment.globals['v2_onion'] = config['onions'][2]
environment.globals['v3_onion'] = config['onions'][3]
environment.globals['emote_url'] = emote_utils.url
for func in add_query_param, remove_query_param, update_query_param:
	environment.globals[func.__name__] = func
del func

@routes.get('/index')
async def index(request):
	return await render_template('index.html', url=url(request, include_path=False))

ONE_YEAR = 60 * 60 * 24 * 365

@routes.get('/confirm-18+')
async def confirm_18plus(request):
	target = request.query.get('next')
	if target is None:
		return web.HTTPTemporaryRedirect('/')
	if not is_safe_url(request, target):
		return web.HTTPBadRequest()
	if '18+' in request.cookies:
		return web.HTTPTemporaryRedirect(target)
	is_18plus = request.query.get('confirm')
	if is_18plus is None:
		return await render_template('confirm-18+.html', target=target)
	elif is_18plus == 'false':
		response = web.HTTPTemporaryRedirect('/')
		return response
	response = web.HTTPTemporaryRedirect(target)
	response.set_cookie('18+', '', max_age=ONE_YEAR)
	return response

@routes.get('/nsfw-handbook')
async def nsfw_handbook(request):
	if '18+' not in request.cookies:
		# incredible that yarl.URL.with_query does not accept yarl.URLs lmao
		url = URL('/confirm-18+').with_query(dict(next=str(request.rel_url)))
		return web.HTTPTemporaryRedirect(url)
	return await render_template('nsfw-handbook.html')

@routes.get('/list')
@routes.get('/list/{author:\d+}')
async def list_(request):
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
		url=url(request),
		allow_nsfw=allow_nsfw)

@routes.get('/e0-list')
async def e0_list(request):
	return web.FileResponse('templates/e0-list.html')

def _int_or_none(x):
	try:
		return int(x)
	except (TypeError, ValueError):
		return None

app.add_routes(routes)
