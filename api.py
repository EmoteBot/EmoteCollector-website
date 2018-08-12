#!/usr/bin/env python3
# encoding: utf-8

import asyncio
from datetime import datetime
import json

from aiohttp import web
from emoji_connoisseur import EmojiConnoisseur
from emoji_connoisseur.utils import errors as emoji_connoisseur_errors

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



def requires_auth(func):
	async def authed_route(request):
		token = request.headers.get('Authorization')
		if not token:
			raise HTTPUnauthorized('no token provided')
		user_id, secret = await api_cog.validate_token(token.encode())
		if not user_id:
			raise HTTPUnauthorized('invalid or incorrect token provided')

		try:
			return await func(request, user_id=user_id)
		except emoji_connoisseur_errors.EmoteExistsError:
			raise HTTPBadRequest('emote exists')
		except emoji_connoisseur_errors.PermissionDeniedError:
			raise HTTPUnauthorized('you do not have permission to modify this emote')
		except emoji_connoisseur_errors.EmoteNotFoundError:
			raise HTTPNotFound('emote exists')
		except emoji_connoisseur_errors.NoMoreSlotsError:
			raise HTTPInternalServiceError('no more slots')

	return authed_route

@routes.patch(api_prefix+'/emote/{name}')
@requires_auth
async def rename(request, *, user_id):
	json = await request.json()
	old_name = request.match_info['name']
	new_name = json['new_name']

	return json_response(await db_cog.rename_emote(old_name, new_name, user_id))

app.add_routes(routes)

class EmojiConnoisseurDateTimeEncoder(json.JSONEncoder):
	EPOCH = 1518652800  # February 15, 2018, the date of the first emote
	MAX_JSON_INT = 2**53

	def default(self, obj):
		if isinstance(obj, datetime):
			return int(obj.timestamp()) - self.EPOCH
		if isinstance(obj, int) and obj > self.MAX_JSON_INT:
			return str(obj)  # JSON compat
		return super().default(obj)

def json_response(obj):
	return web.Response(text=json.dumps(obj, cls=EmojiConnoisseurDateTimeEncoder))

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
