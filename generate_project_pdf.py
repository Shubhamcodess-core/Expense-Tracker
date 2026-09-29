import sys
import os
import shutil
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
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
        self.setFillColor(colors.HexColor("#64748B"))

        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "ExpenseIQ & ML Expense Analyzer — Comprehensive Project Documentation")
            self.drawRightString(612 - 54, 755, "System Architecture & API / ML Reference")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 748, 612 - 54, 748)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 42, 612 - 54, 42)

        self.drawString(54, 30, "ExpenseIQ Technical Reference • Personal Finance & Machine Learning Suite")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 30, page_str)
        self.restoreState()

def build_pdf(filename="ExpenseIQ_Project_Overview.pdf"):
    target_path = os.path.join(os.path.dirname(__file__), filename)
    doc = SimpleDocTemplate(
        target_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#0F172A")    # Deep Navy Slate
    c_blue = colors.HexColor("#1D4ED8")       # Rich Blue
    c_indigo = colors.HexColor("#4338CA")     # Indigo
    c_slate = colors.HexColor("#334155")      # Text Dark Slate
    c_muted = colors.HexColor("#64748B")      # Secondary Slate
    c_bg_light = colors.HexColor("#F8FAFC")   # Light gray table bg
    c_bg_header = colors.HexColor("#0F172A")  # Dark Header
    c_border = colors.HexColor("#E2E8F0")     # Light border
    c_emerald = colors.HexColor("#047857")    # Accent Green

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=23,
        leading=27,
        textColor=c_primary,
        spaceAfter=5
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=c_muted,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=c_blue,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=c_primary,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=c_slate,
        spaceAfter=5
    )

    callout_style = ParagraphStyle(
        'DocCallout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11.5,
        textColor=c_indigo,
    )

    th_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.white
    )

    td_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10.5,
        textColor=c_slate
    )

    td_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10.5,
        textColor=c_primary
    )

    td_code = ParagraphStyle(
        'TableCellCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7,
        leading=9.5,
        textColor=colors.HexColor("#0F766E")
    )

    td_muted = ParagraphStyle(
        'TableCellMuted',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7,
        leading=9.5,
        textColor=c_muted
    )

    story = []

    # ─────────────────────────────────────────────────────────────
    # PAGE 1: TITLE, META, EXECUTIVE SUMMARY & TECH STACK
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("EXPENSEIQ & ML EXPENSE ANALYZER", title_style))
    story.append(Paragraph("Comprehensive Technical Documentation • Architecture Overview • Complete API & Machine Learning Reference", subtitle_style))

    # Meta Info Card Table
    meta_data = [
        [
            Paragraph("<b>Project Name:</b> ExpenseIQ & ML Suite", td_style),
            Paragraph("<b>Architecture:</b> Full-Stack Web + Python ML", td_style),
            Paragraph("<b>Documentation Date:</b> " + datetime.now().strftime("%B %d, %Y"), td_style)
        ],
        [
            Paragraph("<b>Frontend:</b> HTML5, CSS3, Vanilla JS (ES6+)", td_style),
            Paragraph("<b>Backend Server:</b> Node.js & Express REST API", td_style),
            Paragraph("<b>Machine Learning:</b> Scikit-Learn, XGBoost, LightGBM", td_style)
        ],
        [
            Paragraph("<b>Persistence:</b> Local CSV (Atomic Sync)", td_style),
            Paragraph("<b>Server URL:</b> http://localhost:3000", td_style),
            Paragraph("<b>Target Platform:</b> Windows 10/11, macOS, Linux", td_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[170, 165, 169])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # 1. Executive Summary
    story.append(Paragraph("1. Executive Summary & System Architecture", h1_style))
    story.append(Paragraph(
        "<b>ExpenseIQ</b> is an enterprise-grade personal finance tracking and intelligent predictive analytics platform. "
        "It combines a high-performance, zero-latency full-stack web application for day-to-day transaction bookkeeping with a "
        "modular Python Machine Learning pipeline for spending forecasting, customer segmentation clustering, and fraud/anomaly "
        "detection. The system guarantees full data sovereignty by storing all transaction records locally in an RFC 4180-compliant "
        "CSV database (<code>data/expenses.csv</code>), avoiding dependence on external proprietary database engines.",
        body_style
    ))

    arch_box_data = [
        [
            Paragraph(
                "<b>Dual-Core System Architecture Overview:</b><br/>"
                "• <b>Full-Stack Web App:</b> Responsive HTML5/CSS3/ES6+ UI powered by an Express.js backend on Port 3000 with real-time currency conversion.<br/>"
                "• <b>Storage Engine:</b> Automatic CSV synchronization (<code>data/expenses.csv</code>) with write locks and atomic file swap protection.<br/>"
                "• <b>Python ML Engine:</b> 4-stage machine learning pipeline covering Classification, Regression, Clustering, and Anomaly Detection.<br/>"
                "• <b>Desktop Automation:</b> Native Windows batch scripts (<code>start.bat</code> and <code>stop.bat</code>) for zero-config one-click execution.",
                callout_style
            )
        ]
    ]
    arch_box = Table(arch_box_data, colWidths=[504])
    arch_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EEF2FF")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#C7D2FE")),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(arch_box)
    story.append(Spacer(1, 8))

    # 2. Complete Technology Stack
    story.append(Paragraph("2. Complete Technology Stack & Specifications", h1_style))
    story.append(Paragraph(
        "The project emphasizes clean, vanilla foundations to ensure maximum runtime speed, long-term maintainability, and zero bloat:",
        body_style
    ))

    tech_data = [
        [Paragraph("Layer / Subsystem", th_style), Paragraph("Technology / Tool", th_style), Paragraph("Version / Origin", th_style), Paragraph("Role & Key Responsibilities", th_style)],
        [
            Paragraph("<b>Frontend Markup</b>", td_bold),
            Paragraph("HTML5 Semantic", td_style),
            Paragraph("W3C Standard", td_style),
            Paragraph("Accessible DOM structure, modals, forms, tables, metric cards, dashboard grid.", td_style)
        ],
        [
            Paragraph("<b>Frontend Styling</b>", td_bold),
            Paragraph("CSS3 (Vanilla)", td_style),
            Paragraph("Custom System", td_style),
            Paragraph("Custom color tokens, responsive CSS grid/flexbox, glassmorphism, zero Tailwind bloat.", td_style)
        ],
        [
            Paragraph("<b>Frontend Logic</b>", td_bold),
            Paragraph("JavaScript (ES6+)", td_style),
            Paragraph("Native Browser", td_style),
            Paragraph("Asynchronous API fetch client, state management, budget meter, multi-currency engine.", td_style)
        ],
        [
            Paragraph("<b>Data Visualization</b>", td_bold),
            Paragraph("Chart.js", td_style),
            Paragraph("v4.4 (CDN)", td_style),
            Paragraph("Interactive Bar, Doughnut, and Line charts showing category & monthly spending.", td_style)
        ],
        [
            Paragraph("<b>Typography</b>", td_bold),
            Paragraph("Inter Font Family", td_style),
            Paragraph("Google Fonts", td_style),
            Paragraph("Modern geometric sans-serif typeface loaded across weights 300 to 800.", td_style)
        ],
        [
            Paragraph("<b>Backend Server</b>", td_bold),
            Paragraph("Node.js & Express.js", td_style),
            Paragraph("v18+ / v4.18+", td_style),
            Paragraph("RESTful API provider, static asset host on port 3000, request validation, CORS.", td_style)
        ],
        [
            Paragraph("<b>Data Persistence</b>", td_bold),
            Paragraph("CSV Engine", td_style),
            Paragraph("RFC 4180 Format", td_style),
            Paragraph("Auto-managed <code>data/expenses.csv</code> with atomic temp-swap and write-queue locks.", td_style)
        ],
        [
            Paragraph("<b>Desktop Scripting</b>", td_bold),
            Paragraph("Windows Batch", td_style),
            Paragraph("cmd.exe scripts", td_style),
            Paragraph("<code>start.bat</code> & <code>stop.bat</code> with port 3000 detection and auto-browser opening.", td_style)
        ],
        [
            Paragraph("<b>ML & Data Science</b>", td_bold),
            Paragraph("Python, Pandas, NumPy", td_style),
            Paragraph("Python 3.8+", td_style),
            Paragraph("Data cleaning, feature engineering, statistical transformations, matrix computations.", td_style)
        ],
        [
            Paragraph("<b>Machine Learning</b>", td_bold),
            Paragraph("Scikit-Learn, XGBoost, LightGBM", td_style),
            Paragraph("Latest PyPI", td_style),
            Paragraph("Classification, regression, unsupervised clustering, isolation forest anomaly detection.", td_style)
        ],
        [
            Paragraph("<b>CLI & Plotting</b>", td_bold),
            Paragraph("Matplotlib & Seaborn", td_style),
            Paragraph("Python Libs", td_style),
            Paragraph("Interactive visualization for Python CLI tool (<code>expense_tracker.py</code>).", td_style)
        ]
    ]

    tech_table = Table(tech_data, colWidths=[85, 110, 85, 224])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_bg_header),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 10))

    # ─────────────────────────────────────────────────────────────
    # SECTION 3: COMPLETE API INVENTORY
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("3. Complete API Inventory & Integration Map", h1_style))
    story.append(Paragraph(
        "The project integrates exactly <b>7 distinct APIs</b> (3 External Cloud/Web Services and 4 Internal REST Endpoints "
        "comprising 6 HTTP Route Methods):",
        body_style
    ))

    api_summary_data = [
        [
            Paragraph("<b>Total API Count:</b> 7 APIs (3 External Cloud Services + 4 Core Internal Endpoints)", td_bold),
            Paragraph("<b>Protocols & Formats:</b> HTTP/HTTPS • REST • JSON • CSV Streaming", td_bold)
        ]
    ]
    api_summary_table = Table(api_summary_data, colWidths=[300, 204])
    api_summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEF3C7")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#FDE68A")),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(api_summary_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("A. External Web & Cloud APIs (3 Services)", h2_style))
    ext_api_data = [
        [Paragraph("API / Service Name", th_style), Paragraph("Endpoint URL / URI", th_style), Paragraph("File & Line Location", th_style), Paragraph("Purpose, Request & Error Handling", th_style)],
        [
            Paragraph("<b>Live Currency Exchange Rates API</b>", td_bold),
            Paragraph("<code>https://open.er-api.com/v6/latest/{base}</code>", td_code),
            Paragraph("<code>script.js</code><br/>Lines 304–326 (<code>fetchExchangeRates</code>)", td_style),
            Paragraph(
                "• <b>Base Currency:</b> INR (Indian Rupee)<br/>"
                "• <b>Data:</b> Live exchange rates for 30+ world currencies (USD, EUR, GBP, JPY, CAD, AUD, etc.).<br/>"
                "• <b>Caching:</b> Persisted in <code>localStorage['expenseiq_rates_cache']</code> with timestamp.<br/>"
                "• <b>Resilience:</b> If offline or rate limit fails, shows warning toast and maintains base currency values.",
                td_style
            )
        ],
        [
            Paragraph("<b>Google Fonts API</b>", td_bold),
            Paragraph("<code>fonts.googleapis.com</code><br/><code>fonts.gstatic.com</code>", td_code),
            Paragraph("<code>index.html</code><br/>Lines 8–10", td_style),
            Paragraph(
                "• <b>Purpose:</b> Dynamically serves the high-legibility 'Inter' web font (weights 300 to 800).<br/>"
                "• <b>Optimization:</b> Preconnect headers included for sub-millisecond font rendering.",
                td_style
            )
        ],
        [
            Paragraph("<b>Chart.js CDN API</b>", td_bold),
            Paragraph("<code>cdn.jsdelivr.net/npm/chart.js</code>", td_code),
            Paragraph("<code>index.html</code><br/>Line 12", td_style),
            Paragraph(
                "• <b>Purpose:</b> Injects the Canvas-based financial chart rendering engine.<br/>"
                "• <b>Usage:</b> Generates category doughnut breakdown and monthly expenditure bar charts.",
                td_style
            )
        ]
    ]

    ext_api_table = Table(ext_api_data, colWidths=[100, 140, 100, 164])
    ext_api_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_indigo),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(ext_api_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("B. Internal Node.js Backend REST Endpoints (4 Endpoints / 6 Methods)", h2_style))
    int_api_data = [
        [Paragraph("Method & Endpoint", th_style), Paragraph("Handler in server.js", th_style), Paragraph("Consumer in script.js", th_style), Paragraph("Operation & Business Logic", th_style)],
        [
            Paragraph("<b>GET</b> <code>/api/expenses</code>", td_code),
            Paragraph("Lines 161–170<br/><code>readAllExpenses()</code>", td_style),
            Paragraph("Lines 204–222<br/><code>loadExpenses()</code>", td_style),
            Paragraph("Reads <code>data/expenses.csv</code>, strips UTF-8 BOM, validates headers, and returns JSON array of all transactions.", td_style)
        ],
        [
            Paragraph("<b>POST</b> <code>/api/expenses</code>", td_code),
            Paragraph("Lines 212–234<br/>Single creation", td_style),
            Paragraph("Lines 387–420<br/><code>addExpense()</code>", td_style),
            Paragraph("Validates date (YYYY-MM-DD), positive amount, currency, and category. Appends row to CSV using atomic write lock.", td_style)
        ],
        [
            Paragraph("<b>PUT</b> <code>/api/expenses/:id</code>", td_code),
            Paragraph("Lines 250–275<br/>Record update", td_style),
            Paragraph("Lines 490–525<br/><code>updateExpense()</code>", td_style),
            Paragraph("Locates expense by ID, updates properties in-memory, and writes updated dataset to CSV with atomic replace.", td_style)
        ],
        [
            Paragraph("<b>DELETE</b> <code>/api/expenses/:id</code>", td_code),
            Paragraph("Lines 278–292<br/>Record deletion", td_style),
            Paragraph("Lines 530–555<br/><code>confirmDelete()</code>", td_style),
            Paragraph("Filters out deleted expense by ID. Returns 404 if not found. Serializes remaining records to CSV.", td_style)
        ],
        [
            Paragraph("<b>POST</b> <code>/api/expenses/bulk</code>", td_code),
            Paragraph("Lines 173–209<br/>Bulk insert/merge", td_style),
            Paragraph("CSV Import & JSON Restore functions", td_style),
            Paragraph("Accepts array of expenses. Supports <code>mode='replace'</code> or <code>mode='merge'</code>. Validates each row and bulk-saves.", td_style)
        ],
        [
            Paragraph("<b>GET</b> <code>/api/expenses/export</code>", td_code),
            Paragraph("Lines 237–247<br/>File streamer", td_style),
            Paragraph("Export CSV Button (direct download)", td_style),
            Paragraph("Sets <code>Content-Type: text/csv</code> and attachment disposition to trigger instant browser download.", td_style)
        ]
    ]

    int_api_table = Table(int_api_data, colWidths=[110, 95, 100, 199])
    int_api_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_bg_header),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(int_api_table)

    # ─────────────────────────────────────────────────────────────
    # PAGE 3 & 4: MACHINE LEARNING MODELS & ALGORITHMS
    # ─────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("4. Machine Learning Models, Algorithms & Analytics Suite", h1_style))
    story.append(Paragraph(
        "Located in the <code>ML_Expense_Analyzer/</code> package and <code>expense_tracker.py</code>, the system implements "
        "a comprehensive suite of <b>14 distinct Machine Learning algorithms</b> across 4 functional domains, paired with "
        "an end-to-end NLP and feature engineering pipeline:",
        body_style
    ))

    ml_data = [
        [Paragraph("ML Domain / Task", th_style), Paragraph("Algorithm / Model Name", th_style), Paragraph("Library / Class", th_style), Paragraph("Hyperparameters & Business Role", th_style)],
        
        # Classification
        [
            Paragraph("<b>1. Expense Categorization</b><br/>(Multi-Class Classification)", td_bold),
            Paragraph("<b>Random Forest Classifier</b>", td_style),
            Paragraph("<code>sklearn.ensemble.<br/>RandomForestClassifier</code>", td_code),
            Paragraph("• <code>n_estimators=100, n_jobs=-1</code><br/>• Predicts category (Food, Travel, Bills, etc.) from transaction text/amount with ensemble bagging.", td_style)
        ],
        [
            Paragraph("Expense Categorization", td_muted),
            Paragraph("<b>XGBoost Classifier</b>", td_style),
            Paragraph("<code>xgboost.XGBClassifier</code>", td_code),
            Paragraph("• <code>n_estimators=100, eval_metric='logloss'</code><br/>• Extreme gradient boosted decision trees for non-linear feature interactions.", td_style)
        ],
        [
            Paragraph("Expense Categorization", td_muted),
            Paragraph("<b>LightGBM Classifier</b>", td_style),
            Paragraph("<code>lightgbm.LGBMClassifier</code>", td_code),
            Paragraph("• <code>n_estimators=100, verbose=-1</code><br/>• Fast histogram-based gradient boosting optimized for categorical features.", td_style)
        ],
        [
            Paragraph("Expense Categorization", td_muted),
            Paragraph("<b>Support Vector Machine (SVM)</b>", td_style),
            Paragraph("<code>sklearn.svm.SVC</code>", td_code),
            Paragraph("• <code>kernel='rbf', probability=True</code><br/>• High-dimensional margin maximization with probability calibration.", td_style)
        ],
        [
            Paragraph("Expense Categorization", td_muted),
            Paragraph("<b>Neural Network (MLP)</b>", td_style),
            Paragraph("<code>sklearn.neural_network.<br/>MLPClassifier</code>", td_code),
            Paragraph("• <code>hidden_layer_sizes=(100, 50), max_iter=500</code><br/>• Multi-layer Perceptron deep classifier with Adam optimizer.", td_style)
        ],

        # Regression
        [
            Paragraph("<b>2. Expense Forecasting</b><br/>(Continuous Regression)", td_bold),
            Paragraph("<b>Ridge Regression</b> (L2)", td_style),
            Paragraph("<code>sklearn.linear_model.<br/>Ridge</code>", td_code),
            Paragraph("• <code>alpha=1.0</code><br/>• Regularized linear regression preventing multicollinearity in temporal features.", td_style)
        ],
        [
            Paragraph("Expense Forecasting", td_muted),
            Paragraph("<b>Lasso Regression</b> (L1)", td_style),
            Paragraph("<code>sklearn.linear_model.<br/>Lasso</code>", td_code),
            Paragraph("• <code>alpha=0.1</code><br/>• Sparsity-inducing regression performing automated feature selection.", td_style)
        ],
        [
            Paragraph("Expense Forecasting", td_muted),
            Paragraph("<b>Gradient Boosting Regressor</b>", td_style),
            Paragraph("<code>sklearn.ensemble.<br/>GradientBoostingRegressor</code>", td_code),
            Paragraph("• <code>n_estimators=100, learning_rate=0.1</code><br/>• Sequential residual reduction for future monthly spending projections.", td_style)
        ],
        [
            Paragraph("Expense Forecasting", td_muted),
            Paragraph("<b>XGBoost Regressor</b>", td_style),
            Paragraph("<code>xgboost.XGBRegressor</code>", td_code),
            Paragraph("• <code>n_estimators=100</code><br/>• Advanced tree pruning regression for seasonal volatility forecasting.", td_style)
        ],

        # Clustering
        [
            Paragraph("<b>3. Spending Discovery</b><br/>(Unsupervised Clustering)", td_bold),
            Paragraph("<b>K-Means Clustering</b>", td_style),
            Paragraph("<code>sklearn.cluster.<br/>KMeans</code>", td_code),
            Paragraph("• <code>n_clusters=5, n_init=10</code><br/>• Segments spending behavior into distinct clusters (e.g. weekend splurges, bills).", td_style)
        ],
        [
            Paragraph("Spending Discovery", td_muted),
            Paragraph("<b>DBSCAN Clustering</b>", td_style),
            Paragraph("<code>sklearn.cluster.<br/>DBSCAN</code>", td_code),
            Paragraph("• <code>eps=0.5, min_samples=5</code><br/>• Density-based clustering that isolates irregular spending outliers as noise (-1).", td_style)
        ],

        # Anomaly Detection
        [
            Paragraph("<b>4. Fraud & Outlier Detection</b><br/>(Anomaly Detection)", td_bold),
            Paragraph("<b>Isolation Forest</b>", td_style),
            Paragraph("<code>sklearn.ensemble.<br/>IsolationForest</code>", td_code),
            Paragraph("• <code>contamination=0.05, n_jobs=-1</code><br/>• Isolates anomalous transactions by measuring path depth in random partition trees.", td_style)
        ],
        [
            Paragraph("Fraud & Outlier Detection", td_muted),
            Paragraph("<b>One-Class SVM</b>", td_style),
            Paragraph("<code>sklearn.svm.OneClassSVM</code>", td_code),
            Paragraph("• <code>nu=0.05, kernel='rbf'</code><br/>• Maps transactions to feature space to establish a normal-spending decision boundary.", td_style)
        ],

        # Feature Engineering NLP
        [
            Paragraph("<b>5. Feature Engineering</b><br/>(NLP & Representations)", td_bold),
            Paragraph("<b>TF-IDF Vectorizer</b>", td_style),
            Paragraph("<code>sklearn.feature_extraction.<br/>text.TfidfVectorizer</code>", td_code),
            Paragraph("• <code>ngram_range=(1,2), max_features=100</code><br/>• Converts unstructured merchant and note text into numeric TF-IDF vectors.", td_style)
        ]
    ]

    ml_table = Table(ml_data, colWidths=[105, 115, 110, 174])
    ml_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_emerald),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(ml_table)
    story.append(Spacer(1, 8))

    # Feature Engineering Detail Card
    feat_card = [
        [
            Paragraph(
                "<b>Feature Engineering Pipeline (<code>src/features/engineer.py</code>):</b><br/>"
                "• <b>Temporal Features:</b> <code>day_of_week</code>, <code>month</code>, <code>is_weekend</code>, <code>day_of_month</code>, <code>quarter</code>, <code>is_month_end</code>.<br/>"
                "• <b>Amount Transformations:</b> <code>log_amount</code> (log1p to normalize skewness), z-score deviation from category mean.<br/>"
                "• <b>Categorical Encoders:</b> <code>OneHotEncoder</code> and <code>LabelEncoder</code> for multi-category indicators.<br/>"
                "• <b>Scalers:</b> <code>StandardScaler</code> fitted on training partitions to ensure zero-mean and unit-variance.",
                callout_style
            )
        ]
    ]
    feat_table = Table(feat_card, colWidths=[504])
    feat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ECFDF5")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#A7F3D0")),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(feat_table)

    # ─────────────────────────────────────────────────────────────
    # PAGE 5: STORAGE, AUTOMATION, MANIFEST & CONCLUSION
    # ─────────────────────────────────────────────────────────────
    story.append(PageBreak())

    # 5. Data Storage & CSV Concurrency Architecture
    story.append(Paragraph("5. Data Storage & CSV Concurrency Architecture", h1_style))
    storage_data = [
        [Paragraph("Aspect", th_style), Paragraph("Specification", th_style), Paragraph("Implementation Details & Guarantees", th_style)],
        [
            Paragraph("<b>CSV Schema</b>", td_bold),
            Paragraph("<code>id,date,amount,currency,category,note</code>", td_code),
            Paragraph("Strict 6-column format. Amounts stored as decimal numbers, dates as ISO <code>YYYY-MM-DD</code>.", td_style)
        ],
        [
            Paragraph("<b>RFC 4180 Escaping</b>", td_bold),
            Paragraph("<code>csvEscape()</code> & <code>parseCsvLine()</code>", td_code),
            Paragraph("Guarantees correct handling of embedded commas, quotes (escaped as <code>\"\"</code>), and multiline notes.", td_style)
        ],
        [
            Paragraph("<b>Atomic Replacement</b>", td_bold),
            Paragraph("Temp file write + rename", td_code),
            Paragraph("Writes new data to <code>expenses.csv.tmp</code> then atomically renames to <code>expenses.csv</code> via <code>fs.renameSync</code>.", td_style)
        ],
        [
            Paragraph("<b>Write Serialization</b>", td_bold),
            Paragraph("Promise Chain Lock", td_code),
            Paragraph("A serial <code>writeLock = writeLock.then(...)</code> guarantees concurrent HTTP requests cannot corrupt the CSV.", td_style)
        ],
        [
            Paragraph("<b>UTF-8 BOM Protection</b>", td_bold),
            Paragraph("Byte Order Mark Sanitizer", td_code),
            Paragraph("Automatically detects and strips UTF-8 BOM (<code>0xFEFF</code>) on file reads to prevent CSV header parse errors.", td_style)
        ]
    ]

    storage_table = Table(storage_data, colWidths=[110, 140, 254])
    storage_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_bg_header),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(storage_table)
    story.append(Spacer(1, 6))

    # 6. Desktop Automation Scripts
    story.append(Paragraph("6. Automation Scripts & Execution Workflow", h1_style))
    scripts_data = [
        [Paragraph("Script Name", th_style), Paragraph("Command Line / Action", th_style), Paragraph("Internal Behavior & Technical Features", th_style)],
        [
            Paragraph("<b>start.bat</b><br/>(or <code>start_server.bat</code>)", td_bold),
            Paragraph("Double-click in Explorer or run <code>start.bat</code>", td_code),
            Paragraph(
                "1. Verifies Node.js exists in PATH.<br/>"
                "2. Checks if port 3000 is active. If active, opens browser immediately.<br/>"
                "3. Launches Express backend in titled window: <code>Personal Expense Tracker Server</code>.<br/>"
                "4. Pauses for socket initialization and automatically opens <code>http://localhost:3000</code>.",
                td_style
            )
        ],
        [
            Paragraph("<b>stop.bat</b><br/>(or <code>stop_server.bat</code>)", td_bold),
            Paragraph("Double-click in Explorer or run <code>stop.bat</code>", td_code),
            Paragraph(
                "1. Scans active network connections via <code>netstat -ano</code> for port <code>3000</code>.<br/>"
                "2. Extracts PID and executes <code>taskkill /F /T /PID &lt;PID&gt;</code> to terminate the process.<br/>"
                "3. Closes any leftover console windows titled <code>Personal Expense Tracker Server</code>.<br/>"
                "4. Displays status confirmation and safely releases port 3000.",
                td_style
            )
        ]
    ]

    scripts_table = Table(scripts_data, colWidths=[120, 140, 244])
    scripts_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_indigo),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(scripts_table)
    story.append(Spacer(1, 6))

    # 7. Complete Project Directory Manifest
    story.append(Paragraph("7. Complete Directory Tree & File Inventory", h1_style))
    dir_data = [
        [Paragraph("Path / File", th_style), Paragraph("Size / Type", th_style), Paragraph("Component Role in Project", th_style)],
        [Paragraph("<code>d:\\Project\\index.html</code>", td_code), Paragraph("20 KB / HTML5", td_style), Paragraph("Main web application structure, forms, modals, tables, metrics.", td_style)],
        [Paragraph("<code>d:\\Project\\style.css</code>", td_code), Paragraph("34 KB / CSS3", td_style), Paragraph("Design system, responsive layout, CSS variables, dark/light aesthetics.", td_style)],
        [Paragraph("<code>d:\\Project\\script.js</code>", td_code), Paragraph("72 KB / JS", td_style), Paragraph("Frontend state management, Chart.js bindings, exchange rate fetcher, API client.", td_style)],
        [Paragraph("<code>d:\\Project\\server\\server.js</code>", td_code), Paragraph("12 KB / Node.js", td_style), Paragraph("Express.js REST backend, CSV engine, atomic file writer on port 3000.", td_style)],
        [Paragraph("<code>d:\\Project\\data\\expenses.csv</code>", td_code), Paragraph("CSV Data", td_style), Paragraph("Primary local persistence storage containing all transaction records.", td_style)],
        [Paragraph("<code>d:\\Project\\start.bat</code>", td_code), Paragraph("1.3 KB / Batch", td_style), Paragraph("One-click Windows launcher with auto browser opener.", td_style)],
        [Paragraph("<code>d:\\Project\\stop.bat</code>", td_code), Paragraph("0.8 KB / Batch", td_style), Paragraph("One-click Windows server terminator by port PID lookup.", td_style)],
        [Paragraph("<code>d:\\Project\\expense_tracker.py</code>", td_code), Paragraph("23 KB / Python", td_style), Paragraph("Standalone CLI expense manager with Matplotlib chart generation.", td_style)],
        [Paragraph("<code>d:\\Project\\ML_Expense_Analyzer\\</code>", td_code), Paragraph("Python Package", td_style), Paragraph("Machine Learning pipeline (Classification, Regression, Clustering, Outliers).", td_style)],
        [Paragraph("<code>d:\\Project\\package.json</code>", td_code), Paragraph("0.5 KB / JSON", td_style), Paragraph("Node.js dependency manifest (<code>express</code>, <code>npm start</code>).", td_style)],
        [Paragraph("<code>d:\\Project\\README.md</code>", td_code), Paragraph("2.0 KB / Markdown", td_style), Paragraph("End-user quick start guide and project instructions.", td_style)]
    ]

    dir_table = Table(dir_data, colWidths=[150, 85, 269])
    dir_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_bg_header),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(dir_table)
    story.append(Spacer(1, 6))

    # 8. Conclusion
    story.append(Paragraph("8. Architectural Assessment & Conclusion", h1_style))
    story.append(Paragraph(
        "The ExpenseIQ platform achieves an optimal balance between simplicity, user experience, and analytical sophistication. "
        "By coupling a lightweight, dependency-free web interface with an Express-backed atomic CSV storage layer and an advanced Python Machine Learning "
        "ecosystem, the platform provides zero cloud overhead, guaranteed offline data privacy, instant startup, and predictive "
        "intelligence. This document provides the complete, authoritative technical specification for the entire project.",
        body_style
    ))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated: {target_path}")

    # Also make a copy as Project_Documentation.pdf
    alt_path = os.path.join(os.path.dirname(__file__), "Project_Documentation.pdf")
    shutil.copyfile(target_path, alt_path)
    print(f"Successfully generated copy: {alt_path}")

if __name__ == '__main__':
    filename = sys.argv[1] if len(sys.argv) > 1 else "ExpenseIQ_Project_Overview.pdf"
    build_pdf(filename)
