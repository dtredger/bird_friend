"""
Config Loading Module
====================

Provides safe config loading and access without imposing defaults.
Each service should handle its own defaults.
"""

import json


def load_config_file(filename="config.json"):
    """
    Load configuration from JSON file.
    Returns empty dict if file not found or invalid.
    No defaults imposed - services handle their own.
    """
    try:
        with open(filename, "r") as f:
            config = json.load(f)
        print(f"✅ Configuration loaded from {filename}")
        return config

    except (OSError, ValueError) as e:
        print(f"⚠️ {filename} not found or invalid: {e}")
        print("📄 Using empty configuration - services will use their defaults")
        return {}


def merge_configs(base_config, override_config):
    """
    Recursively merge override config with base config.
    Override values take precedence, missing keys remain unchanged.
    """
    result = base_config.copy()

    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = merge_configs(result[key], value)
        else:
            # Override with new value
            result[key] = value

    return result


def get_config_value(config, path, default=None):
    """
    Safely get nested config value with dot notation.

    Args:
        config: Configuration dictionary
        path: Dot-separated path (e.g., "sensors.light_threshold")
        default: Value to return if path not found

    Returns:
        Value at path, or default if not found

    Example:
        threshold = get_config_value(config, "sensors.light_threshold", 1000)
    """
    if not isinstance(config, dict):
        return default

    keys = path.split('.')
    value = config

    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default


def config_section(config, section_name, defaults=None):
    """
    Get a config section with optional defaults.

    Args:
        config: Full configuration dictionary
        section_name: Name of section (e.g., "sensors")
        defaults: Default values for this section

    Returns:
        Section config merged with defaults

    Example:
        sensor_config = config_section(config, "sensors", {
            "light_threshold": 1000,
            "quiet_light_threshold": 3000
        })
    """
    section = config.get(section_name, {})

    if defaults:
        return merge_configs(defaults, section)
    else:
        return section


def has_config_key(config, path):
    """
    Check if a config key exists.

    Args:
        config: Configuration dictionary
        path: Dot-separated path

    Returns:
        True if key exists, False otherwise
    """
    return get_config_value(config, path, None) is not None


# Utility functions for common patterns
def get_pin_config(config, pin_name, default_pin="A0"):
    """Get pin configuration with fallback"""
    return get_config_value(config, f"pins.{pin_name}", default_pin)


def get_enabled_config(config, service_name, default_enabled=True):
    """Check if a service is enabled"""
    return get_config_value(config, f"{service_name}.enabled", default_enabled)
