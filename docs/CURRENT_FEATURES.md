# Glint - Current Features & Capabilities

> **Version**: 0.1.0  
> **Last Updated**: December 6, 2025  
> **Status**: Active Development

---

## Table of Contents

- [Overview](#overview)
- [Core Capabilities](#core-capabilities)
- [Architecture](#architecture)
- [CLI Commands](#cli-commands)
- [Database Schema](#database-schema)
- [Data Sources](#data-sources)
- [How It Works](#how-it-works)
- [Configuration](#configuration)
- [Future Features](#future-features)

---

## Overview

**Glint** is a **100% local, privacy-first tech watch assistant** that helps developers stay updated on new tools, frameworks, and tech trends without relying on cloud services or requiring account creation.

### Key Principles

- ✅ **Privacy First**: All data stored locally in SQLite database
- ✅ **No Accounts**: No registration, no cloud sync, no tracking
- ✅ **Personalized**: Topic-based filtering with relevance scoring
- ✅ **Desktop Native**: System tray integration with desktop notifications
- ✅ **Cross-Platform**: Works on Windows, macOS, and Linux

---

## Core Capabilities

### 1. Topic Management

**Watch specific technologies and frameworks:**
- Add/remove topics (e.g., "python", "react", "kubernetes")
- Toggle topics between Active/Inactive states
- Delete topics with CASCADE deletion (removes all associated trends)
- Topics support unique naming and timestamp tracking

**Topic States:**
- **Active**: Receives notifications, trends visible in GUI/CLI
- **Inactive**: Still fetches trends (standby mode), but hidden from view
- **Deleted**: Permanently removed with ML data export for future training

### 2. Trend Fetching & Aggregation

**Automated content discovery from multiple sources:**

| Source | What It Fetches | Quality Filters |
|--------|----------------|-----------------|
| **GitHub** | Trending repositories, new releases | Min 50 stars, quality heuristics |
| **Hacker News** | Top stories, discussions | Upvote threshold, relevance matching |
| **Reddit** | Tech subreddit posts | Min 10 upvotes, engagement metrics |
| **Dev.to** | Developer articles | Reaction count, reading time |

**Smart Deduplication:**
- URL normalization (http/https, www, trailing slashes)
- Content fingerprinting to avoid duplicate stories from different sources
- Duplicate detection across fetch sessions

### 3. Relevance Scoring

**AI-powered scoring system (0.0 - 1.0) based on:**

| Factor | Weight | Description |
|--------|--------|-------------|
| **Title Match** | 0.4 | Exact topic keyword in title |
| **Description Match** | 0.3 | Topic keyword in description/content |
| **Source Credibility** | 0.2 | GitHub (1.0) > HN (0.8) > Reddit (0.6) > Dev.to (0.5) |
| **Negative Keywords** | -50% | Penalty for false positives (e.g., "python" in "Monty Python") |

**Approval Threshold:** Trends with score ≥ 0.3 are approved and shown to user

### 4. Desktop Notifications

**Background daemon with configurable schedules:**
- Runs every 5 minutes (default)
- Configurable notification hours (default: 09:00 - 18:00)
- Only notifies for Active topics
- Counts unread trends and displays summary

### 5. GUI Application

**Custom Tkinter desktop interface:**
- **System Tray Integration**: Always accessible from taskbar
- **Tabbed View**: Separate tabs for Tools, News, Current Project
- **Pagination**: Load more items on demand
- **Interactive**: Click trends to open in browser, marks as read
- **Terminal-like Command Input**: Built-in CLI for quick commands
- **Theme Support**: Light/Dark mode toggle

### 6. User Activity Tracking

**Prepares for future ML/NLP features:**
- Records when users click on trends
- Tracks which trends are read/unread
- Stores time spent (placeholder for future implementation)
- Data exported before deletion for ML training

### 7. Data Management

**Comprehensive data control:**
- **Export Rejected Trends**: Analyze filtered content, tune scoring
- **Statistics Dashboard**: Approval rates by source/topic
- **Topic Deletion with ML Export**: Preserves historical data as JSON
- **Database Cleanup**: Clear all trends without affecting topics

---

## Architecture

### Directory Structure

```
glint/
├── src/glint/
│   ├── cli/
│   │   ├── commands/          # CLI command implementations
│   │   │   ├── init.py        # Database initialization
│   │   │   ├── topics.py      # Topic management (add, list)
│   │   │   ├── config.py      # Configuration (topics, schedule, secrets)
│   │   │   ├── fetch.py       # Manual trend fetching
│   │   │   ├── show.py        # Display trends in table
│   │   │   ├── status.py      # System status info
│   │   │   ├── clear.py       # Clear database
│   │   │   ├── daemon.py      # Background notifier
│   │   │   └── analyze.py     # Analytics (stats, rejected trends)
│   │   └── main.py            # CLI entry point
│   ├── core/
│   │   ├── models.py          # Database models (SQLModel)
│   │   ├── database.py        # DB connection & initialization
│   │   ├── config.py          # Secret/config management
│   │   ├── logger.py          # Logging setup
│   │   └── notifier.py        # Background daemon logic
│   ├── sources/               # Data fetchers
│   │   ├── base.py            # BaseFetcher abstract class
│   │   ├── github.py          # GitHub API fetcher
│   │   ├── hackernews.py      # HN API fetcher
│   │   ├── reddit.py          # Reddit JSON API fetcher
│   │   └── devto.py           # Dev.to API fetcher
│   ├── utils/
│   │   ├── url_utils.py       # URL normalization
│   │   ├── fingerprint.py     # Content fingerprinting
│   │   ├── relevance.py       # Relevance scoring algorithm
│   │   └── ml_exporter.py     # ML data export utility
│   └── gui/
│       ├── app.py             # Main GUI application
│       ├── components/
│       │   ├── dashboard.py   # Tabbed dashboard
│       │   └── terminal.py    # Terminal-like command input
│       └── utils/
│           └── scrolling.py   # Custom scroll handling
├── docs/                      # Documentation
├── scripts/                   # Test/utility scripts
└── assets/                    # Icons, images
```

### Technology Stack

- **CLI**: Typer + Rich (beautiful terminal output)
- **Database**: SQLite + SQLModel (ORM)
- **GUI**: CustomTkinter (modern tkinter)
- **HTTP**: Requests library
- **Notifications**: Plyer (cross-platform)
- **Packaging**: setuptools with pyproject.toml

---

## CLI Commands

### Initialization

```bash
glint init
```
Creates `.glint` directory, config file, and initializes database.

---

### Topic Management

```bash
# Add a topic to watch
glint add <topic_name>

# List all topics with status
glint list

# Toggle topic between Active/Inactive
glint config topics toggle <topic_name>

# Delete topic permanently (with confirmation)
glint config topics delete <topic_name>

# Delete without confirmation
glint config topics delete <topic_name> --force
```

---

### Fetching Trends

```bash
# Manually fetch latest trends
glint fetch
```

Fetches from all sources for all topics (active and inactive).

---

### Viewing Trends

```bash
# Show latest 20 trends (sorted by relevance)
glint show

# Show 50 trends
glint show --limit 50

# Filter by topic
glint show --topic python

# Show only unread
glint show --unread

# Sort by recent discovery
glint show --sort-by recent

# Sort by publish date
glint show --sort-by date

# Sort by relevance score (default)
glint show --sort-by relevance
```

**Interactive Mode**: After displaying trends, enter a number to open in browser.

---

### Configuration

```bash
# Set notification schedule
glint config schedule set 09:00 18:00

# Show current schedule
glint config schedule show

# Set API key (for future sources)
glint config secrets set <key> <value>

# Show configured secrets (masked)
glint config secrets show
```

---

### Analytics

```bash
# Show approval/rejection statistics
glint analyze stats

# Export rejected trends to CSV
glint analyze rejected --output rejected.csv
```

---

### System

```bash
# Show system status
glint status

# Clear all trends (keeps topics)
glint clear

# Start background daemon
glint daemon
```

---

### GUI

```bash
# Launch GUI application
python -m glint.gui.app
# or use the batch file:
glint-gui.bat
```

---

## Database Schema

### Tables

#### `topic`
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment ID |
| `name` | TEXT UNIQUE | Topic name (e.g., "python") |
| `created_at` | DATETIME | Creation timestamp |
| `is_active` | BOOLEAN | Active/Inactive status |

#### `trend`
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment ID |
| `title` | TEXT | Trend title |
| `description` | TEXT | Trend description |
| `url` | TEXT | Original URL |
| `url_normalized` | TEXT INDEX | Normalized URL for dedup |
| `content_fingerprint` | TEXT INDEX | Content hash for dedup |
| `relevance_score` | FLOAT INDEX | Score 0.0-1.0 |
| `status` | TEXT INDEX | "approved" or "rejected" |
| `source` | TEXT | Source name (GitHub, HN, etc.) |
| `category` | TEXT | "repo", "news", "tool", etc. |
| `published_at` | DATETIME | When content was published |
| `fetched_at` | DATETIME | When Glint discovered it |
| `is_read` | BOOLEAN | Read/unread status |
| `topic_id` | INTEGER FK | Links to `topic.id` |

#### `useractivity`
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment ID |
| `trend_id` | INTEGER FK | Links to `trend.id` |
| `clicked_at` | DATETIME | When user clicked |
| `time_spent` | INTEGER | Seconds spent (future) |

#### `userconfig`
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment ID |
| `notification_start` | TEXT | Start time (HH:MM) |
| `notification_end` | TEXT | End time (HH:MM) |

#### `project` (Future Use)
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment ID |
| `title` | TEXT | Project name |
| `description` | TEXT | Project description |
| `topics_to_watched` | TEXT | Comma-separated topics |
| `created_at` | DATETIME | Creation timestamp |

#### `user` (Future Use)
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment ID |
| `username` | TEXT | Username |
| `local_info` | TEXT | Computer information |

---

## Data Sources

### GitHub

**API**: GitHub Search API (no authentication required for basic usage)

**Fetches**:
- New repositories (created in last 30 days, min 50 stars)
- Repositories with topic keywords
- Quality filters: has description, reasonable stars/forks ratio

**Rate Limits**: 10 requests/minute (unauthenticated)

---

### Hacker News

**API**: Algolia HN Search API (public, no auth)

**Fetches**:
- Top stories from past 7 days
- Minimum 50 points threshold
- Deduplicates by URL and title

---

### Reddit

**API**: Public JSON endpoints (no authentication)

**Subreddits Covered**:
- General: r/programming, r/technology
- Language-specific: r/python, r/javascript, r/golang, etc.
- Domain-specific: r/webdev, r/machinelearning, r/devops

**Filters**:
- Min 10 upvotes
- Must have comments (indicates discussion)
- Not removed/deleted

---

### Dev.to

**API**: Public Dev.to API (no auth)

**Fetches**:
- Recent articles (last 7 days)
- Quality filters: reaction count, reading time
- Categories: tutorial, news, discussion

---

## How It Works

### Data Flow

1. **Initialization** (`glint init`)
   - Creates `~/.glint/` directory
   - Initializes SQLite database
   - Sets up default config

2. **Topic Setup** (`glint add python`)
   - Adds topic to database
   - Sets as Active by default

3. **Trend Fetching** (`glint fetch` or background daemon)
   - For each active/inactive topic:
     - Query all data sources with topic keyword
     - Apply source-specific quality filters
     - Calculate relevance score
     - Check for duplicates (URL norm + fingerprint)
     - Store approved trends (score ≥ 0.3)

4. **Notification** (Background daemon every 5 minutes)
   - Count new trends for Active topics only
   - Check if current time is within notification schedule
   - Send desktop notification if new trends found

5. **Viewing** (`glint show`)
   - Query approved trends
   - Apply user filters (topic, unread, sort)
   - Display in rich table
   - Allow interactive selection to open in browser

6. **User Interaction**
   - Click trend → Open URL in browser
   - Mark as read → Update `is_read = True`
   - Log activity → Create `UserActivity` record

---

## Configuration

### Database Location

```
Windows: C:\Users\<username>\.glint\glint.db
macOS/Linux: ~/.glint/glint.db
```

### Config Files

```
Windows: C:\Users\<username>\.glint\config.json
macOS/Linux: ~/.glint/config.json
```

### ML Export Directory

```
Windows: C:\Users\<username>\.glint\ml_data\
macOS/Linux: ~/.glint/ml_data/
```

Stores JSON exports of deleted topics for future ML training.

---

## Current Limitations

1. **No NLP Recommendations Yet**: User activity is logged but not used
2. **Basic Relevance Scoring**: Keyword-based, not semantic
3. **No Project-Based Filtering**: Project model not yet implemented
4. **Limited API Keys**: Some sources don't support authentication
5. **No Content Summarization**: Shows original descriptions only
6. **Orphaned Data**: Trends from deleted topics (pre-CASCADE) show as "Deleted"

---

## Future Features (Planned)

### Short-Term
- ✅ CASCADE delete (COMPLETED)
- Cleanup command for orphaned trends
- Export trends to markdown/PDF
- Custom notification sounds
- Trend tagging system

### Medium-Term
- NLP-based recommendations using user activity
- Content summarization with LLMs
- Project-based trend filtering
- GitHub authentication for higher rate limits
- Customizable relevance scoring weights

### Long-Term
- Browser extension for web-based discovery
- Team collaboration (shared topics)
- AI-powered trend prediction
- Multi-device sync (opt-in, encrypted)

---

## Development

### Running from Source

```bash
# Clone repository
git clone https://github.com/thiszenon/glint
cd glint

# Create virtual environment
python -m venv glint_env
glint_env\Scripts\activate  # Windows
# source glint_env/bin/activate  # macOS/Linux

# Install dependencies
pip install -e .

# Initialize
python -m glint.cli.main init

# Run CLI
python -m glint.cli.main <command>

# Run GUI
python -m glint.gui.app
```

### Testing

```bash
# Run test scripts
python scripts/test_fetch.py
python scripts/test_cascade_delete.py
```

---

## Support & Contributing

- **Repository**: [github.com/thiszenon/glint](https://github.com/thiszenon/glint)
- **Issues**: Report bugs via GitHub Issues
- **License**: MIT

---

