#!/bin/bash

function configure_ports() {
    printf "\n\n"
    printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' -
    printf "\n"
    read -p "Public Server (Bungeecord) Port [25565]: " port
    port=${port:-25565}
    
    echo "PROXY_PORT=$port" >> .env
    
    read -p "Query Port [25566]: " port
    port=${port:-25566}
    
    echo "STATUS_PORT=$port" >> .env


    printf "\n"
    echo "Starting Bungeecord Proxy under Port $port..."
}

function set_ram() {
    read -p "Set the RAM for the Server [4G]: " ram
    ram=${ram:-4G}
    echo "MEMORY=$ram" >> .env
}

function set_weburl() {

    read -p "What should be the base url of this environment, e.g.: test.your-server.net? [your-server.net]: " base
    base=${base:-your-server.net}
    echo "WEB_BASE_URL=$base" >> .env
}

function set_environment() {
    read -p "What is the environment of this server (e.g.: test, prod)? [test] " env
    env=${env:-test}
    echo "ENVIRONMENT=$env" >> .env
}

function prep_env() {
    if [ ! -f .env ]; then
        echo ".env file not found! Generating..."
        export CURRENT_USER=$(id -u):$(id -g)
        export CURRENT_UID=$(id -u)
        export CURRENT_GID=$(id -g)

        echo "CURRENT_USER=$CURRENT_USER" > .env
        echo "CURRENT_UID=$CURRENT_UID" >> .env
        echo "CURRENT_GID=$CURRENT_GID" >> .env

        for dir in $(pwd)/servers/*/; do
            dir=${dir%*/}
            echo "DIR_${dir##*/}=$dir" >> .env
        done;

        configure_ports
        set_ram
        set_weburl
        set_environment

        echo "You can check the environment config by opening the .env file."
        echo "DO NOT commit the .env file into your VCS!"
    fi
}
