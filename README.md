<div align="center">
  <img src="assets/banner.png" alt="FinAuditPro Banner" width="100%">

  # 🚀 FinAuditPro

  **The Next-Generation AI-Powered Executive Intelligence Platform for Audit Professionals.**

  [![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
  [![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg?style=for-the-badge&logo=githubactions)](https://github.com/aryanyadav/FinAuditPro/actions)
  [![GitHub stars](https://img.shields.io/github/stars/aryanyadav/FinAuditPro.svg?style=for-the-badge&logo=github)](https://github.com/aryanyadav/FinAuditPro/stargazers)
  [![Downloads](https://img.shields.io/github/downloads/aryanyadav/FinAuditPro/total?style=for-the-badge)](https://github.com/aryanyadav/FinAuditPro/releases)
  [![Latest Release](https://img.shields.io/github/v/release/aryanyadav/FinAuditPro?style=for-the-badge)](https://github.com/aryanyadav/FinAuditPro/releases)
  
  ![Platform Support](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg?style=for-the-badge)

  <br />
  <img src="assets/desktop_preview.png" alt="FinAuditPro Desktop App Preview" width="80%">
</div>

---

## 📖 About

### What is FinAuditPro?
FinAuditPro is an enterprise-grade, offline-first desktop application designed to revolutionize the financial auditing process. By combining cutting-edge local AI models (LLMs), Document Intelligence (OCR), and a strict Rule Engine, FinAuditPro automates the tedious aspects of auditing, allowing professionals to focus on high-level executive intelligence and risk analysis.

### Problem Statement
Traditional audits are heavily manual, paper-intensive, and prone to human error. Auditors spend countless hours extracting data from physical documents, manually verifying numbers, and compiling reports. Existing cloud-based solutions compromise client data privacy and require persistent internet connections.

### Why it was built
FinAuditPro was built to provide a zero-trust, privacy-first, offline AI solution for Chartered Accountants and Big 4 firms. We believe that highly sensitive financial data should never leave the auditor's local machine.

### Who is it for?
- **Chartered Accountants (CAs)**
- **Audit Partners & Managers**
- **Financial Analysts**
- **Enterprise Risk Teams**

### Key Benefits
- 🔒 **100% Offline Privacy**: All AI processing and data storage happens locally.
- ⚡ **Automated Intelligence**: Reduce audit time by up to 70% with AI-assisted document review.
- 📊 **Executive Insights**: Real-time dashboards and risk analytics.
- 🛡️ **Enterprise Security**: Role-Based Access Control (RBAC) and immutable audit trails.

---

## ✨ Features

| Category | Features |
| :--- | :--- |
| **🤖 AI** | Local LLM Integration (Ollama), Context-Aware Q&A, Anomaly Detection |
| **📄 OCR** | High-precision text extraction (PaddleOCR/Tesseract), Table parsing |
| **🔒 Security** | PBKDF2 Password Hashing, AES-256 Encryption, Immutable SQLite Audit Log, RBAC |
| **📑 Reporting** | ICAI-Standard PDF Generation, Excel/CSV Export, Dynamic Charting |
| **📈 Analytics** | Real-time CEO/Partner Dashboards, KPI Tracking, Risk Heatmaps |
| **⚙️ Workflow** | Automated Engagement Progress, Working Papers Management, Review Notes |
| **🖥️ Desktop UI** | Modern PySide6 Interface, Responsive Design, Dark Mode Support |
| **🔌 Offline Capability** | Local SQLite Database, Local Vector Store (FAISS), No Cloud Dependency |

---

## 🏗️ Architecture

### High-Level Architecture
FinAuditPro utilizes a robust multi-tier architecture, strictly adhering to Clean Architecture and SOLID principles. 

1. **Presentation Layer**: PySide6 (Qt) UI components.
2. **Service Layer**: Business logic, workflow orchestration, and security enforcement.
3. **Intelligence Layer**: OCR, Document Chunking, FAISS Vectorization, and LLM Inference.
4. **Data Layer**: SQLAlchemy ORM with a highly concurrent SQLite + WAL backend.

### Folders Structure
```text
FinAuditPro/
├── src/
│   ├── main.py                 # Application entry point & bootstrapping
│   ├── ui/                     # PySide6 Desktop Interface components
│   ├── services/               # Core business logic & controllers
│   ├── database/               # SQLAlchemy models & repositories
│   ├── security/               # Crypto, Authentication, RBAC, Audit Trails
│   ├── document_intelligence/  # OCR Engine & AI Pipeline
│   ├── analytics/              # Dashboard Engine & KPI metrics
│   ├── reporting/              # PDF/Excel Generation Engines
│   └── workflow/               # State machine for audit engagements
├── tests/                      # Comprehensive Unit & Integration Tests
├── assets/                     # Icons, images, and branding assets
├── data/                       # Local SQLite database (Generated at runtime)
└── requirements.txt            # Python dependencies
```

### AI Pipeline
1. **Upload**: User uploads PDF/Image financial documents.
2. **OCR**: PaddleOCR extracts raw text and layout information.
3. **Classification**: System classifies document type (Invoice, Ledger, Bank Statement).
4. **Embedding**: Text is chunked and embedded using local Transformer models.
5. **Vector Store**: Embeddings are indexed into a local FAISS database.
6. **LLM**: Local Ollama models analyze the context to find discrepancies.
7. **Rule Engine**: Hardcoded financial rules (e.g., GST mismatches) are evaluated against the data.
8. **Report**: AI findings and rule violations are compiled into the final Audit Report.

---

## 📸 Screenshots

| Login | Dashboard | Client Management |
| :---: | :---: | :---: |
| <img src="assets/screenshots/login.png" width="250"> | <img src="assets/screenshots/dashboard.png" width="250"> | <img src="assets/screenshots/clients.png" width="250"> |

| Document Upload | OCR & Vectorization | AI Analysis |
| :---: | :---: | :---: |
| <img src="assets/screenshots/upload.png" width="250"> | <img src="assets/screenshots/ocr.png" width="250"> | <img src="assets/screenshots/ai.png" width="250"> |

| Rule Engine | Working Papers | Reports |
| :---: | :---: | :---: |
| <img src="assets/screenshots/rules.png" width="250"> | <img src="assets/screenshots/working_papers.png" width="250"> | <img src="assets/screenshots/reports.png" width="250"> |

---

## 🚀 Installation

### Prerequisites
- Python 3.9 or higher
- Tesseract OCR (Optional, for fallback OCR)
- Ollama (Optional, for local AI capabilities)

### Using Git
```bash
# Clone the repository
git clone https://github.com/aryanyadav/FinAuditPro.git

# Navigate to the directory
cd FinAuditPro

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
PYTHONPATH=src python src/main.py
```

### Pre-built Binaries (Coming Soon)
- **Windows**: Download the `.exe` installer from the Releases page.
- **macOS**: Download the `.dmg` from the Releases page.
- **Linux**: Download the `.AppImage` from the Releases page.

---

## 🛠️ Technologies Used

- **Language**: Python 3.9+
- **GUI Framework**: PySide6 (Qt for Python)
- **Database**: SQLite with SQLAlchemy ORM
- **AI & NLP**: Ollama, Transformers
- **Document Processing**: PaddleOCR, PyMuPDF
- **Vector Search**: FAISS
- **Reporting**: ReportLab, Pandas, Matplotlib
- **Packaging**: PyInstaller

---

## 🗺️ Roadmap

- [x] **Version 1.0**: Core Offline Desktop App, SQLite Persistence, Basic OCR, Rule Engine, and AI Analysis.
- [ ] **Version 1.5**: Advanced Reporting Templates, Active Directory Integration, Team Collaboration via LAN.
- [ ] **Version 2.0**: Custom LLM Fine-Tuning for specific accounting standards (IFRS, GAAP), Web-based portal companion.
- [ ] **Future Features**: Real-time Bank API Integration, Automated Tax Filing extensions.

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/aryanyadav/FinAuditPro/issues).

Please read our [Contributing Guide](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md) before making a pull request.

---

## 📄 License
This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for more information.

---

## 👨‍💻 Author
**Aryan Yadav**
- GitHub: [@aryanyadav](https://github.com/aryanyadav)
- LinkedIn: [Aryan Yadav](https://linkedin.com/in/aryanyadav)
- Email: [contact@finauditpro.com](mailto:contact@finauditpro.com)

---

## 🙏 Acknowledgements
Special thanks to:
- The [PySide](https://wiki.qt.io/Qt_for_Python) team for an incredible GUI framework.
- The [Ollama](https://ollama.com/) community for democratizing local AI.
- The open-source OCR communities ([PaddlePaddle](https://github.com/PaddlePaddle/PaddleOCR), [Tesseract](https://github.com/tesseract-ocr/tesseract)).
- All the Chartered Accountants who provided valuable domain expertise during the design phase.

<div align="center">
Made with ❤️ by Aryan Yadav
</div>