"""Configuration management."""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else None
        self.rules: Dict[str, Any] = {}
    
    def load(self, path: Optional[str] = None) -> Dict[str, Any]:
        config_file = Path(path) if path else self.config_path
        if not config_file or not config_file.exists():
            raise FileNotFoundError(f"Config not found: {config_file}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            self.rules = yaml.safe_load(f)
        return self.rules
    
    def get_all_rules(self) -> Dict[str, Any]:
        return self.rules
