#!/bin/bash

echo "Updating submodules..."
git pull origin
git submodule update --remote
git add plugins
git add proxy-plugins
git commit -m "chore(deps): update plugins submodule"
git push origin

echo "syncing data from plugins/ into servers..."
rsync -a --exclude="*.jar" --out-format="update:%f:Last Modified %M" --update --prune-empty-dirs plugins/ servers/main/plugins/
rsync -a --exclude="*.jar" --out-format="update:%f:Last Modified %M" --update --prune-empty-dirs proxy-plugins/ servers/proxy/plugins/

echo "update successful!"
