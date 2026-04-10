"""One-time script to backfill food_name, food_url, serving_description,
and nutrition columns on existing Ingredient rows."""

from nutri import create_app, db, fs
from nutri.helpers import static_nutrition_info
from nutri.models import Ingredient

app = create_app()

with app.app_context():
    ingredients = db.session.execute(
        db.select(Ingredient).where(Ingredient.food_name.is_(None))
    ).scalars().all()

    print(f"Backfilling {len(ingredients)} ingredient(s)...")

    for ing in ingredients:
        try:
            food = fs.food(ing.food_id)
            serving = food.serving(ing.serving_id)
            if serving is None:
                print(f"  [WARN] Ingredient {ing.id}: serving {ing.serving_id} not found for food {ing.food_id}, skipping")
                continue
            ing.food_name = food.name
            ing.food_url = food.url
            ing.serving_description = serving.description
            for key in static_nutrition_info.keys():
                setattr(ing, key, serving.nutrition_info[key])
            print(f"  [OK] Ingredient {ing.id}: {food.name}")
        except Exception as e:
            print(f"  [ERROR] Ingredient {ing.id}: {e}")

    db.session.commit()
    print("Done.")
