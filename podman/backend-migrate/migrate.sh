#!/bin/sh

export PATH="/root/.local/bin:${PATH}" \

# install pipx
apt-get update && apt-get install --no-install-suggests --no-install-recommends --yes pipx

# install poetry
pipx install poetry
# poetry install
poetry install --only=main

# initiate login
poetry run huggingface-cli login --token $HUGGINGFACE_TOKEN
# download from sinar/legisdata
mkdir -p data
poetry run huggingface-cli download sinarproject/legisdata --repo-type dataset --local-dir ./data

poetry run python manage.py migrate
poetry run python manage.py import-legisdata 2020 2