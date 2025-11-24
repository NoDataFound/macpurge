"""
Checkpoint manager for resumable cleanup operations.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.ui.styles import checkpoint, info, warning


class CheckpointManager:
    """Manages checkpoint state for resumable bulk operations."""
    
    def __init__(
        self,
        operation_name: str,
        checkpoint_dir: str | Path = "state"
    ) -> None:
        """
        Initialize checkpoint manager.
        
        Args:
            operation_name: Name of the operation for checkpoint file naming.
            checkpoint_dir: Directory to store checkpoint files.
        """
        self.operation_name = operation_name
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.checkpoint_dir / f"{operation_name}.checkpoint.json"
    
    def save(
        self,
        processed_paths: list[str],
        failed_paths: list[str],
        skipped_paths: list[str],
        metadata: dict[str, Any] | None = None
    ) -> None:
        """
        Save checkpoint state to disk.
        
        Args:
            processed_paths: List of successfully processed paths.
            failed_paths: List of paths that failed processing.
            skipped_paths: List of paths that were skipped.
            metadata: Additional metadata to store.
        """
        checkpoint_data = {
            "timestamp": datetime.now().isoformat(),
            "operation": self.operation_name,
            "processed_paths": processed_paths,
            "failed_paths": failed_paths,
            "skipped_paths": skipped_paths,
            "metadata": metadata or {},
        }
        
        with open(self.checkpoint_file, "w") as f:
            json.dump(checkpoint_data, f, indent=2)
        
        checkpoint(
            f"Checkpoint saved: {len(processed_paths)} processed, "
            f"{len(failed_paths)} failed, {len(skipped_paths)} skipped"
        )
    
    def load(self) -> dict[str, Any] | None:
        """
        Load checkpoint state from disk.
        
        Returns:
            Checkpoint data dict or None if no checkpoint exists.
        """
        if not self.checkpoint_file.exists():
            return None
        
        try:
            with open(self.checkpoint_file, "r") as f:
                data = json.load(f)
            
            timestamp = data.get("timestamp", "unknown")
            processed_count = len(data.get("processed_paths", []))
            info(f"Found checkpoint from {timestamp} with {processed_count} items processed")
            
            return data
        except json.JSONDecodeError:
            warning("Checkpoint file corrupted, starting fresh")
            return None
    
    def clear(self) -> None:
        """Remove checkpoint file after successful completion."""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
            info("Checkpoint cleared - operation complete")
    
    def exists(self) -> bool:
        """Check if a checkpoint file exists."""
        return self.checkpoint_file.exists()
    
    def get_remaining_items(
        self,
        all_items: list[str],
        checkpoint_data: dict[str, Any]
    ) -> list[str]:
        """
        Get items not yet processed based on checkpoint.
        
        Args:
            all_items: Complete list of items to process.
            checkpoint_data: Loaded checkpoint data.
            
        Returns:
            List of items still needing processing.
        """
        processed = set(checkpoint_data.get("processed_paths", []))
        failed = set(checkpoint_data.get("failed_paths", []))
        skipped = set(checkpoint_data.get("skipped_paths", []))
        
        already_handled = processed | failed | skipped
        
        return [item for item in all_items if item not in already_handled]
