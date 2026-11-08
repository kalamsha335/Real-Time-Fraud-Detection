import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable
)
from reportlab.pdfgen import canvas

# Palette Definition
PRIMARY = colors.HexColor('#0F172A')       # Slate 900
SECONDARY = colors.HexColor('#1E293B')     # Slate 800
BRAND_INDIGO = colors.HexColor('#4F46E5')  # Indigo 600
BRAND_BLUE = colors.HexColor('#2563EB')    # Blue 600
ACCENT_CYAN = colors.HexColor('#0284C7')   # Sky 600
SUCCESS = colors.HexColor('#059669')       # Emerald 600
WARNING = colors.HexColor('#D97706')       # Amber 600
DANGER = colors.HexColor('#DC2626')        # Red 600
TEXT_MAIN = colors.HexColor('#1E293B')     # Slate 800
TEXT_MUTED = colors.HexColor('#64748B')    # Slate 500
BG_SUBTLE = colors.HexColor('#F8FAFC')     # Slate 50
BORDER_COLOR = colors.HexColor('#E2E8F0')  # Slate 200


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page numbers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(TEXT_MUTED)

        # Draw header on pages > 1
        if self._pageNumber > 1:
            self.drawString(
                40, letter[1] - 30,
                "Real-Time Financial Fraud Detection Platform — Comprehensive Technical Specification"
            )
            self.setStrokeColor(BORDER_COLOR)
            self.setLineWidth(0.5)
            self.line(40, letter[1] - 34, letter[0] - 40, letter[1] - 34)

        # Draw footer on all pages
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 40, 25, page_str)
        self.drawString(
            40, 25,
            "Confidential & Proprietary • Machine Learning & Security Engineering Architecture"
        )
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(40, 35, letter[0] - 40, 35)

        self.restoreState()


