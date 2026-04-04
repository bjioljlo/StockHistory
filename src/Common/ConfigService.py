import yaml
import os
import re

def substitute_env_vars(config_dict):
    """Recursively substitute environment variables in configuration dictionary."""
    if isinstance(config_dict, dict):
        return {key: substitute_env_vars(value) for key, value in config_dict.items()}
    elif isinstance(config_dict, list):
        return [substitute_env_vars(item) for item in config_dict]
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

def load_config(config_path='config.yml'):
    """Loads the configuration from a YAML file and substitutes environment variables."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Substitute environment variables
    config = substitute_env_vars(config)

    return config

def get_config_path():
    """Determine which config file to use based on environment."""
    env = os.getenv('APP_ENV', 'dev').lower()
    if env == 'production' or env == 'prod':
        return 'config.prod.yml'
    else:
        return 'config.dev.yml'
