# nutri

Flask app for building dishes (recipes) from nutritional food data sourced via the FatSecret API.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in FatSecret API credentials (see below)
flask db upgrade      # apply all migrations
```

FatSecret API credentials can be obtained by registering an application at [platform.fatsecret.com](https://platform.fatsecret.com).

## Run

```bash
flask --app main run --debug
```

## Database migrations

```bash
# After changing a model:
flask db migrate -m "describe the change"
flask db upgrade
```
