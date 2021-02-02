#!/bin/bash

source ${PWD}/scripts/utils.sh
source ${PWD}/scripts/prep-env.sh

download_plugins
prep_env
create_secrets
copy_gradle_scripts

echo "configuration is now all done!"
echo ""
echo "start your server with ./dc.sh up -d"
echo "get the initial db root password: ./dc.sh logs db | grep -i 'GENERATED ROOT PASSWORD'"
