import os
import json
import logging
from typing import Dict, Any, Optional

class Config:
    """Configuration manager for the Excel Comparison Tool"""
    
    DEFAULT_CONFIG = {
        "app_name": "Excel Comparison Tool",
        "version": "1.0.0",
        "temp_dir": "src/backend/temp",
        "reports_dir": "src/backend/reports",
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
            "file": "src/backend/app.log",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "frontend": {
            "images_dir": "src/frontend/images",
            "pages_dir": "src/frontend/pages",
            "css_dir": "src/frontend/css",
            "js_dir": "src/frontend/js"
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
                return self.DEFAULT_CONFIG.copy()
        else:
            return self.DEFAULT_CONFIG.copy()
    
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
            keys = key.split(".")
            value = self.config
            for k in keys:
                value = value.get(k, {}) if isinstance(value, dict) else default
            return value if value != {} else default
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        # Support nested keys with dot notation
        if "." in key:
            keys = key.split(".")
            config_ref = self.config
            for k in keys[:-1]:
                if k not in config_ref:
                    config_ref[k] = {}
                config_ref = config_ref[k]
            config_ref[keys[-1]] = value
        else:
            self.config[key] = value
    
    def _ensure_directories(self) -> None:
        """Ensure required directories exist"""
        # Create temp directory if it doesn't exist
        temp_dir = self.get("temp_dir", "src/backend/temp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)
            
        # Create reports directory if it doesn't exist
        reports_dir = self.get("reports_dir", "src/backend/reports")
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir, exist_ok=True)
            
        # Ensure frontend directories exist
        images_dir = self.get("frontend.images_dir", "src/frontend/images")
        if not os.path.exists(images_dir):
            os.makedirs(images_dir, exist_ok=True)

# Global config instance
config = Config()
