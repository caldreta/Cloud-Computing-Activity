const API_URL = "https://cloud-computing-activity.vercel.app/api/v1";
const API_KEY = "arceo-api-key-123"

const FETCH_OPTIONS = {
    headers: {
        "x-api-key": API_KEY
    }
};

// Champion pictures live in a public Supabase Storage bucket. The API sends the path inside it
// (for example league/zed.jpg), and this is the address that path is added to.
const IMAGE_BASE = "https://rmyhndpralukuvynsnbp.supabase.co/storage/v1/object/public/champion-images/";

const PAGE_SIZE = 12;

let currentCharacters = [];
let currentSortField = "default";
let currentPage = 1;


// Text from the API goes into the page as HTML, so special characters are escaped first.
function esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, (ch) => (
        { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]
    ));
}

function imageHtml(character) {
    if (!character.image) return "";
    return `<img src="${esc(IMAGE_BASE + character.image)}" alt="${esc(character.name)}" loading="lazy" onerror="this.remove()">`;
}


// REGION -> ACCENT COLOR
function getRegionColor(region) {
    if (!region) return "var(--region-default)";
    const r = region.toLowerCase();

    if (r.includes("ionia")) return "var(--region-ionia)";
    if (r.includes("noxus")) return "var(--region-noxus)";
    if (r.includes("freljord")) return "var(--region-freljord)";
    if (r.includes("targon")) return "var(--region-targon)";
    if (r.includes("shurima")) return "var(--region-shurima)";
    if (r.includes("void")) return "var(--region-void)";
    if (r.includes("zaun")) return "var(--region-zaun)";
    if (r.includes("bandle") || r.includes("spirit")) return "var(--region-bandle)";

    return "var(--region-default)";
}


// GAME -> BORDER FRAME CLASS
function getGameFrameClass(game) {
    if (!game) return "";
    const g = game.toLowerCase();

    if (g.includes("league of legends")) return "game-frame-lol";
    // Add more games here later
    // if (g.includes("mobile legends")) return "game-frame-ml";
    // if (g.includes("dota")) return "game-frame-dota";

    return "";
}


// SORT
function sortCharacters(list, field) {
    if (field === "default") return list;

    return [...list].sort((a, b) => {
        const av = (a[field] || "").toLowerCase();
        const bv = (b[field] || "").toLowerCase();
        return av.localeCompare(bv);
    });
}

// Shows the current page of the (sorted) list. A new search, sort or load goes back to page 1.
function renderList(keepPage = false) {
    const sorted = sortCharacters(currentCharacters, currentSortField);
    const pages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
    if (!keepPage) currentPage = 1;
    currentPage = Math.min(Math.max(1, currentPage), pages);

    const start = (currentPage - 1) * PAGE_SIZE;
    displayCharacters(sorted.slice(start, start + PAGE_SIZE));
    renderPagination(sorted.length, pages, start);
}

function handleSortChange() {
    currentSortField = document.getElementById("sortSelect").value;
    renderList();
}


// PAGINATION
// Page numbers to show: the first, the last, and the pages around the current one, with gaps as "…"
function pageWindow(current, pages) {
    const wanted = new Set([1, pages, current - 1, current, current + 1]);
    const numbers = [...wanted].filter((n) => n >= 1 && n <= pages).sort((a, b) => a - b);
    const out = [];
    numbers.forEach((n, i) => {
        if (i > 0 && n - numbers[i - 1] > 1) out.push("gap");
        out.push(n);
    });
    return out;
}

function renderPagination(total, pages, start) {
    const nav = document.getElementById("pagination");
    if (total <= PAGE_SIZE) {
        nav.hidden = true;
        nav.innerHTML = "";
        return;
    }
    const first = start + 1;
    const last = Math.min(start + PAGE_SIZE, total);

    const numbers = pageWindow(currentPage, pages).map((item) => (
        item === "gap"
            ? `<span class="page-gap" aria-hidden="true">&hellip;</span>`
            : `<button type="button" class="page-btn page-num" data-page="${item}"
                   ${item === currentPage ? 'aria-current="page"' : ""} aria-label="Page ${item}">${item}</button>`
    )).join("");

    nav.hidden = false;
    nav.innerHTML = `
        <p class="page-summary" role="status">Showing ${first}&ndash;${last} of ${total} champions</p>
        <div class="page-buttons">
            <button type="button" class="page-btn" data-page="${currentPage - 1}" ${currentPage === 1 ? "disabled" : ""}
                aria-label="Previous page">&lsaquo; Prev</button>
            ${numbers}
            <span class="page-of">Page ${currentPage} of ${pages}</span>
            <button type="button" class="page-btn" data-page="${currentPage + 1}" ${currentPage === pages ? "disabled" : ""}
                aria-label="Next page">Next &rsaquo;</button>
        </div>`;
}

