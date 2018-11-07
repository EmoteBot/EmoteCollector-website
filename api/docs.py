from aiohttp import web
import jinja2

from bot import config
from .constants import API_PREFIX

routes = web.RouteTableDef()
environment = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'), enable_async=True)

urls = tuple(url + API_PREFIX for url in (config['url'], *config['onions'].values()) if url)

@routes.get(API_PREFIX+'/docs')
async def docs(request):
	return await render_template('api_doc.html', urls=urls, prefix=config['prefix'])

async def render_template(template, **kwargs):
	return web.Response(
		text=await environment.get_template(template).render_async(**kwargs),
		content_type='text/html')
