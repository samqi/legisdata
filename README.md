# LegisData Repository

## Quickstart
This is the LegisData repository which will hold the code for Legislative Data codes & services.

## Setting up the development environment

### Prerequisites

You will need the following:

1. Python 3.11
1. Podman
1. OpenSSL
1. Caddy
1. Poetry ([installation instruction](https://python-poetry.org/docs/))
1. Yarn ([installation instruction](https://yarnpkg.com/getting-started/install))
1. A huggingface account
1. In order to parse the documents, you may need a GPU (Project is developed with an NVIDIA GTX1070)

### Installation

1. Clone this repository
1. Installing the dependencies, as well as the project.
    ```
    cd legisdata
    poetry install
    poetry install --group=cli
    yarn install
    ```
1. Log into huggingface
    ```
    huggingface-cli login
    ```

## The command line utility - legisdata

The script is capable of downloading, extract and parse handsards and inquiries from the Selangor State Assembly website (as of 2024 July). You will need to start by creating a new dataset repository (e.g. [sinarproject/legisdata](https://huggingface.co/datasets/sinarproject/legisdata)), so data is backed up to huggingface after the end of each step.

1. In order to download the archive PDFs for year `2020` session `2` (replace the value of `LEGISDATA_HF_REPO` with your own repository ID)
    ```
    LEGISDATA_HF_REPO=sinarproject/legisdata legisdata download 2020 2
    ```
1. Downloaded data from step (1) can be extracted and stored as `.pickle` files
    ```
    LEGISDATA_HF_REPO=sinarproject/legisdata legisdata extract 2020 2
    ```
1. Extracted data from step (2) can be parsed into JSON to be used for other purposes
    ```
    LEGISDATA_HF_REPO=sinarproject/legisdata legisdata parse 2020 2
    ```

The schema for the resulting JSON files is documented in `legisdata.schema`

### Example usage 1: Extracting AkomaNtoso schema out of the resulting JSON

You would need `jq` or equivalent in order to extract the generated XML file. Firstly, identify the file that contain information you need, then

```
jq <data/2020/session-2/hansard-parse/HANSARD-13-JULAI-2020-1.pdf.json -r .akn
```

You can write it into a file as usual

```
jq <data/2020/session-2/hansard-parse/HANSARD-13-JULAI-2020-1.pdf.json -r .akn > hansard.xml
```

### Example usage 2: Running a website displaying the parsed schema

Firstly, you will need to generate the certificates

```
make cert
```

Then, you would need to create an `.env` file, with the following information

```
DOCKER_NETWORK=legisdata_legisdata

POSTGRES_USER=legisweb
POSTGRES_PASSWORD=<YOUR POSTGRES PASSWORD>
POSTGRES_DB=legisweb
DATABASE_PORT=5432
DATABASE_HOST=localhost

ALLOWED_HOSTS=localhost,127.0.0.1

OPENSEARCH_INITIAL_ADMIN_PASSWORD=<YOUR OPENSEARCH PASSWORD>
OPENSEARCH_VERIFY_CERTS=1
OPENSEARCH_SSL_SHOW_WARN=1
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
OPENSEARCH_USER=admin
OPENSEARCH_CA_CERTS=./certificates/root/root-ca.pem
```

Next you will need to compose a `internal_users.yml` (with sample [here](https://opensearch.org/docs/latest/security/configuration/yaml/#internal_usersyml)) and save the file to `./podman/opensearch/usr/share/opensearch/config/opensearch-security/internal_users.yml`. Ensure the password matches the configuration settings in `.env`.

Then start all the servers in one terminal emulator

```
make -j10 dev
```

After everything is started properly, import the parsed data into the database with in another terminal emulator window/tab
```
make migrate
```

Alternatively, if you intend to setup with podman/docker compose instead, create an `.env.docker` file, with the following information

```
DOCKER_NETWORK=legisdata

POSTGRES_USER=legisweb
POSTGRES_PASSWORD=abc123
POSTGRES_DB=legisweb
DATABASE_PORT=5432
DATABASE_HOST=database

ALLOWED_HOSTS=localhost,127.0.0.1

HUGGINGFACE_TOKEN=<YOUR HUGGINGFACE TOKEN>
LEGISDATA_HF_REPO=<YOUR DATASET REPO ID>

OPENSEARCH_INITIAL_ADMIN_PASSWORD=<YOUR OPENSEARCH PASSWORD>
OPENSEARCH_VERIFY_CERTS=0
OPENSEARCH_SSL_SHOW_WARN=0
OPENSEARCH_HOST=search-node
OPENSEARCH_PORT=9200
OPENSEARCH_USER=admin
OPENSEARCH_CA_CERTS=certificates/root/root-ca.crt

discovery.type=single-node
node.name=search-node
bootstrap.memory_lock=true
"OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m"
```

Next you will need to compose a `internal_users.yml` (with sample [here](https://opensearch.org/docs/latest/security/configuration/yaml/#internal_usersyml)) and save the file to `./podman/opensearch/usr/share/opensearch/config/opensearch-security/internal_users.yml`. Ensure the password matches the configuration settings in `.env.docker`.

Remember to setup your [huggingface token](https://huggingface.co/docs/transformers.js/en/guides/private) and specify the dataset repository ID (e.g. `sinarproject/legisdata`). After all the services are up by running the following command in one terminal emulator,

```
podman compose up
```

run the migration script in another terminal emulator window/tab

```
bash ./scripts/migrate.sh
```

Finally, the website can be accessed at `localhost:8080`. In order to deploy it to a network, append your URL to `ALLOWED_HOSTS` in the corresponding `.env` or `.env.docker` file.
