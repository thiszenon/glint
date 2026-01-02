# glint

# Glint ✨

**Your Personal & Private Tech Watch Assistant**

Glint is a privacy-first, local-orchestrated tool designed for developers and tech enthusiasts to stay updated with the latest trends across multiple platforms. It aggregates data from various technical and scientific sources, filters them based on your interests, and presents them through a powerful CLI and a sleek, modern GUI.

---

## 🚀 Key Features

- **Privacy-First**: All data is stored locally in an SQLite database. No external tracking or cloud dependency for your data.
- **Multi-Source Aggregation**: Integrated with GitHub, HackerNews, Reddit, Dev.to, ProductHunt, ArXiv, Semantic Scholar, and OpenAlex.
- **Dual Interface**:
  - **Terminal-First CLI**: Fast and efficient for power users.
  - **Modern GUI**: A beautiful dashboard for a more visual experience.
- **Intelligent Filtering**: Automated relevance scoring and topic-based categorization.
- **Local-First Notifications**: Desktop alerts for new trends in your favorite topics.

---

## 📂 Project Structure

```text
glint/
├── src/glint/
│   ├── cli/         # Typer-powered CLI commands
│   ├── core/        # Core logic: Database, Storage, Notifier, Logging
│   ├── gui/         # CustomTkinter Desktop Application
│   ├── sources/     # Fetchers for various platforms (GitHub, HN, etc.)
│   ├── web/         # Flask-based web dashboard
│   ├── utils/       # Shared utility functions
│   └── assets/      # Icons, logos, and UI assets
├── tests/           # Comprehensive test suite
├── pyproject.toml   # Project dependencies and metadata
└── README.md        # This file!
```

---

## 🛠️ Getting Started

### Prerequisites

- Python 3.8+
- Recommended: A virtual environment (`venv` or `conda`)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/thiszenon/glint.git
   cd glint
   ```

2. **Install dependencies in editable mode**:
   ```bash
   pip install -e .
   ```

3. **Initialize the database**:
   ```bash
   glint init
   ```

---

## 📖 How to Use Glint

### 1. Configure Your Topics
Glint tracks topics you care about. Add some to get started:
```bash
glint add "Artificial Intelligence"
glint add "Python Programming"
```

### 2. Fetch Latest Trends
Update your local database with fresh data from all sources:
```bash
glint fetch
```

### 3. View Trends (CLI)
See what's happening directly in your terminal:
```bash
glint show
```

### 4. Interactive Dashboard (GUI & Web)

> [!NOTE]
> The interactive dashboard is currently in an experimental phase and is being refined for a future stable release. Frontend developers who wish to contribute to the UI/UX are welcome to explore and improve these components!

To launch the experimental experience:
```bash
# Simply run the command without arguments
glint
```
This will open the Glint Dashboard in your browser and start the background notification daemon. Alternatively, use the `glint-gui.bat` if you are on Windows.

---

### 5. API Keys Configuration (Optional)

Glint works perfectly out-of-the-box without any keys. However, for higher rate limits on sources like GitHub or Reddit, you can optionally add your own keys:

```bash
# Example: Setting a GitHub token
glint config secrets set github_token YOUR_TOKEN_HERE
```

For a detailed walkthrough, check out the [API Keys Setup Guide](docs/API_KEYS_SETUP.md).

---

## 🤝 Contributing

We welcome contributions from both frontend and backend developers!

### For Backend Developers
- **Adding a New Source**: Check `src/glint/sources/base.py` for the BaseFetcher class. Implement a new fetcher in a separate file and register it in `sources/__init__.py`.
- **Core Logic**: Improvements to relevance scoring, database migrations, or the notification engine.

### For Frontend Developers
- **Web Dashboard**: The web UI is built with **Flask** and standard **HTML/CSS/JS**. Templates are located in `src/glint/web/templates`.
- **Desktop GUI**: Built using **CustomTkinter**. If you're into Python GUI development, explore `src/glint/gui`.

### Development Setup
```bash
pip install -e ".[dev]"
```

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Created with ❤️ by [Jonathan KABONGA NYATA](https://github.com/thiszenon)

---
[see the user interface UX](docs/glint_ux.png)
