"use strict";
const $ = (selector) => document.querySelector(selector);
const authenticated = document.body.dataset.authenticated === "true";
let toastTimer;
function toast(message) {
  const el = $("#toast");
  el.textContent = message; el.hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => { el.hidden = true; }, 4500);
}
function csrfToken() {
  return document.cookie.split("; ").find((row) => row.startsWith("csrftoken="))?.split("=")[1] || "";
}
async function api(url, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 22000);
  try {
    const response = await fetch(url, {
      credentials: "same-origin", signal: controller.signal, ...options,
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken(), ...options.headers },
    });
    if (response.status === 204) return null;
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "No pudimos completar la solicitud. Revisa los datos e inténtalo de nuevo.");
    return data;
  } catch (error) {
    if (error.name === "AbortError") throw new Error("La consulta tardó demasiado. Vuelve a intentarlo.");
    if (error instanceof TypeError || error instanceof SyntaxError) throw new Error("No pudimos conectar con el servidor. Revisa tu conexión.");
    throw error;
  } finally { clearTimeout(timer); }
}
function node(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined) el.textContent = text;
  return el;
}
function status(message, retry) {
  const el = $("#recipe-status");
  el.replaceChildren(); el.hidden = false;
  el.append(node("p", "", message));
  if (retry) {
    const button = node("button", "button small ghost", "Volver a intentar ↗");
    button.type = "button"; button.addEventListener("click", retry); el.append(button);
  }
}
function recipeCard(meal, favorite = false) {
  const card = node("article", "recipe-card");
  const link = node("a", "recipe-image-link");
  link.href = `/recetas/${encodeURIComponent(meal.id)}/`;
  const img = node("img"); img.src = meal.image || "/static/img/favicon.svg";
  img.alt = meal.name; img.loading = "lazy"; img.width = 480; img.height = 400;
  link.append(img); card.append(link);
  const content = node("div", "recipe-card-content");
  content.append(node("p", "eyebrow", `${meal.category} / ${meal.area}`));
  const heading = node("h3"); const title = node("a", "", meal.name);
  title.href = link.href; heading.append(title); content.append(heading);
  const bottom = node("div", "recipe-card-bottom");
  const detail = node("a", "text-link", "Ver receta ↗"); detail.href = link.href;
  const save = node("button", "save-button", favorite ? "Quitar ♡" : "Guardar ♡");
  save.type = "button"; save.setAttribute("aria-label", `${favorite ? "Quitar" : "Guardar"} ${meal.name}`);
  save.addEventListener("click", async () => {
    if (!authenticated) { window.location.href = "/ingresar/"; return; }
    save.disabled = true;
    try {
      if (favorite) {
        await api(`/api/favoritos/${meal.id}/`, { method: "DELETE" });
        card.remove(); toast("Receta eliminada de tus favoritos.");
        if (!$("#recipe-grid").children.length) emptyFavorites();
      } else {
        await api("/api/favoritos/", { method: "POST", body: JSON.stringify({ meal_id: meal.id }) });
        toast("Receta guardada en tus favoritos."); save.textContent = "Guardada ✓";
      }
    } catch (error) { toast(error.message); }
    finally { save.disabled = false; }
  });
  bottom.append(detail, save); content.append(bottom); card.append(content); return card;
}
function emptyFavorites() {
  status("Tu recetario está esperando su primera receta. Explora y guarda algo que se te antoje.");
  const link = node("a", "button small", "Encontrar mi primera receta ↗");
  link.href = "/recetas/"; $("#recipe-status").append(link);
}
async function loadFavorites() {
  const grid = $("#recipe-grid"); grid.setAttribute("aria-busy", "true");
  status("Abriendo tu recetario…");
  try {
    const data = await api("/api/favoritos/"); grid.replaceChildren();
    if (!data.results.length) { emptyFavorites(); return; }
    $("#recipe-status").hidden = true;
    data.results.forEach((item) => grid.append(recipeCard(item.recipe, true)));
  } catch (error) { status(error.message, loadFavorites); }
  finally { grid.setAttribute("aria-busy", "false"); }
}
let searchVersion = 0;
async function loadRecipes(query = "") {
  const version = ++searchVersion;
  const grid = $("#recipe-grid"); grid.replaceChildren(); grid.setAttribute("aria-busy", "true");
  $("#result-count").textContent = "";
  status("Consultando el recetario…");
  document.querySelectorAll("[data-query]").forEach((el) => el.classList.toggle("active", el.dataset.query === query));
  try {
    const data = await api(`/api/recetas/?q=${encodeURIComponent(query)}`);
    if (version !== searchVersion) return;
    $("#result-count").textContent = `${data.count} ${data.count === 1 ? "receta encontrada" : "recetas encontradas"}`;
    if (!data.count) { status("No encontramos recetas con ese nombre. Prueba con pasta, chicken o cake."); return; }
    $("#recipe-status").hidden = true;
    data.results.forEach((meal) => grid.append(recipeCard(meal)));
  } catch (error) { if (version === searchVersion) status(error.message, () => loadRecipes(query)); }
  finally { if (version === searchVersion) grid.setAttribute("aria-busy", "false"); }
}
async function loadDetail(id) {
  status("Preparando la receta…");
  try {
    const meal = await api(`/api/recetas/${id}/`);
    document.title = `${meal.name} · Mesa Viva`;
    $("#detail-image").src = meal.image || "/static/img/favicon.svg"; $("#detail-image").alt = meal.name;
    $("#detail-title").textContent = meal.name;
    $("#detail-meta").textContent = `${meal.category} / ${meal.area}`;
    const list = $("#detail-ingredients"); list.replaceChildren();
    meal.ingredients.forEach((item, index) => {
      const li = node("li"); const label = node("label"); const check = node("input");
      check.type = "checkbox"; check.id = `ingredient-${index}`;
      label.append(check, node("span", "", `${item.measure} ${item.name}`)); li.append(label); list.append(li);
    });
    const instructions = $("#detail-instructions"); instructions.replaceChildren();
    meal.instructions.split(/\r?\n+/).filter((p) => p.trim()).forEach((p) => instructions.append(node("p", "", p)));
    if (meal.video) { $("#detail-video").href = meal.video; $("#detail-video").hidden = false; }
    $("#save-recipe").onclick = async () => {
      if (!authenticated) { window.location.href = "/ingresar/"; return; }
      const button = $("#save-recipe"); button.disabled = true;
      try { await api("/api/favoritos/", { method: "POST", body: JSON.stringify({ meal_id: meal.id }) });
        button.textContent = "✓ Guardada en tus favoritos"; toast("Ya está en tu recetario.");
      } catch (error) { toast(error.message); }
      finally { button.disabled = false; }
    };
    $("#recipe-status").hidden = true; $("#recipe-detail").hidden = false;
  } catch (error) { status(error.message, () => loadDetail(id)); }
}
const page = $("[data-page]");
if (page?.dataset.page === "recipes") {
  const input = $("#recipe-search");
  const initial = (new URLSearchParams(window.location.search).get("q") || "").slice(0, 60);
  input.value = initial;
  const search = (q) => {
    input.value = q;
    const url = new URL(window.location.href);
    if (q) url.searchParams.set("q", q); else url.searchParams.delete("q");
    history.replaceState(null, "", url); loadRecipes(q);
  };
  $("#search-form").addEventListener("submit", (event) => { event.preventDefault(); search(input.value.trim()); });
  document.querySelectorAll("[data-query]").forEach((button) => button.addEventListener("click", () => search(button.dataset.query)));
  loadRecipes(initial);
}
if (page?.dataset.page === "favorites") loadFavorites();
if (page?.dataset.page === "detail") loadDetail(page.dataset.mealId);
const register = $("#register-form");
if (register) {
  const password = $("#id_password1"), confirmation = $("#id_password2");
  const name = $("#id_first_name"), email = $("#id_email");
  password.setAttribute("aria-describedby", "password-hint");
  email.setAttribute("aria-describedby", "email-hint");
  function validateFields() {
    const value = password.value;
    let error = "";
    if (value && (value.length < 12 || value.length > 128)) error = "Usa de 12 a 128 caracteres.";
    else if (value && (!/\p{Lu}/u.test(value) || !/\p{Ll}/u.test(value) || !/[0-9]/.test(value))) error = "Incluye mayúscula, minúscula y número.";
    else if (/\p{C}/u.test(value)) error = "No uses caracteres invisibles ni de control.";
    else if (/(.)\1{3,}/i.test(value) || /12345|54321|abcde|edcba|qwerty|asdfgh/i.test(value)) error = "Evita secuencias predecibles o cuatro caracteres iguales seguidos.";
    password.setCustomValidity(error);
    confirmation.setCustomValidity(confirmation.value && confirmation.value !== value ? "Las contraseñas no coinciden." : "");
    const person = name.value.trim().normalize("NFC").replaceAll("’", "'");
    name.setCustomValidity(person && (!/^\p{L}+(?:[ '\-]\p{L}+)*$/u.test(person) || person.replace(/[^\p{L}]/gu, "").length < 2) ? "Escribe tu nombre con letras y separadores simples, sin números ni símbolos." : "");
    email.setCustomValidity(email.value && /[\s\p{C}]/u.test(email.value.trim()) ? "El correo no puede contener espacios ni caracteres invisibles." : "");
  }
  [password, confirmation, name, email].forEach((field) => field.addEventListener("input", validateFields));
  register.addEventListener("submit", (event) => {
    validateFields();
    if (!register.checkValidity()) { event.preventDefault(); register.reportValidity(); }
    else { const button = register.querySelector('button[type="submit"]'); button.disabled = true; button.textContent = "Verificando tus datos…"; }
  });
}
