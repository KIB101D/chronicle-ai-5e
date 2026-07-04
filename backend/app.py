import asyncio
import re
import random
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from ddgs import DDGS

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = SentenceTransformer('all-MiniLM-L6-v2')

class UserStory(BaseModel):
    story: str

OFFICIAL_CLASSES_LIBRARY = {
    "Fighter": "A master of martial combat, skilled with swords, shields, bows, and all forms of armor. A veteran soldier, dark warrior, outlaw, or mercenary.",
    "Rogue": "A scoundrel who uses stealth, precision, and trickery to overcome foes. Perfect for assassins, thieves, bandits, and shadow stalkers.",
    "Barbarian": "A fierce warrior who can enter a battle rage to tank damage and deal devastating melee strikes. Driven by fury and revenge for a destroyed home or burned village.",
    "Wizard": "A scholarly magic-user capable of manipulating the structures of reality through arcane spells, ancient scrolls, and intense study.",
    "Warlock": "A spellcaster who gained magical power through a dark pact with an otherworldly patron, fiend, cosmic entity, or ancient deity.",
    "Sorcerer": "A gifted mage whose magic comes naturally from an innate bloodline, wild magic, dragons, or a cosmic spark.",
    "Cleric": "A priestly champion who wields divine magic in service of a higher power, healing allies and smiting enemies.",
    "Paladin": "A holy knight bound by a sacred oath, combining heavy steel armor, martial prowess, and divine smites.",
    "Druid": "A keeper of the wild world who can wildshape into animals and cast nature-focused elemental spells.",
    "Ranger": "A scout, hunter, and tracker who specializes in navigating the wilderness and killing specific foes from a distance with a bow.",
    "Bard": "An inspiring performer and weaver of words who uses music, lore, and charm to cast spells and support companions.",
    "Monk": "An expert martial artist who channels inner ki energy to strike fast, dodge attacks, and fight unarmed.",
    "Artificer": "A master of invention and magical technology, using tools to channel arcane power, craft magical items, and modify gear."
}

STOP_WORDS = {
    "who", "was", "were", "the", "and", "for", "that", "this", "with", "from", "into", "your", "their",
    "young", "old", "worn", "fights", "talks", "out", "about", "him", "her", "them", "unknowingly", "disguised"
}

COMBAT_STYLE_KEYWORDS = {
    "melee": ["sword", "blade", "melee", "strike", "claw", "fist", "brawl", "axe", "hammer"],
    "ranged": ["bow", "arrow", "ranged", "gun", "rifle", "throw", "dart", "sling"],
    "magic": ["spell", "magic", "arcane", "sorcery", "mana", "wizard", "caster", "ritual"],
    "support": ["heal", "buff", "inspire", "bard", "ally", "support", "charm"],
    "assassin": ["stealth", "assassin", "shadow", "sneak", "poison", "thief", "ambush"],
    "tank": ["armor", "shield", "tank", "defense", "guard", "bulwark"],
    "gambler": ["card", "deck", "tarot", "gamble", "fate", "luck", "dice", "coin", "fortune", "dealer"],
    "tinkerer": ["potion", "alchemist", "vial", "bomb", "brew", "elixir", "tinker", "clockwork", "gear", "gadget", "invention", "forge", "craft", "acid"],
    "summoner": ["summon", "summoner", "minion", "eidolon", "pet", "companion", "call", "conjure", "horde"],
}

STYLE_LABELS = {
    "melee": "Melee Combat", 
    "ranged": "Ranged Combat", 
    "magic": "Magic",
    "support": "Ally Support", 
    "assassin": "Stealth/Assassin", 
    "tank": "Tank/Defense",
    "gambler": "Gambling/Fate",
    "tinkerer": "Alchemy/Invention",
    "summoner": "Summoning"
}

