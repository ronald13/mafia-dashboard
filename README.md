# mafia-dashboard
Dashboard displays information about tournaments of the КCHB series in the sports mafia

## Running Locally
Create a virtualenv:
```bash
virtualenv -p python3 venv/
. venv/bin/activate && pip install -r requirements.txt
```

And from the upper level:

```bash
python dashboard.py 
```

## Local setup (Docker)
Run the following command to start local containers:
```shell
docker compose -f docker-compose-local.yml up -d
```

## Infrastructure

There are 2 environments available:

- **Local setup** (docker-compose-local.yml) - for local development.
- **Development setup** (docker-compose-dev.yml) - for testing before release.

The working version of the dashboard can be found here -  [Mafia-Dashboard](https://mafia-kchb-dash.herokuapp.com/)

<img src="./assets/img/mafia_dash.gif">