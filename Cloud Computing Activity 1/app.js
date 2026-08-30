const API_URL = "https://cloud-computing-activity.vercel.app";


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
    // Add more games here later, e.g.:
    // if (g.includes("mobile legends")) return "game-frame-ml";
    // if (g.includes("dota")) return "game-frame-dota";

    return "";
}


// GET ALL CHARACTERS
async function loadCharacters() {
    try {
        const response = await fetch(`${API_URL}/characters`);
        const data = await response.json();
        displayCharacters(data.characters);
    }

    catch (error) {
        console.error(error);
        document.getElementById("characterList").innerHTML = "Unable to reach the archive.";
    }
}


// DISPLAY CHARACTERS
function displayCharacters(characters) {
    const characterList =
        document.getElementById("characterList");

    characterList.innerHTML = "";

    if (!characters || characters.length === 0) {
        characterList.innerHTML = "No champions found.";
        return;
    }

    characters.forEach(character => {
        const accent = getRegionColor(character.region);

        const card = document.createElement("div");
        card.className = "character-card";
        card.style.setProperty("--accent", accent);
        card.dataset.id = character.id;

        const gameFrameClass = getGameFrameClass(character.game);
        if (gameFrameClass) card.classList.add(gameFrameClass);

        const gameCorners = gameFrameClass
            ? `
            <div class="game-corner tl"></div>
            <div class="game-corner tr"></div>
            <div class="game-corner bl"></div>
            <div class="game-corner br"></div>`
            : "";

        const cardImg = character.image_url
            ? `<img src="${API_URL}${character.image_url}" alt="${character.name}">`
            : "";

        card.innerHTML = `
            ${gameCorners}
            <div class="card-media">${cardImg}</div>
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
                <span class="card-region">${character.region || "Unknown"}</span>
                <span class="card-dot">&middot;</span>
                <span class="card-faction">${character.faction || "Unaffiliated"}</span>
            </div>
            <h3>${character.name}</h3>
            <p class="character-title">${character.title || ""}</p>
            <p class="character-blurb">${character.personality || ""}</p>
            <p class="character-origin">${character.race || "Unknown"} &middot; ${character.origin || "Unknown origin"}</p>
            <button>View Full Entry</button>
        `;

        characterList.appendChild(card);
    });

}

// GET ONE CHARACTER
async function viewCharacter(id) {

    try {
        const response = await fetch(`${API_URL}/characters/${id}`);
        const character = await response.json();
        openModal(character);
    }
    catch (error) {
        console.error(error);
        alert("Unable to retrieve that champion's entry.");
    }

}


// MODAL
function openModal(character) {
    const accent = getRegionColor(character.region);
    const overlay = document.getElementById("modalOverlay");
    const modal = document.getElementById("modalContent");

    modal.style.setProperty("--accent", accent);

    const modalImg = character.image_url
        ? `<img src="${API_URL}${character.image_url}" alt="${character.name}">`
        : "";

    let sections = "";

    const addSection = (label, value) => {
        if (!value) return;
        sections += `
            <div class="modal-section">
                <h4>${label}</h4>
                <p>${value}</p>
            </div>
        `;
    };

    addSection("Personality", character.personality);
    addSection("Relationships", character.relationships);
    addSection("Allies", character.allies);
    addSection("Enemies", character.enemies);
    addSection("Major Events", character.major_events);
    addSection("Current Status", character.current_status);
    addSection("Lore", character.lore);

    modal.innerHTML = `
        <button class="modal-close" onclick="closeModal()" aria-label="Close">&times;</button>
        <div class="modal-media">${modalImg}</div>
        <p class="modal-eyebrow">${character.region || "Unknown Region"}</p>
        <h3>${character.name}</h3>
        <p class="character-title">${character.title || ""}</p>
        <div class="modal-tags">
            <span class="modal-tag">${character.race || "Unknown race"}</span>
            <span class="modal-tag">${character.faction || "Unaffiliated"}</span>
            <span class="modal-tag">${character.origin || "Unknown origin"}</span>
        </div>
        ${sections}
    `;

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
// converging toward the middle, then fades back out, and opens that
// character's full entry.
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
            await fetch(`${API_URL}/characters/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        displayCharacters(data.results);
    }

    catch (error) {
        console.error(error);
        alert("Search failed.");
    }
}

loadCharacters();