function goToPage(page) {
    currentPage = page;
    renderList(true);
    const top = document.getElementById("roster");
    const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    top.scrollIntoView({ behavior: calm ? "auto" : "smooth", block: "start" });
}

document.getElementById("pagination").addEventListener("click", (event) => {
    const button = event.target.closest(".page-btn");
    if (!button || button.disabled) return;
    goToPage(Number(button.dataset.page));
});


// GET ALL CHARACTERS
async function loadCharacters() {
    try {
        const response = await fetch(`${API_URL}/characters`, FETCH_OPTIONS);
        const data = await response.json();
        currentCharacters = data.characters;
        renderList();
    }

    catch (error) {
        console.error(error);
        document.getElementById("characterList").innerHTML = "Unable to reach the archive.";
        document.getElementById("pagination").hidden = true;
    }
}


// DISPLAY CHARACTERS (one page of them)
function displayCharacters(characters) {
    const characterList =
        document.getElementById("characterList");

    characterList.innerHTML = "";

    if (!characters || characters.length === 0) {
        characterList.innerHTML = "No champions found.";
        return;
    }

    characters.forEach((character, index) => {
        const accent = getRegionColor(character.region);

        const card = document.createElement("div");
        card.className = "character-card";
        card.style.setProperty("--accent", accent);
        card.style.setProperty("--i", index);
        card.dataset.id = character.id;

        const gameFrameClass = getGameFrameClass(character.game);
        if (gameFrameClass) card.classList.add(gameFrameClass);

        card.innerHTML = `
            <div class="card-media">${imageHtml(character)}</div>
            <div class="ignite-corner tl"></div>
            <div class="ignite-corner tr"></div>
            <div class="ignite-corner bl"></div>
            <div class="ignite-corner br"></div>
            <div class="ignite-edge t-l"></div>
            <div class="ignite-edge t-r"></div>
            <div class="ignite-edge b-l"></div>
            <div class="ignite-edge b-r"></div>
            <div class="ignite-edge l-t"></div>
            <div class="ignite-edge l-b"></div>
            <div class="ignite-edge r-t"></div>
            <div class="ignite-edge r-b"></div>
            <div class="card-eyebrow">
                <span class="card-region">${esc(character.region || "Unknown")}</span>
                <span class="card-dot">&middot;</span>
                <span class="card-faction">${esc(character.faction || "Unaffiliated")}</span>
            </div>
            <h3>${esc(character.name)}</h3>
            <p class="character-title">${esc(character.title || "")}</p>
            <p class="character-blurb">${esc(character.personality || "")}</p>
            <p class="character-origin">${esc(character.race || "Unknown")} &middot; ${esc(character.origin || "Unknown origin")}</p>
            <button>View Full Entry</button>
        `;

        characterList.appendChild(card);
    });

}

// GET ONE CHARACTER
async function viewCharacter(id) {

    try {
        const response = await fetch(`${API_URL}/characters/${id}`, FETCH_OPTIONS);
        const character = await response.json();
        openModal(character);
    }
    catch (error) {
        console.error(error);
        alert("Unable to retrieve that champion's entry.");
    }

}


