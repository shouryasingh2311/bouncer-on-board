"""Configuration management for BOB (.bob/config.yaml)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class Config:
    """BOB runtime configuration matching PROJECT.md Section 6.3."""

    model: str = "gemma4:e2b"
    ollama_url: str = "http://localhost:11434"
    min_package_age_days: int = 14
    offline_policy: str = "warn"  # warn | block
    registry_overrides: Dict[str, str] = field(default_factory=dict)
    sensitive_paths_extra: List[str] = field(default_factory=list)
    fail_gate_on: List[str] = field(
        default_factory=lambda: ["critical", "high"]
    )
    api_key: Optional[str] = None
    ai_provider: str = "ide_native"  # ide_native | ollama | cloud | deterministic

    def get_pypi_base_url(self) -> str:
        """Get base PyPI URL taking into account registry overrides."""
        return self.registry_overrides.get("pypi", "https://pypi.org/pypi").rstrip("/")

    def get_npm_base_url(self) -> str:
        """Get base npm registry URL taking into account registry overrides."""
        return self.registry_overrides.get("npm", "https://registry.npmjs.org").rstrip("/")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def find_config_path() -> Optional[Path]:
    """Resolve configuration file path from environment or default locations.

    Priority:
    1. BOB_CONFIG environment variable.
    2. ./.bob/config.yaml in current working directory.
    """
    env_override = os.environ.get("BOB_CONFIG")
    if env_override:
        path = Path(env_override)
        if path.is_file():
            return path
        # If explicitly specified in BOB_CONFIG but missing, return path so caller can log/raise
        return path

    local_path = Path.cwd() / ".bob" / "config.yaml"
    if local_path.is_file():
        return local_path

    home_path = Path.home() / ".bob" / "config.yaml"
    if home_path.is_file():
        return home_path

    return None


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from YAML file or return defaults if absent.

    Never crashes on missing file; falls back safely to default Config().
    """
    resolved_path = config_path or find_config_path()

    if not resolved_path or not resolved_path.is_file():
        return Config()

    try:
        with open(resolved_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        if not isinstance(data, dict):
            return Config()

        # Parse known fields cleanly
        return Config(
            model=str(data.get("model", Config.model)),
            ollama_url=str(data.get("ollama_url", Config.ollama_url)),
            min_package_age_days=int(
                data.get("min_package_age_days", Config.min_package_age_days)
            ),
            offline_policy=str(
                data.get("offline_policy", Config.offline_policy)
            ),
            registry_overrides=dict(
                data.get("registry_overrides", {})
            ),
            sensitive_paths_extra=list(
                data.get("sensitive_paths_extra", [])
            ),
            fail_gate_on=[
                str(s).lower()
                for s in data.get("fail_gate_on", ["critical", "high"])
            ],
            api_key=data.get("api_key"),
            ai_provider=str(data.get("ai_provider", Config.ai_provider)),
        )
    except Exception:
        # Fall back to default config if file is unparseable
        return Config()


def save_config(cfg: Config, path: Optional[Path] = None) -> Path:
    """Save configuration to .bob/config.yaml."""
    target_path = path or (Path.cwd() / ".bob" / "config.yaml")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg.to_dict(), f, sort_keys=False)
    return target_path
