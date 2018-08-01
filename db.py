#!/usr/bin/env python3
# encoding: utf-8

import json

import psycopg2
import psycopg2.extras


def iter_from_query(query, *args):
	"""return an iterator from a query that retrieves multiple records"""
	with db.cursor() as cursor:
		cursor.execute(query, args)
		yield from cursor

def format_sql_conditions(conditions):
	"""format a sequence of SQL predicates as a single WHERE clause"""
	if not conditions:
		return ''
	return 'WHERE ' + ' AND '.join(conditions) + ' '

def emote(name):
	with db.cursor() as cursor:
		cursor.execute("""
			SELECT *
			FROM emote
			WHERE LOWER(name) = LOWER(%s)
		""", (name,))
		return cursor.fetchone()

def usage(id):
	with db.cursor() as cursor:
		cursor.execute("""
			SELECT COUNT(*) AS usage
			FROM emote_usage_history
			WHERE id = %s
			AND time > (CURRENT_TIMESTAMP - INTERVAL '4 weeks')
		""", (id,))
		return cursor.fetchone()['usage']

def emotes(author_id=None):
	"""return an iterator that gets emotes from the database.
	If author id is provided, get only emotes from them.
	"""
	query = 'SELECT * FROM emote '
	conditions = []
	args = []
	if author_id is not None:
		conditions.append('author = %s')
		args.append(author_id)

	query += format_sql_conditions(conditions)
	query += 'ORDER BY LOWER(name)'
	return iter_from_query(query, *args)

def search(substring):
	"""return an iterator that gets emotes from the database whose name contains `query`."""
	return iter_from_query("""
		SELECT *
		FROM emote
		WHERE str_contains(LOWER(%s), LOWER(name))
		ORDER BY LOWER(name)
	""", substring)

def popular():
	return iter_from_query("""
		SELECT *, (
			SELECT COUNT(*)
			FROM emote_usage_history
			WHERE id = emote.id
			AND time > (CURRENT_TIMESTAMP - INTERVAL '4 weeks')
		) AS usage
		FROM emote
		ORDER BY usage DESC, LOWER("name")
	""")

def _get_db():
	global config

	with open('config.py') as config_file:
		config = load_json_compat(config_file.read())
		credentials = config.pop('database')

	# pylint: disable=invalid-name
	db = psycopg2.connect(**credentials, cursor_factory=psycopg2.extras.RealDictCursor)
	db.autocommit = True
	return db

def load_json_compat(data: str):
	"""evaluate a python dictionary/list/thing, while maintaining compatibility some compatibility with JSON"""
	globals = dict(true=True, false=False, null=None)
	return eval(data, globals)

# hides the temporary variables like credentials and config_file
db = _get_db()  # pylint: disable=invalid-name
