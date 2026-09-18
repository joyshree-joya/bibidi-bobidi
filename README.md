# ⚡ GridWise LLM

<p align="center">
  <strong>LLM-Powered Smart Campus Energy Optimization API</strong>
</p>

<p align="center">
  Convert natural-language energy instructions into safe, structured directives and generate a minimum-cost 24-hour energy schedule.
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat-square&logo=openai&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white)

</p>

---

## 🌟 Overview

**GridWise LLM** is a smart-campus energy optimization API that allows operators to control energy policies using natural language.

For example:

> "Reduce solar generation from 1 PM to 3 PM by 80%."

The system uses an LLM to understand the instruction, converts it into structured JSON, validates it using deterministic guardrails, and generates an optimized 24-hour energy schedule.

---

## 🔄 How It Works

```text
Natural Language
      │
      ▼
┌──────────────┐
│   OpenAI LLM │
└──────┬───────┘
       │
       ▼
Structured Directives
       │
       ▼
┌──────────────┐
│  Guardrails  │
│ Validate +   │
│  Normalize   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Optimizer  │
│ Minimum Cost │
└──────┬───────┘
       │
       ▼
24-Hour Energy Plan



🚀 Getting Started
1. Clone the repository
git clone https://github.com/joyshree-joya/bibidi-bobidi.git
cd bibidi-bobidi
2. Create a virtual environment
Windows
python -m venv .venv
.venv\Scripts\Activate.ps1
Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
3. Install dependencies
pip install -r requirements.txt
4. Configure environment variables

Create a .env file in the project root:

OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5.6-luna

⚠️ Never commit .env to GitHub.

5. Run the API
python -m uvicorn app.main:app --reload

The API will be available at:

http://127.0.0.1:8000
📚 API Documentation

Once the server is running, open:

Swagger UI
http://127.0.0.1:8000/docs

You can test the API directly from your browser.

Health Check
GET /health

Response:

{
  "status": "ok"
}

🧪 Testing

Run deterministic guardrail tests:

pytest tests/test_guardrails.py -v

Run the public integration tests:

pytest tests/test_public_samples.py -v

⚠️ test_public_samples.py uses the real OpenAI API and consumes API requests. Avoid running it unnecessarily.

🛠️ Tech Stack
Technology	Purpose
Python	Core application
FastAPI	REST API
OpenAI API	LLM interpretation
Pydantic	Data validation
PuLP	Optimization
CBC	Solver
Pytest	Testing