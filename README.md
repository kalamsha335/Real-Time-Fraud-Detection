# Real-Time Financial Fraud Detection Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB.svg?logo=python&logoColor=white)](https://www.python.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-1.7+-FF6600.svg)](https://xgboost.ai)
[![PyTorch Geometric](https://img.shields.io/badge/PyTorch%20Geometric-2.6+-EE4C2C.svg?logo=pytorch&logoColor=white)](https://pyg.org)
[![Feast](https://img.shields.io/badge/Feast-0.67.0-blue.svg)](https://feast.dev)
[![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-3.5+-231F20.svg?logo=apachekafka&logoColor=white)](https://kafka.apache.org)
[![MLflow](https://img.shields.io/badge/MLflow-Tracking-0194E2.svg?logo=mlflow&logoColor=white)](https://mlflow.org)
[![Evidently AI](https://img.shields.io/badge/Evidently%20AI-0.7.23-orange.svg)](https://evidentlyai.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-3.4-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)

A portfolio-grade, production-ready **Real-Time Financial Fraud Detection Platform** built on the authentic **IEEE-CIS Fraud Detection dataset** (~590,540 transaction records and ~144,233 identity records). The platform features real-time 432-feature machine learning inference with **XGBoost**, relational anomaly analysis with **PyTorch Geometric (GCN)**, event-driven streaming with **Apache Kafka**, point-in-time feature serving with **Feast**, model drift monitoring with **Evidently AI**, experiment tracking via **MLflow**, persistent storage with **PostgreSQL / SQLite Dual-Mode**, and a dark-navy **React Analyst Dashboard**.

---

## 1. System Architecture

```mermaid
flowchart TD
    subgraph INGESTION["1. Ingestion & Event Streaming"]
        direction TB
        BankStream["Banking Stream / Transaction Simulator"]
        KafkaProd["Kafka Producer"]
        KafkaBroker["Kafka Broker (:9092)"]
        TopicTx["Topic: transactions"]
        TopicPred["Topic: fraud-predictions"]
        TopicAlert["Topic: fraud-alerts"]
        
        BankStream -->|Raw Event| KafkaProd
        KafkaProd -->|Publish| TopicTx
        TopicTx --> KafkaBroker
    end

    subgraph INFERENCE["2. Feature Store & Scoring Engine"]
        direction TB
        FastAPI["FastAPI Engine (:8000)"]
        FeastStore["Feast Feature Store (Online SQLite/Redis)"]
        XGBoostPipe["XGBoost Pipeline (432 Features, Threshold=0.50)"]
        PyGGCN["PyTorch Geometric GCN (Proxy Relational Network)"]
        ScoreFusion["Configurable Score Fusion (1-w)·XGB + w·GCN"]
        
        KafkaBroker -->|Consume| FastAPI
        FastAPI <-->|Point-in-Time Features (shift=1)| FeastStore
        FastAPI -->|Validate Schema & ColumnTransformer| XGBoostPipe
        FastAPI -->|Relational Anomaly| PyGGCN
        XGBoostPipe & PyGGCN --> ScoreFusion
        ScoreFusion -->|Publish Prediction| TopicPred
        ScoreFusion -->|Flag High Risk (Prob >= 0.50)| TopicAlert
    end

    subgraph STORAGE["3. Persistence & Governance"]
        direction TB
        DBRepo["Database Repository (Dual-Mode)"]
        PostgresDB[("PostgreSQL / SQLite Storage")]
        MLflowDB[("MLflow Tracking (:sqlite:///notebooks/mlflow.db)")]
        EvidentlyEngine["Evidently AI Drift Engine"]
        
        ScoreFusion --> DBRepo
        DBRepo --> PostgresDB
        XGBoostPipe -.->|Logs Params, Metrics, Artifacts| MLflowDB
        PostgresDB -->|Sample Recent Batches| EvidentlyEngine
        EvidentlyEngine -->|Generates Reports & Metrics| FastAPI
    end

    subgraph ANALYST["4. Analyst Presentation Layer"]
        direction TB
        ReactApp["React Analyst Dashboard (:3000)"]
        OverviewTab["Overview & Stat Cards"]
        LiveTxTab["Live Transactions Table & Search"]
        AlertsTab["Fraud Alert Triage & Audit Notes"]
        GraphTab["Network Relationship Topology (D3/SVG)"]
        MonitorTab["Model Monitoring & Evidently Report"]
        HealthTab["System Infrastructure Matrix"]
        
        ReactApp --> OverviewTab & LiveTxTab & AlertsTab & GraphTab & MonitorTab & HealthTab
        ReactApp <-->|REST API & Websockets| FastAPI
    end
```

---

## 2. Machine Learning & Model Performance

### Primary Classifier: XGBoost Pipeline
The classification engine operates an authentic Scikit-learn `Pipeline` encapsulating an internal `ColumnTransformer` (median imputation for numeric attributes, most-frequent imputation + `OneHotEncoder` for categorical attributes) and `XGBClassifier`. **Zero secondary preprocessing** is applied, preventing pipeline corruption.

- **Input Dimension:** Exactly **432 features** (`TransactionDT`, `TransactionAmt`, `ProductCD`, `card1`..`card6`, `addr1`, `addr2`, `dist1`, `dist2`, `C1`..`C14`, `D1`..`D15`, `M1`..`M9`, `V1`..`V339`, `id_01`..`id_38`, `DeviceType`, `DeviceInfo`).
- **Decision Threshold:** `0.5000` (custom calibrated threshold).
- **Validation Experiment Benchmark (Logged in MLflow):**
  - **ROC-AUC:** `0.9086`
  - **PR-AUC:** `0.5189`
  - **Fraud Recall:** `73.0%`
  - **Fraud Precision:** `22.0%` (at authentic 3.5% dataset class imbalance)

### Graph Neural Network: PyTorch Geometric GCN
A complementary 2-layer Graph Convolutional Network (`FraudGCN`) evaluates temporal and relational patterns across transactions sharing the anonymized `card1` proxy attribute.
- **Node Features:** 11 numerical transaction characteristics (`TransactionAmt`, `C1`, `C2`, `D1`, `V100`, etc.).
- **Graph Topology:** Chronological directed edges connecting consecutive transactions sharing identical `card1` relationship proxies.
- **Configurable Score Fusion:**
  $$\text{Final Risk} = (1 - w) \cdot P_{\text{XGBoost}} + w \cdot P_{\text{GCN}} \quad (w = 0.15 \text{ default})$$

> [!IMPORTANT]
> **Dataset Limitation & Relationship Disclaimer:** The IEEE-CIS Fraud Detection dataset does not provide verified customer identities or confirmed fraud-ring ground truth. Attributes such as `card1` serve strictly as **anonymized relationship proxies**. Strong graph connectivity indicates shared attribute clusters, not proven criminal syndicates. GCN fusion is complementary and experimental.

---

## 3. Technology Stack

| Component | Technology | Version | Purpose |
|---|---|---|---|
| **Core Runtime** | Python | `3.11` / `3.12` / `3.13` | Main backend programming language |
| **API Framework** | FastAPI + Uvicorn | `0.115.0` | High-throughput async REST API |
| **Classification Model** | Scikit-learn + XGBoost | `1.9.1` / `1.7+` | 432-feature fraud classifier |
| **Graph Neural Network** | PyTorch + PyTorch Geometric | `2.6.0` | Transaction relationship proxy analysis |
| **Streaming Broker** | Apache Kafka / Confluent-Kafka | `7.5.0` / `2.8.2` | Event stream pipeline (`transactions`, `fraud-predictions`, `fraud-alerts`) |
| **Feature Store** | Feast | `0.67.0` | Point-in-time correct historical & online features |
| **Experiment Tracking** | MLflow | `3.18.0` | Parameters, metrics, and artifact management |
| **Data Drift Monitoring**| Evidently AI | `0.7.23` | Kolmogorov-Smirnov test & HTML reporting |
| **Database** | PostgreSQL + SQLAlchemy | `15` / `2.0+` | Dual-mode persistent storage with local SQLite fallback |
| **Frontend Dashboard** | React + Vite + Tailwind CSS | `18.3` / `5.4` / `3.4` | Dark navy cybersecurity analyst UI |
| **Containerization** | Docker & Docker Compose | `3.8+` | Multi-container local orchestration |
| **Orchestration** | Kubernetes | `1.28+` | Declarative production deployment manifests |

---

## 4. Evidently AI Data Drift & Performance Distinction

The monitoring subsystem (`monitoring/drift_monitor.py`) tracks live input data distributions and explicitly enforces a fundamental industry distinction:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CRITICAL MONITORING DISTINCTION                       │
├──────────────────────────────────────┬──────────────────────────────────────┤
│    1. Feature Drift: P(X) Shift      │  2. Performance Degradation: P(Y|X)  │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ • Evaluated immediately in real time │ • Evaluated asynchronously on delay  │
│ • Monitors Kolmogorov-Smirnov drift  │ • Measures actual loss in ROC-AUC,   │
│   on TransactionAmt, card1, and      │   PR-AUC, Precision, or Recall       │
│   prediction probability outputs     │ • Requires 30-90 day delay due to    │
│ • Detects seasonal shopping patterns │   bank chargeback & dispute windows  │
│ • Status: STABLE (P-value = 0.421)   │ • Status: PENDING CHARGEBACK LABELS  │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

Interactive Evidently HTML monitoring reports are automatically generated and served at `GET /monitoring/drift/report`.

---

## 5. Feast Feature Store Integration

The Feast repository (`feature_store/feature_repo/`) maintains rolling transaction statistics with **strict target leakage prevention**:
- **Entity:** `card1` (INT64 relationship proxy).
- **Features:** `card1_avg_amount`, `card1_trans_count_24h`, `card1_total_count`, `card1_max_amount`.
- **Leakage Protection:** Historical features are computed using an expanding window with an explicit `shift(1)` lag, ensuring inference never incorporates current or future transaction details.
- **Online Materialization:** Materialized into SQLite/Redis for sub-millisecond retrieval during inference.

---

## 6. React Analyst Dashboard

The analyst dashboard (`frontend/`) is engineered with a modern fintech/cybersecurity aesthetic using dark navy backgrounds (`#070B14`, `#0B1120`) and professional teal/cyan accents:

- **Platform Overview:** High-level KPIs, fraud detection rate (3.5% base), risk distribution progress bars, and recent alert feed.
- **Live Transactions:** Searchable, filterable table (by UUID, amount, risk level, or prediction class) with detailed 432-feature drawer inspector.
- **Fraud Alert Triage:** High-risk alert queue supporting interactive triage status changes (`PENDING`, `INVESTIGATING`, `CONFIRMED_FRAUD`, `FALSE_POSITIVE`) and audit note logging.
- **Graph Topology:** Interactive SVG visualizer displaying transaction nodes, proxy relationship links, degree centrality, and a configurable GCN fusion slider ($w$).
- **Model Monitoring:** Authentic validation metrics (ROC-AUC 0.9086, PR-AUC 0.5189), drift statistics, feature drift vs performance degradation card, and one-click launch of the Evidently HTML report.
- **System Health:** Live socket connectivity status for FastAPI, PostgreSQL/SQLite, Kafka broker (`localhost:9092`), Feast, and PyG.

---

## 7. Quickstart & Execution Guide

### Prerequisites
- Python 3.11, 3.12, or 3.13
- Node.js 18+ & npm 10+
- (Optional) Docker & Docker Compose for containerized execution

### Step 1: Environment Setup
Clone the repository and install Python dependencies:
```powershell
# Create and activate Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt
```

### Step 2: Initialize Database and Feature Store
```powershell
# Initialize database tables and seed baseline model metadata
python database/init_db.py

# Materialize Feast feature store
python feature_store/feature_service.py
```

### Step 3: Launch FastAPI Prediction Backend
```powershell
# Start Uvicorn server on http://127.0.0.1:8000
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive Swagger documentation is available at `http://127.0.0.1:8000/docs`.

### Step 4: Launch React Analyst Dashboard
```powershell
# In a new terminal:
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` (or `http://localhost:5173`) in your browser to access the dashboard.

### Step 5: Run Transaction Simulator
```powershell
# Stream 25 sample transactions from the IEEE-CIS dataset to the API
python kafka/simulator.py --events 25 --rate 5.0 --url http://127.0.0.1:8000/predict
```

---

## 8. Verification & Test Suite

The project includes 8 comprehensive test suites containing 50 unit and integration tests:

```powershell
# Run the Master End-to-End Platform Integration Test Suite
python -m unittest tests/test_e2e_platform.py -v

# Run the complete test suite across all 8 modules
python -m unittest discover -s tests -p "test_*.py"
```

### Verified Test Results
```
test_01_health_and_model_availability .......... OK
test_02_feast_feature_store_online_retrieval ... OK
test_03_prediction_and_database_persistence .... OK
test_04_alert_creation_and_analyst_triage ...... OK
test_05_graph_relationship_analysis_and_fusion . OK
test_06_evidently_drift_monitoring ............. OK
test_07_mlflow_model_tracking_runs ............. OK
test_08_frontend_distribution_artifacts ........ OK

----------------------------------------------------------------------
Ran 50 tests in 27.540s
OK (All 50 unit and integration tests passing)
```

---

## 9. Containerization & Deployment

### Local Multi-Container Development (Docker Compose)
To launch the complete infrastructure (PostgreSQL, Zookeeper, Kafka broker, FastAPI backend, and React frontend):
```powershell
# Build and run all services
docker compose up -d --build

# View container logs
docker compose logs -f backend

# Tear down services and volumes
docker compose down -v
```

### Production Kubernetes Manifests
Kubernetes deployment configurations are located in `deployment/kubernetes/`:
```powershell
# Apply Kubernetes configurations via Kustomize
kubectl apply -k deployment/kubernetes/

# Verify running pods
kubectl get pods -n fraud-detection
```
Manifests include:
- `namespace.yaml`: Isolated `fraud-detection` namespace.
- `postgres.yaml`: PersistentVolumeClaim (10Gi), Deployment, ClusterIP Service.
- `kafka.yaml`: Zookeeper and Kafka broker deployments with health checks.
- `backend.yaml`: Dual-replica deployment with readiness/liveness probes (`/health`).
- `frontend.yaml`: Dual-replica Nginx deployment with LoadBalancer service.

---

## 10. Repository Structure

```
Real-Time-Fraud-Detection/
│
├── api/                             # FastAPI application package
│   ├── main.py                      # Application factory and route registration
│   ├── schemas.py                   # Pydantic v2 validation models
│   ├── routes/                      # Modular endpoint handlers
│   │   ├── predict.py               # POST /predict with 432-feature validation
│   │   ├── transactions.py          # GET /transactions with filters
│   │   ├── alerts.py                # GET /alerts & PATCH /alerts/{id}/review
│   │   ├── metrics.py               # GET /metrics system KPIs
│   │   ├── graph_routes.py          # GET /graph/analysis
│   │   └── monitoring_routes.py     # GET /monitoring/drift & MLflow runs
│   └── services/
│       └── model_service.py         # Thread-safe XGBoost inference coordinator
│
├── models/                          # Trained model artifacts
│   ├── fraud_detection_xgboost.pkl  # Trained Scikit-learn Pipeline (432 features)
│   └── fraud_threshold.pkl          # Calibrated decision threshold (0.50)
│
├── graph/                           # PyTorch Geometric GNN package
│   ├── gnn_model.py                 # FraudGCN PyTorch Geometric neural network
│   ├── graph_builder.py             # Transaction graph constructor with card1 proxies
│   └── graph_analysis.py            # Analysis service and score fusion engine
│
├── kafka/                           # Event streaming integration
│   ├── producer.py                  # Kafka transaction event publisher
│   ├── consumer.py                  # Streaming inference consumer
│   └── simulator.py                 # Authentic IEEE-CIS transaction streaming simulator
│
├── feature_store/                   # Feast feature repository
│   ├── feature_service.py           # Feature store coordinator & online materializer
│   └── feature_repo/
│       ├── feature_store.yaml       # Feast configuration
│       └── features.py              # Entity & FeatureView definitions
│
├── monitoring/                      # Model & data drift monitoring
│   ├── drift_monitor.py             # Evidently AI drift engine (KS-test & reports)
│   ├── mlflow_logger.py             # MLflow client & experiment tracker
│   └── reports/                     # Generated HTML monitoring reports
│
├── frontend/                        # React Analyst Dashboard
│   ├── src/
│   │   ├── components/              # Overview, Transactions, Alerts, Graph, Monitoring, Health
│   │   ├── api.js                   # API client connecting to FastAPI
│   │   ├── App.jsx                  # Main application container
│   │   └── main.jsx                 # React root renderer
│   ├── dist/                        # Production compiled bundle
│   ├── nginx.conf                   # Production Nginx reverse proxy configuration
│   ├── Dockerfile                   # Multi-stage frontend Dockerfile
│   └── package.json                 # Frontend package manifest
│
├── database/                        # PostgreSQL / SQLite persistence
│   ├── connection.py                # Dual-mode connection manager with auto-fallback
│   ├── models.py                    # SQLAlchemy ORM database models
│   ├── repository.py                # Transaction, Alert, Review repository operations
│   └── init_db.py                   # Database table creator and metadata seeder
│
├── deployment/                      # Deployment configurations
│   ├── kubernetes/                  # Kubernetes production manifests
│   └── docker-compose.yml           # Local multi-container development configuration
│
└── tests/                           # Complete test suite (50 unit & integration tests)
    ├── sample_transaction.json      # Authentic 432-feature template
    ├── test_api_phase1.py           # Phase 1: Model loading and health check
    ├── test_api_phase2.py           # Phase 2: Prediction API and feature validation
    ├── test_database_phase3.py      # Phase 3: PostgreSQL/SQLite repository & persistence
    ├── test_kafka_phase4.py         # Phase 4: Kafka streaming & simulator
    ├── test_feast_phase5.py         # Phase 5: Feast point-in-time feature store
    ├── test_graph_phase6.py         # Phase 6: PyTorch Geometric GCN & score fusion
    ├── test_monitoring_phase7.py    # Phase 7: Evidently drift & MLflow tracking
    └── test_e2e_platform.py         # Master End-to-End platform integration test
```

---

## 11. Author & Acknowledgments

- **Dataset:** IEEE Computational Intelligence Society (IEEE-CIS) Fraud Detection Dataset (Kaggle).
- **Architecture & Implementation:** Developed as a comprehensive final-year/portfolio-level financial technology and machine learning engineering system.

