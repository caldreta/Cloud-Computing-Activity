const API_URL = "https://cloud-computing-activity.vercel.app";
 
 
// GET ALL CHARACTERS
async function loadCharacters() {
    try {
        const response = await fetch(`${API_URL}/characters`);
        const data = await response.json();
        displayCharacters(data.characters);
    }
 
    catch (error) {
        console.error(error);
        document.getElementById("characterList").innerHTML = "Unable to connect to the API.";
    }
}
 
 
// DISPLAY CHARACTERS
function displayCharacters(characters) {
    const characterList =
        document.getElementById("characterList");
 
    characterList.innerHTML = "";
 
    characters.forEach(character => {
        const card = document.createElement("div");
        card.className = "character-card";
        card.innerHTML = `
            <div class="character-year">${character.year}</div>
            <h3>${character.name}</h3>
            <p class="character-anime">${character.anime}</p>
            <p>${character.moral_alignment}</p>
            <p>${character.description}</p>
            <button onclick="viewCharacter(${character.id})"> View Details</button>
        `;
 
        characterList.appendChild(card);
    });
 
}
 
// GET ONE CHARACTER
async function viewCharacter(id) {
 
    try {
        const response = await fetch(`${API_URL}/characters/${id}`);
        const character = await response.json();
 
        alert(`
            ${character.year} ${character.name} (${character.anime})
            Moral Alignment:
            ${character.moral_alignment}
 
            Description:
            ${character.description}
        `);
    }
    catch (error) {
        console.error(error);
        alert("Unable to retrieve character.");
    }
 
}
 
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