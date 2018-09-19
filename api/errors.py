
# NOTE: This file is auto generated. Do not edit it! Edit api/errors_gen.py instead.

import json

from aiohttp import web

class JSONHTTPError(web.HTTPException):
	def __init__(self, reason=None, **kwargs):
		if reason:
			kwargs['message'] = reason

		super().__init__(
			text=json.dumps(dict(status=self.status_code, **kwargs)),
			content_type='application/json')

class HTTPRequestEntityTooLarge(JSONHTTPError):
	status_code = 413

	def __init__(self, reason=None, *, max_size=None, actual_size=None):
		super().__init__(reason=reason, max_size=max_size, actual_size=actual_size)

class HTTPBadRequest(JSONHTTPError, web.HTTPBadRequest):
	pass

class HTTPUnauthorized(JSONHTTPError, web.HTTPUnauthorized):
	pass

class HTTPForbidden(JSONHTTPError, web.HTTPForbidden):
	pass

class HTTPNotFound(JSONHTTPError, web.HTTPNotFound):
	pass

class HTTPConflict(JSONHTTPError, web.HTTPConflict):
	pass

class HTTPUnsupportedMediaType(JSONHTTPError, web.HTTPUnsupportedMediaType):
	pass

class HTTPInternalServerError(JSONHTTPError, web.HTTPInternalServerError):
	pass

errors = {
	413: HTTPRequestEntityTooLarge,
	400: HTTPBadRequest,
	401: HTTPUnauthorized,
	403: HTTPForbidden,
	404: HTTPNotFound,
	409: HTTPConflict,
	415: HTTPUnsupportedMediaType,
	500: HTTPInternalServerError,
}
