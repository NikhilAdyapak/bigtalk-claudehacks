# Big Talk — When Small Talk Ends, Big Talk Starts

> UW-Madison Claude Hacks Hackathon Project — a 1-hour speed hackathon organized by the Claude Builder Club

## What Is It?
Big Talk uses Claude AI to find *surprising, non-obvious connections* between people. Enter a room code, fill out your interests (anime, games, shows, hot takes), and Claude automatically matches you with everyone else — ranking them by vibe score and generating deep conversation starters that skip the awkward small talk.

## Demo Flow
1. Everyone opens the same URL on their phone/laptop
2. Enter a shared room code (e.g. `CS577`)
3. Fill out your profile — takes 30 seconds
4. Claude auto-matches you with every person in the room
5. Cards rank in real time by vibe score (0–100)
6. Tap any card → animated reveal with 3 non-obvious connections + a Big Talk question

## Tech Stack
- **Backend:** Python FastAPI + Anthropic SDK (Claude Sonnet)
- **Frontend:** Single vanilla HTML/CSS/JS file — no React, no build step
- **Database:** In-memory Python dict (no setup needed)
- **Cross-device:** All devices hit the same FastAPI server over local WiFi

## Project Structure
```
main.py              # FastAPI backend — all API endpoints
templates/index.html # Full frontend — single file, no build step
demo_profiles.py     # Seeds 5 demo profiles + runs test matches
PITCH.md             # Hackathon pitch + demo script
requirements.txt     # Python dependencies
```

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Serve frontend |
| POST | `/api/join` | Join a room with a profile |
| GET | `/api/room/{code}` | Get all profiles in a room |
| POST | `/api/match` | Claude analyzes two profiles → returns connections + vibe score |
| GET | `/api/leaderboard/{code}` | Ranked leaderboard by match count |
| GET | `/api/health` | Health check |

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...

# Start the server (accessible on local network)
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000` in your browser.

**Share with teammates on the same WiFi:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
# Open http://<your-ip>:8000 on any device
```

## Running the Demo Script
Seeds 5 pre-built profiles and fires 3 Claude matches — good for testing before a live demo:
```bash
python3 demo_profiles.py
# or against a remote server:
python3 demo_profiles.py http://192.168.1.X:8000
```

## Team
Built in a hackathon sprint — Person 1 (backend), Person 2 (frontend), Person 3 (demo + pitch).
