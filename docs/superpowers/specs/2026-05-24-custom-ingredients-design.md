# Custom Ingredients Feature Design

**Date:** 2026-05-24  
**Feature:** Custom Foods Library for Nutri App  
**Status:** Approved Design

## Context

The Nutri Flask application currently supports ingredients sourced exclusively from the FatSecret API. Users frequently encounter foods that don't exist in FatSecret or need custom nutrition profiles (e.g., homemade dishes, regional foods, custom supplements). This feature introduces a reusable personal library of custom foods, enabling users to build dishes with ingredients beyond FatSecret's database while maintaining a consistent and organized workflow.

## Approved Design Decisions

### Storage Model
- **Custom foods are stored in a reusable library**, not as one-off entries. This allows users to build multiple dishes using the same custom ingredient.
- Custom foods are distinct from FatSecret ingredients in the data model but integrate seamlessly into the search and ingredient selection workflows.

### Nutrition Data
- Each custom food defines **exactly one serving size** plus all 6 nutrition values (all required):
  - Calories
  - Fat (g)
  - Sodium (mg)
  - Carbohydrate (g)
  - Fiber (g)
  - Protein (g)
- Users provide a descriptive serving definition (e.g., "1 cup", "100g", "1 piece").

### Snapshot Pattern
- When a custom food is added to a dish, its nutrition values are **snapshotted into the Ingredient record** at that moment.
- **Editing a custom food library entry does not retroactively affect past dishes**. Dishes maintain the exact nutrition values they had when the ingredient was added.
- This ensures recipe stability and prevents accidental recipe changes.

### Search Integration
- Custom foods appear in the search results on the dish ingredient page alongside FatSecret results.
- Custom foods are visually distinguished with a **"Custom" badge** to make their origin immediately clear.
- Custom results appear **before** FatSecret results in search output.

### Entry Points
1. **Inline create-and-add:** Users can create a custom food directly from the search page on the dish ingredient form and immediately add it to the dish.
2. **Dedicated library management page:** A dedicated `/custom-foods` section allows users to view, create, edit, and delete custom foods independently of any specific dish.

### Deletion Safety
- When deleting a custom food that is currently used in one or more dishes, the system warns the user with a **count of affected dishes**.
- Deletion requires explicit confirmation via a confirm query parameter on the POST request.
- Unused custom foods can be deleted immediately.

## Data Model

### New Table: CustomFood

