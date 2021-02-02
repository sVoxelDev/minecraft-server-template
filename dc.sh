#!/bin/bash

args=""

while IFS=  read -r -d $'\0'; do
    if [[ ! $REPLY == *.minimal.yml ]]; then
	    args+="-f $REPLY "
    fi
done < <(find . -maxdepth 1 -type f -name "docker-compose.*.yml" -print0)

docker-compose $args $@
