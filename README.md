⚡ GridWise LLM

LLM-powered Smart Campus Energy Optimization API

GridWise converts natural-language energy instructions into structured directives, validates them using deterministic guardrails, and generates a minimum-cost 24-hour energy schedule.

✨ Features
🤖 LLM-powered operator note interpretation
🧩 Structured JSON directives
🛡️ Deterministic validation & normalization
☀️ Solar reduction
🔋 Battery reserve management
🚫 No-charge / no-discharge windows
⚡ Maximum grid-import limits
💰 Minimum-cost energy optimization
🚀 FastAPI REST API
🧪 Automated unit & integration testing
🔄 How It Works
Natural-Language Notes
        ↓
      OpenAI LLM
        ↓
Structured Directives
        ↓
Deterministic Guardrails
        ↓
Energy Optimizer
        ↓
24-Hour Optimized Schedule
🛠️ Tech Stack

Python · FastAPI · OpenAI API · Pydantic · PuLP · CBC · pytest

🚀 Run Locally
pip install -r requirements.txt

Create .env:

OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-5.6-luna

Run:

python -m uvicorn app.main:app --reload

API documentation:

http://127.0.0.1:8000/docs
🧪 Testing

Run guardrail tests:

pytest tests/test_guardrails.py -v

Run public integration cases:

pytest tests/test_public_samples.py -v

The public integration tests use real LLM API requests.