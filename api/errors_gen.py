#!/usr/bin/env python3
# encoding: utf-8

import io
import os.path

from aiohttp import web

BASE = os.path.dirname(__file__)
OUTPUT_FILENAME = os.path.join(BASE, 'errors.py')

out = open(OUTPUT_FILENAME, 'w')

out.write("""
# NOTE: This file is auto generated. Do not edit it! Edit api/errors_gen.py instead.

import json

from aiohttp import web
""")

# write customized classes which cannot be generated
out.write("""
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
""")

template = """
class HTTP{0}(JSONHTTPError, web.HTTP{0}):
	pass
"""

errors = io.StringIO()
errors.write('\nerrors = {\n')

def write_http_error(cls):
	errors.write('\t')
	errors.write(str(cls.status_code))
	errors.write(': ')
	errors.write(cls.__name__)
	errors.write(',\n')

write_http_error(web.HTTPRequestEntityTooLarge)

# generate the rest
for class_name in (
	'BadRequest',
	'Unauthorized',
	'Forbidden',
	'NotFound',
	'Conflict',
	'UnsupportedMediaType',
	'InternalServerError',
):
	cls = getattr(web, 'HTTP' + class_name)
	write_http_error(cls)

	out.write(template.format(class_name))

errors.write('}\n')

out.write(errors.getvalue())
out.close()
