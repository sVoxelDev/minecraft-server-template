#!/bin/bash

source ${PWD}/scripts/utils.sh
source ${PWD}/scripts/prep-env.sh

create_dirs
clone_minimal
download_plugins
prep_env
create_secrets
copy_gradle_scripts