POWER_SOURCE_KEYWORDS = {
    "divine": (["god", "divine", "holy", "oath", "faith", "deity", "blessed", "smite", "cleric", "paladin"], "Power from a divine source"),
    "pact": (["pact", "patron", "fiend", "otherworldly", "demon", "warlock", "bargain"], "Power granted through a dark pact with a patron"),
    "innate": (["bloodline", "innate", "born", "natural", "wild magic", "sorcerer", "ancestral"], "Innate or hereditary power"),
    "study": (["study", "scroll", "arcane school", "academy", "scholar", "wizard", "spellbook", "library"], "Power acquired through intense study"),
    "nature": (["nature", "wild", "beast", "forest", "druid", "elemental", "swarm", "bug", "insect", "ranger", "plant", "fae", "fey"], "Power derived from a connection to nature"),
    "ki": (["ki", "chi", "inner energy", "meditation", "discipline", "monk", "unarmed"], "Inner discipline and ki energy"),
    "spirit": (["spirit", "ghost", "soul", "possessed", "haunt", "phantom", "specter", "apparition", "guardian", "ancestor", "light"], "Power from spirits or otherworldly entities"),
    "martial": (["training", "veteran", "soldier", "mercenary", "skill", "warrior", "fighter", "sword", "armor", "shield", "blade", "knight", "weapon", "combat"], "Pure martial prowess without magic"),
    "blood": (["blood", "bleed", "vitality", "hemomancy", "sacrificial", "ichor", "scar"], "Power drawn from blood and vitality"),
    "death": (["necromancy", "undead", "death", "corpse", "skeleton", "zombie", "grave", "reaper", "ghoul", "vampire"], "Power over death and the undead"),
    "psionic": (["psionic", "mind", "telekinesis", "psi", "brain", "mental", "telepathy", "anomaly", "intellect"], "Psionic power of the mind"),
    "runic": (["rune", "inscription", "glyph", "engrave", "sigil", "mark"], "Magic anchored in ancient runes"),
    "occult": (["witch", "hex", "curse", "shaman", "totem", "voodoo", "jinx", "hag", "malice", "plague", "disease", "rot"], "Occult witchcraft and curses"),
    "draconic": (["dragon", "drake", "draconic", "wyrm", "breath weapon", "scale"], "Power inherited from dragons"),
    "cosmic": (["void", "cosmic", "abyss", "star", "astral", "alien", "eldritch", "galaxy", "space", "meteor", "moon"], "Power from the cosmos or the void"),
    "temporal": (["time", "chrono", "temporal", "clock", "timeline", "past", "future", "age"], "Control over the flow of time")
}

def classify_combat(text_for_tags: str):
    matched_styles = [key for key, words in COMBAT_STYLE_KEYWORDS.items() if any(w in text_for_tags for w in words)]
    if not matched_styles: 
        return [], ""
    return matched_styles, "Combat Style: " + " + ".join([STYLE_LABELS[s] for s in matched_styles])

def classify_power_source(text_for_tags: str):
    for key, (words, phrase) in POWER_SOURCE_KEYWORDS.items():
        if any(w in text_for_tags for w in words): 
            return key, phrase
    return None, ""

