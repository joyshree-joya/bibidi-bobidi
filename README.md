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