def build_pdf(filename="Real_Time_Fraud_Detection_Comprehensive_Documentation.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=BRAND_INDIGO,
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=BRAND_BLUE,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'Heading3_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=SECONDARY,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=TEXT_MAIN,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=TEXT_MAIN,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    table_body = ParagraphStyle(
        'TableBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=TEXT_MAIN
    )

    table_body_bold = ParagraphStyle(
        'TableBodyBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=PRIMARY
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=TEXT_MAIN
    )

    story = []

    # =========================================================================
    # DOCUMENT HEADER / TITLE BLOCK
    # =========================================================================
    story.append(Paragraph("Real-Time Financial Fraud Detection Platform", title_style))
    story.append(Paragraph(
        "Comprehensive End-to-End System Architecture, Tool Engineering & Industrial Deployment Specification",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_INDIGO, spaceBefore=0, spaceAfter=12))

    # Metadata Summary Box
    meta_data = [
        [
            Paragraph("<b>Target Domain:</b> Real-Time Payment Fraud Prevention", table_body),
            Paragraph("<b>Dataset Benchmark:</b> IEEE-CIS Fraud Detection (590K Records)", table_body)
        ],
        [
            Paragraph("<b>Primary Classifier:</b> XGBoost Pipeline (432 Features)", table_body),
            Paragraph("<b>Relational Analysis:</b> PyTorch Geometric GCN Module", table_body)
        ],
        [
            Paragraph("<b>Streaming Engine:</b> Apache Kafka Pub/Sub Clustering", table_body),
            Paragraph("<b>Feature Serving:</b> Feast Point-in-Time Feature Store", table_body)
        ],
        [
            Paragraph("<b>Governance & Audit:</b> MLflow Tracking & Evidently AI Drift Engine", table_body),
            Paragraph("<b>Persistence:</b> PostgreSQL / SQLite Dual-Mode Repository", table_body)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[260, 272])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_SUBTLE),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # =========================================================================
    # SECTION 1: MAIN GOAL & PROBLEM STATEMENT
    # =========================================================================
    story.append(Paragraph("1. Project Executive Summary & Core Objective", h1_style))
    story.append(Paragraph(
        "The primary mission of the <b>Real-Time Financial Fraud Detection Platform</b> is to solve the critical "
        "trade-off in modern electronic payments: preventing catastrophic financial loss from fraudulent transactions "
        "while guaranteeing sub-second latency and minimizing false declines for legitimate customers.",
        body_style
    ))
    story.append(Paragraph(
        "Traditional fraud auditing systems operate in <b>batch mode</b>—processing transactions hours or days after "
        "settlement. In modern card-not-present (CNP) e-commerce, instant bank transfers, and neobanking networks, "
        "delayed batch auditing arrives too late to intercept fund transfers. This platform intercepts, transforms, "
        "scores, and routes incoming transaction events in <b>real time (&asymp; 1.2 ms inference latency)</b>.",
        body_style
    ))

    story.append(Paragraph("Core Technical Challenges Addressed by the Platform:", h2_style))
    story.append(Paragraph(
        "• <b>Extreme Class Imbalance:</b> In real-world payment networks and the IEEE-CIS benchmark dataset, fraudulent "
        "events account for only approximately <b>3.5%</b> of all transactions. Conventional accuracy metrics are useless "
        "(a naive model predicting all transactions as legitimate would achieve 96.5% accuracy but catch 0% of fraud). "
        "The platform optimizes for <b>PR-AUC (0.5189)</b> and <b>Fraud Recall (73.0%)</b>.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>High-Dimensional Heterogeneous Data:</b> The platform strictly enforces the authentic <b>432-feature "
        "IEEE-CIS schema</b>, encompassing transactional amounts, card proxies (`card1`-`card6`), address distances, "
        "counting velocities (`C1`-`C14`), time deltas (`D1`-`D15`), and Vesta engineered features (`V1`-`V339`).",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Relational Anomaly Patterns:</b> Modern fraudsters rarely operate with isolated single cards; they deploy "
        "automated scripts, botnets, and shared proxy attributes. The platform incorporates a <b>Graph Neural Network (GCN)</b> "
        "to evaluate relational neighborhood density alongside tabular XGBoost classification.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Continuous Production Drift:</b> Fraud patterns shift rapidly due to consumer holidays, market fluctuations, "
        "and fraudster adaptation. The platform integrates continuous data drift monitoring via <b>Evidently AI</b> and "
        "lifecycle experiment tracking via <b>MLflow</b>.",
        bullet_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 2: STEP-BY-STEP PLATFORM WORKFLOW
    # =========================================================================
    story.append(Paragraph("2. End-to-End System Architecture: Step-by-Step Flow", h1_style))
    story.append(Paragraph(
        "The platform executes an 8-stage pipeline from raw transaction ingestion to human-in-the-loop analyst triage:",
        body_style
    ))

    steps_data = [
        [
            Paragraph("Stage", table_header),
            Paragraph("Subsystem Component", table_header),
            Paragraph("Operational Mechanism & Data Transformation", table_header),
            Paragraph("Latency / SLA", table_header)
        ],
        [
            Paragraph("<b>Step 1</b>", table_body_bold),
            Paragraph("Real-Time Ingestion (Kafka / Simulator)", table_body),
            Paragraph("Incoming payments arrive via REST or Apache Kafka. Raw events publish to the <code>transactions</code> topic. A multi-threaded simulator generates authentic IEEE-CIS payloads.", table_body),
            Paragraph("&lt; 5 ms", table_body)
        ],
        [
            Paragraph("<b>Step 2</b>", table_body_bold),
            Paragraph("Feature Store (Feast)", table_body),
            Paragraph("Feast retrieves point-in-time correct aggregates (24h card spending velocity, historical mean amount) using a strict shift(1) offset to eliminate future data leakage.", table_body),
            Paragraph("&lt; 3 ms", table_body)
        ],
        [
            Paragraph("<b>Step 3</b>", table_body_bold),
            Paragraph("Tabular Inference (XGBoost Pipeline)", table_body),
            Paragraph("Validates strict 432-feature contract. ColumnTransformer applies SimpleImputer (median for numeric, mode for categorical) and OneHotEncoder. XGBoost computes fraud probability P(XGB).", table_body),
            Paragraph("&asymp; 1.2 ms", table_body)
        ],
        [
            Paragraph("<b>Step 4</b>", table_body_bold),
            Paragraph("Graph Relationship (PyG GCN)", table_body),
            Paragraph("Builds dynamic edges connecting transactions sharing anonymized `card1` proxies. 2-layer GCN computes relational anomaly score S(GCN). Blends via formula: Score = (1-w)·P + w·S.", table_body),
            Paragraph("&lt; 15 ms", table_body)
        ],
        [
            Paragraph("<b>Step 5</b>", table_body_bold),
            Paragraph("Risk Stratification & Cutoff", table_body),
            Paragraph("Compares score against decision threshold (&tau; = 0.50). Categorizes into Low Risk (&lt;0.30), Medium Risk (0.30-0.50), or High Risk (&ge;0.50).", table_body),
            Paragraph("&lt; 0.1 ms", table_body)
        ],
        [
            Paragraph("<b>Step 6</b>", table_body_bold),
            Paragraph("Dual-Mode Persistence", table_body),
            Paragraph("Persists raw transaction, model probability, latency, and status in PostgreSQL (production) or local SQLite (standalone). Flagged high-risk events trigger security alert records.", table_body),
            Paragraph("&lt; 4 ms", table_body)
        ],
        [
            Paragraph("<b>Step 7</b>", table_body_bold),
            Paragraph("Analyst Triage (React UI)", table_body),
            Paragraph("Surfaces alerts to the SOC dashboard. Fraud analysts inspect full 432-feature vector, view graph topology, add investigation notes, and update review status.", table_body),
            Paragraph("Real-Time", table_body)
        ],
        [
            Paragraph("<b>Step 8</b>", table_body_bold),
            Paragraph("Governance & Drift (Evidently/MLflow)", table_body),
            Paragraph("Runs two-sample Kolmogorov-Smirnov test on numerical distributions. Distinguishes immediate input feature drift P(X) from delayed 30-90 day chargeback degradation P(Y|X).", table_body),
            Paragraph("Periodic / Async", table_body)
        ]
    ]

    steps_table = Table(steps_data, colWidths=[45, 110, 315, 62])
    steps_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_INDIGO),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_SUBTLE]),
        ('PADDING', (0, 0), (-1, -1), 4.5),
    ]))
    story.append(steps_table)
    story.append(Spacer(1, 14))

    # =========================================================================
    # SECTION 3: TOOL-BY-TOOL TECHNICAL BREAKDOWN
    # =========================================================================
    story.append(Paragraph("3. Deep-Dive Tool Breakdown: How Each Tool Works Under the Hood", h1_style))
    story.append(Paragraph(
        "Every tool in the platform's technology stack was selected to satisfy specific latency, throughput, and "
        "governance requirements. Below is the operational analysis for each subsystem:",
        body_style
    ))

    tools_info = [
        ("XGBoost (Extreme Gradient Boosting)",
         "Primary Machine Learning Classifier",
         "XGBoost constructs an ensemble of shallow decision trees in a sequential boosting framework. For each new tree, it calculates the gradient and hessian of the binary log-loss objective function to determine optimal split points across the 432 input features. In this platform, XGBoost is wrapped inside a Scikit-Learn Pipeline with ColumnTransformer, SimpleImputer, and OneHotEncoder. It handles non-linear interactions, severe feature missingness, and high cardinality without manual feature pruning, achieving an ROC-AUC of 0.9086 and inference latency of ~1.2 ms."),

        ("PyTorch Geometric (PyG)",
         "Graph-Based Relationship Anomaly Detection",
         "PyTorch Geometric is a specialized deep learning library for graph-structured data. In this platform, it models transactions as nodes and shared attributes (specifically anonymized `card1` proxies) as directed edges. The 2-layer FraudGCN network executes spatial message passing: node representations are iteratively updated by aggregating the feature vectors of their immediate neighborhood. This allows the model to compute a relational anomaly score S(GCN) to determine whether a transaction is part of an abnormally dense cluster of suspicious activity."),

        ("Apache Kafka",
         "Distributed Real-Time Event Streaming",
         "Apache Kafka provides an asynchronous, horizontally partitioned commit log for high-throughput event processing. The platform configures three discrete topics: `transactions` (ingesting raw inbound payment streams), `fraud-predictions` (broadcasting scored inferences), and `fraud-alerts` (queueing high-risk events for investigation). Kafka decouples the payment ingestion gateway from the compute-intensive inference engines, guaranteeing zero message loss even during burst payment traffic."),

        ("Feast (Feature Store)",
         "Point-in-Time Correct Feature Serving",
         "Feast (Feature Store) acts as the centralized feature repository ensuring consistency between historical training data and real-time inference. It manages feature entities, definitions, and data sources. In this project, Feast serves aggregated velocity features (e.g. 24-hour transaction count, average amount for a cardholder proxy). To prevent future data leakage during training, Feast enforces point-in-time correctness with a strict shift(1) offset, ensuring features only incorporate events that occurred before the transaction timestamp."),

        ("MLflow",
         "Lifecycle Management & Experiment Registry",
         "MLflow logs model parameters, training hyperparameters, evaluation metrics (ROC-AUC, PR-AUC, Precision, Recall), and serialized binary model artifacts. The platform connects to an SQLite-backed tracking database (`sqlite:///mlflow.db`). MLflow provides immutable versioning for deployed pipelines, enabling automated audits, model lineage tracking, and rollback capabilities without manual file management."),

        ("Evidently AI",
         "Statistical Data Drift & Model Monitoring",
         "Evidently AI performs continuous distribution monitoring on production inference traffic. It executes a two-sample Kolmogorov-Smirnov (K-S) statistical test comparing recent transaction batches against a 500-row baseline reference set. It evaluates feature distribution shifts P(X) on numerical variables (e.g. `TransactionAmt`, prediction probabilities) and generates an interactive HTML diagnostic report."),

        ("FastAPI & Uvicorn",
         "High-Performance Asynchronous REST Engine",
         "FastAPI serves as the API gateway running on top of Starlette and the Uvicorn ASGI server. It uses Pydantic schemas for data validation, enforcing all 432 IEEE-CIS features at the request boundary. FastAPI handles asynchronous non-blocking I/O, allowing simultaneous transaction scoring, telemetry polling, and alert updates with sub-5 millisecond response times."),

        ("PostgreSQL & SQLite (Dual-Mode)",
         "Relational Persistence & Fallback Architecture",
         "The platform uses SQLAlchemy ORM to manage five relational tables: `transactions`, `predictions`, `fraud_alerts`, `model_metadata`, and `analyst_reviews`. It implements an automatic Dual-Mode connection engine: if a production PostgreSQL cluster is unreachable or credentials fail, it falls back to local SQLite (`database/fraud_detection.db`) with zero downtime."),

        ("React & Tailwind CSS",
         "Analyst Operations Center & SOC Dashboard",
         "The front-end analyst dashboard is built with React 18, Vite, and Tailwind CSS. It features a dark slate/carbon fintech aesthetic, modular views (Overview KPIs, Live Ledger, Alert Triage Workspace, SVG Graph Visualizer, Model Monitoring, System Health), and an interactive Transaction Stream Simulator.")
    ]

    for tool_name, tool_role, tool_desc in tools_info:
        story.append(Paragraph(f"<b>{tool_name}</b> — <i>{tool_role}</i>", h2_style))
        story.append(Paragraph(tool_desc, body_style))
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 4: ADVANTAGES & DISADVANTAGES (TECHNICAL TRADEOFFS)
    # =========================================================================
    story.append(Paragraph("4. Technical Advantages, Disadvantages & Engineering Trade-Offs", h1_style))
    story.append(Paragraph(
        "Every production machine learning architecture involves architectural trade-offs. The table below provides "
        "a rigorous, balanced evaluation of the platform's strengths and operational constraints:",
        body_style
    ))

    tradeoffs_data = [
        [
            Paragraph("Subsystem", table_header),
            Paragraph("Key Advantages & Strengths", table_header),
            Paragraph("Disadvantages & Technical Constraints", table_header)
        ],
        [
            Paragraph("<b>XGBoost Classifier</b>", table_body_bold),
            Paragraph("• State-of-the-art tabular performance (ROC-AUC 0.9086)<br/>• Fast inference (~1.2 ms)<br/>• Native handling of missing values and mixed categorical/numerical types", table_body),
            Paragraph("• Strictly requires all 432 input features<br/>• Static decision trees cannot automatically learn graph topological features without explicit engineering", table_body)
        ],
        [
            Paragraph("<b>PyTorch Geometric GCN</b>", table_body_bold),
            Paragraph("• Detects coordinated relational anomalies across shared cards<br/>• Captures structural neighborhood risk beyond individual row data", table_body),
            Paragraph("• Higher computational overhead (~15 ms)<br/>• IEEE-CIS dataset limitations: `card1` is an anonymized proxy, not verified human identity", table_body)
        ],
        [
            Paragraph("<b>Apache Kafka Streaming</b>", table_body_bold),
            Paragraph("• High-throughput decoupled architecture<br/>• Zero event loss via distributed partitioned commit logs<br/>• Independent scaling of producers and consumers", table_body),
            Paragraph("• Operational infrastructure complexity<br/>• Requires Zookeeper or KRaft cluster management and persistent disk storage", table_body)
        ],
        [
            Paragraph("<b>Feast Feature Store</b>", table_body_bold),
            Paragraph("• Guarantees training-serving feature consistency<br/>• Point-in-time correctness prevents future data leakage<br/>• Low-latency online feature retrieval", table_body),
            Paragraph("• Added serialization overhead<br/>• Parquet file synchronization requires background batch materialization pipelines", table_body)
        ],
        [
            Paragraph("<b>Dual-Mode Persistence</b>", table_body_bold),
            Paragraph("• Resilience: Zero-configuration fallback to SQLite ensures local demos and offline testing never crash", table_body),
            Paragraph("• SQLite lacks multi-process concurrency locks under extreme high-write loads compared to distributed PostgreSQL", table_body)
        ],
        [
            Paragraph("<b>Evidently AI Drift Suite</b>", table_body_bold),
            Paragraph("• Real-time statistical distribution tracking (K-S test)<br/>• Decoupled input drift detection without waiting for delayed labels", table_body),
            Paragraph("• Statistical drift does not prove accuracy degradation; false drift alarms can trigger on normal holiday volume surges", table_body)
        ]
    ]

    tradeoffs_table = Table(tradeoffs_data, colWidths=[100, 215, 217])
    tradeoffs_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_INDIGO),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_SUBTLE]),
        ('PADDING', (0, 0), (-1, -1), 4.5),
    ]))
    story.append(tradeoffs_table)
    story.append(Spacer(1, 14))

    # =========================================================================
    # SECTION 5: REAL-WORLD INDUSTRY EXECUTION
    # =========================================================================
    story.append(Paragraph("5. How to Execute This in Real-World Enterprise Problems", h1_style))
    story.append(Paragraph(
        "Deploying this architecture in a tier-1 payment processor, card network, or banking infrastructure requires "
        "integrating with payment rails, regulatory standards, and security operations workflows:",
        body_style
    ))

    story.append(Paragraph("A. Regulatory & Compliance Architecture (PCI-DSS & Tokenization)", h2_style))
    story.append(Paragraph(
        "In production, raw Primary Account Numbers (PANs), CVVs, and cardholder PII must never be stored in plain text. "
        "The ingestion gateway tokenizes card numbers into cryptographically salted surrogate tokens (such as `card1_token`) "
        "before persisting to PostgreSQL. The entire platform operates inside a PCI-DSS certified Virtual Private Cloud (VPC) "
        "with TLS 1.3 encryption in transit and AES-256 encryption at rest.",
        body_style
    ))

    story.append(Paragraph("B. The 4-Tier Automated Customer Verification Loop", h2_style))
    story.append(Paragraph(
        "Manual telephone calls to customers for every flagged transaction do not scale. Real-world banks use a "
        "tiered automated confirmation hierarchy triggered by the model's risk stratification score:",
        body_style
    ))
    story.append(Paragraph(
        "1. <b>Tier 1: Instant In-App Biometric Push Notification (80% of checks):</b> A FaceID/fingerprint prompt pops up "
        "on the user's banking app: <i>'Did you attempt $422.50 at Merchant X? [Yes] [No]'</i>. Tapping 'Yes' automatically "
        "resolves the alert as `FALSE_POSITIVE` in under 3 seconds.",
        bullet_style
    ))
    story.append(Paragraph(
        "2. <b>Tier 2: Interactive Two-Way SMS (15% of checks):</b> If no smartphone app is active, an automated SMS gateway "
        "sends: <i>'Did you spend $49.09 on card 1392? Reply 1 for YES, 2 for NO'</i>.",
        bullet_style
    ))
    story.append(Paragraph(
        "3. <b>Tier 3: Automated IVR Phone Dialing (4% of checks):</b> Computerized voice call prompts customer: <i>'Press 1 to "
        "authorize, press 2 to report stolen'</i>.",
        bullet_style
    ))
    story.append(Paragraph(
        "4. <b>Tier 4: Live Human Fraud Analyst Intervention (&lt; 1% of checks):</b> Reserved exclusively for high-value corporate "
        "wire transfers (&gt; $10,000) or high-risk profile changes.",
        bullet_style
    ))

    story.append(Paragraph("C. Managing the 30-to-90 Day Bank Chargeback Lag", h2_style))
    story.append(Paragraph(
        "In financial payments, true ground-truth fraud labels arrive with a <b>30 to 90 day delay</b> due to cardholder dispute "
        "and bank chargeback cycles. The platform handles this via a two-speed feedback loop: "
        "<b>Speed 1 (Immediate):</b> Evidently AI monitors input distribution shifts P(X) on live traffic. "
        "<b>Speed 2 (Retrospective):</b> Settled chargebacks update the database with true labels `isFraud = 1`, triggering "
        "an automated retraining pipeline in MLflow to refresh XGBoost weights.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 6: RESEARCH & DATASET DISCLAIMER
    # =========================================================================
    story.append(Paragraph("6. Academic & Research Disclaimer: IEEE-CIS Dataset Limitations", h1_style))
    
    disclaimer_text = (
        "<b>Mandatory Technical Disclaimer & Ethical Boundaries:</b><br/>"
        "The IEEE-CIS Fraud Detection benchmark dataset was released by Vesta Corporation with personally identifiable "
        "information (PII) deliberately removed to protect consumer privacy. The dataset does not provide verified "
        "customer identities or explicit fraud syndicate labels. All graph relationships in this platform use <code>card1</code> "
        "as an <b>anonymized relationship proxy</b>. High graph connectivity indicates shared attribute patterns, "
        "<i>not proven criminal syndicates</i>. The PyTorch Geometric GCN model serves as a complementary graph analysis "
        "module alongside XGBoost, using a configurable fusion weight (&tau; = 0.50, w = 0.15) to maintain accountable, "
        "interpretable predictions."
    )
    disclaimer_table = Table([[Paragraph(disclaimer_text, callout_style)]], colWidths=[532])
    disclaimer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF3C7')), # Amber 100
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#F59E0B')),    # Amber 500
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(disclaimer_table)
    story.append(Spacer(1, 14))

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    return filename


if __name__ == '__main__':
    out_pdf = "Real_Time_Fraud_Detection_Comprehensive_Documentation.pdf"
    res = build_pdf(out_pdf)
    print(f"Generated PDF successfully: {res} ({os.path.getsize(res)} bytes)")

