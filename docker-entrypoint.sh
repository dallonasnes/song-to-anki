#!/bin/sh

set -e

gunicorn -c gunicorn.config.py app:app
