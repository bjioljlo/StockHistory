import yaml
import os
import re
from typing import Any, Dict, Optional
from functools import lru_cache


class ConfigService:
    """
    Unified configuration management service.
    Provides singleton access to application configuration with environment variable substitution.
    """
    _instance: Optional['ConfigService'] = None
    _config: Optional[Dict[str, Any]] = None

    def __new__(cls) -> 'ConfigService':
        if cls._instance is None:
            cls._instance = super(ConfigService, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing purposes)
        """
        cls._instance = None
        cls._config = None

    def _load_config(self) -> None:
        """Load and initialize configuration"""
        config_path = self.get_config_path()

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Substitute environment variables
        self._config = self.substitute_env_vars(config)

    @staticmethod
    def substitute_env_vars(config_dict: Any) -> Any:
        """Recursively substitute environment variables in configuration dictionary."""
        if isinstance(config_dict, dict):
            return {key: ConfigService.substitute_env_vars(value) for key, value in config_dict.items()}
        elif isinstance(config_dict, list):
            return [ConfigService.substitute_env_vars(item) for item in config_dict]
        elif isinstance(config_dict, str):
            # Pattern to match ${VAR_NAME} or ${VAR_NAME:-default_value}
            pattern = r'\$\{([^}]+)\}'

            def replace_var(match):
                var_expr = match.group(1)
                if ':-' in var_expr:
                    var_name, default_value = var_expr.split(':-', 1)
                    return os.getenv(var_name, default_value)
                else:
                    return os.getenv(var_expr, '')

            return re.sub(pattern, replace_var, config_dict)
        else:
            return config_dict

    @staticmethod
    def get_config_path() -> str:
        """Determine which config file to use based on environment."""
        env = os.getenv('APP_ENV', 'dev').lower()
        if env == 'production' or env == 'prod':
            return 'config.prod.yml'
        else:
            return 'config.dev.yml'

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated key.
        Example: get('database.host')
        """
        if not self._config:
            return default

        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_all(self) -> Dict[str, Any]:
        """Get full configuration dictionary"""
        return self._config.copy() if self._config else {}


@lru_cache(maxsize=None)
def get_config() -> ConfigService:
    """Get ConfigService singleton instance"""
    return ConfigService()

