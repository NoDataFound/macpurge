"""
Cleaner service for safely removing files and directories.
"""

import shutil
import subprocess
from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Confirm

from src.models.cleanup import CleanupCategory, CleanupTarget, CleanupProgress, ScanResult
from src.utils.checkpoint_manager import CheckpointManager
from src.ui.styles import console, success, error, warning, info, processing


class MacCleaner:
    """Performs cleanup operations on macOS with checkpoint support."""
    
    CHECKPOINT_INTERVAL = 10
    
    def __init__(self, dry_run: bool = False, state_dir: str = "state") -> None:
        """
        Initialize cleaner.
        
        Args:
            dry_run: If True, simulate deletion without removing files.
            state_dir: Directory for checkpoint files.
        """
        self.dry_run = dry_run
        self.state_dir = Path(state_dir)
        self.checkpoint_manager = CheckpointManager("cleanup", self.state_dir)
    
    def delete_path(self, path: Path) -> bool:
        """
        Safely delete a file or directory.
        
        Args:
            path: Path to delete.
            
        Returns:
            True if successful, False otherwise.
        """
        if self.dry_run:
            processing(f"[DRY RUN] Would delete: {path}")
            return True
        
        try:
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path, ignore_errors=False)
            return True
        except PermissionError:
            error(f"Permission denied: {path}")
            return False
        except OSError as e:
            error(f"Failed to delete {path}: {e}")
            return False
    
    def clean_docker(self) -> int:
        """
        Clean Docker system (images, containers, build cache).
        
        Returns:
            Bytes freed (estimated).
        """
        if self.dry_run:
            processing("[DRY RUN] Would run: docker system prune -af")
            return 0
        
        try:
            result = subprocess.run(
                ["docker", "system", "df", "--format", "{{.Reclaimable}}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            reclaimable = 0
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if "GB" in line:
                        val = float(line.split("(")[0].replace("GB", "").strip())
                        reclaimable += int(val * 1024 * 1024 * 1024)
                    elif "MB" in line:
                        val = float(line.split("(")[0].replace("MB", "").strip())
                        reclaimable += int(val * 1024 * 1024)
            
            subprocess.run(
                ["docker", "system", "prune", "-af"],
                capture_output=True,
                timeout=300,
            )
            
            return reclaimable
        except (subprocess.TimeoutExpired, FileNotFoundError):
            warning("Docker cleanup skipped - docker not available or timed out")
            return 0
    
    def clean_homebrew(self) -> int:
        """
        Clean Homebrew caches.
        
        Returns:
            Bytes freed (estimated).
        """
        if self.dry_run:
            processing("[DRY RUN] Would run: brew cleanup --prune=all")
            return 0
        
        try:
            brew_cache = Path.home() / "Library" / "Caches" / "Homebrew"
            size_before = 0
            if brew_cache.exists():
                for item in brew_cache.rglob("*"):
                    if item.is_file():
                        size_before += item.stat().st_size
            
            subprocess.run(
                ["brew", "cleanup", "--prune=all"],
                capture_output=True,
                timeout=300,
            )
            
            size_after = 0
            if brew_cache.exists():
                for item in brew_cache.rglob("*"):
                    if item.is_file():
                        size_after += item.stat().st_size
            
            return max(0, size_before - size_after)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            warning("Homebrew cleanup skipped - brew not available or timed out")
            return 0
    
    def clean_targets(
        self,
        targets: list[CleanupTarget],
        resume: bool = True,
        interactive: bool = True,
    ) -> CleanupProgress:
        """
        Clean selected targets with checkpoint support.
        
        Args:
            targets: List of cleanup targets to process.
            resume: Whether to resume from checkpoint if available.
            interactive: Whether to prompt for confirmation on dangerous items.
            
        Returns:
            CleanupProgress with results.
        """
        progress_result = CleanupProgress(total_items=len(targets))
        processed_paths: list[str] = []
        failed_paths: list[str] = []
        skipped_paths: list[str] = []
        
        if resume and self.checkpoint_manager.exists():
            checkpoint = self.checkpoint_manager.load()
            if checkpoint:
                processed_paths = checkpoint.get("processed_paths", [])
                failed_paths = checkpoint.get("failed_paths", [])
                skipped_paths = checkpoint.get("skipped_paths", [])
                
                already_handled = set(processed_paths + failed_paths + skipped_paths)
                targets = [t for t in targets if str(t.path) not in already_handled]
                
                if targets:
                    info(f"Resuming with {len(targets)} remaining items")
                else:
                    success("All items already processed in previous run")
                    self.checkpoint_manager.clear()
                    return progress_result
        
        with Progress(
            SpinnerColumn(spinner_name="dots", style="bold cyan"),
            TextColumn("[bold purple]{task.description}[/bold purple]"),
            BarColumn(complete_style="cyan", finished_style="magenta"),
            TaskProgressColumn(),
            console=console,
        ) as progress_bar:
            task = progress_bar.add_task("Cleaning...", total=len(targets))
            
            for i, target in enumerate(targets):
                path_str = str(target.path)
                progress_bar.update(
                    task,
                    description=f"Cleaning {target.path.name}..."
                )
                
                should_clean = True
                if target.requires_confirmation and interactive and not self.dry_run:
                    console.print()
                    should_clean = Confirm.ask(
                        f"[warning]\u26a0[/warning] Delete [path]{target.path}[/path] "
                        f"([size]{target.human_size}[/size])?"
                    )
                
                if not should_clean:
                    skipped_paths.append(path_str)
                    progress_result.skipped_items.append(path_str)
                    progress_bar.advance(task)
                    continue
                
                if target.category == CleanupCategory.DOCKER:
                    freed = self.clean_docker()
                    if freed > 0 or self.dry_run:
                        processed_paths.append(path_str)
                        progress_result.deleted_bytes += freed
                        progress_result.processed_items += 1
                    else:
                        failed_paths.append(path_str)
                        progress_result.failed_items.append(path_str)
                elif target.category == CleanupCategory.BREW:
                    freed = self.clean_homebrew()
                    if freed >= 0:
                        processed_paths.append(path_str)
                        progress_result.deleted_bytes += freed
                        progress_result.processed_items += 1
                    else:
                        failed_paths.append(path_str)
                        progress_result.failed_items.append(path_str)
                else:
                    if self.delete_path(target.path):
                        processed_paths.append(path_str)
                        progress_result.deleted_bytes += target.size_bytes
                        progress_result.processed_items += 1
                    else:
                        failed_paths.append(path_str)
                        progress_result.failed_items.append(path_str)
                
                if (i + 1) % self.CHECKPOINT_INTERVAL == 0:
                    self.checkpoint_manager.save(
                        processed_paths,
                        failed_paths,
                        skipped_paths,
                        {"total_targets": progress_result.total_items},
                    )
                
                progress_bar.advance(task)
        
        self.checkpoint_manager.clear()
        
        return progress_result
    
    def quick_clean(self) -> CleanupProgress:
        """
        Perform quick cleanup of safe-to-delete items only.
        
        Returns:
            CleanupProgress with results.
        """
        safe_targets = [
            Path.home() / "Library" / "Caches",
            Path.home() / ".cache",
            Path.home() / "Library" / "Logs",
        ]
        
        progress_result = CleanupProgress()
        
        for target_path in safe_targets:
            if not target_path.exists():
                continue
            
            processing(f"Cleaning {target_path.name}...")
            
            try:
                for item in target_path.iterdir():
                    if item.is_dir():
                        size = sum(
                            f.stat().st_size for f in item.rglob("*") if f.is_file()
                        )
                        if self.delete_path(item):
                            progress_result.deleted_bytes += size
                            progress_result.processed_items += 1
                        else:
                            progress_result.failed_items.append(str(item))
            except PermissionError:
                warning(f"Permission denied accessing {target_path}")
        
        return progress_result
