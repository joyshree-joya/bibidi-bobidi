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
  <li>🧪 Automated unit and integration testing</li>
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
      <td>Reduce usable solar generation during selected hours</td>
    </tr>
    <tr>
      <td><code>minimum_battery_reserve</code></td>
      <td>Maintain a minimum battery energy level</td>
    </tr>
    <tr>
      <td><code>no_charge_window</code></td>
      <td>Prevent battery charging during selected hours</td>
    </tr>
    <tr>
      <td><code>no_discharge_window</code></td>
      <td>Prevent battery discharging during selected hours</td>
    </tr>
    <tr>
      <td><code>max_grid_window</code></td>
      <td>Limit grid import during selected hours</td>
    </tr>
    <tr>
      <td><code>no_op</code></td>
      <td>Ignore instructions unrelated to energy optimization</td>
    </tr>
  </tbody>
</table>

<hr>

<h2>🧠 LLM Interpretation</h2>

<p>
  The OpenAI LLM converts every operator note into exactly one structured
  directive.
</p>

<p><strong>Example:</strong></p>

<pre>Reduce solar generation from 1 PM to 3 PM by 80%.</pre>

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

<p>
  Percentage expressions are also interpreted correctly:
</p>

<table>
  <thead>
    <tr>
      <th>Instruction</th>
      <th>Remaining Factor</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Reduce by 80%</td>
      <td><code>0.2</code></td>
    </tr>
    <tr>
      <td>Reduce to 80%</td>
      <td><code>0.8</code></td>
    </tr>
    <tr>
      <td>Drop by half</td>
      <td><code>0.5</code></td>
    </tr>
  </tbody>
</table>

<hr>

<h2>🛡️ Deterministic Guardrails</h2>

<p>
  LLM output is treated as <strong>untrusted data</strong>. It must pass
  deterministic validation before reaching the optimizer.
</p>

<ul>
  <li>Exactly one directive per operator note</li>
  <li>Valid and unique note indices</li>
  <li>Supported directive types only</li>
  <li>Valid hours from <code>0</code> to <code>23</code></li>
  <li>Duplicate-hour normalization</li>
  <li>Valid numeric ranges</li>
  <li>Battery reserve cannot exceed battery capacity</li>
  <li>Correct <code>applies</code> values</li>
  <li>Correct structured adjustment format</li>
  <li>Unsupported or malformed data is rejected</li>
</ul>

<p>
  This separation ensures that the LLM interprets human language while
  deterministic code controls what is allowed into the optimization stage.
</p>

<hr>

<h2>⚙️ Optimizer & Solver</h2>

<p>
  After validation, GridWise generates a feasible
  <strong>minimum-cost 24-hour energy schedule</strong>.
</p>

<p>The optimizer considers:</p>

<ul>
  <li>🏢 Campus electricity demand</li>
  <li>☀️ Available solar generation</li>
  <li>🔋 Battery capacity and current energy</li>
  <li>🔋 Battery charge/discharge limits</li>
  <li>🔋 Minimum battery reserve</li>
  <li>🚫 Charge and discharge restrictions</li>
  <li>⚡ Grid import limits</li>
  <li>💵 Hourly electricity tariffs</li>
  <li>📋 Validated operator directives</li>
</ul>

<p>
  <strong>Optimization tools:</strong> PuLP + CBC solver
</p>

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
      <th>Responsibility</th>
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
      <td>Directive validation and normalization</td>
    </tr>
    <tr>
      <td><code>optimizer.py</code></td>
      <td>Energy optimization using PuLP/CBC</td>
    </tr>
    <tr>
      <td><code>schemas.py</code></td>
      <td>Pydantic request and response models</td>
    </tr>
  </tbody>
</table>

<hr>

<h2>🛠️ Dependencies & Tech Stack</h2>

<table>
  <thead>
    <tr>
      <th>Technology</th>
      <th>Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>🐍 Python 3.11+</td>
      <td>Core application</td>
    </tr>
    <tr>
      <td>🚀 FastAPI</td>
      <td>REST API</td>
    </tr>
    <tr>
      <td>🤖 OpenAI API</td>
      <td>Natural-language interpretation</td>
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

<pre><code>OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.6-luna</code></pre>

<table>
  <thead>
    <tr>
      <th>Variable</th>
      <th>Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>OPENAI_API_KEY</code></td>
      <td>OpenAI API authentication</td>
    </tr>
    <tr>
      <td><code>OPENAI_MODEL</code></td>
      <td>Model used for operator-note interpretation</td>
    </tr>
  </tbody>
</table>

<p>
  ⚠️ <strong>Never commit your <code>.env</code> file or API key.</strong>
</p>

<h3>5. Run the API</h3>

<pre><code>python -m uvicorn app.main:app --reload</code></pre>

<p>
  The local API will be available at:
</p>

<pre>http://127.0.0.1:8000</pre>

<hr>

<h2>❤️ Health Check</h2>

<pre><code>curl http://127.0.0.1:8000/health</code></pre>

<p><strong>Expected response:</strong></p>

<pre><code>{
  "status": "ok"
}</code></pre>

<hr>

<h2>📚 API Documentation</h2>

