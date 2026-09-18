<h1 align="center">⚡ GridWise LLM</h1>

<p align="center">
  <strong>LLM-Powered Smart Campus Energy Optimization API</strong>
</p>

<p align="center">
  Convert natural-language energy instructions into safe, structured directives
  and generate a minimum-cost 24-hour energy schedule.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/OpenAI-412991?style=flat-square&logo=openai&logoColor=white" alt="OpenAI">
  <img src="https://img.shields.io/badge/Pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white" alt="Pytest">
</p>

<hr>

<h2>🌟 Overview</h2>

<p>
  <strong>GridWise LLM</strong> is a smart-campus energy optimization API
  that allows operators to control energy policies using natural language.
</p>

<p>For example:</p>

<blockquote>
  Reduce solar generation from 1 PM to 3 PM by 80%.
</blockquote>

<p>
  The system uses an LLM to understand the instruction, converts it into
  structured JSON, validates it using deterministic guardrails, and generates
  an optimized 24-hour energy schedule.
</p>

<hr>

<h2>🔄 How It Works</h2>

<pre>
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
</pre>

<p align="center">
  <strong>LLM interprets → Guardrails validate → Optimizer calculates</strong>
</p>

<hr>

<h2>✨ Features</h2>

<ul>
  <li>🤖 Natural-language energy instruction interpretation</li>
  <li>🧩 Structured JSON directives</li>
  <li>🛡️ Deterministic validation & normalization</li>
  <li>☀️ Solar generation reduction</li>
  <li>🔋 Minimum battery reserve</li>
  <li>🚫 No-charge windows</li>
  <li>🚫 No-discharge windows</li>
  <li>⚡ Maximum grid-import limits</li>
  <li>💰 Minimum-cost 24-hour scheduling</li>
  <li>🚀 FastAPI REST API</li>
  <li>🧪 Automated testing</li>
</ul>

<hr>

<h2>📋 Supported Directives</h2>

<table>
  <thead>
    <tr>
      <th>Directive</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>solar_reduction</code></td>
      <td>Reduce usable solar generation</td>
    </tr>
    <tr>
      <td><code>minimum_battery_reserve</code></td>
      <td>Maintain minimum battery energy</td>
    </tr>
    <tr>
      <td><code>no_charge_window</code></td>
      <td>Prevent battery charging</td>
    </tr>
    <tr>
      <td><code>no_discharge_window</code></td>
      <td>Prevent battery discharging</td>
    </tr>
    <tr>
      <td><code>max_grid_window</code></td>
      <td>Limit grid import</td>
    </tr>
    <tr>
      <td><code>no_op</code></td>
      <td>Ignore energy-irrelevant instructions</td>
    </tr>
  </tbody>
</table>

<hr>

<h2>🧠 Example</h2>

<p><strong>Operator Note:</strong></p>

<pre>Reduce solar generation from 1 PM to 3 PM by 80%.</pre>

<p><strong>Structured Output:</strong></p>

<pre><code>{
  "note_index": 0,
  "applies": true,
  "directive_type": "solar_reduction",
  "structured_adjustment": {
    "hours": [13, 14],
    "factor": 0.2
  },
  "explanation": "Usable solar is reduced to 20 percent."
}</code></pre>

<p>
  Time ranges use <strong>start-inclusive, end-exclusive</strong> semantics.
</p>

<pre>
1 PM to 3 PM  → [13, 14]
11 PM to 2 AM → [23, 0, 1]
</pre>

<hr>

<h2>🛡️ Deterministic Guardrails</h2>

<p>
  LLM output is treated as <strong>untrusted data</strong> and is validated
  before reaching the optimizer.
</p>

<ul>
  <li>Exactly one directive per operator note</li>
  <li>Valid directive types</li>
  <li>Valid and unique note indices</li>
  <li>Valid hours from 0 to 23</li>
  <li>Duplicate hour normalization</li>
  <li>Valid numeric ranges</li>
  <li>Battery reserve cannot exceed battery capacity</li>
  <li>Correct <code>applies</code> values</li>
  <li>Correct adjustment structure</li>
  <li>Unsupported or malformed data is rejected</li>
</ul>

<hr>

<h2>⚙️ Energy Optimization</h2>

<p>
  After validation, the optimizer generates a feasible
  <strong>minimum-cost 24-hour energy schedule</strong>.
</p>

<p>The optimization considers:</p>

<ul>
  <li>🏢 Campus electricity demand</li>
  <li>☀️ Solar generation</li>
  <li>🔋 Battery capacity and energy</li>
  <li>🔋 Battery charge/discharge limits</li>
  <li>⚡ Grid electricity</li>
  <li>💵 Electricity tariffs</li>
  <li>📋 Operator-defined constraints</li>
</ul>

<p>The final response contains:</p>

<ul>
  <li>Directive interpretation</li>
  <li>24-hour energy plan</li>
  <li>Total grid consumption</li>
  <li>Total cost</li>
  <li>Peak grid usage</li>
  <li>Plan summary</li>
