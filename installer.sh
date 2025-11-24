#!/bin/bash
# MacPurge Installer
# Synthwave-themed macOS cleanup utility

set -e

# Colors
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
PURPLE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ASCII Banner
echo -e "${MAGENTA}"
cat << 'EOF'
    __  ___           ____                       
   /  |/  /___ ______/ __ \__  ___________  ___ 
  / /|_/ / __ `/ ___/ /_/ / / / / ___/ __ `/ _ \
 / /  / / /_/ / /__/ ____/ /_/ / /  / /_/ /  __/
/_/  /_/\__,_/\___/_/    \__,_/_/   \__, /\___/ 
                                   /____/       
EOF
echo -e "${NC}"

echo -e "${CYAN}Reclaim Your Storage${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo

VENV_NAME="macpurge_venv"

# Check for Homebrew
echo -e "${CYAN}[1/7]${NC} Checking for Homebrew..."
if command -v brew &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Homebrew found"
else
    echo -e "  ${YELLOW}⚠${NC} Homebrew not found, installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add brew to path for Apple Silicon or Intel
    if [ -f "/opt/homebrew/bin/brew" ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [ -f "/usr/local/bin/brew" ]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
    echo -e "  ${GREEN}✓${NC} Homebrew installed"
fi

# Install latest Python via Homebrew
echo -e "${CYAN}[2/7]${NC} Installing latest Python via Homebrew..."
brew install python@3.13 2>/dev/null || brew upgrade python@3.13 2>/dev/null || true

# Find the Homebrew Python path
if [ -f "/opt/homebrew/bin/python3.13" ]; then
    PYTHON_BIN="/opt/homebrew/bin/python3.13"
elif [ -f "/usr/local/bin/python3.13" ]; then
    PYTHON_BIN="/usr/local/bin/python3.13"
elif [ -f "/opt/homebrew/bin/python3.12" ]; then
    brew install python@3.13 || true
    PYTHON_BIN="/opt/homebrew/bin/python3.13"
else
    # Fallback: try to find any recent brew python
    PYTHON_BIN=$(brew --prefix python@3.13 2>/dev/null)/bin/python3.13 || \
    PYTHON_BIN=$(brew --prefix python@3.12 2>/dev/null)/bin/python3.12 || \
    PYTHON_BIN=$(brew --prefix python)/bin/python3
fi

if [ ! -f "$PYTHON_BIN" ]; then
    echo -e "  ${RED}✗${NC} Could not find Homebrew Python"
    echo -e "  ${YELLOW}Trying: brew install python@3.13${NC}"
    brew install python@3.13
    PYTHON_BIN="/opt/homebrew/bin/python3.13"
fi

PYTHON_VERSION=$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "  ${GREEN}✓${NC} Using Python $PYTHON_VERSION at $PYTHON_BIN"

# Remove old venv if exists
echo -e "${CYAN}[3/7]${NC} Creating virtual environment with Python $PYTHON_VERSION..."
if [ -d "$VENV_NAME" ]; then
    echo -e "  ${YELLOW}⚠${NC} Removing old venv..."
    rm -rf "$VENV_NAME"
fi

# Create venv with the NEW Python
"$PYTHON_BIN" -m venv "$VENV_NAME"
echo -e "  ${GREEN}✓${NC} Virtual environment created"

# Verify venv Python version
VENV_PYTHON_VERSION=$("$VENV_NAME/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "  ${GREEN}✓${NC} Venv Python version: $VENV_PYTHON_VERSION"

# Upgrade pip inside venv
echo -e "${CYAN}[4/7]${NC} Upgrading pip..."
"$VENV_NAME/bin/pip" install --upgrade pip --quiet
echo -e "  ${GREEN}✓${NC} pip upgraded"

# Install dependencies into venv
echo -e "${CYAN}[5/7]${NC} Installing dependencies..."
"$VENV_NAME/bin/pip" install -r requirements.txt --quiet
echo -e "  ${GREEN}✓${NC} Dependencies installed"

# Setup environment
echo -e "${CYAN}[6/7]${NC} Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "  ${GREEN}✓${NC} Created .env from template"
else
    echo -e "  ${YELLOW}⚠${NC} .env already exists, skipping"
fi

# Create directories
echo -e "${CYAN}[7/7]${NC} Creating directories..."
mkdir -p state logs docs/help
echo -e "  ${GREEN}✓${NC} Directories created"

# Done!
echo
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Installation complete!${NC}"
echo
echo -e "${CYAN}Python version in venv:${NC} ${MAGENTA}$VENV_PYTHON_VERSION${NC}"
echo
echo -e "${CYAN}To get started:${NC}"
echo -e "  ${MAGENTA}source $VENV_NAME/bin/activate${NC}"
echo -e "  ${MAGENTA}python src/main.py scan${NC}"
echo
echo -e "${CYAN}Or run directly:${NC}"
echo -e "  ${MAGENTA}$VENV_NAME/bin/python src/main.py scan${NC}"
echo
echo -e "${CYAN}Available commands:${NC}"
echo -e "  ${PURPLE}scan${NC}         - Scan for cleanable items"
echo -e "  ${PURPLE}clean${NC}        - Interactive cleanup"
echo -e "  ${PURPLE}quick${NC}        - Quick safe cleanup (caches/logs only)"
echo -e "  ${PURPLE}interactive${NC}  - Menu-driven cleanup"
echo -e "  ${PURPLE}status${NC}       - Show checkpoint status"
echo
echo -e "${CYAN}Options:${NC}"
echo -e "  ${PURPLE}--dry-run${NC}    - Preview without deleting"
echo -e "  ${PURPLE}--help${NC}       - Show all options"
echo