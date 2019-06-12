#!/usr/bin/env python3
# encoding: utf-8

from aiohttp import web

from .middleware import error_middleware
from .docs import routes as docs_routes
from .routes import routes as api_routes

app = web.Application(client_max_size=16 * 1024**2)  # controls max size of PUT/POST request data
for routes in docs_routes, api_routes:
	app.add_routes(routes)

app.middlewares.append(error_middleware)
