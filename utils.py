import sys
import urllib.parse

import jinja2
from aiohttp import web

from emote_collector.extensions.db import PageSpecifier, PageDirection

def parse_keyset_params(before, after):
	# before='' means last
	# after='' means first

	if before is None and after is None:
		# default to first page
		return PageSpecifier.first()

	if before is not None and after is not None:
		raise HTTPBadRequest('only one of before, after may be specified')

	if not before and not after:
		reference = None
	else:
		reference = before or after

	if before is not None:
		direction = PageDirection.before
	if after is not None:
		direction = PageDirection.after

	return PageSpecifier(direction, reference)

def url(request, *, include_path=True):
	return (
		f'{request.headers["X-Forwarded-Proto"]}://{request.headers["X-Forwarded-For"]}'
		f'{request.rel_url if include_path else ""}')

async def render_template(template, environment=None, response_kwargs={}, **kwargs):
	if environment is None:
		environment = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'), enable_async=True)

	rendered = await environment.get_template(template).render_async(**kwargs)
	return web.Response(text=rendered, content_type='text/html', **response_kwargs)

# https://web.archive.org/web/20190217035443/http://flask.pocoo.org/snippets/62/
def is_safe_url(request, target):
	if not target: return False
	ref_url = f'{request.headers["X-Forwarded-Proto"]}://{request.headers["X-Forwarded-For"]}'
	test_url = urllib.parse.urlparse(urllib.parse.urljoin(str(ref_url), target))
	return test_url.scheme in {'http', 'https'} and urllib.parse.urlparse(ref_url).netloc == test_url.netloc

# this is the same as urllib.parse.urlencode except:
# - it encodes {'foo': ''} as 'foo', not 'foo='
# - it adds a ? at the beginning of the return value, but only if there were any query params to begin with
def urlencode(query, doseq=False, safe='', encoding=None, errors=None,
              quote_via=urllib.parse.quote_plus):
    """Encode a dict or sequence of two-element tuples into a URL query string.

    If any values in the query arg are sequences and doseq is true, each
    sequence element is converted to a separate parameter.

    If the query arg is a sequence of two-element tuples, the order of the
    parameters in the output will match the order of parameters in the
    input.

    The components of a query arg may each be either a string or a bytes type.

    The safe, encoding, and errors parameters are passed down to the function
    specified by quote_via (encoding and errors only if a component is a str).
    """

    if hasattr(query, "items"):
        query = query.items()
    else:
        # It's a bother at times that strings and string-like objects are
        # sequences.
        try:
            # non-sequence items should not work with len()
            # non-empty strings will fail this
            if len(query) and not isinstance(query[0], tuple):
                raise TypeError
            # Zero-length sequences of all types will get here and succeed,
            # but that's a minor nit.  Since the original implementation
            # allowed empty dicts that type of behavior probably should be
            # preserved for consistency
        except TypeError:
            ty, va, tb = sys.exc_info()
            raise TypeError("not a valid non-string sequence "
                            "or mapping object").with_traceback(tb)

    l = []
    joiner = lambda k, v: k + '=' + v if v else k
    if not doseq:
        for k, v in query:
            if isinstance(k, bytes):
                k = quote_via(k, safe)
            else:
                k = quote_via(str(k), safe, encoding, errors)

            if isinstance(v, bytes):
                v = quote_via(v, safe)
            else:
                v = quote_via(str(v), safe, encoding, errors)
            l.append(joiner(k, v))
    else:
        for k, v in query:
            if isinstance(k, bytes):
                k = quote_via(k, safe)
            else:
                k = quote_via(str(k), safe, encoding, errors)

            if isinstance(v, bytes):
                v = quote_via(v, safe)
                l.append(joiner(k, v))
            elif isinstance(v, str):
                v = quote_via(v, safe, encoding, errors)
                l.append(joiner(k, v))
            else:
                try:
                    # Is this a sufficient test for sequence-ness?
                    x = len(v)
                except TypeError:
                    # not a sequence
                    v = quote_via(str(v), safe, encoding, errors)
                    l.append(joiner(k, v))
                else:
                    # loop over the sequence
                    for elt in v:
                        if isinstance(elt, bytes):
                            elt = quote_via(elt, safe)
                        else:
                            elt = quote_via(str(elt), safe, encoding, errors)
                        l.append(joiner(k, elt))
    final = '&'.join(l)
    if final:
        return '?' + final
    return ''

