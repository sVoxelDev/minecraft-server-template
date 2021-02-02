#!/bin/bash

function generatePassword() {
	echo $(cat /dev/urandom | tr -dc a-zA-Z0-9 | head -c21; echo)
}

function set_backup_secrets() {
    echo "" > backup.secrets.env
    # set_aws_creds
    set_restic_pw
}

function set_aws_creds() {

    echo "Please enter your AWS Access Token ID: "
    read -s awsid
    echo "Please enter your AWS secret: "
    read -s awspw
    echo "AWS_ACCESS_KEY_ID=$awsid" >> backup.secrets.env
    echo "AWS_SECRET_ACCESS_KEY=$awspw" >> backup.secrets.env
}

function set_restic_pw() {

    echo "Please enter the restic repository password: "
    read -s resticpw
    echo "RESTIC_PASSWORD=$resticpw" >> backup.secrets.env
}

function set_mysql_pw() {
    local password=$(generatePassword)
    echo "CFG_DB_PASSWORD=$password" > sql.secrets.env
    echo "MYSQL_PASSWORD=$password" >> sql.secrets.env
    echo "PMA_PASSWORD=$password" >> sql.secrets.env
}

function set_rcon_pw() {
    local rconpassword=$(generatePassword)
    echo "RWA_PASSWORD=$(generatePassword)" > rcon.secrets.env
}

function create_secrets() {
    
    if [ ! -f rcon.secrets.env ]; then
	    set_rcon_pw
        echo "created rcon.secrets.env ..."
    fi
    
    if [ ! -f sql.secrets.env ]; then
        set_mysql_pw
        echo "created sql.secrets.env ..."
    fi

    if [ ! -f backup.secrets.env ]; then
        set_backup_secrets
        echo "created backup.secrets.env ..."
    fi

    chmod 600 *.secrets.env
}

function copy_gradle_scripts() {
    if command -v wslpath &> /dev/null; then
        server_path="$(pwd)"
        gradle_home="$(wslpath "$(wslvar USERPROFILE)")/.gradle"
        gradle_scripts="$gradle_home/scripts"
        mkdir -p "$gradle_scripts"
        if [ ! -f "$gradle_scripts/build.local.gradle" ]; then
            cp -f "lib/scripts/build.local.gradle" "$gradle_scripts/build.local.gradle"

            win_server_path=$(echo "$server_path" | sed "s#/mnt/c/#C:/#g")
            sed -i "s#into 'BASE_PATH'#into '$win_server_path'#" "$gradle_scripts/build.local.gradle"

            win_path=$(echo "$gradle_scripts" | sed "s#/mnt/c/#C:/#g")
            set_property "$gradle_home/gradle.properties" "local_script" "$win_path"
        fi
    fi
}

function set_property() {
    filename=$1
    thekey="$2"
    newvalue="$3"

    if ! grep -R "^[#]*\s*${thekey}=.*" $filename > /dev/null; then
        echo "APPENDING because '${thekey}' not found"
        echo "$thekey=$newvalue" >> $filename
    else
        echo "SETTING because '${thekey}' found already"
        sed -ir "s#^${thekey}=.*#$thekey=$newvalue#" $filename
    fi
}

function download_plugins() {

    read -p "Download URL to initial plugins zip file? Leave empty to skip. [your-url.net/plugins.zip]: " plugins
    
    if [[ -v plugins ]]; then
        TMPFILE=`mktemp`
        DEST="$(pwd)/plugins"
        wget "$plugins" -O $TMPFILE
        unzip $TMPFILE -d $DEST
        rm $TMPFILE
    else
        echo "skipping download of plugins..."
    fi
}
