# ClassFinder — D&D 5e Class Analyzer

Describe your character in plain text. The AI reads your story and finds the D&D 5e class that fits — comparing against official classes and live homebrew sources.

**Stack:** FastAPI · sentence-transformers · DuckDuckGo Search · Vanilla JS

---

## How it works

1. You describe your character's personality, history, and abilities
2. The backend encodes your text using `all-MiniLM-L6-v2` (semantic embeddings)
3. It searches for homebrew classes via DuckDuckGo and scores all candidates by cosine similarity
4. Results are ranked and returned with combat style, power source, and match percentage

---

## Project structure

```
dnd-generator/
├── backend/
│   ├── app.py            # FastAPI app — analysis endpoint
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── styles.css
    ├── app.js            # State, form, view navigation
    ├── api.js            # Fetch logic
    └── ui.js             # Render functions
```

---

## Setup & launch

### 1. Backend

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate       # macOS / Linux
# venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app:app --reload
```

Backend runs at `http://127.0.0.1:8000`.  
The semantic model downloads automatically on first launch (~90 MB).

### 2. Frontend

Open `frontend/index.html` with **VS Code Live Server** (right-click → _Open with Live Server_), or any static file server.

---

## API

```
POST /api/analyze
Content-Type: application/json

{ "story": "A young warrior who talks to spirits disguised as bugs…" }
```

```json
{
  "status": "success",
  "matches": [
    {
      "class_name": "Spirit Warrior",
      "description": "…",
      "score": 0.528,
      "raw_score": 0.418,
      "tags": ["magic", "martial", "homebrew"],
      "combat_styles": ["melee"],
      "combat_style_label": "Combat Style: Melee Combat",
      "power_source": "spirit",
      "power_source_label": "Power from spirits or otherworldly entities",
      "link": "https://…",
      "variants": []
    }
  ]
}
```

---

## Notes

- Web search uses DuckDuckGo scraping — occasional rate-limiting is expected. The app gracefully falls back to official classes only.
- The semantic model runs locally, no API keys required.
- PDF export uses the browser's native print dialog (_Save as PDF_).
