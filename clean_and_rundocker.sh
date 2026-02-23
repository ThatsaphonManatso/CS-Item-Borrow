#!/bin/sh

docker compose down
docker system prune -a -f
./run_docker_compose.sh

