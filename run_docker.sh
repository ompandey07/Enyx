#!/bin/bash

docker stop exptrac_app || true
docker rm exptrac_app || true

# Build only once (no --no-cache)
docker build -t exptrac .

# Run container, mount code for fast reload
docker run -d \
  --name exptrac_app \
  --network host \
  --restart unless-stopped \
  -v $(pwd):/app \
  exptrac

# Run migrations
docker exec -it exptrac_app python manage.py makemigrations
docker exec -it exptrac_app python manage.py migrate
