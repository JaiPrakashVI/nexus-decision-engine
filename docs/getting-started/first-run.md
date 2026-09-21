# NEXUS Quickstart & First Run Guide

This guide walks you through running the entire NEXUS platform from a fresh clone. Every command is explained so you understand what is happening under the hood.

---

## Step 1: Prerequisites
Ensure you have the following installed on your machine:
- **Python 3.11+** (Python 3.13 supported)
- **Node.js 18+** & npm
- **Docker & Docker Compose** (Optional for containerized mode, or run locally)

---

## Step 2: Clone & Configure Environment

```bash
# Clone the repository
git clone https://github.com/nexus-twin/nexus.git
cd nexus

# Copy the environment template to .env
cp .env.example .env
```
*What this does*: Creates your local `.env` configuration with safe default ports and settings for the Gateway, Redis, PostgreSQL/TimescaleDB, and the Simulator.

---

## Step 3: Set Up Python Virtual Environment

```bash
# Create Python virtual environment
python -m venv .venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Install core dependencies
pip install -r requirements.txt
```
*What this does*: Installs FastAPI, Uvicorn, SQLAlchemy, Redis, NetworkX, Scikit-Learn, Cryptography, and Pytest in an isolated environment.

---

## Step 4: Generate Cryptographic mTLS Certificates

```bash
python scripts/generate_certs.py
```
*What this does*: Generates a private Root Certificate Authority (`certs/ca.crt`), the Gateway Server TLS certificate with Subject Alternative Names (`certs/gateway.crt`), and mutual-TLS client certificates (`certs/device_001.crt`). It also generates a rogue CA (`certs/rogue_ca.crt`) for failure testing.

---

## Step 5: Run Automated Tests

```bash
pytest -v
```
*What this does*: Runs all 23 automated tests across unit validation, state reconstruction, anomaly detection, cascading failure simulation, decision logic, and chaos failure modes.

---

## Step 6: Start the Platform Services

You can start NEXUS via **Docker Compose** or **Local Standalone Mode**.

### Option A: Docker Compose (Full Stack)
```bash
docker compose up --build
```
*What this does*: Launches TimescaleDB, Redis, the Secure Gateway, the Stream Consumer, the Digital Twin API, and the React Dashboard in containerized networks with automated health checks.

### Option B: Local Standalone Development (Zero Docker Required!)
In local mode, NEXUS runs with SQLite and in-memory streams:

```bash
# Terminal 1: Start the Digital Twin API & In-Process Simulator
python -m digital_twin.api

# Terminal 2: Start the Operations Command Center Frontend
cd dashboard
npm install
npm run dev
```

---

## Step 7: Open the Operations Command Center
Open your browser and navigate to:
```
http://localhost:3000
```

You will see:
1. **Live Dashboard**: High-density system KPIs, active assets, and stream completeness.
2. **Digital Twin Dependency Graph**: Click nodes to inspect pressure, flow, and Bayesian confidence.
3. **Data Degradation Slider**: Dial packet loss from 0% up to 40% and watch state reconstruction seamlessly infer physical states!
4. **Cascading Failure Simulator**: Trigger controlled asset outages and observe discrete-event propagation.
5. **Decision Studio**: Watch the Deterministic Engine and Local Agentic AI ensemble formulate and validate recovery interventions.
