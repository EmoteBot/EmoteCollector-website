from datetime import datetime
import io

from aiohttp import web
import discord
from emote_collector.utils import errors as emote_collector_errors
from emote_collector import utils as emote_collector_utils

from bot import *
from .constants import API_PREFIX
from .errors import *

routes = web.RouteTableDef()

def db_route(func):
	async def wrapped(request):
		try:
			return await func(request)
		except emote_collector_errors.EmoteNotFoundError:
			raise HTTPNotFound('emote does not exist')

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
		except emote_collector_errors.EmoteExistsError:
			raise HTTPConflict('emote exists', name=request.match_info['name'])
		except emote_collector_errors.EmoteDescriptionTooLongError as exception:
			raise HTTPRequestEntityTooLarge(
				'emote description too long',
				actual_size=exception.actual_length,
				max_size=exception.limit)
		except emote_collector_errors.PermissionDeniedError:
			raise HTTPForbidden('you do not have permission to modify this emote')
		except emote_collector_errors.NoMoreSlotsError:
			raise HTTPInternalServerError('no more slots')
		except discord.HTTPException as exception:
			status = exception.response.status
			cls = errors[status]

			raise cls(
				'HTTP error from Discord: {exception.text}'.format(exception=exception),
				error=dict(
					status=status,
					reason=exception.response.reason,
					text=exception.text))

	return authed_route

@routes.get(API_PREFIX+'/emote/{name}')
@db_route
async def emote(request):
	name = request.match_info['name']

	emote = await db_cog.get_emote(name)
	emote.usage = await db_cog.get_emote_usage(emote)
	return emote_response(emote)

@routes.get(API_PREFIX+'/login')
@requires_auth
async def login(request):
	return web.json_response(str(request.user_id))

@routes.patch(API_PREFIX+'/emote/{name}')
@requires_auth
async def edit_emote(request):
	name = request.match_info['name']
	user_id = request.user_id

	json = await request.json()

	if 'description' not in json and 'name' not in json:
		raise HTTPBadRequest('no edits were specified')

	if 'description' in json:
		result = await db_cog.set_emote_description(name, json['description'], user_id)

	if 'name' in json:
		result = await db_cog.rename_emote(name, json['name'], user_id)

	return emote_response(result)

@routes.delete(API_PREFIX+'/emote/{name}')
@requires_auth
async def delete_emote(request):
	name = request.match_info['name']
	user_id = request.user_id

	return emote_response(await db_cog.remove_emote(name, user_id))

@routes.put(API_PREFIX+'/emote/{name}/{url}')
@requires_auth
async def create_emote(request):
	name, url = map(request.match_info.get, ('name', 'url'))
	author = request.user_id

	try:
		return emote_response(await emotes_cog.add_from_url(name, url, author))
	except emote_collector_errors.URLTimeoutError:
		raise HTTPBadRequest('retrieving the image timed out')
	except emote_collector_errors.ImageResizeTimeoutError:
		raise HTTPRequestEntityTooLarge('resizing the image took too long')
	except ValueError:
		raise HTTPBadRequest('invalid URL')

@routes.put(API_PREFIX+'/emote/{name}')
@requires_auth
async def create_emote_from_data(request):
	if not request.can_read_body:
		raise HTTPBadRequest('image data required in body')

	name = request.match_info['name']
	author = request.user_id
	image = await request.read()

	try:
		return emote_response(await emotes_cog.create_emote_from_bytes(name, author, image))
	except emote_collector_errors.ImageResizeTimeoutError:
		raise HTTPRequestEntityTooLarge('image resize took too long')
	except emote_collector_errors.InvalidImageError:
		raise HTTPUnsupportedMediaType('PNG, GIF, or JPEG required in body')

@routes.get(API_PREFIX+'/emotes')
async def list_(request):
	allow_nsfw = _should_allow_nsfw(request)
	after = request.rel_url.query.get('after')
	before = request.rel_url.query.get('before')
	limit = int(request.rel_url.query.get('limit', 100))
	if before is not None and after is not None:
		raise HTTPBadRequest('only one of before, after may be specified')

	results = list(map(_marshal_emote,
		await db_cog.all_emotes_keyset(allow_nsfw=allow_nsfw, after=after, before=before, limit=limit)))
	return web.json_response(results)

@routes.get(API_PREFIX+'/emotes/{author}')
async def list_by_author(request):
	try:
		author_id = int(request.match_info['author'])
	except ValueError:
		raise HTTPBadRequest('Author ID must be a snowflake.')

	allow_nsfw = _should_allow_nsfw(request)
	after = request.rel_url.query.get('after')
	results = list(map(_marshal_emote, await db_cog.all_emotes_keyset(author_id, allow_nsfw=allow_nsfw, after=after)))
	return web.json_response(results)

@routes.get(API_PREFIX+'/search/{query}')
async def search(request):
	allow_nsfw = _should_allow_nsfw(request)
	query = request.match_info['query']
	results = [_marshal_emote(emote) async for emote in db_cog.search(query, allow_nsfw=allow_nsfw)]
	return web.json_response(results)

@routes.get(API_PREFIX+'/popular')
async def popular(request):
	allow_nsfw = _should_allow_nsfw(request)
	results = [_marshal_emote(emote) async for emote in db_cog.popular_emotes(allow_nsfw=allow_nsfw)]
	return web.json_response(results)

# why is this route necessary?
# you actually can't just filter /popular by author, because that will only return the first N emotes
# so if the user made an emote that has 3 uses, it probably won't show up in /popular

@routes.get(API_PREFIX+'/popular/{author}')
async def popular_by_author(request):
	try:
		author_id = int(request.match_info['author'])
	except ValueError:
		raise HTTPBadRequest('Author ID must be a snowflake.')

	allow_nsfw = _should_allow_nsfw(request)
	results = [_marshal_emote(emote) async for emote in db_cog.popular_emotes(author_id, allow_nsfw=allow_nsfw)]
	return web.json_response(results)

def _should_allow_nsfw(request):
	return _unmarshal_bool(request.rel_url.query.get('allow_nsfw', 'true'))

def _unmarshal_bool(x):
	if x == 'true':
		return True
	if x == 'false':
		return False
	raise HTTPBadRequest('boolean param was not "true" or "false"')

def _marshal_emote(emote):
	EPOCH = 1518652800  # February 15, 2018, the date of the first emote
	MAX_JSON_INT = 2**53

	allowed_fields = (
		'name',
		'id',
		'author',
		'animated',
		'created',
		'modified',
		'preserve',
		'description',
		'usage',
		'nsfw',
	)

	marshalled = {}

	for field in allowed_fields:
		try:
			value = getattr(emote, field)
		except AttributeError:
			continue

		if isinstance(value, int) and value > MAX_JSON_INT:
			marshalled[field] = str(value)
		elif isinstance(value, datetime):
			marshalled[field] = int(value.timestamp()) - EPOCH
		else:
			marshalled[field] = value

	return marshalled

async def _marshaled_iterator(iterator):
	async for emote in iterator:
		yield _marshal_emote(emote)

def emote_response(emote):
	return web.json_response(_marshal_emote(emote))
