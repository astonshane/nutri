# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup (first time)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in FatSecret API credentials
flask db upgrade      # apply all migrations

# Run
flask --app main run --debug
```

## Database migrations

Migrations are managed with Flask-Migrate (Alembic). The `migrations/` folder is committed to git.

```bash
# After changing a model:
flask db migrate -m "describe the change"  # generate migration file
flask db upgrade                           # apply to the database

# Other useful commands:
flask db downgrade   # roll back one migration
flask db history     # list all migrations
flask db current     # show which migration the DB is at
```

Never modify the DB schema manually (ALTER TABLE, etc.) — always go through migrations so the history stays consistent.

## Architecture

**Nutri** is a Flask app for building dishes (recipes) from nutritional food data sourced via the FatSecret API.

### Key files

- `nutri/__init__.py` — app factory; registers extensions (SQLAlchemy) and routes
- `nutri/models.py` — two SQLAlchemy models: `Dish` and `Ingredient`
- `nutri/routes/dishes.py` — all dish and ingredient routes (main business logic)
- `nutri/fatsecret/fatsecret.py` — FatSecret API client (OAuth, caching, search)
- `nutri/helpers.py` — `BaseModel` mixin and `static_nutrition_info` (shared nutrition field list)
- `config.py` — Flask config loaded from `.env`

### Data model

A **Dish** has many **Ingredients**. Each Ingredient stores a reference to a FatSecret food ID + serving ID, plus a cached copy of the nutrition values (calories, fat, carbs, protein, fiber, sodium) so the app doesn't re-query FatSecret on every page load.

Dish-level nutrition is computed by summing ingredient nutrition values, scaled by the ingredient quantity and divided by the number of dish portions.

### FatSecret integration

The `fatsecret/` package handles OAuth token management, food search, and serving resolution. `token.py` manages token persistence; `fatsecret.py` is the API client. The `Food` and `Serving` classes (`food.py`, `serving.py`) are local models that wrap FatSecret JSON responses. Credentials (`FATSECRET_CLIENT_ID`, `FATSECRET_CLIENT_SECRET`) are read from `.env`.

### Nutrition fields

The canonical list of nutrition metrics is defined once in `helpers.py` as `static_nutrition_info` and reused across templates and models via the `BaseModel` mixin to avoid duplication.
