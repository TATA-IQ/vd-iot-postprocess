#!/bin/bash
redis-server --daemonize yes &
python3 app.py