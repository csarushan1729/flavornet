# FlavorNet: Culinary Knowledge Graph

A complete web application backed by **CognoDB** (a managed graph database that speaks openCypher over Bolt).  
FlavorNet lets anyone explore recipes through *connections*: ingredient substitutions, multi-hop substitution paths, flavor pairings, cuisines and dietary constraints.

**Why this use case?**  
Recipes, ingredients, substitutions and pairings form a natural network. The interesting questions are almost always about *paths* and *relationships*, not simple tabular lookups.

---

## Why a graph database?

| Question | Relational approach | Graph approach |
|----------|---------------------|----------------|
| “What can I use instead of butter (including multi-step vegan paths)?” | Recursive CTE or multiple self-joins on a substitution table; awkward to parameterise depth | `MATCH (butter)-[:SUBSTITUTES_FOR*1..3]-(alt)` |
| “Find recipes reachable if I allow up to 2 substitutions from an ingredient I have” | Complex join explosion + aggregation | Variable-length path + recipe aggregation in one query |
| “Ingredients that pair well, and recipes that already use both” | Adjacency table + extra joins | Typed `PAIRS_WITH` relationships with strength properties |
| Provenance / reason on every substitution | Extra columns or audit tables | Relationship properties (`reason`, `strength`, `notes`) travel with the path |

A graph model makes the domain vocabulary (CONTAINS, SUBSTITUTES_FOR, PAIRS_WITH, BELONGS_TO, TAGGED_AS) first-class. The same questions that require recursive CTEs or application-level graph walking in SQL become readable, parameterised Cypher.

---

## Data model

```
(:Recipe {name, description, difficulty, prep_time_minutes, cook_time_minutes, instructions})
(:Ingredient {name, category})
(:Cuisine {name, description})
(:DietaryTag {name})

(:Recipe)-[:CONTAINS {quantity, unit}]->(:Ingredient)
(:Ingredient)-[:SUBSTITUTES_FOR {reason}]->(:Ingredient)
(:Ingredient)-[:PAIRS_WITH {strength, notes}]->(:Ingredient)   // stored both directions
(:Recipe)-[:BELONGS_TO]->(:Cuisine)
(:Recipe)-[:TAGGED_AS]->(:DietaryTag)
```

### Diagram (text)

```
                    ┌─────────────┐
                    │  Cuisine    │
                    └──────▲──────┘
                           │ BELONGS_TO
┌──────────┐    CONTAINS   │
│Ingredient│◄──────────────┤
└────┬─────┘               │
     │                     │
     │ SUBSTITUTES_FOR     │
     │ PAIRS_WITH          │
     ▼                     │
┌──────────┐          ┌────┴─────┐
│Ingredient│          │  Recipe  │──TAGGED_AS──►(:DietaryTag)
└──────────┘          └──────────┘
```

---

## Features demonstrated

- **Thoughtful graph model** with labelled nodes, typed relationships and properties
- **Realistic seed data** (12+ recipes, 50+ ingredients, substitution & pairing edges)
- **Parameterised Cypher only** (no string concatenation)
- **Multi-hop traversal** (`SUBSTITUTES_FOR*1..n`)
- **Relationally-awkward query**: recommend recipes via substitution paths of variable depth, optionally filtered by dietary tag
- Clean FastAPI backend + intentional dark UI with loading / empty / error states
- Connection secrets exclusively via environment variables
- Graceful degradation when the database is unreachable

---

## Quick start

### 1. Create a CognoDB instance

1. Go to https://console.cognodb.com/signup and create a free account (no credit card).
2. Create a free **c0** instance and pick a region.
3. Copy the `bolt+s://…` URI and the generated password for user `cognodb` (shown only once).

### 2. Clone & configure

```bash
git clone <your-repo-url>
cd flavornet

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your real URI and password
```

### 3. Seed the graph

```bash
python scripts/seed.py
```

You should see something like:

```
Connecting to CognoDB…
Clearing existing data…
Creating constraints…
Seeding graph…
Done. Nodes: ~80, Relationships: ~200
Seed complete.
```

### 4. Run the application

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

---

## Main Cypher queries (explained)

### Multi-hop substitutions
```cypher
MATCH path = (start:Ingredient {name: $name})-[:SUBSTITUTES_FOR*1..$max_hops]-(alt:Ingredient)
WHERE start <> alt
RETURN DISTINCT alt.name, min(length(path)) AS hops, …
```
Finds direct *and* indirect substitutes (e.g. Butter → Olive Oil → Sesame Oil).

### Recommendation via substitution paths (awkward in pure SQL)
```cypher
MATCH (start:Ingredient {name: $start})
MATCH path = (start)-[:SUBSTITUTES_FOR*0..$max_hops]-(candidate:Ingredient)
MATCH (r:Recipe)-[:CONTAINS]->(candidate)
WHERE ($dietary IS NULL OR EXISTS { … })
RETURN r, min(length(path)) AS closest_hops, …
```
“Show me recipes I can make if I allow up to 3 substitutions from the ingredient I have, optionally only vegan ones.”

### Flavor pairings
```cypher
MATCH (i:Ingredient {name: $name})-[p:PAIRS_WITH]-(other)
WHERE p.strength >= $min_strength
RETURN other.name, p.strength, p.notes
```

All queries are executed through the official Neo4j Python driver with parameters — never string-concatenated Cypher.

---

## Project structure

```
flavornet/
├── backend/
│   ├── main.py          # FastAPI app + routes
│   ├── database.py      # Driver singleton, env-based config
│   └── queries.py       # All Cypher (parameterised)
├── scripts/
│   └── seed.py          # Realistic seed data + constraints
├── static/
│   ├── index.html
│   ├── css/styles.css
│   └── js/app.js
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```
---
## Demo


https://github.com/user-attachments/assets/3611c322-61e6-437a-84b1-519471801c09


---

Built for the Wexa AI / CognoDB take-home assignment.
