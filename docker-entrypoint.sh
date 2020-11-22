#!/bin/sh

set -e
flask db upgrade
gunicorn -c gunicorn.config.py app:app
