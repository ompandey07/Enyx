#!/bin/bash

# Stop and remove container if exists (quietly)
docker rm -f exptrac_app 2>/dev/null || true

# Build image
docker build -t exptrac .

# Run container in detached mode
docker run -d --name exptrac_app --network host exptrac

# Run migrations once inside container
docker exec exptrac_app python manage.py makemigrations
docker exec exptrac_app python manage.py migrate
