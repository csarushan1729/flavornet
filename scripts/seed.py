#!/usr/bin/env python3
"""
Seed script for FlavorNet culinary knowledge graph.
Loads realistic recipes, ingredients, substitutions and flavor pairings
into CognoDB / Neo4j via the official driver.
"""

import os
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER", "cognodb")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not URI or not PASSWORD:
    print("ERROR: Set NEO4J_URI and NEO4J_PASSWORD in .env")
    sys.exit(1)

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


def clear_graph(tx):
    tx.run("MATCH (n) DETACH DELETE n")


def create_constraints(tx):
    tx.run("CREATE CONSTRAINT recipe_name IF NOT EXISTS FOR (r:Recipe) REQUIRE r.name IS UNIQUE")
    tx.run("CREATE CONSTRAINT ingredient_name IF NOT EXISTS FOR (i:Ingredient) REQUIRE i.name IS UNIQUE")
    tx.run("CREATE CONSTRAINT cuisine_name IF NOT EXISTS FOR (c:Cuisine) REQUIRE c.name IS UNIQUE")
    tx.run("CREATE CONSTRAINT dietary_name IF NOT EXISTS FOR (d:DietaryTag) REQUIRE d.name IS UNIQUE")


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

CUISINES = [
    ("Italian", "Mediterranean classic built on olive oil, tomatoes, herbs and pasta"),
    ("Indian", "Complex spice layers, aromatic basmati and vibrant vegetarian tradition"),
    ("Mexican", "Corn, beans, chiles and bright citrus"),
    ("Japanese", "Umami, seasonality and minimalist precision"),
    ("Thai", "Sweet-sour-salty-spicy balance with fresh herbs"),
    ("French", "Technique-driven, butter, wine and refined sauces"),
    ("Middle Eastern", "Tahini, pomegranate, grilled meats and fragrant spices"),
    ("American", "Comfort food with regional diversity"),
]

DIETARY_TAGS = ["Vegan", "Vegetarian", "Gluten-Free", "Dairy-Free", "Nut-Free", "Keto"]

INGREDIENTS = [
    # Dairy & alternatives
    ("Butter", "dairy"),
    ("Olive Oil", "oil"),
    ("Coconut Oil", "oil"),
    ("Ghee", "dairy"),
    ("Milk", "dairy"),
    ("Coconut Milk", "plant"),
    ("Cream", "dairy"),
    ("Cashew Cream", "plant"),
    ("Parmesan", "dairy"),
    ("Nutritional Yeast", "plant"),
    # Proteins
    ("Chicken Breast", "protein"),
    ("Tofu", "protein"),
    ("Chickpeas", "protein"),
    ("Lentils", "protein"),
    ("Eggs", "protein"),
    ("Salmon", "protein"),
    ("Ground Beef", "protein"),
    ("Tempeh", "protein"),
    # Vegetables & aromatics
    ("Garlic", "vegetable"),
    ("Onion", "vegetable"),
    ("Tomato", "vegetable"),
    ("Spinach", "vegetable"),
    ("Bell Pepper", "vegetable"),
    ("Mushroom", "vegetable"),
    ("Carrot", "vegetable"),
    ("Potato", "vegetable"),
    ("Avocado", "vegetable"),
    ("Zucchini", "vegetable"),
    ("Eggplant", "vegetable"),
    ("Broccoli", "vegetable"),
    # Herbs & spices
    ("Basil", "herb"),
    ("Cilantro", "herb"),
    ("Parsley", "herb"),
    ("Cumin", "spice"),
    ("Turmeric", "spice"),
    ("Chili Flakes", "spice"),
    ("Ginger", "spice"),
    ("Black Pepper", "spice"),
    ("Oregano", "herb"),
    ("Thyme", "herb"),
    # Grains & staples
    ("Pasta", "grain"),
    ("Rice", "grain"),
    ("Quinoa", "grain"),
    ("Tortilla", "grain"),
    ("Bread", "grain"),
    ("Flour", "grain"),
    ("Cornmeal", "grain"),
    # Others
    ("Lemon", "fruit"),
    ("Lime", "fruit"),
    ("Soy Sauce", "condiment"),
    ("Tamari", "condiment"),
    ("Honey", "sweetener"),
    ("Maple Syrup", "sweetener"),
    ("Sesame Oil", "oil"),
    ("Peanut Butter", "nut"),
    ("Almond Butter", "nut"),
    ("Coconut", "fruit"),
    ("Yogurt", "dairy"),
    ("Greek Yogurt", "dairy"),
    ("Coconut Yogurt", "plant"),
]

