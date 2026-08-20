/**
 * FlavorNet frontend – clean, intentional interactions
 */

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => [...document.querySelectorAll(sel)];

const ui = {
  status: $("#connection-status"),
  ingredient: $("#search-ingredient"),
  cuisine: $("#filter-cuisine"),
  dietary: $("#filter-dietary"),
  loading: $("#loading"),
  empty: $("#empty"),
  error: $("#error"),
  errorMsg: $("#error-message"),
  results: $("#results-list"),
  chips: $("#suggestion-chips"),
  modal: $("#modal"),
  modalBody: $("#modal-body"),
};

let lastAction = null;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function show(el) {
  el.classList.remove("hidden");
}
function hide(el) {
  el.classList.add("hidden");
}

function setLoading(isLoading) {
  hide(ui.empty);
  hide(ui.error);
  hide(ui.results);
  if (isLoading) show(ui.loading);
  else hide(ui.loading);
}

function showError(msg) {
  hide(ui.loading);
  hide(ui.empty);
  hide(ui.results);
  ui.errorMsg.textContent = msg;
  show(ui.error);
}

function showResults() {
  hide(ui.loading);
  hide(ui.empty);
  hide(ui.error);
  show(ui.results);
}

async function api(path) {
  const res = await fetch(path);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Connection check
// ---------------------------------------------------------------------------

async function checkHealth() {
  try {
    await api("/api/health");
    ui.status.textContent = "Database connected";
    ui.status.className = "status status--ok";
    return true;
  } catch (e) {
    ui.status.textContent = "Database offline";
    ui.status.className = "status status--error";
    return false;
  }
}

// ---------------------------------------------------------------------------
// Populate filters & suggestions
// ---------------------------------------------------------------------------

async function loadFilters() {
  try {
    const [cuisines, tags, ingredients] = await Promise.all([
      api("/api/cuisines"),
      api("/api/dietary-tags"),
      api("/api/random-ingredients?limit=10"),
    ]);

    cuisines.forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c.name;
      opt.textContent = c.name;
      ui.cuisine.appendChild(opt);
    });

    tags.forEach((t) => {
      const opt = document.createElement("option");
      opt.value = t.name;
      opt.textContent = t.name;
      ui.dietary.appendChild(opt);
    });

    ui.chips.innerHTML = "";
    ingredients.forEach((name) => {
      const chip = document.createElement("button");
      chip.className = "chip";
      chip.textContent = name;
      chip.addEventListener("click", () => {
        ui.ingredient.value = name;
        doSearch();
      });
      ui.chips.appendChild(chip);
    });
  } catch (e) {
    console.warn("Could not load filters", e);
  }
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

function renderRecipeCards(items, extraKey = null) {
  ui.results.innerHTML = "";
  if (!items || items.length === 0) {
    hide(ui.results);
    show(ui.empty);
    ui.empty.querySelector("p").textContent = "No recipes matched. Try a different ingredient or filter.";
    return;
  }

  items.forEach((r) => {
    const card = document.createElement("article");
    card.className = "result-card";
    card.innerHTML = `
      <h3>${escapeHtml(r.name)}</h3>
      <div class="meta">
        ${(r.cuisines || []).map((c) => `<span class="badge">${escapeHtml(c)}</span>`).join("")}
        ${(r.dietary_tags || []).map((t) => `<span class="badge badge--accent">${escapeHtml(t)}</span>`).join("")}
        ${r.difficulty ? `<span class="badge">${escapeHtml(r.difficulty)}</span>` : ""}
      </div>
      <p>${escapeHtml(r.description || "")}</p>
      ${extraKey && r[extraKey] !== undefined ? `<div class="extra">${formatExtra(extraKey, r)}</div>` : ""}
    `;
    card.addEventListener("click", () => openRecipe(r.name));
    ui.results.appendChild(card);
  });
  showResults();
}

function formatExtra(key, r) {
  if (key === "closest_hops") {
    return r.closest_hops === 0
      ? "Contains the ingredient"
      : `Reachable in ${r.closest_hops} substitution hop${r.closest_hops > 1 ? "s" : ""}`;
  }
  if (key === "substitute") return `Category: ${r.category || "—"} · ${r.hops} hop(s)`;
  if (key === "strength") return `Strength ${(r.strength * 100).toFixed(0)}%`;
  return "";
}

function renderSubstitutionCards(items) {
  ui.results.innerHTML = "";
  if (!items.length) {
    hide(ui.results);
    show(ui.empty);
    ui.empty.querySelector("p").textContent = "No substitutions found for that ingredient.";
    return;
  }
  items.forEach((s) => {
    const card = document.createElement("article");
    card.className = "result-card";
    card.style.cursor = "default";
    card.innerHTML = `
      <h3>${escapeHtml(s.substitute)}</h3>
      <div class="meta">
        <span class="badge">${escapeHtml(s.category || "ingredient")}</span>
        <span class="badge badge--accent">${s.hops} hop${s.hops > 1 ? "s" : ""}</span>
      </div>
      <p>${(s.reasons || []).filter(Boolean).join(" → ") || "Direct or multi-hop substitute"}</p>
    `;
    ui.results.appendChild(card);
  });
  showResults();
}