// MODAL FIELDS
// Each field of a champion's entry gets its own icon, colour and frame.
// "half" fields sit side by side, and "quote" gives the lore a decorated, storybook look.
const ICONS = {
    star: '<path d="M12 3l2.6 5.6 6.1.7-4.5 4.2 1.2 6L12 16.5l-5.4 3 1.2-6L3.3 9.3l6.1-.7z"/>',
    link: '<circle cx="8" cy="12" r="4"/><circle cx="16" cy="12" r="4"/>',
    shield: '<path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z"/>',
    swords: '<path d="M5 19L19 5M14 5h5v5M5 5l14 14M5 10V5h5"/>',
    hourglass: '<path d="M7 3h10M7 21h10M8 3v3l4 6-4 6v3M16 3v3l-4 6 4 6v3"/>',
    pulse: '<path d="M3 12h4l2-6 4 12 2-6h6"/>',
    book: '<path d="M5 4h10a3 3 0 013 3v13H8a3 3 0 01-3-3zM5 17a3 3 0 013-3h10"/>'
};

const FIELDS = [
    { key: "personality", label: "Personality", icon: "star", tone: "var(--accent)" },
    { key: "relationships", label: "Relationships", icon: "link", tone: "#d98cb0" },
    { key: "allies", label: "Allies", icon: "shield", tone: "#4cbb8a", half: true },
    { key: "enemies", label: "Enemies", icon: "swords", tone: "#d2584d", half: true },
    { key: "major_events", label: "Major Events", icon: "hourglass", tone: "var(--gold-bright)" },
    { key: "current_status", label: "Current Status", icon: "pulse", tone: "var(--cyan)" },
    { key: "lore", label: "Lore", icon: "book", tone: "var(--accent)", quote: true }
];

function fieldHtml(field, value, order) {
    const classes = ["field"];
    if (field.half) classes.push("field-half");
    if (field.quote) classes.push("field-lore");
    return `
        <section class="${classes.join(" ")}" style="--tone: ${field.tone}; --f: ${order}">
            <div class="field-head">
                <span class="field-icon" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false">${ICONS[field.icon]}</svg></span>
                <h4>${field.label}</h4>
            </div>
            <p>${esc(value)}</p>
        </section>
    `;
}


// MODAL
function openModal(character) {
    const accent = getRegionColor(character.region);
    const overlay = document.getElementById("modalOverlay");
    const modal = document.getElementById("modalContent");

    modal.style.setProperty("--accent", accent);

    const shown = FIELDS.filter((field) => character[field.key]);
    const sections = shown.map((field, order) => fieldHtml(field, character[field.key], order)).join("");

    modal.innerHTML = `
        <button class="modal-close" onclick="closeModal()" aria-label="Close">&times;</button>
        <div class="modal-media">${imageHtml(character)}</div>
        <p class="modal-eyebrow">${esc(character.region || "Unknown Region")}</p>
        <h3>${esc(character.name)}</h3>
        <p class="character-title">${esc(character.title || "")}</p>
        <div class="modal-tags">
            <span class="modal-tag"><b>Race</b>${esc(character.race || "Unknown race")}</span>
            <span class="modal-tag"><b>Faction</b>${esc(character.faction || "Unaffiliated")}</span>
            <span class="modal-tag"><b>Origin</b>${esc(character.origin || "Unknown origin")}</span>
        </div>
        <div class="fields">${sections}</div>
    `;

    modal.scrollTop = 0;
    overlay.classList.add("open");
}

function closeModal() {
    document.getElementById("modalOverlay").classList.remove("open");
}

function closeModalOnBackdrop(event) {
    if (event.target.id === "modalOverlay") {
        closeModal();
    }
}

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeModal();
    }
});


// IGNITE CLICK EFFECT + OPEN FULL ENTRY
// Any click on a character card lights up its four edges (region-colored)
document.getElementById("characterList").addEventListener("click", (event) => {
    const card = event.target.closest(".character-card");
    if (!card) return;

    card.classList.add("igniting");
    setTimeout(() => card.classList.remove("igniting"), 900);

    viewCharacter(card.dataset.id);
});


// SEARCH
async function searchCharacters() {

    const query = document.getElementById("searchInput").value;
    if (!query) {
        loadCharacters();
        return;
    }

    try {
        const response =
            await fetch(
                `${API_URL}/characters/search?q=${encodeURIComponent(query)}`,
                FETCH_OPTIONS
            );

        const data = await response.json();
        currentCharacters = data.results;
        renderList();
    }

    catch (error) {
        console.error(error);
        alert("Search failed.");
    }
}

loadCharacters();
