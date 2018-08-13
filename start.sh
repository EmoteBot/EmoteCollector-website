#!/usr/bin/env sh

run_with_worker() {
	worker=$1
	shift

	gunicorn \
		--worker-class $worker \
		"$@"
}

has_uvloop() {
	python3 -c 'import uvloop' >/dev/null 2>&1
}

start() {
	if has_uvloop; then
		worker=aiohttp.GunicornUVLoopWebWorker
	else
		worker=aiohttp.GunicornWebWorker
	fi

	run_with_worker $worker \
		--workers 1 \
		--threads 4 \
		--max-requests 10000 \
		--reload \
		--bind 0.0.0.0:$2 $1:app &
}

start app 8080
start api 8081

wait
