"""
All Cypher queries used by FlavorNet.
Every query is parameterised — never string-concatenated.
Includes multi-hop traversals and queries that are awkward in pure SQL.
"""

from typing import Any, Dict, List, Optional

from .database import get_session


def run_query(cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Execute a parameterised Cypher query and return list of records as dicts."""
    with get_session() as session:
        result = session.run(cypher, params or {})
        return [dict(record) for record in result]


# ---------------------------------------------------------------------------
# Discovery queries
# ---------------------------------------------------------------------------

def get_all_cuisines() -> List[Dict[str, Any]]:
    return run_query(
        """
        MATCH (c:Cuisine)
        RETURN c.name AS name, c.description AS description
        ORDER BY c.name
        """
    )


def get_all_dietary_tags() -> List[Dict[str, Any]]:
    return run_query(
        """
        MATCH (d:DietaryTag)
        RETURN d.name AS name
        ORDER BY d.name
        """
    )


def search_recipes(
    cuisine: Optional[str] = None,
    dietary: Optional[str] = None,
    ingredient: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Flexible search with optional filters (compatible Cypher)."""
    return run_query(
        """
        MATCH (r:Recipe)
        OPTIONAL MATCH (r)-[:BELONGS_TO]->(c:Cuisine)
        OPTIONAL MATCH (r)-[:TAGGED_AS]->(d:DietaryTag)
        OPTIONAL MATCH (r)-[:CONTAINS]->(i:Ingredient)
        WITH r,
             collect(DISTINCT c.name) AS cuisines,
             collect(DISTINCT d.name) AS dietary_tags,
             collect(DISTINCT toLower(i.name)) AS ingredient_names
        WHERE ($cuisine IS NULL OR $cuisine IN cuisines)
          AND ($dietary IS NULL OR $dietary IN dietary_tags)
          AND ($ingredient IS NULL OR any(n IN ingredient_names WHERE n CONTAINS toLower($ingredient)))
        RETURN r.name AS name,
               r.description AS description,
               r.difficulty AS difficulty,
               r.prep_time_minutes AS prep_time,
               r.cook_time_minutes AS cook_time,
               cuisines,
               dietary_tags
        ORDER BY r.name
        LIMIT $limit
        """,
        {
            "cuisine": cuisine,
            "dietary": dietary,
            "ingredient": ingredient,
            "limit": limit,
        },
    )


def get_recipe_detail(name: str) -> Optional[Dict[str, Any]]:
    results = run_query(
        """
        MATCH (r:Recipe {name: $name})
        OPTIONAL MATCH (r)-[c:CONTAINS]->(i:Ingredient)
        OPTIONAL MATCH (r)-[:BELONGS_TO]->(cuisine:Cuisine)
        OPTIONAL MATCH (r)-[:TAGGED_AS]->(tag:DietaryTag)
        RETURN r.name AS name,
               r.description AS description,
               r.difficulty AS difficulty,
               r.prep_time_minutes AS prep_time,
               r.cook_time_minutes AS cook_time,
               r.instructions AS instructions,
               collect(DISTINCT {
                   name: i.name,
                   quantity: c.quantity,
                   unit: c.unit,
                   category: i.category
               }) AS ingredients,
               collect(DISTINCT cuisine.name) AS cuisines,
               collect(DISTINCT tag.name) AS dietary_tags
        """,
        {"name": name},
    )
    return results[0] if results else None


# ---------------------------------------------------------------------------
# Multi-hop & graph-native queries
# ---------------------------------------------------------------------------

def find_substitutions(ingredient_name: str, max_hops: int = 2) -> List[Dict[str, Any]]:
    """
    Multi-hop substitution paths.
    Example: "butter" → "olive oil" → "coconut oil" (vegan path).
    Note: Cypher does not allow parameters in variable-length bounds,
    so we use a fixed *1..4 and filter by length afterwards.
    """
    return run_query(
        """
        MATCH path = (start:Ingredient {name: $name})-[:SUBSTITUTES_FOR*1..4]-(alt:Ingredient)
        WHERE start <> alt AND length(path) <= $max_hops
        WITH alt, min(length(path)) AS hops,
             [r IN relationships(path) | r.reason] AS reasons
        RETURN DISTINCT alt.name AS substitute,
               alt.category AS category,
               hops,
               reasons
        ORDER BY hops, alt.name
        LIMIT 15
        """,
        {"name": ingredient_name, "max_hops": max_hops},
    )


def find_flavor_pairings(ingredient_name: str, min_strength: float = 0.5) -> List[Dict[str, Any]]:
    """Direct + one-hop flavor pairings."""
    return run_query(
        """
        MATCH (i:Ingredient {name: $name})-[p:PAIRS_WITH]-(other:Ingredient)
        WHERE p.strength >= $min_strength
        RETURN other.name AS ingredient,
               other.category AS category,
               p.strength AS strength,
               p.notes AS notes
        ORDER BY p.strength DESC
        LIMIT 12
        """,
        {"name": ingredient_name, "min_strength": min_strength},
    )


def recommend_recipes_by_ingredient_path(
    start_ingredient: str,
    target_dietary: Optional[str] = None,
    max_hops: int = 3,
) -> List[Dict[str, Any]]:
    """
    The "awkward for relational" query:
    Find recipes that either contain the ingredient OR contain a substitute
    reachable within max_hops, optionally filtered by dietary tag.
    Variable-length path + recipe aggregation is painful in pure SQL.
    """
    return run_query(
        """
        MATCH (start:Ingredient {name: $start})
        MATCH path = (start)-[:SUBSTITUTES_FOR*0..4]-(candidate:Ingredient)
        WHERE length(path) <= $max_hops
        MATCH (r:Recipe)-[:CONTAINS]->(candidate)
        OPTIONAL MATCH (r)-[:TAGGED_AS]->(dtag:DietaryTag)
        WITH r, candidate, path, collect(DISTINCT dtag.name) AS tags
        WHERE ($dietary IS NULL OR $dietary IN tags)
        WITH r, collect(DISTINCT candidate.name) AS matched_ingredients,
             min(length(path)) AS closest_hops
        OPTIONAL MATCH (r)-[:BELONGS_TO]->(c:Cuisine)
        OPTIONAL MATCH (r)-[:TAGGED_AS]->(d:DietaryTag)
        RETURN r.name AS name,
               r.description AS description,
               r.difficulty AS difficulty,
               closest_hops,
               matched_ingredients,
               collect(DISTINCT c.name) AS cuisines,
               collect(DISTINCT d.name) AS dietary_tags
        ORDER BY closest_hops, r.name
        LIMIT 15
        """,
        {
            "start": start_ingredient,
            "dietary": target_dietary,
            "max_hops": max_hops,
        },
    )


def find_compatible_recipes(ingredient_a: str, ingredient_b: str) -> List[Dict[str, Any]]:
    """
    Recipes that already contain both ingredients, or that contain
    a strong pairing path between them.
    """
    return run_query(
        """
        MATCH (a:Ingredient {name: $a}), (b:Ingredient {name: $b})
        // Direct co-occurrence
        OPTIONAL MATCH (r1:Recipe)-[:CONTAINS]->(a), (r1)-[:CONTAINS]->(b)
        // Or recipes that use a strong pairing
        OPTIONAL MATCH (a)-[p:PAIRS_WITH]-(b)
        OPTIONAL MATCH (r2:Recipe)-[:CONTAINS]->(a)
        WHERE p IS NOT NULL AND p.strength >= 0.7
        WITH collect(DISTINCT r1) + collect(DISTINCT r2) AS recipes
        UNWIND recipes AS r
        WITH DISTINCT r
        WHERE r IS NOT NULL
        OPTIONAL MATCH (r)-[:BELONGS_TO]->(c:Cuisine)
        RETURN r.name AS name,
               r.description AS description,
               r.difficulty AS difficulty,
               collect(DISTINCT c.name) AS cuisines
        ORDER BY r.name
        LIMIT 12
        """,
        {"a": ingredient_a, "b": ingredient_b},
    )


def get_graph_stats() -> Dict[str, Any]:
    results = run_query(
        """
        MATCH (n)
        WITH labels(n)[0] AS label, count(*) AS cnt
        RETURN collect({label: label, count: cnt}) AS node_counts
        """
    )
    rel_results = run_query(
        """
        MATCH ()-[r]->()
        RETURN type(r) AS type, count(*) AS count
        ORDER BY count DESC
        """
    )
    return {
        "nodes": results[0]["node_counts"] if results else [],
        "relationships": rel_results,
    }


def get_random_ingredients(limit: int = 8) -> List[str]:
    rows = run_query(
        """
        MATCH (i:Ingredient)
        RETURN i.name AS name
        ORDER BY rand()
        LIMIT $limit
        """,
        {"limit": limit},
    )
    return [r["name"] for r in rows]