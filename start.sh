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
		--timeout 120 \
		--reload \
		--bind "$ip":"$port" "$module":app
}

start app "${EC_WEBSITE_PORT:-8080}" "$EC_WEBSITE_IP" &
start api "${EC_API_PORT:-8081}" "$EC_API_IP" &

wait
