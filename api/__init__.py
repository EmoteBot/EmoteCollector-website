#!/usr/bin/env python3
# encoding: utf-8

import asyncio
import re

from aiohttp import web

from .middleware import error_middleware
from .routes import routes

app = web.Application(client_max_size=16 * 1024**2)  # controls max size of PUT/POST request data
app.add_routes(routes)
app.middlewares.append(error_middleware)