# (from, to, reason)
SUBSTITUTIONS = [
    ("Butter", "Olive Oil", "vegan / dairy-free cooking fat"),
    ("Butter", "Coconut Oil", "vegan solid fat alternative"),
    ("Butter", "Ghee", "lactose-reduced, higher smoke point"),
    ("Milk", "Coconut Milk", "dairy-free creamy liquid"),
    ("Cream", "Cashew Cream", "rich vegan cream substitute"),
    ("Cream", "Coconut Milk", "light dairy-free cream"),
    ("Parmesan", "Nutritional Yeast", "cheesy umami for vegan dishes"),
    ("Chicken Breast", "Tofu", "plant-based protein swap"),
    ("Chicken Breast", "Tempeh", "fermented soy protein with bite"),
    ("Ground Beef", "Lentils", "hearty plant-based mince"),
    ("Ground Beef", "Chickpeas", "textured vegetarian base"),
    ("Eggs", "Tofu", "scramble alternative"),
    ("Honey", "Maple Syrup", "vegan liquid sweetener"),
    ("Soy Sauce", "Tamari", "gluten-free soy alternative"),
    ("Peanut Butter", "Almond Butter", "nut allergy alternative (tree-nut)"),
    ("Yogurt", "Coconut Yogurt", "dairy-free cultured product"),
    ("Greek Yogurt", "Coconut Yogurt", "dairy-free thick yogurt"),
    ("Flour", "Cornmeal", "gluten-free coating / binding"),
    ("Bread", "Rice", "gluten-free carb base"),
    ("Olive Oil", "Sesame Oil", "toasty Asian flavor profile"),
]

# (a, b, strength 0-1, notes) – will be created in both directions
PAIRINGS = [
    ("Garlic", "Basil", 0.95, "classic Italian aromatic duo"),
    ("Garlic", "Olive Oil", 0.9, "foundation of Mediterranean cooking"),
    ("Tomato", "Basil", 0.95, "Caprese and pasta perfection"),
    ("Tomato", "Garlic", 0.9, "sofrito / soffritto base"),
    ("Lemon", "Garlic", 0.85, "bright and pungent"),
    ("Lemon", "Parsley", 0.8, "fresh finishing combination"),
    ("Cumin", "Cilantro", 0.9, "Mexican & Indian staple"),
    ("Cumin", "Turmeric", 0.85, "warm earthy spice blend"),
    ("Ginger", "Garlic", 0.9, "Asian aromatic base"),
    ("Ginger", "Soy Sauce", 0.85, "umami + warmth"),
    ("Coconut Milk", "Lime", 0.9, "Thai & South Indian classic"),
    ("Coconut Milk", "Ginger", 0.85, "aromatic curry base"),
    ("Chili Flakes", "Garlic", 0.8, "spicy Italian / Chinese heat"),
    ("Avocado", "Lime", 0.9, "guacamole essential"),
    ("Avocado", "Cilantro", 0.85, "fresh Mexican pairing"),
    ("Mushroom", "Thyme", 0.9, "earthy French combination"),
    ("Mushroom", "Garlic", 0.85, "sauté foundation"),
    ("Spinach", "Garlic", 0.8, "quick sauté classic"),
    ("Spinach", "Lemon", 0.75, "bright greens"),
    ("Salmon", "Lemon", 0.9, "classic fish finish"),
    ("Salmon", "Dill", 0.85, "Nordic inspired"),  # Dill not in list – skip or add
    ("Chicken Breast", "Thyme", 0.8, "herby roast"),
    ("Chickpeas", "Cumin", 0.9, "hummus & falafel soul"),
    ("Lentils", "Cumin", 0.85, "dal and stews"),
    ("Tofu", "Soy Sauce", 0.9, "marinade essential"),
    ("Tofu", "Ginger", 0.85, "Asian marinade"),
    ("Pasta", "Parmesan", 0.95, "Italian comfort"),
    ("Pasta", "Basil", 0.9, "pesto and more"),
    ("Rice", "Coconut Milk", 0.8, "coconut rice"),
    ("Quinoa", "Lemon", 0.75, "bright grain salad"),
    ("Bell Pepper", "Onion", 0.8, "fajita / sofrito base"),
    ("Potato", "Garlic", 0.75, "roasted potatoes"),
    ("Eggplant", "Garlic", 0.85, "baba ganoush & ratatouille"),
    ("Zucchini", "Basil", 0.8, "summer vegetable"),
    ("Honey", "Ginger", 0.8, "sweet-spicy glaze"),
    ("Maple Syrup", "Thyme", 0.7, "roasted vegetable glaze"),
]