function renderPairingCards(items) {
  ui.results.innerHTML = "";
  if (!items.length) {
    hide(ui.results);
    show(ui.empty);
    ui.empty.querySelector("p").textContent = "No strong pairings found.";
    return;
  }
  items.forEach((p) => {
    const card = document.createElement("article");
    card.className = "result-card";
    card.style.cursor = "default";
    card.innerHTML = `
      <h3>${escapeHtml(p.ingredient)}</h3>
      <div class="meta">
        <span class="badge">${escapeHtml(p.category || "")}</span>
        <span class="badge badge--accent">${(p.strength * 100).toFixed(0)}% strength</span>
      </div>
      <p>${escapeHtml(p.notes || "Goes well together")}</p>
    `;
    ui.results.appendChild(card);
  });
  showResults();
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

async function doSearch() {
  lastAction = doSearch;
  setLoading(true);
  try {
    const params = new URLSearchParams();
    if (ui.ingredient.value.trim()) params.set("ingredient", ui.ingredient.value.trim());
    if (ui.cuisine.value) params.set("cuisine", ui.cuisine.value);
    if (ui.dietary.value) params.set("dietary", ui.dietary.value);
    const data = await api(`/api/recipes?${params}`);
    renderRecipeCards(data);
  } catch (e) {
    showError(e.message);
  }
}

async function doRecommend() {
  const ing = ui.ingredient.value.trim();
  if (!ing) {
    showError("Enter an ingredient to recommend recipes via substitution paths.");
    return;
  }
  lastAction = doRecommend;
  setLoading(true);
  try {
    const params = new URLSearchParams({ ingredient: ing, max_hops: 3 });
    if (ui.dietary.value) params.set("dietary", ui.dietary.value);
    const data = await api(`/api/recommend?${params}`);
    renderRecipeCards(data, "closest_hops");
  } catch (e) {
    showError(e.message);
  }
}

async function doSubstitutions() {
  const ing = ui.ingredient.value.trim();
  if (!ing) {
    showError("Enter an ingredient to find substitutions.");
    return;
  }
  lastAction = doSubstitutions;
  setLoading(true);
  try {
    const data = await api(`/api/substitutions/${encodeURIComponent(ing)}?max_hops=2`);
    renderSubstitutionCards(data);
  } catch (e) {
    showError(e.message);
  }
}

async function doPairings() {
  const ing = ui.ingredient.value.trim();
  if (!ing) {
    showError("Enter an ingredient to explore flavor pairings.");
    return;
  }
  lastAction = doPairings;
  setLoading(true);
  try {
    const data = await api(`/api/pairings/${encodeURIComponent(ing)}`);
    renderPairingCards(data);
  } catch (e) {
    showError(e.message);
  }
}

async function openRecipe(name) {
  try {
    const r = await api(`/api/recipes/${encodeURIComponent(name)}`);
    ui.modalBody.innerHTML = `
      <h2>${escapeHtml(r.name)}</h2>
      <div class="meta">
        ${(r.cuisines || []).map((c) => `<span class="badge">${escapeHtml(c)}</span>`).join("")}
        ${(r.dietary_tags || []).map((t) => `<span class="badge badge--accent">${escapeHtml(t)}</span>`).join("")}
        ${r.difficulty ? `<span class="badge">${escapeHtml(r.difficulty)}</span>` : ""}
        ${r.prep_time != null ? `<span class="badge">${r.prep_time + (r.cook_time || 0)} min</span>` : ""}
      </div>
      <p>${escapeHtml(r.description || "")}</p>
      <div class="section">
        <h4>Ingredients</h4>
        <ul class="ingredient-list">
          ${(r.ingredients || [])
            .filter((i) => i.name)
            .map(
              (i) => `
            <li>
              <span>${escapeHtml(i.name)}</span>
              <span class="qty">${escapeHtml([i.quantity, i.unit].filter(Boolean).join(" "))}</span>
            </li>`
            )
            .join("")}
        </ul>
      </div>
      ${
        r.instructions
          ? `<div class="section"><h4>Method</h4><p>${escapeHtml(r.instructions)}</p></div>`
          : ""
      }
    `;
    show(ui.modal);
  } catch (e) {
    showError(e.message);
  }
}

function closeModal() {
  hide(ui.modal);
}

// ---------------------------------------------------------------------------
// Event listeners
// ---------------------------------------------------------------------------

$("#btn-search").addEventListener("click", doSearch);
$("#btn-recommend").addEventListener("click", doRecommend);
$("#btn-subs").addEventListener("click", doSubstitutions);
$("#btn-pairings").addEventListener("click", doPairings);
$("#btn-retry").addEventListener("click", () => lastAction && lastAction());
$("#modal-close").addEventListener("click", closeModal);
$("#modal-backdrop").addEventListener("click", closeModal);

ui.ingredient.addEventListener("keydown", (e) => {
  if (e.key === "Enter") doSearch();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeModal();
});

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

(async function init() {
  const ok = await checkHealth();
  if (ok) {
    await loadFilters();
  } else {
    showError("Cannot reach the graph database. Check your CognoDB credentials and that the instance is running.");
  }
})();