```sql
CREATE TABLE custom_food (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    serving_description TEXT NOT NULL,
    calories REAL NOT NULL,
    fat REAL NOT NULL,
    sodium REAL NOT NULL,
    carbohydrate REAL NOT NULL,
    fiber REAL NOT NULL,
    protein REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Modified Table: Ingredient

Add these nullable foreign key and columns:

```sql
ALTER TABLE ingredient ADD COLUMN custom_food_id INTEGER;
ALTER TABLE ingredient ADD FOREIGN KEY (custom_food_id) REFERENCES custom_food(id);
ALTER TABLE ingredient ALTER COLUMN food_id DROP NOT NULL;
ALTER TABLE ingredient ALTER COLUMN serving_id DROP NOT NULL;
```

**Logic:**
- For FatSecret ingredients: `custom_food_id=NULL`, `food_id` and `serving_id` populated.
- For custom ingredients: `custom_food_id` populated, `food_id=NULL`, `serving_id=NULL`.
- An Ingredient record must have either (food_id AND serving_id) OR (custom_food_id), never both.

## Routes

### Library CRUD (New Blueprint: `nutri/routes/custom_foods.py`)

#### `GET /custom-foods` — List all custom foods
- **Response:** Render `custom_foods/index.html` with paginated list of all custom foods.
- **Display:** Name, serving description, key macros (calories, protein, fat, carbs), action links (edit, delete).
- **Empty state:** Message if no custom foods exist.

#### `GET /custom-foods/new` — Create form
- **Response:** Render `custom_foods/form.html` with empty form.
- **Form fields:**
  - Name (text, required, unique validation)
  - Serving description (text, required)
  - Calories (number, required)
  - Fat (number, required)
  - Sodium (number, required)
  - Carbohydrate (number, required)
  - Fiber (number, required)
  - Protein (number, required)

#### `POST /custom-foods` — Save new custom food
- **Input:** Form data (name, serving_description, nutrition values).
- **Validation:**
  - Name is required and unique (flash error if duplicate).
  - All nutrition fields are required and numeric.
- **Success:** Create CustomFood record, redirect to `/custom-foods/<id>/edit` with success flash.
- **Error:** Re-render form with validation errors.

#### `GET /custom-foods/<id>/edit` — Edit form
- **Response:** Render `custom_foods/form.html` pre-populated with CustomFood data.
- **Button label:** "Update" instead of "Create".

#### `POST /custom-foods/<id>/update` — Save edits
- **Input:** Form data (all fields).
- **Validation:** Same as POST /custom-foods.
- **Success:** Update CustomFood record, redirect to `/custom-foods/<id>` (detail/success page) with success flash.
- **Error:** Re-render form with validation errors.

#### `POST /custom-foods/<id>/delete` — Delete with usage warning
- **Logic:**
  1. Query the count of Ingredients where `custom_food_id == id`.
  2. If count > 0 (custom food is in use):
     - Flash warning: `"This custom food is used in {count} dish(es). Are you sure you want to delete it?"`
     - Require `?confirm=1` on the POST request.
     - If confirm != 1, re-render a confirmation page showing the warning and affected dishes.
  3. If count == 0 (unused) OR confirm == 1:
     - Delete the CustomFood record.
     - Flash success message.
     - Redirect to `/custom-foods`.
- **Affected dishes display:** List dish names/links so users see what will be affected.

### Dish Integration Routes (Modified: `nutri/routes/dishes.py`)

#### `GET /dishes/<id>/ingredients/custom/<cf_id>` — Quantity form
- **Response:** Render a form modal/page for specifying quantity.
- **Form fields:**
  - Quantity (number, required, default 1).
  - Unit or serving description (displayed from CustomFood, read-only or reference).
- **Button:** "Add to dish".

#### `POST /dishes/<id>/ingredients/custom/<cf_id>/insert` — Snapshot into Ingredient
- **Input:** `quantity` (numeric, required).
- **Logic:**
  1. Fetch the Dish and CustomFood (404 if either missing).
  2. Create a new Ingredient record with:
     - `dish_id = id`
     - `custom_food_id = cf_id`
     - `food_id = NULL`
     - `serving_id = NULL`
     - `quantity = quantity` (from form)
     - All nutrition fields snapshotted from CustomFood, scaled by quantity:
       - `calories = custom_food.calories * quantity`
       - `fat = custom_food.fat * quantity`
       - `sodium = custom_food.sodium * quantity`
       - `carbohydrate = custom_food.carbohydrate * quantity`
       - `fiber = custom_food.fiber * quantity`
       - `protein = custom_food.protein * quantity`
  3. Save Ingredient.
- **Response:** Redirect to `/dishes/<id>` (dish detail page) with success flash.
- **Error:** If CustomFood or Dish not found, redirect with error flash.

#### `Modified: search_ingredients` function in dishes.py
- **Existing behavior:** Queries FatSecret for foods matching search term.
- **New behavior:**
  1. Query CustomFood table: `CustomFood.name.ilike('%search%')`
  2. Format custom results with marker `is_custom=True` and `is_custom_food_id=<id>` for routing.
  3. **Prepend custom results to FatSecret results** (custom foods appear first).
  4. Return combined list to template.

## Templates

### New Templates

#### `custom_foods/index.html` — Library list view
- **Display:**
  - Heading: "Custom Foods Library"
  - Table with columns: Name, Serving Description, Calories, Protein, Fat, Carbs, Actions (Edit, Delete).
  - Empty state message if no custom foods.
  - "Add New Custom Food" button (links to `/custom-foods/new`).
- **Styling:** Match existing Nutri table styles (Bootstrap 5).

#### `custom_foods/form.html` — Create/edit form
- **Fields:**
  - Name (text input)
  - Serving Description (text input)
  - Calories (number input)
  - Fat (number input)
  - Sodium (number input)
  - Carbohydrate (number input)
  - Fiber (number input)
  - Protein (number input)
- **Buttons:** "Create" (new) or "Update" (edit) + "Cancel" (back to list).
- **Validation errors:** Display inline near each field.
- **Styling:** Match existing Nutri form styles.

#### `custom_foods/detail.html` — Detail/success page (optional, can redirect to list instead)
- **Display:** Full custom food details, "Edit" and "Delete" buttons, back to list link.
- **Used if:** User wants to see the created/updated food immediately before navigating away.

#### `custom_foods/confirm_delete.html` — Delete confirmation with usage warning
- **Display:**
  - Warning message: "This custom food is used in X dish(es)."
  - List of affected dishes (with links to view them).
  - Buttons: "Cancel" (back to list) + "Delete anyway" (POST with `confirm=1`).

### Modified Templates

#### `table-of-foods.html` — Search results table
- **New:** Add a "Custom" badge next to custom food names in search results.
- **Badge styling:** Visual distinction (e.g., different color, label).
- **Clicking custom food:** Links to `/dishes/<id>/ingredients/custom/<cf_id>` (quantity form).
- **Clicking FatSecret food:** Maintains existing behavior (links to FatSecret quantity form).

#### `base.html` — Navigation
- **New nav link:** Add "Custom Foods Library" or "My Foods" link pointing to `/custom-foods`.
- **Placement:** In main navigation menu, grouped with other content management options.

## Verification Steps

### 1. Database Migration
```bash
flask db upgrade
```
**Expected:** Migration applies cleanly without errors. Ingredient table has nullable `food_id`, `serving_id`, and new `custom_food_id` foreign key. CustomFood table exists with all required columns.

### 2. Library List (Empty)
```
GET /custom-foods
```
**Expected:** Renders custom_foods/index.html with empty state message and "Add New" button.

### 3. Create Custom Food
```
GET /custom-foods/new
POST /custom-foods with:
  name = "Test Food"
  serving_description = "1 cup"
  calories = 150
  fat = 5
  sodium = 300
  carbohydrate = 20
  fiber = 2
  protein = 10
