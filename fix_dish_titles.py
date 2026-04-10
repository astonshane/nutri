"""One-off script to title-case all dish titles. Run with: flask --app main shell < fix_dish_titles.py"""
from nutri.models import Dish, db

dishes = db.session.execute(db.select(Dish)).scalars().all()
for dish in dishes:
    titled = dish.title.title()
    if titled != dish.title:
        print(f"  {dish.title!r} -> {titled!r}")
        dish.title = titled

db.session.commit()
print("Done.")