<p>
  FastAPI provides an interactive Swagger UI:
</p>

<p>
  <a href="http://127.0.0.1:8000/docs">
    http://127.0.0.1:8000/docs
  </a>
</p>

<p>
  Swagger UI allows organizers to inspect the API and send requests directly
  from the browser.
</p>

<hr>

<h2>🔌 API Endpoint</h2>

<h3>POST /optimize-energy</h3>

<p>The main endpoint accepts:</p>

<ul>
  <li>Scenario ID</li>
  <li>1–3 natural-language operator notes</li>
  <li>24 hourly demand, solar and tariff values</li>
  <li>Battery configuration</li>
</ul>

<p>It returns:</p>

<ul>
  <li>Directive interpretation</li>
  <li>24-hour optimized schedule</li>
  <li>Total grid consumption</li>
  <li>Total energy cost</li>
  <li>Peak grid usage</li>
  <li>Plan summary</li>
</ul>

<h3>Example Request Structure</h3>

<pre><code>{
  "scenario_id": "SAMPLE-02",
  "operator_notes": [
    "The battery charger will be isolated from 2 AM until 5 AM for electrical maintenance."
  ],
  "hours": [
    {
      "hour": 0,
      "demand_kwh": 100,
      "solar_kwh": 0,
      "tariff_bdt_per_kwh": 6
    }
  ],
  "battery": {
    "capacity_kwh": 200,
    "initial_energy_kwh": 70,
    "minimum_energy_kwh": 30,
    "max_charge_kwh_per_hour": 55,
    "max_discharge_kwh_per_hour": 55
  }
}</code></pre>

<p>
  <strong>Note:</strong> An actual request must contain all 24 hourly entries,
  from hour <code>0</code> through hour <code>23</code>.
</p>

<hr>

<h2>🧪 Testing</h2>

<h3>Guardrail Unit Tests</h3>

<pre><code>python -m pytest tests/test_guardrails.py -v</code></pre>

<p>
  These tests verify the deterministic validation and normalization layer
  without making live LLM requests.
</p>

<h3>Public Sample Integration Tests</h3>

<pre><code>python -m pytest tests/test_public_samples.py -v</code></pre>

<p>
  This runs all <strong>10 public sample cases</strong> through the complete
  pipeline:
</p>

<pre>
Public Sample
      ↓
   FastAPI
      ↓
 OpenAI LLM
      ↓
  Guardrails
      ↓
   Optimizer
      ↓
API Response
</pre>

<p>
  ⚠️ <strong>Important:</strong>
  <code>test_public_samples.py</code> uses the real OpenAI API and consumes
  API requests. Avoid running it unnecessarily.
</p>

<hr>

<h2>🌐 Live Deployment</h2>

<p>
  The project is deployed and available for remote testing.
</p>

<p>
  🌐
  <a href="https://bibidi-bobidi.onrender.com">
    Open Live API
  </a>
</p>

<p>
  📚
  <a href="https://bibidi-bobidi.onrender.com/docs">
    Open Swagger UI
  </a>
</p>

<h3>Live Health Check</h3>

<pre><code>curl https://bibidi-bobidi.onrender.com/health</code></pre>

<p><strong>Expected:</strong></p>

<pre><code>{
  "status": "ok"
}</code></pre>

<hr>

<h2>⚠️ Known Limitations</h2>

<ul>
  <li>
    A valid OpenAI API key and access to the configured model are required
    for LLM-based interpretation.
  </li>
  <li>
    LLM requests are subject to provider availability, quota, rate limits,
    cost and network latency.
  </li>
  <li>
    The public integration tests consume real OpenAI API requests.
  </li>
  <li>
    The optimizer works with the supplied 24-hour synthetic scenario data
    and does not retrieve live campus or utility data.
  </li>
  <li>
    Each request supports 1–3 operator notes.
  </li>
  <li>
    The optimization horizon is fixed to 24 hours.
  </li>
  <li>
    Only the six supported directive types are accepted.
  </li>
  <li>
    No frontend dashboard is included; Swagger UI is provided for API testing.
  </li>
  <li>
    No local or backup LLM provider is currently configured.
  </li>
</ul>

<hr>

<h2>🔐 Security</h2>

<ul>
  <li>API credentials are loaded through environment variables.</li>
  <li>Secrets are not included in the repository.</li>
  <li>LLM output is validated before reaching the optimizer.</li>
  <li>Malformed and unsupported directives are rejected.</li>
</ul>

<hr>

<h2>🎯 Core Architecture</h2>

<pre>
┌──────────────────────────┐
│   Human Operator Notes   │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│       OpenAI LLM         │
│  Natural Language → JSON │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│   Deterministic          │
│      Guardrails          │
│ Validate + Normalize     │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│     PuLP + CBC Solver    │
│   Minimum-Cost Schedule  │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│    24-Hour Energy Plan   │
└──────────────────────────┘
</pre>

<p align="center">
  <strong>⚡ Natural Language → Safe Directives → Optimized Energy</strong>
</p>

<hr>

<p align="center">
  <strong>⚡ GridWise LLM</strong>
  <br>
  <em>Making campus energy management smarter, safer and easier.</em>
</p>