</ul>

<hr>

<h2>📁 Project Structure</h2>

<pre>
bibidi-bobidi/
│
├── app/
│   ├── main.py
│   ├── llm_interpreter.py
│   ├── guardrails.py
│   ├── optimizer.py
│   └── schemas.py
│
├── tests/
│   ├── test_guardrails.py
│   └── test_public_samples.py
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
</pre>

<table>
  <thead>
    <tr>
      <th>File</th>
      <th>Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>main.py</code></td>
      <td>FastAPI application and API endpoint</td>
    </tr>
    <tr>
      <td><code>llm_interpreter.py</code></td>
      <td>Natural language → structured directives</td>
    </tr>
    <tr>
      <td><code>guardrails.py</code></td>
      <td>Validation and normalization</td>
    </tr>
    <tr>
      <td><code>optimizer.py</code></td>
      <td>Energy optimization</td>
    </tr>
    <tr>
      <td><code>schemas.py</code></td>
      <td>Pydantic request/response models</td>
    </tr>
  </tbody>
</table>

<hr>

<h2>🚀 Getting Started</h2>

<h3>1. Clone the Repository</h3>

<pre><code>git clone https://github.com/joyshree-joya/bibidi-bobidi.git
cd bibidi-bobidi</code></pre>

<h3>2. Create a Virtual Environment</h3>

<h4>🪟 Windows</h4>

<pre><code>python -m venv .venv
.venv\Scripts\Activate.ps1</code></pre>

<h4>🐧 Linux / macOS</h4>

<pre><code>python3 -m venv .venv
source .venv/bin/activate</code></pre>

<h3>3. Install Dependencies</h3>

<pre><code>pip install -r requirements.txt</code></pre>

<h3>4. Configure Environment Variables</h3>

<p>
  Create a <code>.env</code> file in the project root:
</p>

<pre><code>OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5.6-luna</code></pre>

<p>
  ⚠️ <strong>Never commit <code>.env</code> to GitHub.</strong>
</p>

<h3>5. Run the API</h3>

<pre><code>python -m uvicorn app.main:app --reload</code></pre>

<p>
  The API will be available at:
</p>

<p>
  🌐
  <a href="https://bibidi-bobidi.onrender.com">
    https://bibidi-bobidi.onrender.com
  </a>
</p>

<hr>

<h2>📚 API Documentation</h2>

<p>
  Once the server is running, open the interactive Swagger documentation:
</p>

<p>
  📖
  <a href="https://bibidi-bobidi.onrender.com/docs">
    Open Swagger UI
  </a>
</p>

<p>
  You can test the API directly from your browser.
</p>

<h3>❤️ Health Check</h3>

<pre><code>GET /health</code></pre>

<p><strong>Response:</strong></p>

<pre><code>{
  "status": "ok"
}</code></pre>

<h3>🔌 Main Endpoint</h3>

<pre><code>POST /optimize-energy</code></pre>

<p>
  The endpoint accepts operator notes, 24-hour energy data, and battery
  configuration, then returns the optimized energy schedule.
</p>

<hr>

<h2>🧪 Testing</h2>

<h3>Guardrail Unit Tests</h3>

<pre><code>pytest tests/test_guardrails.py -v</code></pre>

<p>
  These tests verify the deterministic validation and normalization layer.
</p>

<h3>Public Integration Tests</h3>

<pre><code>pytest tests/test_public_samples.py -v</code></pre>

<p>
  ⚠️ <code>test_public_samples.py</code> uses the real OpenAI API and
  consumes API requests. Avoid running it unnecessarily.
</p>

<hr>

<h2>🛠️ Tech Stack</h2>

<table>
  <thead>
    <tr>
      <th>Technology</th>
      <th>Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>🐍 Python</td>
      <td>Core application</td>
    </tr>
    <tr>
      <td>🚀 FastAPI</td>
      <td>REST API</td>
    </tr>
    <tr>
      <td>🤖 OpenAI API</td>
      <td>LLM interpretation</td>
    </tr>
    <tr>
      <td>🔐 Pydantic</td>
      <td>Data validation</td>
    </tr>
    <tr>
      <td>⚙️ PuLP</td>
      <td>Mathematical optimization</td>
    </tr>
    <tr>
      <td>🔢 CBC</td>
      <td>Optimization solver</td>
    </tr>
    <tr>
      <td>🧪 Pytest</td>
      <td>Automated testing</td>
    </tr>
  </tbody>
</table>

<hr>

<h2>🎯 Core Idea</h2>

<pre>
Human Instruction
       ↓
      🤖 AI
       ↓
Structured Intent
       ↓
🛡️ Safety Validation
       ↓
⚙️ Optimization
       ↓
📊 Cost-Efficient Energy Schedule
</pre>

<hr>

<p align="center">
  <strong>⚡ GridWise LLM</strong>
  <br><br>
  Making campus energy management smarter, safer and easier.
</p>