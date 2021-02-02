#!/bin/bash

rm .env
rm *.secrets.env
find servers/ database/ rcon/ ! -name '.gitkeep' -type f -exec rm -f {} +
