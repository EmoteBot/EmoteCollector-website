import re

from aiohttp import web

from .errors import JSONHTTPError, HTTPRequestEntityTooLarge, errors

@web.middleware
async def error_middleware(request, handler):
	try:
		return await handler(request)
	except JSONHTTPError:
		# supress custom handling of JSONHTTPErrors, ensuring that the next except branch
		# *only* runs for non-customized errors
		raise
	except web.HTTPRequestEntityTooLarge as exception:
		max_size_actual_size = re.search(br'(\d+) exceeded, actual body size (\d+)', exception.body).groups()
		max_size, actual_size = map(int, max_size_actual_size)
		raise HTTPRequestEntityTooLarge(exception.body.decode(), max_size=max_size, actual_size=actual_size)
	except web.HTTPException as exception:
		try:
			raise errors[exception.status]
		except KeyError:
			raise exception
