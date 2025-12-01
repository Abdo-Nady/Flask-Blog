#!/bin/sh
while ! pgت_isready -h "$DATABASE_HOST" -p "$DATABASE_PORT" -U flaskuser; do
  echo "Waiting for Postgres..."
  sleep 2
done


python - <<END
from app import db, app
with app.app_context():
    db.create_all()
END

python app.py
