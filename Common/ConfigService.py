import yaml

def load_config(config_path='config.yml'):
    """Loads the configuration from a YAML file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
