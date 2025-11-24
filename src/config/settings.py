"""
Configuration settings for Mac Cleaner.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment."""
    
    HOME_DIR: Path = Path(os.getenv("MACPURGE_HOME_DIR", str(Path.home())))
    STATE_DIR: Path = Path(os.getenv("MACPURGE_STATE_DIR", "state"))
    CHECKPOINT_INTERVAL: int = int(os.getenv("MACPURGE_CHECKPOINT_INTERVAL", "10"))
    
    MIN_SIZE_MB: int = int(os.getenv("MACPURGE_MIN_SIZE_MB", "10"))
    
    SCAN_DOWNLOADS: bool = os.getenv("MACPURGE_SCAN_DOWNLOADS", "true").lower() == "true"
    SCAN_TRASH: bool = os.getenv("MACPURGE_SCAN_TRASH", "true").lower() == "true"
    SCAN_XCODE: bool = os.getenv("MACPURGE_SCAN_XCODE", "true").lower() == "true"
    SCAN_DOCKER: bool = os.getenv("MACPURGE_SCAN_DOCKER", "true").lower() == "true"
    SCAN_HOMEBREW: bool = os.getenv("MACPURGE_SCAN_HOMEBREW", "true").lower() == "true"
    SCAN_PYTHON: bool = os.getenv("MACPURGE_SCAN_PYTHON", "true").lower() == "true"
    SCAN_NODE: bool = os.getenv("MACPURGE_SCAN_NODE", "true").lower() == "true"
    
    @classmethod
    def ensure_state_dir(cls) -> Path:
        """Ensure state directory exists and return path."""
        cls.STATE_DIR.mkdir(parents=True, exist_ok=True)
        return cls.STATE_DIR


settings = Settings()
