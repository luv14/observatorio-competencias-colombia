/**
 * Dashboard estático para orientar formación a partir de menciones del mercado.
 * Datos: data.json.gz, generado por procesar_ofertas.py.
 * Contrato de fila: 0 identidad, 1 departamento, 2 municipio, 4 educación,
 * 8 puestos, 10 vencimiento, 13 índices de habilidades en meta.skills.
 * No alterar índices sin actualizar también el procesador.
 * Los porcentajes de competencias no son excluyentes y pueden sumar más de 100 %.
 */
let SKILL_CATEGORIES = [];
const expandedSkills = new Set(),
  categoryItems = new Map();
// Dibuja el top 10 o el listado completo de una categoría y actualiza su botón.
function renderSkillCategory(id) {
  const items = categoryItems.get(id) || [],
    expanded = expandedSkills.has(id) && items.length > 10;
  bars("skills-" + id, items, expanded ? items.length : 10);
  const button = $("toggle-" + id);
  button.hidden = items.length <= 10;
  button.textContent = expanded
    ? "Ver menos"
    : "Ver todas (" + fmt(items.length) + ")";
  button.setAttribute("aria-expanded", String(expanded));
}
// Alterna la expansión de una tarjeta sin modificar el filtro territorial.
function toggleSkillCategory(id) {
  if (expandedSkills.has(id)) expandedSkills.delete(id);
  else expandedSkills.add(id);
  renderSkillCategory(id);
}
const $ = (id) => document.getElementById(id),
  fmt = (n) => n.toLocaleString("es-CO"),
  esc = (s) =>
    String(s).replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
let activeZone = null;
let data,
  filtered = [],
  unique = [];
