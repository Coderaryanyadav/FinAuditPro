# Contributing to FinAuditPro

First off, thank you for considering contributing to FinAuditPro! It's people like you that make FinAuditPro such a great tool for the accounting community.

## 1. Where to Start

If you are looking for a good issue to start with, please check the following labels on our issue tracker:
- `good first issue`
- `help wanted`
- `documentation`

## 2. Setting Up Your Development Environment

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/FinAuditPro.git
   cd FinAuditPro
   ```
3. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Run the test suite** to ensure everything is working:
   ```bash
   PYTHONPATH=src python3 -m unittest discover -s tests
   ```

## 3. Making Changes

1. **Create a new branch** for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Make your changes**. Please ensure you adhere to our coding standards (PEP-8 for Python).
3. **Write tests** for your new code. FinAuditPro relies heavily on its test suite to prevent regressions.
4. **Run the test suite** again and ensure all tests pass.
5. **Commit your changes** using a descriptive commit message:
   ```bash
   git commit -m "feat: Add new advanced risk scoring algorithm"
   ```

## 4. Submitting a Pull Request (PR)

1. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
2. **Open a Pull Request** on the main FinAuditPro repository.
3. Fill out the **Pull Request Template** provided.
4. Wait for a maintainer to review your code. We may suggest some changes or improvements.

## 5. Coding Standards

- **SOLID Principles**: FinAuditPro heavily utilizes Clean Architecture. Please keep the UI, Services, and Repositories strictly decoupled.
- **Typing**: Use Python type hints (`typing` module) wherever possible.
- **Documentation**: All new classes and complex methods should have a concise docstring.
- **Offline-First**: Do NOT add any dependencies or API calls that require the application to connect to the internet (unless explicitly toggled by the user in a non-default setting).

## 6. Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). We expect all contributors to follow these guidelines to ensure a welcoming and inclusive environment.