# Fix: remove Dill reference
PAIRINGS = [p for p in PAIRINGS if p[1] != "Dill" and p[0] != "Dill"]

RECIPES = [
    {
        "name": "Classic Margherita Pizza",
        "description": "Simple Neapolitan-style pizza with tomato, mozzarella and fresh basil.",
        "difficulty": "Medium",
        "prep_time": 30,
        "cook_time": 15,
        "instructions": "Make dough, top with crushed tomato, mozzarella and basil. Bake hot.",
        "cuisine": "Italian",
        "tags": ["Vegetarian"],
        "ingredients": [
            ("Flour", "300", "g"),
            ("Tomato", "200", "g"),
            ("Basil", "10", "leaves"),
            ("Olive Oil", "2", "tbsp"),
            ("Garlic", "1", "clove"),
        ],
    },
    {
        "name": "Vegan Chickpea Curry",
        "description": "Creamy coconut-based curry with chickpeas, spinach and warm spices.",
        "difficulty": "Easy",
        "prep_time": 15,
        "cook_time": 25,
        "instructions": "Sauté aromatics, add spices, chickpeas and coconut milk. Finish with spinach.",
        "cuisine": "Indian",
        "tags": ["Vegan", "Gluten-Free", "Dairy-Free"],
        "ingredients": [
            ("Chickpeas", "400", "g"),
            ("Coconut Milk", "400", "ml"),
            ("Spinach", "150", "g"),
            ("Onion", "1", "large"),
            ("Garlic", "3", "cloves"),
            ("Ginger", "1", "tbsp"),
            ("Cumin", "1", "tsp"),
            ("Turmeric", "1", "tsp"),
            ("Chili Flakes", "0.5", "tsp"),
            ("Rice", "200", "g"),
        ],
    },
    {
        "name": "Garlic Butter Salmon",
        "description": "Pan-seared salmon with a quick garlic-butter and lemon pan sauce.",
        "difficulty": "Easy",
        "prep_time": 10,
        "cook_time": 12,
        "instructions": "Season salmon, sear skin-side down, baste with garlic butter and lemon.",
        "cuisine": "American",
        "tags": ["Gluten-Free", "Keto"],
        "ingredients": [
            ("Salmon", "2", "fillets"),
            ("Butter", "40", "g"),
            ("Garlic", "3", "cloves"),
            ("Lemon", "1", "whole"),
            ("Parsley", "2", "tbsp"),
            ("Black Pepper", "1", "tsp"),
        ],
    },
    {
        "name": "Thai Green Curry with Tofu",
        "description": "Aromatic Thai curry with tofu, vegetables and coconut milk.",
        "difficulty": "Medium",
        "prep_time": 20,
        "cook_time": 20,
        "instructions": "Fry curry paste, add coconut milk, tofu and vegetables. Simmer and serve with rice.",
        "cuisine": "Thai",
        "tags": ["Vegan", "Gluten-Free", "Dairy-Free"],
        "ingredients": [
            ("Tofu", "300", "g"),
            ("Coconut Milk", "400", "ml"),
            ("Bell Pepper", "1", "large"),
            ("Zucchini", "1", "medium"),
            ("Garlic", "2", "cloves"),
            ("Ginger", "1", "tbsp"),
            ("Lime", "1", "whole"),
            ("Cilantro", "handful", ""),
            ("Rice", "200", "g"),
        ],
    },
    {
        "name": "Mushroom Risotto",
        "description": "Creamy Italian rice dish with sautéed mushrooms and thyme.",
        "difficulty": "Medium",
        "prep_time": 15,
        "cook_time": 35,
        "instructions": "Toast rice, add warm stock ladle by ladle, fold in mushrooms and Parmesan.",
        "cuisine": "Italian",
        "tags": ["Vegetarian"],
        "ingredients": [
            ("Rice", "300", "g"),
            ("Mushroom", "250", "g"),
            ("Onion", "1", "small"),
            ("Garlic", "2", "cloves"),
            ("Thyme", "1", "tsp"),
            ("Parmesan", "50", "g"),
            ("Butter", "30", "g"),
            ("Olive Oil", "2", "tbsp"),
            ("Parsley", "2", "tbsp"),
        ],
    },
    {
        "name": "Lentil Shepherd's Pie",
        "description": "Hearty plant-based shepherd's pie with a creamy potato topping.",
        "difficulty": "Medium",
        "prep_time": 25,
        "cook_time": 40,
        "instructions": "Cook lentils with vegetables and spices, top with mashed potato, bake.",
        "cuisine": "American",
        "tags": ["Vegan", "Gluten-Free", "Dairy-Free"],
        "ingredients": [
            ("Lentils", "250", "g"),
            ("Potato", "600", "g"),
            ("Carrot", "2", "medium"),
            ("Onion", "1", "large"),
            ("Garlic", "3", "cloves"),
            ("Cumin", "1", "tsp"),
            ("Tomato", "200", "g"),
            ("Olive Oil", "3", "tbsp"),
            ("Parsley", "2", "tbsp"),
        ],
    },
    {
        "name": "Avocado Toast with Chili",
        "description": "Simple elevated breakfast – smashed avocado, chili flakes and lemon.",
        "difficulty": "Easy",
        "prep_time": 5,
        "cook_time": 5,
        "instructions": "Toast bread, smash avocado with lemon and salt, top with chili flakes.",
        "cuisine": "American",
        "tags": ["Vegan", "Vegetarian"],
        "ingredients": [
            ("Bread", "2", "slices"),
            ("Avocado", "1", "ripe"),
            ("Lemon", "0.5", "whole"),
            ("Chili Flakes", "0.5", "tsp"),
            ("Olive Oil", "1", "tsp"),
            ("Black Pepper", "pinch", ""),
        ],
    },
    {
        "name": "Shakshuka",
        "description": "North-African / Middle-Eastern eggs poached in spiced tomato sauce.",
        "difficulty": "Easy",
        "prep_time": 10,
        "cook_time": 25,
        "instructions": "Cook onion, pepper and spices, add tomatoes, make wells and poach eggs.",
        "cuisine": "Middle Eastern",
        "tags": ["Vegetarian", "Gluten-Free"],
        "ingredients": [
            ("Eggs", "4", "large"),
            ("Tomato", "400", "g"),
            ("Bell Pepper", "1", "large"),
            ("Onion", "1", "medium"),
            ("Garlic", "3", "cloves"),
            ("Cumin", "1", "tsp"),
            ("Chili Flakes", "0.5", "tsp"),
            ("Parsley", "handful", ""),
            ("Olive Oil", "2", "tbsp"),
        ],
    },
    {
        "name": "Lemon Garlic Pasta",
        "description": "Bright, simple pasta with lots of garlic, lemon and parsley.",
        "difficulty": "Easy",
        "prep_time": 5,
        "cook_time": 15,
        "instructions": "Cook pasta, make garlic-lemon oil, toss with pasta water and parsley.",
        "cuisine": "Italian",
        "tags": ["Vegetarian"],
        "ingredients": [
            ("Pasta", "300", "g"),
            ("Garlic", "4", "cloves"),
            ("Lemon", "1", "whole"),
            ("Parsley", "3", "tbsp"),
            ("Olive Oil", "4", "tbsp"),
            ("Parmesan", "40", "g"),
            ("Black Pepper", "1", "tsp"),
        ],
    },
    {
        "name": "Quinoa Buddha Bowl",
        "description": "Nourishing bowl with quinoa, roasted vegetables, avocado and tahini-like dressing.",
        "difficulty": "Easy",
        "prep_time": 15,
        "cook_time": 25,
        "instructions": "Cook quinoa, roast vegetables, assemble with avocado and lemon dressing.",
        "cuisine": "American",
        "tags": ["Vegan", "Gluten-Free", "Dairy-Free"],
        "ingredients": [
            ("Quinoa", "150", "g"),
            ("Broccoli", "1", "head"),
            ("Carrot", "2", "medium"),
            ("Avocado", "1", "ripe"),
            ("Chickpeas", "200", "g"),
            ("Lemon", "1", "whole"),
            ("Olive Oil", "3", "tbsp"),
            ("Garlic", "1", "clove"),
            ("Cumin", "0.5", "tsp"),
        ],
    },
    {
        "name": "Japanese-inspired Tofu Stir-fry",
        "description": "Quick stir-fry with tofu, vegetables and a soy-ginger glaze.",
        "difficulty": "Easy",
        "prep_time": 15,
        "cook_time": 12,
        "instructions": "Press and cube tofu, stir-fry with vegetables, finish with soy-ginger sauce.",
        "cuisine": "Japanese",
        "tags": ["Vegan", "Dairy-Free"],
        "ingredients": [
            ("Tofu", "300", "g"),
            ("Broccoli", "1", "head"),
            ("Bell Pepper", "1", "large"),
            ("Garlic", "2", "cloves"),
            ("Ginger", "1", "tbsp"),
            ("Soy Sauce", "3", "tbsp"),
            ("Sesame Oil", "1", "tbsp"),
            ("Rice", "200", "g"),
        ],
    },
    {
        "name": "French Onion Soup (simplified)",
        "description": "Caramelised onion soup finished with thyme and a touch of butter.",
        "difficulty": "Medium",
        "prep_time": 15,
        "cook_time": 60,
        "instructions": "Slowly caramelise onions, deglaze, simmer, finish with thyme.",
        "cuisine": "French",
        "tags": ["Vegetarian"],
        "ingredients": [
            ("Onion", "4", "large"),
            ("Butter", "40", "g"),
            ("Thyme", "1", "tsp"),
            ("Garlic", "2", "cloves"),
            ("Bread", "4", "slices"),
            ("Parsley", "1", "tbsp"),
            ("Black Pepper", "1", "tsp"),
        ],
    },
]


