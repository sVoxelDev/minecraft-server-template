#!/bin/bash

while [ -n "$1" ]; do
    case "$1" in
        now) echo "starting backup..."
            ./dc.sh exec backup rcb backup --no-cleanup
            ;;
        cleanup) echo "cleaning up old backups..."
            ./dc.sh exec backup rcb cleanup
            ;;
        snapshots)
            ./dc.sh exec backup rcb snapshots
            ;;
        attach)
            ./dc.sh exec -it backup sh
            ;;
        --) shift
            break ;;
        *) echo "$1 is not an option. Valid options: now, cleanup, snapshots or attach";;
    esac
    shift
done
