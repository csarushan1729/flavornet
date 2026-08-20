"""
FlavorNet – Culinary Knowledge Graph Application
FastAPI backend powered by CognoDB (Neo4j-compatible graph database).
"""

from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import queries
from .database import verify_connectivity, close_driver

app = FastAPI(
    title="FlavorNet",
    description="Culinary Knowledge Graph – explore recipes through ingredient relationships",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("shutdown")
def shutdown_event():
    close_driver()


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.get("/api/health")
async def health():
    """Health check – used by the frontend to show connection status."""
    ok = verify_connectivity()
    if not ok:
        raise HTTPException(
            status_code=503,
            detail="Database unreachable. Check NEO4J_URI and NEO4J_PASSWORD.",
        )
    return {"status": "ok", "database": "connected"}


@app.get("/api/cuisines")
async def list_cuisines():
    try:
        return queries.get_all_cuisines()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/dietary-tags")
async def list_dietary_tags():
    try:
        return queries.get_all_dietary_tags()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/recipes")
async def search_recipes(
    cuisine: Optional[str] = Query(None),
    dietary: Optional[str] = Query(None),
    ingredient: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=50),
):
    try:
        return queries.search_recipes(cuisine, dietary, ingredient, limit)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/recipes/{name}")
async def recipe_detail(name: str):
    try:
        recipe = queries.get_recipe_detail(name)
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        return recipe
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/substitutions/{ingredient}")
async def substitutions(ingredient: str, max_hops: int = Query(2, ge=1, le=4)):
    """Multi-hop substitution paths – classic graph query."""
    try:
        return queries.find_substitutions(ingredient, max_hops)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/pairings/{ingredient}")
async def pairings(ingredient: str, min_strength: float = Query(0.5, ge=0.0, le=1.0)):
    try:
        return queries.find_flavor_pairings(ingredient, min_strength)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/recommend")
async def recommend(
    ingredient: str = Query(..., description="Starting ingredient"),
    dietary: Optional[str] = Query(None),
    max_hops: int = Query(3, ge=0, le=5),
):
    """
    Graph-native recommendation:
    Recipes reachable via substitution paths (including the ingredient itself).
    """
    try:
        return queries.recommend_recipes_by_ingredient_path(ingredient, dietary, max_hops)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/compatible")
async def compatible(
    a: str = Query(..., description="First ingredient"),
    b: str = Query(..., description="Second ingredient"),
):
    try:
        return queries.find_compatible_recipes(a, b)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/stats")
async def stats():
    try:
        return queries.get_graph_stats()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/random-ingredients")
async def random_ingredients(limit: int = Query(8, ge=1, le=20)):
    try:
        return queries.get_random_ingredients(limit)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