@app.post("/api/analyze")
async def analyze_character(data: UserStory):
    user_text = data.story[:1000]
    user_vector = model.encode([user_text])

    official_results = []
    web_results = []

    for name, desc in OFFICIAL_CLASSES_LIBRARY.items():
        official_results.append({
            "title": name,
            "snippet": desc,
            "link": "https://www.dndbeyond.com/classes"
        })

    mechanical_vocabulary = set()
    
    for words in COMBAT_STYLE_KEYWORDS.values():
        for word in words:
            mechanical_vocabulary.update(word.lower().split())
            
    for words, _ in POWER_SOURCE_KEYWORDS.values():
        for word in words:
            mechanical_vocabulary.update(word.lower().split())
    
    # Базові класи D&D як безумовний VIP-пріоритет
    dnd_nouns = [
        "warrior", "knight", "mage", "cleric", "rogue", "paladin", "ranger", "druid", 
        "bard", "monk", "sorcerer", "warlock", "wizard", "fighter", "artificer",
        "brawler", "pugilist", "gunslinger", "alchemist", "summoner", "necromancer", 
        "shaman", "witch", "spellsword", "magus", "gish", "gambler", "tinkerer",
        "corsair", "reaper", "tactician", "scholar"
    ]
    mechanical_vocabulary.update(dnd_nouns)

    all_words = re.findall(r'\b\w+\b', user_text.lower())
    
    high_priority = []  # Сюди потраплять: sword, armor, spirit, warrior...
    low_priority = []   # Сюди відсіється шлак: garden, girl, village...
    seen_words = set()

    for w in all_words:
        if w in STOP_WORDS or len(w) <= 2 or w in seen_words:
            continue
        seen_words.add(w)
        
        # Легкий стемінг (відкидаємо закінчення множини 's', щоб "spirits" збіглося з "spirit")
        stemmed = w.rstrip('s')
        
        if w in mechanical_vocabulary or stemmed in mechanical_vocabulary:
            high_priority.append(w)
        else:
            low_priority.append(w)

    # Збираємо щільне ядро для пошуку — максимум 4 найсильніших слова
    clean_keywords = high_priority[:4]
    
    # Якщо VIP-слів замало (дуже короткий опис), добираємо з художньої частини
    if len(clean_keywords) < 3:
        remaining = 3 - len(clean_keywords)
        clean_keywords.extend(low_priority[:remaining])

    keywords_str = " ".join(clean_keywords) if clean_keywords else "custom"
    
    # Ідеально збалансований запит без води
    search_query = f"{keywords_str} 5e homebrew class"
    # ===================================================

    def run_search(query: str):
        last_error = None
        for backend in ["html", "lite", "duckduckgo", "bing"]:
            try:
                with DDGS() as ddgs:
                    return list(ddgs.text(query, max_results=12, backend=backend))
            except Exception as exc:
                err_msg = str(exc).lower()
                last_error = (backend, exc)
                if any(err in err_msg for err in ["429", "rate limit", "202", "timeout", "blocked"]):
                    break
                continue
        if last_error:
            raise last_error[1]
        return []

    try:
        jitter = random.uniform(0.5, 2.0)
        await asyncio.sleep(jitter)
        web_responses = await asyncio.to_thread(run_search, search_query)

        for resp in web_responses:
            title = resp.get("title", "")
            snippet = resp.get("body", "")
            link = resp.get("href", "")

            junk_domains = ["facebook.com", "pinterest.com", "quora.com", "twitter.com", "x.com", "instagram.com"]
            if any(d in link.lower() for d in junk_domains):
                continue

            clean_snippet = re.sub(r"^[A-Za-z]+ \d{1,2},? \d{4}\s*[-–]\s*", "", snippet)
            sentences = re.split(r"(?<=[.!?])\s+", clean_snippet)
            clean_snippet = " ".join(sentences[:3]).strip()

            web_results.append({
                "title": title,
                "snippet": clean_snippet or snippet,
                "link": link
            })
    except Exception:
        pass

    def score_pool(pool_items, is_web=False):
        if not pool_items:
            return []
        snippets = [item['snippet'] for item in pool_items]
        vectors = model.encode(snippets)

        TRUSTED_DOMAINS = ["dandwiki.com", "reddit.com/r/unearthedarcana", "reddit.com/r/dndhomebrew"]
        DND_STRUCTURAL_TOKENS = [
            "hit points", "proficiency", "features", "subclass", "spellcasting", 
            "hit dice", "archetype", "level", "spell slots", "cantrip"
        ]

        scored = []
        for i, item in enumerate(pool_items):
            base_similarity = float(cosine_similarity(user_vector, [vectors[i]])[0][0])
            similarity = base_similarity
            text_for_tags = (item['title'] + " " + item['snippet']).lower()

            if is_web:
                structural_matches = sum(1 for token in DND_STRUCTURAL_TOKENS if token in text_for_tags)
                if structural_matches == 0:
                    similarity -= 0.25
                elif structural_matches >= 2:
                    similarity += 0.05

            link_lower = item['link'].lower()
            if any(domain in link_lower for domain in TRUSTED_DOMAINS):
                similarity += 0.10

            tags = []
            if any(w in text_for_tags for w in ["magic", "spell", "wizard", "caster", "spirit", "light"]): tags.append("magic")
            if any(w in text_for_tags for w in ["stealth", "rogue", "thief", "shadow"]): tags.append("stealth")
            if any(w in text_for_tags for w in ["tank", "warrior", "armor", "fighter", "combat", "knight"]): tags.append("martial")
            if any(w in text_for_tags for w in ["range", "bow", "hunter", "bug", "swarm"]): tags.append("range")
            if "homebrew" in text_for_tags or "dandwiki" in item['link'] or "reddit" in item['link']: tags.append("homebrew")

            combat_styles, style_phrase = classify_combat(text_for_tags)
            power_key, power_phrase = classify_power_source(text_for_tags)

            clean_title = re.sub(r"(- DnD Wiki|- D&D|\| Reddit.*|· D&D Beyond| - Class.*|\s*:\s*r/\w+.*|\s*-\s*Reddit$)", "", item['title']).strip()
            clean_title = re.sub(r"^Homebrew class:\s*", "", clean_title, flags=re.IGNORECASE).strip()

            scored.append({
                "class_name": clean_title,
                "description": item['snippet'],
                "link": item['link'],
                "score": similarity,
                "raw_score": base_similarity,
                "tags": tags,
                "combat_styles": combat_styles,
                "combat_style_label": style_phrase,
                "power_source": power_key,
                "power_source_label": power_phrase,
            })
        return sorted(scored, key=lambda x: x['score'], reverse=True)

    scored_official = score_pool(official_results, is_web=False)
    scored_web = score_pool(web_results, is_web=True)

    cleaned_web_pool = []
    for match in scored_web:
        if match['score'] < 0.30:
            continue

        title_lower = match['class_name'].lower()
        link_lower = match['link'].lower()
        desc_lower = match['description'].lower()

        junk_patterns = [
            "discussion", "forum", "thread", "comment", "house rules", "rules - dungeons",
            "weekly brews", "all classes", "list of", "top 10", "top 5", "top 12", "index", 
            "directory", "main page", "category", "compilation", "brewery", "arena"
        ]
        if any(pat in title_lower or pat in link_lower or pat in desc_lower for pat in junk_patterns):
            continue

        cleaned_web_pool.append(match)

    groups = []
    COMMON_CONNECTORS = {
        "the", "and", "for", "with", "this", "that", "from", "class", "subclass", 
        "archetype", "5e", "homebrew", "d", "dnd", "edition", "5th", "version", 
        "wiki", "classes", "r", "dndnext", "unearthedarcana", "page"
    }

    for match in cleaned_web_pool:
        words = re.findall(r'\b\w+\b', match['class_name'].lower())
        match_phrases = set()
        
        for i in range(len(words) - 1):
            if words[i] in COMMON_CONNECTORS or words[i+1] in COMMON_CONNECTORS:
                continue
            match_phrases.add(f"{words[i]} {words[i+1]}")
            
        for i in range(len(words) - 2):
            if words[i] in COMMON_CONNECTORS or words[i+1] in COMMON_CONNECTORS or words[i+2] in COMMON_CONNECTORS:
                continue
            match_phrases.add(f"{words[i]} {words[i+1]} {words[i+2]}")

        found_group_idx = None
        for idx, group in enumerate(groups):
            for existing_item in group:
                if existing_item['class_name'].lower() == match['class_name'].lower():
                    found_group_idx = idx
                    break
                
                ex_words = re.findall(r'\b\w+\b', existing_item['class_name'].lower())
                ex_phrases = set()
                for i in range(len(ex_words) - 1):
                    if ex_words[i] in COMMON_CONNECTORS or ex_words[i+1] in COMMON_CONNECTORS:
                        continue
                    ex_phrases.add(f"{ex_words[i]} {ex_words[i+1]}")
                for i in range(len(ex_words) - 2):
                    if ex_words[i] in COMMON_CONNECTORS or ex_words[i+1] in COMMON_CONNECTORS or ex_words[i+2] in COMMON_CONNECTORS:
                        continue
                    ex_phrases.add(f"{ex_words[i]} {ex_words[i+1]} {ex_words[i+2]}")

                if match_phrases and (match_phrases & ex_phrases):
                    found_group_idx = idx
                    break
            if found_group_idx is not None:
                break

        if found_group_idx is not None:
            groups[found_group_idx].append(match)
        else:
            groups.append([match])

    unique_web = []
    for group in groups:
        group_sorted = sorted(group, key=lambda x: x['score'], reverse=True)
        main_card = group_sorted[0]
        main_card['variants'] = [
            {
                "title": item['class_name'],
                "link": item['link'],
                "score": item['score']
            } for item in group_sorted[1:]
        ]
        unique_web.append(main_card)

    final_web = []
    for match in unique_web:
        if match['class_name'].lower() not in [o['class_name'].lower() for o in scored_official]:
            final_web.append(match)

    final_pool = scored_official[:2] + final_web[:3]
    final_pool = sorted(
        final_pool,
        key=lambda x: (1 if (x['score'] >= 0.30 and x['link'] != "https://www.dndbeyond.com/classes") else 0, x['score']),
        reverse=True
    )

    return {"status": "success", "matches": final_pool}