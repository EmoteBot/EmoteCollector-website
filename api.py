#!/usr/bin/env python3
# encoding: utf-8

import asyncio
from datetime import datetime
import json

from aiohttp import web
from emoji_connoisseur import EmojiConnoisseur
from emoji_connoisseur.utils import errors as emoji_connoisseur_errors
import jinja2

from db import config

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

app = web.Application()
routes = web.RouteTableDef()
api_prefix = '/api/v0'

environment = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
environment.globals['filter'] = filter

def db_route(func):
	async def wrapped(request):
		try:
			return await func(request)
		except emoji_connoisseur_errors.EmoteNotFoundError:
			raise HTTPNotFound('emote does not exist')
		except emoji_connoisseur_errors.NoMoreSlotsError:
			raise HTTPInternalServiceError('no more slots')

	return wrapped

def requires_auth(func):
	func = db_route(func)

	async def authed_route(request):
		token = request.headers.get('Authorization')
		if not token:
			raise HTTPUnauthorized('no token provided')
		user_id = await api_cog.validate_token(token.encode())
		if not user_id:
			raise HTTPUnauthorized('invalid or incorrect token provided')

		request.user_id = user_id

		try:
			return await func(request)
		except emoji_connoisseur_errors.EmoteExistsError:
			raise HTTPBadRequest('emote exists')
		except emoji_connoisseur_errors.PermissionDeniedError:
			raise HTTPUnauthorized('you do not have permission to modify this emote')

	return authed_route

@routes.patch(api_prefix+'/emote/{name}')
@requires_auth
async def rename(request):
	json = await request.json()
	old_name = request.match_info['name']
	new_name = json['new_name']
	user_id = request.user_id

	return emote_response(await db_cog.rename_emote(old_name, new_name, user_id))

@routes.get(api_prefix+'/emote/{name}')
@db_route
async def emote(request):
	return emote_response(await db_cog.get_emote(request.match_info['name']))

@routes.get(api_prefix+'/docs')
async def docs(request):
	return render_template('api_doc.html')

app.add_routes(routes)

def _marshal_emote(emote):
	EPOCH = 1518652800  # February 15, 2018, the date of the first emote
	MAX_JSON_INT = 2**53

	for key, value in emote.copy().items():
		if isinstance(value, int) and value > MAX_JSON_INT:
			emote[key] = str(value)
		if isinstance(value, datetime):
			emote[key] = int(value.timestamp()) - EPOCH

def emote_response(emote):
	_marshal_emote(emote)
	return web.Response(text=json.dumps(emote))

def render_template(template, **kwargs):
	return web.Response(
		text=environment.get_template(template).render(**kwargs),
		content_type='text/html')

class JSONHTTPError(web.HTTPException):
	def __init__(self, reason):
		super().__init__(text=json.dumps(dict(status=self.status_code, message=reason)))

class HTTPBadRequest(web.HTTPBadRequest, JSONHTTPError):
	# god i love multiple inheritance
	pass

class HTTPUnauthorized(web.HTTPUnauthorized, JSONHTTPError):
	pass

class HTTPNotFound(web.HTTPNotFound, JSONHTTPError):
	pass

class HTTPInternalServerError(web.HTTPInternalServerError, JSONHTTPError):
	pass