```
**Expected:** CustomFood record created. Redirect to custom foods list or detail. New custom food appears in library.

### 4. Search Integration
```
GET /dishes/<id>/ingredients (search page)
Search for "Test Food" (or part of name)
```
**Expected:** Custom food appears in results above FatSecret results, with "Custom" badge visible.

### 5. Add Custom Food to Dish (Quantity)
```
Click custom food in search results
GET /dishes/<id>/ingredients/custom/<cf_id>
Enter quantity = 2
POST /dishes/<id>/ingredients/custom/<cf_id>/insert
```
**Expected:** 
- Quantity form renders and accepts input.
- Ingredient created with `custom_food_id` set, `food_id` and `serving_id` NULL.
- Nutrition values snapshotted and scaled by quantity (doubled if quantity=2).
- Redirect to dish page with success message.
- Ingredient appears in dish with correct doubled nutrition.

### 6. Edit Custom Food (No Impact on Existing Dishes)
```
GET /custom-foods/<id>/edit
Modify: calories = 200 (was 150)
POST /custom-foods/<id>/update
GET /dishes/<id> (view the dish from step 5)
```
**Expected:**
- Custom food updated in library (calories now 200).
- Dish ingredient nutrition remains unchanged (still shows doubled 300 calories from snapshot, not doubled 400).
- This confirms snapshot isolation.

### 7. Delete Used Custom Food (Warning)
```
POST /custom-foods/<id>/delete (without ?confirm=1)
```
**Expected:**
- Confirmation page renders showing: "This custom food is used in 1 dish(es)."
- List of affected dishes displayed with links.
- "Cancel" and "Delete anyway" buttons shown.

### 8. Confirm Delete (With Confirmation)
```
POST /custom-foods/<id>/delete?confirm=1
```
**Expected:**
- CustomFood record deleted.
- Ingredient record in dish remains (with snapshotted nutrition intact).
- Redirect to `/custom-foods` with success flash.
- Custom food no longer appears in library.
- Dish still shows the ingredient with original nutrition values.

### 9. Delete Unused Custom Food (No Warning)
```
Create a new custom food (unused)
POST /custom-foods/<new_id>/delete
```
**Expected:**
- Confirmation page does NOT render.
- CustomFood deleted immediately.
- Redirect to `/custom-foods` with success flash.

## Implementation Notes

### Model Definition
The `CustomFood` model should be added to `nutri/models.py` alongside `Dish` and `Ingredient`. The `Ingredient` model must be updated to include the `custom_food_id` foreign key and make `food_id` and `serving_id` nullable.

### Migration File
Create a new Alembic migration with:
1. CreateTable for custom_food.
2. AddColumn for custom_food_id, and nullable modifications to Ingredient.

### Error Handling
- All routes should validate input and provide clear error messages.
- Unique constraint on CustomFood.name should be handled gracefully in forms.
- 404 responses for missing custom foods or dishes.

### Nutrition Computation
- Dish-level nutrition sums across all ingredients (both FatSecret and custom).
- Ingredient-level nutrition is pre-computed and stored (no re-calculation from CustomFood).

### Search Performance
- CustomFood search uses simple string matching (`ilike`). Index name column if needed for performance.

---

**End of Design Document**
