# Git Repository Setup

This repository is initialized and ready for version control.

## Initial Setup

Before making your first commit, configure your git identity:

```bash
# Set your name and email (replace with your actual information)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Or set globally for all repositories:
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Make Initial Commit

After configuring your identity, make the initial commit:

```bash
git commit -m "Initial commit: GCP Support library with H3 cell parsing, USGS/NOAA GCP finding, and export functionality"
```

## What's Ignored

The `.gitignore` file is configured to ignore:

- **Test outputs**: `gcps_output/` directory and all `*.log` files
- **Generated files**: CSV, TXT, XML, shapefiles, GeoJSON files
- **Build artifacts**: `*.egg-info/`, `dist/`, `build/`
- **Python cache**: `__pycache__/`, `*.pyc`, etc.
- **IDE files**: `.vscode/`, `.idea/`, etc.
- **OS files**: `.DS_Store` (macOS)
- **Credentials**: `*.key`, `*.pem`, `.env`, `credentials.json`

## What's Tracked

The repository tracks:
- All source code files (`.py`)
- Configuration files (`setup.py`, `requirements.txt`)
- Documentation (`README.md`, `USGS_API_NOTES.md`)
- Input manifest file (`input/input-file.manifest`)
- License and other project files

## Adding a Remote Repository

To push to a remote repository (e.g., GitHub):

```bash
# Add remote (replace with your repository URL)
git remote add origin https://github.com/yourusername/gcp_support.git

# Push to remote
git push -u origin main
```

## Daily Workflow

```bash
# Check status
git status

# Add changes
git add <files>

# Commit changes
git commit -m "Description of changes"

# Push to remote
git push
```

