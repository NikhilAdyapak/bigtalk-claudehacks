# Big Talk — Claude Hacks Speed Hackathon

## What This Is
"Big Talk" — When small talk ends, Big Talk starts. An app where students fill out quick interest profiles (anime, games, shows, hot takes) and Claude AI finds *non-obvious, surprising connections* between them — generating deep conversation starters that skip the awkward small talk.

## Theme Alignment
UW-Madison hackathon theme: "The tools that were supposed to connect us made us more lonely. What if we built better ones?" Big Talk directly answers this — it uses AI to find genuine human bridges, not algorithmic bubbles.

## Tech Stack
- **Backend:** Python FastAPI (main.py)
- **Frontend:** Single vanilla HTML/JS/CSS file (templates/index.html) — NO React, NO npm
- **AI:** Claude API (claude-sonnet-4-20250514) via anthropic Python SDK
- **Database:** In-memory Python dict (no DB needed for demo)
- **Cross-device:** All devices hit the same FastAPI server over local WiFi

## Architecture
```
POST /api/join          → Join a room with a room code, submit profile
GET  /api/room/{code}   → Get all profiles in a room
POST /api/match         → Send two profile IDs → Claude finds connections
GET  /api/leaderboard/{code} → Get leaderboard for a room
```

## File Ownership (DO NOT touch other people's files)
- main.py → Person 1 (Backend + Claude API)
- templates/index.html → Person 2 (Frontend UI)
- demo_profiles.py → Person 3 (Demo script + seed data)

## Key Design Decisions
- Room codes (e.g., "CS577") let people in the same lecture/table find each other
- Leaderboard: people who match with more people rank higher, expanding their "radius" (shown as a visual circle)
- Hot takes are the secret sauce — Claude uses them to find spicy connections
- NO accounts, NO login — just name + interests + room code

## Claude API Prompt Strategy
Claude receives two profiles and must return JSON with:
- 3 non-obvious connections (not "you both like Naruto" but WHY the overlap matters)
- A Big Talk conversation starter for each
- A vibe_match_score (0-100)
- An opening line to actually say to the person

## Demo Flow (90 seconds)
1. Show the landing page — "When small talk ends, Big Talk starts"
2. Two phones join room "CS577"
3. Both fill out quick profiles
4. Tap "Find My Big Talk" → Claude analyzes
5. Reveal: animated connection card showing the surprising bridge
6. Show leaderboard — who's the most connected person in CS577?
