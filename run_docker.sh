#!/bin/bash

docker stop exptrac_app || true
docker rm exptrac_app || true

docker build --no-cache -t exptrac .

docker run -d \
  --name exptrac_app \
  --network host \
  exptrac

docker exec -it exptrac_app python manage.py makemigrations
docker exec -it exptrac_app python manage.py migrate
