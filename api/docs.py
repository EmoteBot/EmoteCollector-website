from aiohttp import web

from bot import config
from utils import render_template, url
from .constants import API_PREFIX

routes = web.RouteTableDef()

urls = tuple(url + API_PREFIX for url in (config['url'], *config['onions'].values()) if url)

@routes.get(API_PREFIX+'/docs')
async def docs(request):
	return await render_template('api_doc.html', url=url(request), urls=urls, prefix=config['prefix'])
