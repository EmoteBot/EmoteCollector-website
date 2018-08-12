#!/usr/bin/env python3
# encoding: utf-8

from emoji_connoisseur.utils import emote as emote_utils
from flask import Flask, Response

import db

app = Flask('emoji-connoisseur')
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

@app.route('/list')
@app.route('/list/<int:author>')
def list(author=None):
	return Response(stream_template('list.html', emotes=db.emotes(author), author=author))

# http://flask.pocoo.org/docs/1.0/patterns/streaming/#streaming-from-templates
def stream_template(template_name, **context):
	app.update_template_context(context)
	template = app.jinja_env.get_template(template_name)
	template_stream = template.stream(context)
	template_stream.enable_buffering(5)
	return template_stream

app.jinja_env.globals['emote_url'] = emote_utils.url
app.jinja_env.globals['v2_onion'] = db.config['onions'][2]
app.jinja_env.globals['v3_onion'] = db.config['onions'][3]
