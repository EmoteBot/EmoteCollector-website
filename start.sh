#!/usr/bin/env sh

start() {
	module="$1"
	port="$2"
	ip="${3:-0.0.0.0}"

	gunicorn \
		--worker-class aiohttp.GunicornWebWorker \
		--workers 1 \
		--threads 4 \
		--max-requests 10000 \
		--reload \
		--bind "$ip":"$port" "$module":app
}

start app "${EC_WEBSITE_PORT:-8080}" "$EC_WEBSITE_IP" &
# running the schema code from the bot requires an exclusive lock on the database
# so we can't have them both run at the same time
# XXX this is a bunk way to synchronize processes
sleep 2
start api "${EC_API_PORT:-8081}" "$EC_API_IP" &

wait
