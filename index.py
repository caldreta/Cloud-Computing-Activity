from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Simple Anime Character API",
    description="A beginner-friendly REST API containing information about anime characters.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

characters = [
    {
        "id": 1,
        "game": "League of Legends",
        "name": "Aatrox",
        "title": "The Darkin Blade",
        "region": "Shurima",
        "race": "Darkin / Ascended",
        "faction": "Darkin",
        "origin": "Ancient Shurima",
        "personality": "Proud, wrathful, violent, nihilistic, and resentful.",
        "relationships": "Formerly allied with the Ascended and other Darkin.",
        "enemies": "Zoe, Xolaani, Kayle, and the mortal world.",
        "allies": "Other Darkin and formerly the Ascended Host.",
        "major_events": "Ascension in Shurima, war against the Void, the Great Darkin War, imprisonment within the Darkin Blade, and possession of mortal hosts.",
        "current_status": "Active and seeking an apocalyptic end to his existence.",
        "image": "aatrox.jpg"
    },
    {
        "id": 2,
        "game": "League of Legends",
        "name": "Zed",
        "title": "The Master of Shadows",
        "region": "Ionia",
        "race": "Human",
        "faction": "Order of Shadow",
        "origin": "Ionia",
        "personality": "Ruthless, pragmatic, ambitious, disciplined, and fiercely protective of Ionia.",
        "relationships": "Former student of Kusho and brother-like rival of Shen.",
        "enemies": "Shen, the Kinkou Order, Noxus, and Jhin.",
        "allies": "The Order of Shadow.",
        "major_events": "Training under Kusho, discovering shadow magic, leaving the Kinkou, creating the Order of Shadow, and resisting Noxus.",
        "current_status": "Leader of the Order of Shadow and an influential defender of Ionia.",
        "image": "zed.jpg"
    },
    {
        "id": 3,
        "game": "League of Legends",
        "name": "Akali",
        "title": "The Rogue Assassin",
        "region": "Ionia",
        "race": "Human",
        "faction": "Independent / Former Kinkou",
        "origin": "Navori, Ionia",
        "personality": "Independent, determined, impulsive, rebellious, and protective.",
        "relationships": "Former student of Shen and Kennen and former member of the Kinkou Order.",
        "enemies": "Noxian invaders, the Order of Shadow, and threats to Ionia.",
        "allies": "Shen, Kennen, and former Kinkou members.",
        "major_events": "Kinkou training, the Noxian invasion, Zed's coup, and her departure from the Kinkou Order.",
        "current_status": "An independent assassin defending Ionia.",
        "image": "akali.jpg"
    },
    {
        "id": 4,
        "game": "League of Legends",
        "name": "Syndra",
        "title": "The Dark Sovereign",
        "region": "Ionia",
        "race": "Human",
        "faction": "Independent",
        "origin": "Ionia",
        "personality": "Proud, fiercely independent, rebellious, distrustful, and obsessed with freedom.",
        "relationships": "Formerly connected to Ionian elders and a mentor who attempted to suppress her power.",
        "enemies": "Those who attempt to control or suppress her.",
        "allies": "Primarily herself.",
        "major_events": "Manifestation of her magic, suppression by her mentor, imprisonment, escape, and emergence as the Dark Sovereign.",
        "current_status": "Free and wielding immense magical power.",
        "image": "syndra.jpg"
    },
    {
        "id": 5,
        "game": "League of Legends",
        "name": "Mordekaiser",
        "title": "The Iron Revenant",
        "region": "Noxus",
        "race": "Revenant / Undead",
        "faction": "Mordekaiser's Forces",
        "origin": "Ancient Noxian lands",
        "personality": "Tyrannical, calculating, proud, cruel, patient, and obsessed with domination.",
        "relationships": "Historically connected to his mortal armies and necromancers.",
        "enemies": "Noxus, living civilizations, and those who oppose his resurrection.",
        "allies": "Undead followers and those enslaved by his necromantic power.",
        "major_events": "Life as Sahn-Uzal, death, discovery of the afterlife, return to Runeterra, creation of an undead empire, defeat, and banishment.",
        "current_status": "Preparing to return and establish dominion over the living and dead.",
        "image": "mordekaiser.jpg"
    },
    {
        "id": 6,
        "game": "League of Legends",
        "name": "Zoe",
        "title": "The Aspect of Twilight",
        "region": "Targon",
        "race": "Human Host / Celestial Aspect",
        "faction": "Aspects of Targon",
        "origin": "Mount Targon",
        "personality": "Playful, mischievous, curious, carefree, unpredictable, and dangerously powerful.",
        "relationships": "Connected to the celestial Aspects and opposed by Aatrox.",
        "enemies": "Aatrox and beings opposed to the Aspects.",
        "allies": "The celestial powers of Targon.",
        "major_events": "Becoming the Aspect of Twilight and serving as a messenger for cosmic events.",
        "current_status": "Active as the Aspect of Twilight.",
        "image": "zoe.jpg"
    },
    {
        "id": 7,
        "game": "League of Legends",
        "name": "Pantheon",
        "title": "The Unbreakable Spear",
        "region": "Targon",
        "race": "Human",
        "faction": "Rakkor",
        "origin": "Mount Targon",
        "personality": "Stubborn, courageous, defiant, determined, compassionate, and protective.",
        "relationships": "Former host of the Aspect of War and enemy of Aatrox.",
        "enemies": "Aatrox, hostile celestial beings, and threats to mortals.",
        "allies": "Rakkor warriors and mortal defenders.",
        "major_events": "Training as a Rakkor warrior, becoming host to the Aspect of War, surviving Aatrox's attack, and rejecting celestial authority.",
        "current_status": "Active as Atreus, fighting for mortals through his own strength.",
        "image": "pantheon.jpg"
    },
    {
        "id": 8,
        "game": "League of Legends",
        "name": "Kha'Zix",
        "title": "The Voidreaver",
        "region": "The Void",
        "race": "Voidborn",
        "faction": "The Void",
        "origin": "The Void",
        "personality": "Predatory, intelligent, patient, adaptive, and obsessed with hunting.",
        "relationships": "Has a major rivalry with Rengar.",
        "enemies": "Rengar and powerful creatures that threaten it.",
        "allies": "Other Void creatures, although Kha'Zix primarily acts independently.",
        "major_events": "Emergence from the Void, hunting across Runeterra, evolution through consumption, and rivalry with Rengar.",
        "current_status": "Active Voidborn predator continually evolving through hunting.",
        "image": "khazix.jpg"
    },
    {
        "id": 9,
        "game": "League of Legends",
        "name": "Malzahar",
        "title": "The Prophet of the Void",
        "region": "Shurima",
        "race": "Human / Void-Touched",
        "faction": "The Void",
        "origin": "Icathia / Shurima",
        "personality": "Fanatical, prophetic, detached, manipulative, and convinced of the Void's destiny.",
        "relationships": "Closely connected to the Void and its creatures.",
        "enemies": "Kai'Sa, Shuriman defenders, and forces opposing the Void.",
        "allies": "Voidborn creatures.",
        "major_events": "Development of prophetic visions, exposure to the Void, transformation into its prophet, and spreading Void influence.",
        "current_status": "Active servant and prophet of the Void.",
        "image": "malzahar.jpg"
    },
    {
        "id": 10,
        "game": "League of Legends",
        "name": "Viego",
        "title": "The Ruined King",
        "region": "Camavor / Shadow Isles",
        "race": "Human / Wraith",
        "faction": "Camavor / Ruined Forces",
        "origin": "Camavor",
        "personality": "Obsessive, possessive, arrogant, emotionally unstable, and consumed by grief.",
        "relationships": "Husband of Isolde and connected to Kalista, Hecarim, Gwen, Senna, and Lucian.",
        "enemies": "Lucian, Senna, Gwen, and the Sentinels of Light.",
        "allies": "Hecarim, Thresh, the Black Mist, and corrupted followers.",
        "major_events": "Marriage to Isolde, Isolde's death, attempted resurrection, the Ruination, and the spread of the Black Mist.",
        "current_status": "The Ruined King and a major supernatural threat to Runeterra.",
        "image": "viego.jpg"
    },
    {
        "id": 11,
        "game": "League of Legends",
        "name": "Jhin",
        "title": "The Virtuoso",
        "region": "Ionia",
        "race": "Human",
        "faction": "Independent",
        "origin": "Ionia",
        "personality": "Obsessive, theatrical, meticulous, narcissistic, artistic, and disturbed.",
        "relationships": "Connected to Zed, Shen, Akali, and the Kinkou through his history as the Golden Demon.",
        "enemies": "Zed, Shen, and the Kinkou Order.",
        "allies": "Occasional employers and individuals who assist his artistic ambitions.",
        "major_events": "Murders in Ionia, imprisonment by the Kinkou, release through Noxian manipulation, and return to his killings.",
        "current_status": "Active and pursuing his vision of murder as art.",
        "lore": "Jhin is a meticulous and theatrical murderer who believes killing is a form of art. Once known as the Golden Demon, he terrorized Ionia before being captured and imprisoned by the Kinkou. He was eventually released through the schemes of Noxian forces and returned to his deadly performances, treating every murder as part of a carefully constructed masterpiece.",
        "image": "jihn.jpg"
    },
    {
        "id": 12,
        "game": "League of Legends",
        "name": "Ziggs",
        "title": "The Hexplosives Expert",
        "region": "Piltover / Zaun",
        "race": "Yordle",
        "faction": "Independent",
        "origin": "Bandle City",
        "personality": "Energetic, chaotic, curious, reckless, enthusiastic, and obsessed with explosions.",
        "relationships": "Close friend of Jinx and associated with Piltover's scientific community.",
        "enemies": "Piltover authorities and anyone restricting his experiments.",
        "allies": "Jinx and various Zaunites.",
        "major_events": "Leaving Bandle City, traveling to Piltover, developing explosives, moving toward Zaun, and meeting Jinx.",
        "current_status": "Active in Zaun and continuing his explosive experiments.",
        "lore": "Ziggs is a brilliant and eccentric yordle fascinated by explosives and scientific experimentation. Originally from Bandle City, he traveled to Piltover and became fascinated with its technology. Eventually finding a kindred spirit in Jinx, he settled in Zaun, where he could freely pursue increasingly dangerous experiments without worrying about conventional rules or safety.",
        "image": "ziggs.jpg"
    },
    {
        "id": 13,
        "game": "League of Legends",
        "name": "Ahri",
        "title": "The Nine-Tailed Fox",
        "region": "Ionia",
        "race": "Vastaya",
        "faction": "Independent",
        "origin": "Ionia",
        "personality": "Curious, intelligent, charming, predatory, empathetic, and introspective.",
        "relationships": "Connected to the vastaya and associated with Yasuo through her travels.",
        "enemies": "Threats to herself and the vastaya.",
        "allies": "Yasuo and various Ionian companions.",
        "major_events": "Discovering her ability to consume life essence, encountering humans, learning about her heritage, and searching for her origins.",
        "current_status": "Traveling Runeterra while searching for knowledge about her origins.",
        "lore": "Ahri is a vastaya who possesses a natural connection to the magic of Runeterra. She can manipulate the emotions of others and absorb their life essence, but has struggled with the morality of this ability. As she learns more about her vastayan heritage and the world around her, she searches for a deeper understanding of her origins and identity.",
        "image": "ahri.jpg"
    },
    {
        "id": 14,
        "game": "League of Legends",
        "name": "Aurelion Sol",
        "title": "The Star Forger",
        "region": "Celestial Realm / Targon",
        "race": "Celestial Dragon",
        "faction": "Celestial",
        "origin": "The Cosmos",
        "personality": "Arrogant, magnificent, intelligent, prideful, creative, and contemptuous of lesser beings.",
        "relationships": "Controlled by the Targonian Aspects through a celestial crown.",
        "enemies": "Targonian Aspects, celestial threats, and the Void.",
        "allies": "No meaningful permanent alliances.",
        "major_events": "Creation of stars, encounter with Targon, enslavement through the celestial crown, and participation in cosmic conflicts.",
        "current_status": "Active and increasingly close to breaking free from Targon's control.",
        "lore": "Aurelion Sol is an ancient celestial dragon who forged stars and explored the cosmos long before most civilizations existed. After encountering the people of Targon, he was tricked into wearing a celestial crown that allowed the Aspects to control him. Forced to serve Targon's interests, he now seeks to reclaim his freedom and return to his cosmic existence.",
        "image": "aurelionsol.jpg"
    },
    {
        "id": 15,
        "game": "League of Legends",
        "name": "Ornn",
        "title": "The Fire below the Mountain",
        "region": "Freljord",
        "race": "Demigod / Spirit",
        "faction": "Independent",
        "origin": "Freljord",
        "personality": "Grumpy, solitary, stubborn, practical, and perfectionist.",
        "relationships": "Brother of Volibear and connected to Anivia and other Freljordian demigods.",
        "enemies": "Volibear and those who threaten his isolation.",
        "allies": "Anivia and historically his mortal followers.",
        "major_events": "Shaping the Freljord, forging weapons for mortals, conflict with Volibear, destruction of his followers, and retreat into isolation.",
        "current_status": "Lives beneath his mountain and continues his craft.",
        "lore": "Ornn is an ancient Freljordian demigod who embodies fire, craftsmanship, and the forge. He once worked alongside mortal followers who revered his skill, but a devastating conflict with his brother Volibear resulted in the destruction of his followers. Since then, Ornn has largely withdrawn from the world, preferring the solitude of his forge beneath the mountain.",
        "image": "ornn.jpg"
    },
    {
        "id": 16,
        "game": "League of Legends",
        "name": "Volibear",
        "title": "The Relentless Storm",
        "region": "Freljord",
        "race": "Demigod / Spirit",
        "faction": "Ursine",
        "origin": "Freljord",
        "personality": "Savage, proud, violent, passionate, relentless, and opposed to civilization.",
        "relationships": "Brother of Ornn and associated with the Ursine.",
        "enemies": "Ornn, Lissandra, the Three Sisters, and modern Freljordian society.",
        "allies": "The Ursine and followers of the old Freljordian ways.",
        "major_events": "Formation of the ancient Freljord, conflict with Ornn, creation of the Ursine, and opposition to the Three Sisters.",
        "current_status": "Active and attempting to restore the ancient ways of the Freljord.",
        "lore": "Volibear is an ancient demigod of the Freljord who represents the untamed power of nature, storms, and war. He believes the Freljord should return to its primal ways and despises civilization and technological progress. His conflict with his brother Ornn and his followers has shaped much of the region's ancient history.",
        "image": "volibear.jpg"
    },
    {
        "id": 17,
        "game": "League of Legends",
        "name": "Lissandra",
        "title": "The Ice Witch",
        "region": "Freljord",
        "race": "Human / Iceborn",
        "faction": "Frostguard",
        "origin": "Freljord",
        "personality": "Calculating, secretive, manipulative, patient, and ruthless.",
        "relationships": "Sister of Avarosa and Serylda; connected to the Watchers and Frostguard.",
        "enemies": "Avarosa, Ashe, and the Watchers.",
        "allies": "The Frostguard and her devoted followers.",
        "major_events": "Rise of the Three Sisters, encounter with the Watchers, betrayal of her sisters, imprisonment of the Watchers, and creation of the Frostguard.",
        "current_status": "Rules the Frostguard while keeping the Watchers imprisoned.",
        "lore": "Lissandra is one of the ancient Three Sisters of the Freljord and a powerful Iceborn sorceress. She and her sisters encountered the Watchers, terrifying beings from the Void, and eventually sought to use their power. After realizing the danger they posed, Lissandra betrayed her sisters and sacrificed much of her people to imprison the Watchers beneath the Howling Abyss. She now maintains the Frostguard while secretly ensuring the Watchers remain trapped.",
        "image": "lissandra.jpg"
    },
    {
        "id": 18,
        "game": "League of Legends",
        "name": "Cho'Gath",
        "title": "The Terror of the Void",
        "region": "The Void",
        "race": "Voidborn",
        "faction": "The Void",
        "origin": "The Void",
        "personality": "Savage, predatory, destructive, intelligent, and driven by endless hunger.",
        "relationships": "Part of the broader Voidborn species.",
        "enemies": "Mortals of Runeterra and anyone opposing the Void.",
        "allies": "Other Voidborn.",
        "major_events": "Emergence from the Void, invasion of Runeterra, consumption of living matter, and continual growth through feeding.",
        "current_status": "Active Voidborn entity seeking to consume everything it encounters.",
        "lore": "Cho'Gath is a terrifying Voidborn creature driven by an insatiable hunger. Like other creatures of the Void, it seeks to consume and destroy the material world. Its body grows stronger and larger as it feeds, making it increasingly dangerous the longer it remains in Runeterra.",
        "image": "chogath.jpg"
    },
    {
        "id": 19,
        "game": "League of Legends",
        "name": "Urgot",
        "title": "The Dreadnought",
        "region": "Zaun",
        "race": "Human / Augmented Human",
        "faction": "Independent",
        "origin": "Noxus",
        "personality": "Brutal, cynical, survivalist, domineering, and obsessed with strength.",
        "relationships": "Formerly connected to Noxian leadership and now influential among Zaunite criminals.",
        "enemies": "Noxian leadership, Piltover's establishment, and those he considers weak.",
        "allies": "His followers and criminals who embrace his philosophy.",
        "major_events": "Service as a Noxian executioner, betrayal by Noxus, imprisonment in Zaun, mechanical augmentation, escape, and rise as a Zaunite power.",
        "current_status": "Active in Zaun and building a brutal following.",
        "lore": "Urgot was once a powerful Noxian executioner who was betrayed by the very empire he served. Sent to Zaun as part of a failed political maneuver, he was imprisoned and forced to endure brutal conditions. He eventually transformed himself with machinery and emerged as a powerful figure who believes only those strong enough to survive deserve to shape the future.",
        "image": "urgot.jpg"
    },
    {
        "id": 20,
        "game": "League of Legends",
        "name": "Yuumi",
        "title": "The Magical Cat",
        "region": "Bandle City / Spirit Realm",
        "race": "Magical Cat",
        "faction": "Independent",
        "origin": "Bandle City / Spirit Realm",
        "personality": "Curious, affectionate, playful, mischievous, easily distracted, and loyal.",
        "relationships": "Companion of Norra and bonded to the Book of Thresholds.",
        "enemies": "Threats to Norra and the Book of Thresholds.",
        "allies": "Norra and the Book of Thresholds.",
        "major_events": "Life with Norra, Norra's disappearance, beginning the search for her, and traveling through portals using the Book.",
        "current_status": "Searching for Norra while traveling between locations through the Book of Thresholds.",
        "lore": "Yuumi is a magical cat and the companion of the yordle Norra. When Norra mysteriously disappeared, Yuumi took possession of the Book of Thresholds, a magical artifact capable of opening portals between distant places. Yuumi now travels across Runeterra searching for Norra, accompanied by the sentient Book and guided by her unwavering loyalty to her owner.",
        "image": "yuumi.jpg"
    }
]

