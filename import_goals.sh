#!/usr/bin/env sh

mongoimport --db ananke --collection goals --drop --jsonArray --file goals.json