// Descarga y descomprime el JSON; requiere soporte de DecompressionStream.
async function load(path) {
  const r = await fetch(path);
  if (!r.ok) throw Error("No se pudo cargar " + path);
  return JSON.parse(
    await new Response(
      r.body.pipeThrough(new DecompressionStream("gzip")),
    ).text(),
  );
}
// Utilidad para llenar un selector con etiquetas ordenadas en español.
function options(id, values, label) {
  $(id).replaceChildren(
    new Option(label, ""),
    ...values
      .sort((a, b) => a.localeCompare(b, "es"))
      .map((v) => new Option(v, v)),
  );
}
// Construye municipios de la zona elegida; la clave incluye departamento para evitar homónimos.
function cities() {
  const pairs = new Map();
  for (const r of data.rows) {
    if (activeZone?.deps.includes(r[1]))
      pairs.set(r[1] + "|" + r[2], r[2] + " · " + r[1]);
  }
  const choices = [...pairs].sort((a, b) => a[1].localeCompare(b[1], "es"));
  $("city").replaceChildren(
    new Option("Todas las ciudades de la zona", ""),
    ...choices.map(([key, label]) => new Option(label, key)),
  );
}
// Cuenta identidades únicas por grupo; una publicación puede pertenecer a varios municipios.
function counts(rows, fn) {
  const m = new Map();
  for (const r of rows) {
    const k = fn(r);
    if (!m.has(k)) m.set(k, new Set());
    m.get(k).add(r[0]);
  }
  return [...m].map(([k, v]) => [k, v.size]).sort((a, b) => b[1] - a[1]);
}
// Formato institucional del indicador: dos decimales y configuración colombiana.
const pct = (n) =>
  (n * 100).toLocaleString("es-CO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }) + " %";
// Dibuja porcentajes usando unique.length como denominador; escapa etiquetas antes de insertar HTML.
function bars(id, items, limit = 8) {
  const top = items.slice(0, limit),
    total = unique.length;
  $(id).innerHTML = top.length
    ? top
        .map(
          ([k, v]) =>
            `<div class="barrow"><span title="${esc(k)}">${esc(k)}</span><div class="track"><div class="fill" style="width:${total ? (v / total) * 100 : 0}%"></div></div><span class="percent" data-count="${v}" data-share="${total ? v / total : 0}">${pct(total ? v / total : 0)}<small class="bar-count">${fmt(v)} ofertas</small></span></div>`,
        )
        .join("")
    : '<p class="note">No se encontraron menciones para esta selección.</p>';
}
// Normaliza variantes ortográficas de educación sin inferir niveles ausentes.
function educationLabel(raw) {
  return (
    {
      Tecnólogico: "Tecnológico",
      Especilización: "Especialización",
      "No Aplica": "No aplica",
    }[raw] ||
    raw ||
    "Sin información"
  );
}
// Asigna un grupo por publicación; conserva como grupo propio los niveles contradictorios.
function educationDistribution() {
  const m = new Map();
  for (const o of unique) {
    const levels = [...o.education].map(educationLabel);
    const distinct = [...new Set(levels)];
    const k = distinct.length > 1 ? "Varios niveles informados" : distinct[0];
    m.set(k, (m.get(k) || 0) + 1);
  }
  return [...m].sort((a, b) => b[1] - a[1]);
}
// Presenta todos los niveles educativos en barras.
function educationBars() {
  const items = educationDistribution();
  bars("educ", items, items.length);
}
// Recalcula la selección: zona → ciudad → vencimiento → unión de habilidades por identidad.
// Reinicia tarjetas al cambiar filtros. Solo incluye vencimientos presentes y >= fecha de corte.
function update() {
  expandedSkills.clear();
  if (!activeZone) {
    syncMap();
    return;
  }
  const city = $("city").value;
  filtered = data.rows.filter(
    (r) =>
      activeZone.deps.includes(r[1]) &&
      (!city || r[1] + "|" + r[2] === city) &&
      r[10] &&
      r[10] >= data.meta.cutoff,
  );
  const m = new Map();
  for (const r of filtered) {
    if (!m.has(r[0]))
      m.set(r[0], {
        r,
        qty: r[8],
        skills: new Set(r[13]),
        education: new Set([r[4]]),
      });
    else {
      const o = m.get(r[0]);
      o.qty = Math.max(o.qty, r[8]);
      r[13].forEach((s) => o.skills.add(s));
      o.education.add(r[4]);
    }
  }
  unique = [...m.values()];
  bars(
    "territory",
    counts(filtered, (r) => r[2] + " · " + r[1]),
  );
  educationBars();
  const sc = data.meta.skills
    .map((s, i) => [s, unique.filter((o) => o.skills.has(i)).length])
    .filter((x) => x[1])
    .sort((a, b) => b[1] - a[1]);
  for (const category of SKILL_CATEGORIES) {
    const items = sc.filter(([term]) => category.terms.includes(term));
    categoryItems.set(category.id, items);
    renderSkillCategory(category.id);
  }
  syncMap();
}
$("city").onchange = update;
$("reset").onclick = () => {
  $("city").value = "";
  update();
};
// Inicio: cargar metadatos, conectar categorías y preparar mapa; errores se muestran al usuario.
load("data.json.gz")
  .then((d) => {
    data = d;
    SKILL_CATEGORIES = d.meta.skill_categories;
    for (const c of SKILL_CATEGORIES)
      $("toggle-" + c.id).onclick = () => toggleSkillCategory(c.id);
    $("dictionary-coverage").textContent =
      `Cobertura actual: ${d.meta.skills.length} conceptos, con sinónimos y variantes agrupados. Se buscan menciones explícitas y se aplican reglas de contexto para reducir coincidencias ambiguas. Pueden faltar competencias implícitas y no se distingue de forma completa lo obligatorio de lo deseable.`;
    $("snapshot").textContent = "Corte del archivo: " + d.meta.cutoff;
    cities();
    initMap();
    $("quality").textContent =
      `${fmt(d.meta.raw)} filas originales; ${fmt(d.meta.duplicates)} duplicados exactos eliminados; ${fmt(d.meta.clean)} registros conservados; ${fmt(d.meta.offers)} ofertas identificadas; ${fmt(d.meta.blank_clean)} registros conservados sin código; ${fmt(d.meta.multi_location)} ofertas presentes en varias ubicaciones. ${d.meta.method} ${d.meta.skill_method || ""}`;
    $("status").hidden = true;
    update();
  })
  .catch((e) => {
    $("status").textContent = e.message;
  });

// Limpia el municipio al cambiar de zona para no conservar una selección incompatible.
function clearZoneFilters() {
  $("city").value = "";
}
// Selecciona una zona del catálogo y vuelve a generar filtros y resultados.
function selectZone(id) {
  activeZone = UNAD_ZONES.find((z) => z.id === id) || null;
  clearZoneFilters();
  cities();
  update();
}
// Sincroniza el estado visual y la visibilidad de los resultados con la zona seleccionada.
function syncMap() {
  const selected = !!activeZone;
  $("zone-details").hidden = !selected;
  $("zone-summary").hidden = !selected;
  $("map-selection").textContent = selected
    ? activeZone.name
    : "Elige una zona de Colombia";
  $("zone-intro").textContent = selected
    ? "Consulta las habilidades y competencias de esta zona y filtra por sus ciudades. Puedes cambiar de zona desde el mapa o la lista."
    : "Selecciona una zona en el mapa o en la lista. Se desplegarán sus habilidades, competencias e indicadores y podrás filtrar por las ciudades de ese territorio.";
  if (selected) {
    $("map-selected-count").textContent = fmt(unique.length);
    $("zone-heading").textContent =
      activeZone.name + " · Habilidades y competencias";
    $("zone-coverage").textContent =
      "Departamentos agrupados: " + activeZone.deps.join(", ");
  }
  document.querySelectorAll(".unad-zone").forEach((g) => {
    const on = g.dataset.zone === activeZone?.id;
    g.classList.toggle("selected", on);
    g.classList.toggle("dimmed", selected && !on);
    g.setAttribute("aria-pressed", String(on));
  });
  document.querySelectorAll("[data-zone-button]").forEach((b) => {
    const on = b.dataset.zoneButton === activeZone?.id;
    b.classList.toggle("selected", on);
    b.setAttribute("aria-pressed", String(on));
  });
}
// Conecta mapa, botones y teclado; mantiene accesibilidad con Enter y Espacio.
function initMap() {
  document.querySelectorAll(".unad-zone").forEach((g) => {
    const z = UNAD_ZONES.find((x) => x.id === g.dataset.zone);
    g.onclick = () => selectZone(z.id);
    g.onkeydown = (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        selectZone(z.id);
      }
    };
    g.onmouseenter = g.onfocus = () => {
      $("map-tooltip").textContent =
        z.name + " · " + z.deps.length + " territorios agrupados";
    };
  });
  document
    .querySelectorAll("[data-zone-button]")
    .forEach((b) => (b.onclick = () => selectZone(b.dataset.zoneButton)));
  $("map-national").onclick = () => {
    selectZone(null);
    $("map-tooltip").textContent = "Selecciona una zona UNAD para comenzar";
  };
}
