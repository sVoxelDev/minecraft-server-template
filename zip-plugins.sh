#!/bin/bash

rm ./downloads/files/plugins.zip
cd ./plugins
zip -r ../downloads/files/plugins.zip . -i '*.jar'
