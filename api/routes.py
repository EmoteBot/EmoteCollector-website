from datetime import datetime
import io

from aiohttp import web
import discord
from emote_collector.utils import errors as emote_collector_errors
from emote_collector import utils as emote_collector_utils
import jinja2

from bot import *
from .errors import *

routes = web.RouteTableDef()
api_prefix = '/api/v0'

environment = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'), enable_async=True)

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

@routes.get(api_prefix+'/emote/{name}')
@db_route
async def emote(request):
	name = request.match_info['name']

	emote = await db_cog.get_emote(name)
	emote.usage = await db_cog.get_emote_usage(emote)
	return emote_response(emote)

@routes.get(api_prefix+'/login')
@requires_auth
async def login(request):
	return web.json_response(str(request.user_id))

@routes.patch(api_prefix+'/emote/{name}')
@requires_auth
async def edit_emote(request):
	name = request.match_info['name']
	user_id = request.user_id

	json = await request.json()

	if 'description' not in json and 'name' not in json:
		raise HTTPBadRequest('no edits were specified')

	if 'description' in json:
		result = await db_cog.set_emote_description(name, user_id, json['description'])

	if 'name' in json:
		result = await db_cog.rename_emote(name, json['name'], user_id)

	return emote_response(result)

@routes.delete(api_prefix+'/emote/{name}')
@requires_auth
async def delete_emote(request):
	name = request.match_info['name']
	user_id = request.user_id

	return emote_response(await db_cog.remove_emote(name, user_id))

@routes.put(api_prefix+'/emote/{name}/{url}')
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

@routes.put(api_prefix+'/emote/{name}')
@requires_auth
async def create_emote_from_data(request):
	if not request.can_read_body:
		raise HTTPBadRequest('image data required in body')

	name = request.match_info['name']
	author = request.user_id
	image = io.BytesIO(await request.read())

	try:
		return emote_response(await emotes_cog.create_emote_from_bytes(name, author, image))
	except emote_collector_errors.ImageResizeTimeoutError:
		raise HTTPRequestEntityTooLarge('image resize took too long')
	except emote_collector_errors.InvalidImageError:
		raise HTTPUnsupportedMediaType('PNG, GIF, or JPEG required in body')

@routes.get(api_prefix+'/emotes')
async def list(request):
	results = [_marshal_emote(emote) async for emote in db_cog.all_emotes()]
	return json_or_not_found(results)

@routes.get(api_prefix+'/emotes/{author}')
async def list_by_author(request):
	try:
		author_id = int(request.match_info['author'])
	except ValueError:
		raise HTTPBadRequest('Author ID must be a snowflake.')

	results = [_marshal_emote(emote) async for emote in db_cog.all_emotes(author_id)]
	return json_or_not_found(results)

@routes.get(api_prefix+'/search/{query}')
async def search(request):
	results = [_marshal_emote(emote) async for emote in db_cog.search(request.match_info['query'])]
	return json_or_not_found(results)

@routes.get(api_prefix+'/popular')
async def popular(request):
	results = [_marshal_emote(emote) async for emote in db_cog.popular_emotes() if emote.usage]
	return json_or_not_found(results)

@routes.get(api_prefix+'/docs')
async def docs(request):
	return await render_template('api_doc.html',
		urls=filter(None, (config['url'], *config['onions'].values())),
		prefix=config['prefix'])

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

def json_or_not_found(obj):
	if not obj:
		raise HTTPNotFound
	return web.json_response(obj)

async def render_template(template, **kwargs):
	return web.Response(
		text=await environment.get_template(template).render_async(**kwargs),
		content_type='text/html')
