#!/bin/bash

export MODPACK=https://dl.raid-craft.de/plugins.zip

docker-compose -f docker-compose.main.yml -f docker-compose.proxy.yml -f docker-compose.db.yml -f docker-compose.db.minimal.yml -f docker-compose.main.debug.yml $@
