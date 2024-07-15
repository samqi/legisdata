SHELL=/bin/bash
DOCKER_NETWORK ?= legisdata

.PHONY: dev cert database migrate caddy backend frontend docker-migrate search-node search-dashboard

dev: database caddy frontend backend search-node

cert:
	bash ./scripts/cert-generator.sh

database:
	podman run \
		--rm --replace \
		--name=legisdata_database \
		--publish=0.0.0.0:5432:5432 \
		--env-file=.env \
		--network ${DOCKER_NETWORK} \
		postgres:16

migrate:
	poetry run python manage.py migrate && \
		poetry run python manage.py import-legisdata 2020 2 && \
		poetry run python manage.py opensearch index rebuild --force && \
		poetry run python manage.py opensearch document index --force

frontend:
	(FORCE_COLOR=1 BROWSER=none yarn run dev | cat)

backend:
	poetry run gunicorn legisweb.wsgi:application --reload --bind=0.0.0.0:8000

caddy:
	caddy run

search-node:
	podman run \
		--rm --replace \
		--name=search-node \
		--publish 9200:9200 \
		--publish 9600:9600 \
		--env "discovery.type=single-node" \
		--env-file=.env \
		--network ${DOCKER_NETWORK} \
		--mount type=bind,source="$(shell pwd)/podman/opensearch/usr/share/opensearch/config/opensearch-dev.yml",target=/usr/share/opensearch/config/opensearch.yml \
		--mount type=bind,source="$(shell pwd)/podman/opensearch/usr/share/opensearch/config/opensearch-security/internal_users.yml",target=/usr/share/opensearch/config/opensearch-security/internal_users.yml \
		--mount type=bind,source="$(shell pwd)/certificates/root/root-ca.pem",target=/usr/share/opensearch/config/root-ca.pem \
		--mount type=bind,source="$(shell pwd)/certificates/admin/admin.pem",target=/usr/share/opensearch/config/admin.pem \
		--mount type=bind,source="$(shell pwd)/certificates/admin/admin-key.pem",target=/usr/share/opensearch/config/admin-key.pem \
		--mount type=bind,source="$(shell pwd)/certificates/dev/dev.pem",target=/usr/share/opensearch/config/node.pem \
		--mount type=bind,source="$(shell pwd)/certificates/dev/dev-key.pem",target=/usr/share/opensearch/config/node-key.pem \
		opensearchproject/opensearch:latest

search-dashboard:
	podman run \
		--rm --replace \
		--name=search-dashboard \
		--publish 5601:5601 \
		--env 'OPENSEARCH_HOSTS=["https://search-node:9200/"]' \
		--env-file=.env \
		--network ${DOCKER_NETWORK} \
		opensearchproject/opensearch-dashboards:2.11.1