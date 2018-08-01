#!/usr/bin/env python3
# encoding: utf-8

from datetime import datetime

from flask import Flask
from flask_restful import (
	abort,
	fields,
	marshal_with,
	Resource,
	Api as API)
from flask_restful.reqparse import RequestParser

import db

app = Flask('emoji connoisseur API')
api = API(app, prefix='/api/v0')

class EmojiConnoisseurDateTime(fields.Raw):
	EPOCH = 1518652800  # February 15, 2018, the date of the first emote

	@classmethod
	def format(cls, time: datetime):
		# time.timestamp() is a float, but we don't need that much precision
		return int(time.timestamp()) - cls.EPOCH

EMOTE_FIELDS = {
	'name': fields.String,
	'id': fields.String,  # JS cannot handle large nums
	'author': fields.String,  # same here
	'animated': fields.Boolean,
	'created': EmojiConnoisseurDateTime,
	'modified': EmojiConnoisseurDateTime,
	'preserve': fields.Boolean,
	'description': fields.String,
}

class Emote(Resource):
	@marshal_with(EMOTE_WITH_POPULARITY)
	def get(self, name):
		emote = db.emote(name)
		if not emote:
			abort(404, message='Emote not found.')

		emote['usage'] = db.usage(emote['id'])
		return emote

api.add_resource(Emote, '/emote/<string:name>')

class List(Resource):
	@marshal_with(EMOTE_FIELDS)
	def get(self):
		parser = RequestParser()
		parser.add_argument('author', type=int, default=None)
		args = parser.parse_args()
		return list(map(dict, db.emotes(args.author)))

api.add_resource(List, '/emotes')


class Emote(Resource):
	@marshal_with(EMOTE_FIELDS)
	def get(self, name):
		return dict(db.emote(name))

api.add_resource(Emote, '/emote/<string:name>')
