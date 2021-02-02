#!/bin/bash

rm .env
rm *.secrets.env
find servers/ database/ rcon/ ! -name '.gitkeep' -delete
