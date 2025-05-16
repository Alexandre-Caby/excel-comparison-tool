import os
import json
import logging
from typing import Dict, Any, Optional

class Config:
    """Configuration manager for the Excel Comparison Tool"""
    
    DEFAULT_CONFIG = {
        "app_name": "Excel Comparison Tool",
        "version": "1.0.0",
        "temp_dir": "temp",
        "reports_dir": "reports",
        "max_file_size_mb": 100,
        "allowed_extensions": [".xlsx", ".xls"],
        "default_comparison_options": {
            "ignore_case": True,
            "ignore_whitespace": True,
            "match_by_column_name": False,
            "match_by_column_position": True 
        },
        "ui_settings": {
            "theme": "light",
            "show_welcome_screen": True,
            "max_recent_comparisons": 10
        },
        "logging": {
            "level": "INFO",
            "file": "app.log",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize configuration manager"""
        self.config_file = config_file
        self.config = self._load_config()
        
        # Ensure required directories exist
        self._ensure_directories()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    
                # Merge user config with default config
                config = self.DEFAULT_CONFIG.copy()
                config.update(user_config)
                return config
            except Exception:
                return self.DEFAULT_CONFIG
        else:
            return self.DEFAULT_CONFIG
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception:
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key"""
        # Support nested keys with dot notation (e.g., "ui_settings.theme")
        if "." in key:
            main_key, sub_key = key.split(".", 1)
            return self.config.get(main_key, {}).get(sub_key, default)
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        # Support nested keys with dot notation
        if "." in key:
            main_key, sub_key = key.split(".", 1)
            if main_key not in self.config:
                self.config[main_key] = {}
            self.config[main_key][sub_key] = value
        else:
            self.config[key] = value
    
    def _ensure_directories(self) -> None:
        """Ensure required directories exist"""
        # Create temp directory if it doesn't exist
        temp_dir = self.get("temp_dir", "temp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        # Create reports directory if it doesn't exist
        reports_dir = self.get("reports_dir", "reports")
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)

# Global config instance
config = Config()
