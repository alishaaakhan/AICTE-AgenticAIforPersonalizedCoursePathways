# LearnMate 🎓
### Agentic AI for Personalized Course Pathways
**AICTE Problem Statement #12 | Powered by IBM Granite on IBM watsonx.ai**

---

## Overview

LearnMate is an **Agentic AI learning coach** that interacts with students,
understands their interests and goals, and dynamically builds a **personalized
course roadmap** that adapts over time based on progress.

It uses **IBM Granite** (via IBM watsonx.ai) as the reasoning engine for:
- Natural conversation coaching
- Personalized roadmap generation
- AI-powered skill assessment quizzes
- Adaptive roadmap updates

---

## Features

| Feature | Description |
|---|---|
| 🎯 Personalized Onboarding | Collects domain, skill level, goals, and weekly hours |
| 🗺️ AI Roadmap Generation | IBM Granite builds a phased, prerequisite-aware roadmap |
| 🧠 Skill Assessment | AI quiz that evaluates and updates skill level |
| 📈 Progress Tracking | Marks courses started/completed, visualizes progress |
| 🔄 Adaptive Roadmap | Roadmap regenerates based on real progress |
| 💬 Free-form Q&A | Multi-turn AI conversation with IBM Granite |
| 💾 Persistent Profiles | Student data saved as JSON, survives restarts |
| 🔌 Offline Fallback | Rule-based roadmap when IBM Granite not configured |

---

## Project Structure

```
learnmate/
├── __init__.py
├── granite_client.py       # IBM watsonx.ai / IBM Granite integration
├── student_profile.py      # Student data model + ProfileManager
├── course_catalog.py       # 40+ curated courses across 12 tech domains
├── roadmap_generator.py    # LLM-powered + rule-based roadmap builder
├── progress_tracker.py     # Progress analytics and reporting
└── agents/
    ├── __init__.py
    └── coach_agent.py      # Main agentic loop (CoachAgent)

main.py                     # Application entry point
requirements.txt            # Python dependencies
.env                        # IBM Cloud credentials (edit before running)
data/                       # Auto-created; stores student profile JSONs
```

---

## Quick Start

### 1. Prerequisites

- Python 3.11+
- An [IBM Cloud account](https://cloud.ibm.com/) (Lite/Free tier works)
- An [IBM watsonx.ai](https://www.ibm.com/watsonx) project with an IBM Granite model

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure IBM credentials

Edit the `.env` file in the project root:

```env
IBM_API_KEY=<your IBM Cloud IAM API key>
WATSONX_PROJECT_ID=<your watsonx.ai project ID>
WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-3-8b-instruct
```

**Where to find these:**
| Variable | How to get it |
|---|---|
| `IBM_API_KEY` | [IBM Cloud → IAM → API keys](https://cloud.ibm.com/iam/apikeys) → Create |
| `WATSONX_PROJECT_ID` | [watsonx.ai](https://dataplatform.cloud.ibm.com) → your project → Manage → General |
| `WATSONX_URL` | Use the URL for your IBM Cloud region (Dallas = `us-south`) |
| `GRANITE_MODEL_ID` | `ibm/granite-3-8b-instruct` (or any Granite model in your region) |

### 4. Run LearnMate

```bash
python main.py
```

---

## Usage Guide

### Starting a session

```
python main.py
```

You'll be greeted and asked for your name. Returning students are
recognized automatically (profiles are saved in `./data/`).

### Available commands (type during the chat)

| Command | Action |
|---|---|
| `show roadmap` | Display your personalized learning roadmap |
| `start course` | Mark a course as in-progress |
| `completed …` | Mark a course as completed |
| `my progress` | Show progress dashboard |
| `adapt roadmap` | Regenerate roadmap based on current progress |
| `assess skills` | Take an AI skill-assessment quiz |
| `help` | Show all commands |
| `quit` | Exit LearnMate |
| *anything else* | Free-form Q&A with IBM Granite |

### CLI utilities

```bash
python main.py --list     # List all saved student profiles
python main.py --report   # Print a detailed progress report
```

---

## Supported Domains (12 total)

1. Frontend Development
2. Backend Development
3. Full Stack Development
4. Data Science & Machine Learning
5. Cybersecurity
6. UI/UX Design
7. Mobile Development
8. Cloud Computing
9. DevOps & MLOps
10. Blockchain
11. Game Development
12. Embedded Systems & IoT

---

## IBM Technology Used

| Technology | Role |
|---|---|
| **IBM Granite** (`ibm/granite-3-8b-instruct`) | Roadmap generation, skill assessment, coaching Q&A |
| **IBM watsonx.ai** | Model hosting, inference API |
| **IBM Cloud IAM** | Authentication (API key) |
| **ibm-watsonx-ai SDK** | Python client for watsonx.ai |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────┐
│                  main.py                    │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────▼──────────┐
        │    CoachAgent       │  ← Agentic loop
        │  agents/coach_agent │
        └──┬──────┬──────┬────┘
           │      │      │
    ┌──────▼─┐ ┌──▼──┐ ┌─▼──────────────┐
    │Granite │ │Road-│ │ ProfileManager │
    │Client  │ │map  │ │ student_profile│
    │(IBM AI)│ │Gen. │ │ (JSON on disk) │
    └────────┘ └──┬──┘ └────────────────┘
                  │
        ┌─────────▼──────────┐
        │  Course Catalog    │
        │  (40+ courses,     │
        │   12 domains)      │
        └────────────────────┘
```

---

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `IBM_API_KEY` | *(required)* | IBM Cloud IAM API key |
| `WATSONX_PROJECT_ID` | *(required)* | watsonx.ai project ID |
| `WATSONX_URL` | `https://us-south.ml.cloud.ibm.com` | Regional endpoint |
| `GRANITE_MODEL_ID` | `ibm/granite-3-8b-instruct` | Granite model to use |
| `DATA_DIR` | `./data` | Folder for student profile JSON files |
| `MAX_NEW_TOKENS` | `1024` | Max tokens per LLM response |
| `TEMPERATURE` | `0.7` | Sampling temperature |
| `TOP_P` | `0.9` | Nucleus sampling |

---

## License

MIT – free for educational and research use.