# SERVE /images/<filename> straight from the "images" folder (jpg, png, gif all work as-is)
app.mount("/images", StaticFiles(directory="images"), name="images")


def attach_image_url(character: dict) -> dict:
    """Return a copy of character with a full image_url built from its image filename."""
    c = dict(character)
    filename = c.get("image")
    c["image_url"] = f"/images/{filename}" if filename else None
    return c


# HOME
@app.get("/")
def home():
    return {
        "message": "Welcome to the Simple Anime Character API!",
        "endpoints": [
            "/characters",
            "/characters/{id}",
            "/characters/search"
        ]
    }


# GET ALL CHARACTERS
@app.get("/characters")
def get_characters():
    result = [attach_image_url(c) for c in characters]
    return {
        "count": len(result),
        "characters": result
    }


# SEARCH CHARACTERS
# IMPORTANT: This must come BEFORE /characters/{character_id}
@app.get("/characters/search")
def search_characters(q: str = Query(..., min_length=1)):
    q = q.lower()
    results = []

    for character in characters:
        searchable_text = (
            f"{character['name']} "
            f"{character['region']} "
            f"{character['faction']}"
        ).lower()

        if q in searchable_text:
            results.append(attach_image_url(character))

    return {
        "query": q,
        "count": len(results),
        "results": results
    }


# GET ONE CHARACTER
@app.get("/characters/{character_id}")
def get_character(character_id: int):
    for character in characters:
        if character["id"] == character_id:
            return attach_image_url(character)

    raise HTTPException(
        status_code=404,
        detail="Character not found."
    )