def seed(tx):
    # Cuisines
    for name, desc in CUISINES:
        tx.run(
            "MERGE (c:Cuisine {name: $name}) SET c.description = $desc",
            name=name, desc=desc,
        )

    # Dietary tags
    for name in DIETARY_TAGS:
        tx.run("MERGE (d:DietaryTag {name: $name})", name=name)

    # Ingredients
    for name, category in INGREDIENTS:
        tx.run(
            "MERGE (i:Ingredient {name: $name}) SET i.category = $category",
            name=name, category=category,
        )

    # Substitutions (directed)
    for src, tgt, reason in SUBSTITUTIONS:
        tx.run(
            """
            MATCH (a:Ingredient {name: $src}), (b:Ingredient {name: $tgt})
            MERGE (a)-[r:SUBSTITUTES_FOR]->(b)
            SET r.reason = $reason
            """,
            src=src, tgt=tgt, reason=reason,
        )

    # Flavor pairings (undirected – create both ways for easy traversal)
    for a, b, strength, notes in PAIRINGS:
        tx.run(
            """
            MATCH (x:Ingredient {name: $a}), (y:Ingredient {name: $b})
            MERGE (x)-[r:PAIRS_WITH]->(y)
            SET r.strength = $strength, r.notes = $notes
            MERGE (y)-[r2:PAIRS_WITH]->(x)
            SET r2.strength = $strength, r2.notes = $notes
            """,
            a=a, b=b, strength=strength, notes=notes,
        )

    # Recipes
    for recipe in RECIPES:
        tx.run(
            """
            MERGE (r:Recipe {name: $name})
            SET r.description = $description,
                r.difficulty = $difficulty,
                r.prep_time_minutes = $prep,
                r.cook_time_minutes = $cook,
                r.instructions = $instructions
            """,
            name=recipe["name"],
            description=recipe["description"],
            difficulty=recipe["difficulty"],
            prep=recipe["prep_time"],
            cook=recipe["cook_time"],
            instructions=recipe["instructions"],
        )

        # Cuisine link
        tx.run(
            """
            MATCH (r:Recipe {name: $rname}), (c:Cuisine {name: $cname})
            MERGE (r)-[:BELONGS_TO]->(c)
            """,
            rname=recipe["name"], cname=recipe["cuisine"],
        )

        # Dietary tags
        for tag in recipe["tags"]:
            tx.run(
                """
                MATCH (r:Recipe {name: $rname}), (d:DietaryTag {name: $tag})
                MERGE (r)-[:TAGGED_AS]->(d)
                """,
                rname=recipe["name"], tag=tag,
            )

        # Ingredients
        for ing_name, qty, unit in recipe["ingredients"]:
            tx.run(
                """
                MATCH (r:Recipe {name: $rname}), (i:Ingredient {name: $iname})
                MERGE (r)-[c:CONTAINS]->(i)
                SET c.quantity = $qty, c.unit = $unit
                """,
                rname=recipe["name"], iname=ing_name, qty=qty, unit=unit,
            )


def main():
    print("Connecting to CognoDB…")
    with driver.session() as session:
        print("Clearing existing data…")
        session.execute_write(clear_graph)
        print("Creating constraints…")
        session.execute_write(create_constraints)
        print("Seeding graph…")
        session.execute_write(seed)

    # Quick stats
    with driver.session() as session:
        nodes = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        rels = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        print(f"Done. Nodes: {nodes}, Relationships: {rels}")

    driver.close()
    print("Seed complete.")


if __name__ == "__main__":
    main()
