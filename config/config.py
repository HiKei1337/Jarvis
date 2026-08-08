"""
JARVIS Configuration System

Loads configuration from config/config.yaml with fallback to defaults.
"""
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = BASE_DIR / "config" / "config.yaml"

# Default configuration values
DEFAULTS: Dict[str, Any] = {
    "llm": {
        "provider": "ollama",
        "model": "gpt-oss:20b",
        "fast_model": "qwen2.5-coder:7b",
        "vision_model": "qwen3-vl:8b",
        "temperature": 0.7,
        "timeout": 180,
    },
    "agent": {
        "max_steps": 20,
        "max_retries": 3,
        "step_timeout": 30,
    },
    "vision": {
        "enabled": True,
        "coordinate_system": "normalized",
    },
    "voice": {
        "stt_enabled": True,
        "tts_enabled": True,
        "wake_word_enabled": True,
        "wake_word": "джарвис",
        "speaker": "eugene",
        "depth": 1.0,
    },
    "browser": {
        "browser_path": "",
        "cdp_port": 9222,
    },
    "memory": {
        "database_path": "jarvis.db",
        "max_context_messages": 8,
    },
    "security": {
        "require_confirmation": True,
        "trusted_mode": False,
        "sandbox_mode": False,
    },
    "gui": {
        "enabled": True,
        "theme": "dark",
        "width": 800,
        "height": 560,
    },
    "logging": {
        "enabled": True,
        "screenshot_on_risk": True,
        "log_dir": "logs",
    },
}


class Config:
    """Configuration manager for JARVIS."""
    
    _instance: Optional["Config"] = None
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self._config: Dict[str, Any] = {}
        self._load()
    
    @classmethod
    def get_instance(cls, config_path: Optional[Path] = None) -> "Config":
        """Get singleton config instance."""
        if cls._instance is None:
            cls._instance = cls(config_path)
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reset singleton instance (for testing)."""
        cls._instance = None
    
    def _load(self):
        """Load configuration from YAML file."""
        self._config = {}
        
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = yaml.safe_load(f)
                    if loaded:
                        self._merge_config(loaded)
            except Exception as e:
                print(f"[Config] Warning: Could not load config file: {e}")
                print("[Config] Using defaults.")
        
        # Apply defaults for missing keys
        self._merge_config({})
    
    def _merge_config(self, loaded: Dict[str, Any]):
        """Merge loaded config with defaults."""
        for section, defaults in DEFAULTS.items():
            if section not in self._config:
                self._config[section] = {}
            
            loaded_section = loaded.get(section, {})
            for key, default_value in defaults.items():
                if key in loaded_section:
                    self._config[section][key] = loaded_section[key]
                elif key not in self._config[section]:
                    self._config[section][key] = default_value
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(section, {}).get(key, default)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get an entire configuration section."""
        return self._config.get(section, {})
    
    def set(self, section: str, key: str, value: Any):
        """Set a configuration value (runtime only, not saved)."""
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value
    
    @property
    def llm_model(self) -> str:
        return self.get("llm", "model")
    
    @property
    def fast_model(self) -> str:
        return self.get("llm", "fast_model")
    
    @property
    def vision_model(self) -> str:
        return self.get("llm", "vision_model")
    
    @property
    def max_steps(self) -> int:
        return self.get("agent", "max_steps")
    
    @property
    def database_path(self) -> str:
        return self.get("memory", "database_path")
    
    @property
    def browser_path(self) -> str:
        return self.get("browser", "browser_path")
    
    @property
    def wake_word(self) -> str:
        return self.get("voice", "wake_word")


# Global config instance
config: Optional[Config] = None


def get_config() -> Config:
    """Get the global config instance."""
    global config
    if config is None:
        config = Config.get_instance()
    return config


def reload_config(config_path: Optional[Path] = None):
    """Reload configuration from file."""
    global config
    config = Config(config_path)
    return config