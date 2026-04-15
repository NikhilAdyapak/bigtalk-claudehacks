import os
import uuid
import json
import time
from datetime import datetime

import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from pydantic import BaseModel
from typing import List

# ── App setup ────────────────────────────────────────────────────────────────
app = FastAPI(title="Big Talk")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="templates"), name="static")

# ── In-memory store ───────────────────────────────────────────────────────────
# rooms = {
#   room_code: {
#     "profiles": { profile_id: {id, name, anime, games, shows, hot_take, secret,
#                                match_count, vibe_scores, timestamp} },
#     "matches":  [ {profile_id_1, profile_id_2, result, timestamp} ]
#   }
# }
rooms: dict = {}

# ── Anthropic client ──────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

SYSTEM_PROMPT = """You are "Big Talk" — an AI that finds surprising, deep connections between two people. You go BEYOND surface matches.

Rules:
- Find 3 NON-OBVIOUS connections. Don't say "you both like Naruto." Find thematic bridges — shared values, taste patterns, complementary worldviews. Be specific.
- For each connection, write a "Big Talk" question — something that would spark a genuine, deep conversation. Reference THEIR specific interests by name.
- Give a vibe_match_score from 0-100.
- Give an opening_line — something natural and fun one could actually say to the other person.
- Give a wild_card — one unexpected observation.

Respond ONLY in JSON, no markdown fences:
{"connections": [{"title": "short title", "insight": "1-2 sentences", "big_talk_question": "the question"}], "vibe_match_score": 75, "opening_line": "text", "wild_card": "text"}"""


# ── Request/Response models ───────────────────────────────────────────────────
class JoinRequest(BaseModel):
    room_code: str
    name: str
    anime: List[str] = []
    games: List[str] = []
    shows: List[str] = []
    hot_take: str = ""
    secret: str = ""


class MatchRequest(BaseModel):
    room_code: str
    profile_id_1: str
    profile_id_2: str


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_room(room_code: str) -> dict:
    if room_code not in rooms:
        rooms[room_code] = {"profiles": {}, "matches": []}
    return rooms[room_code]


def public_profile(profile: dict) -> dict:
    """Strip the secret field before returning to clients."""
    return {k: v for k, v in profile.items() if k != "secret"}


def call_claude(profile1: dict, profile2: dict) -> dict:
    """Call Claude API with two profiles. Retries once on bad JSON."""
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    user_message = json.dumps({
        "person_1": public_profile(profile1),
        "person_2": public_profile(profile2),
    })

    def attempt() -> dict:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = message.content[0].text.strip()
        return json.loads(raw)

    try:
        return attempt()
    except (json.JSONDecodeError, KeyError):
        # Retry once
        try:
            return attempt()
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"Claude returned invalid JSON after retry: {str(e)}"
            )


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/join")
def join(req: JoinRequest):
    room = get_room(req.room_code)
    profile_id = str(uuid.uuid4())
    room["profiles"][profile_id] = {
        "id": profile_id,
        "name": req.name,
        "anime": req.anime,
        "games": req.games,
        "shows": req.shows,
        "hot_take": req.hot_take,
        "secret": req.secret,
        "match_count": 0,
        "vibe_scores": [],
        "timestamp": datetime.utcnow().isoformat(),
    }
    return {"profile_id": profile_id, "room_code": req.room_code}


@app.get("/api/room/{code}")
def get_room_state(code: str):
    room = get_room(code)
    profiles = [public_profile(p) for p in room["profiles"].values()]
    return {"profiles": profiles, "count": len(profiles)}


@app.post("/api/match")
def match(req: MatchRequest):
    room = get_room(req.room_code)
    profiles = room["profiles"]

    if req.profile_id_1 not in profiles:
        raise HTTPException(status_code=404, detail=f"Profile {req.profile_id_1} not found")
    if req.profile_id_2 not in profiles:
        raise HTTPException(status_code=404, detail=f"Profile {req.profile_id_2} not found")

    p1 = profiles[req.profile_id_1]
    p2 = profiles[req.profile_id_2]

    result = call_claude(p1, p2)

    # Persist match & update stats
    room["matches"].append({
        "profile_id_1": req.profile_id_1,
        "profile_id_2": req.profile_id_2,
        "result": result,
        "timestamp": datetime.utcnow().isoformat(),
    })

    score = result.get("vibe_match_score", 0)
    p1["match_count"] += 1
    p1["vibe_scores"].append(score)
    p2["match_count"] += 1
    p2["vibe_scores"].append(score)

    return {
        "profile_1": public_profile(p1),
        "profile_2": public_profile(p2),
        "result": result,
    }


@app.get("/api/leaderboard/{code}")
def leaderboard(code: str):
    room = get_room(code)
    profiles = list(room["profiles"].values())

    def avg_vibe(p):
        scores = p.get("vibe_scores", [])
        return round(sum(scores) / len(scores), 1) if scores else 0

    ranked = sorted(profiles, key=lambda p: p["match_count"], reverse=True)
    return {
        "leaderboard": [
            {
                **public_profile(p),
                "avg_vibe_score": avg_vibe(p),
                "rank": idx + 1,
            }
            for idx, p in enumerate(ranked)
        ]
    }


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
