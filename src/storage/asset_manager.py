"""
Asset Manager
Manages generated assets (images, audio, video) lifecycle
"""
import hashlib
import logging
import shutil
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AssetManager:
    """
    Centralized asset management with deduplication and caching
    """

    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_index: Dict[str, str] = {}  # hash -> path

    def _compute_hash(self, content: bytes) -> str:
        """Compute content hash for deduplication"""
        return hashlib.sha256(content).hexdigest()[:16]

    def cache_asset(self, content: bytes, extension: str = "bin") -> str:
        """Cache asset and return cached path"""
        asset_hash = self._compute_hash(content)

        if asset_hash in self._cache_index:
            return self._cache_index[asset_hash]

        cache_path = self.cache_dir / f"{asset_hash}.{extension}"
        with open(cache_path, "wb") as f:
            f.write(content)

        self._cache_index[asset_hash] = str(cache_path)
        return str(cache_path)

    def get_cached(self, content_hash: str) -> Optional[str]:
        """Get cached asset path by hash"""
        return self._cache_index.get(content_hash)

    def copy_to_project(self, source_path: str, project_dir: str, asset_type: str) -> str:
        """Copy asset to project directory"""
        dest_dir = Path(project_dir) / asset_type
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest_path = dest_dir / Path(source_path).name
        shutil.copy2(source_path, dest_path)

        return str(dest_path)

    def cleanup_project(self, project_dir: str):
        """Clean up project assets"""
        import shutil
        path = Path(project_dir)
        if path.exists():
            shutil.rmtree(path)
            logger.info(f"Cleaned up project assets: {project_dir}")
