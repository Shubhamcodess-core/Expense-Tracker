import logging
import logging.config
import yaml
import os
from pathlib import Path


def setup_logging(config_path="config.yaml", default_level=logging.INFO):
    """
    Setup logging configuration
    """
    try:
        with open(config_path, 'rt') as f:
            config = yaml.safe_load(f.read())

        # Ensure logs directory exists
        log_config = config.get('logging')
        if log_config and isinstance(log_config, dict) and 'version' in log_config:
            log_file_path = log_config.get('file_path', 'logs/project.log')
            log_dir = os.path.dirname(log_file_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            logging.config.dictConfig(log_config)
        else:
            os.makedirs("logs", exist_ok=True)
            logging.basicConfig(
                level=default_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(),
                    logging.FileHandler('logs/project.log', encoding='utf-8')
                ]
            )
    except Exception as e:
        # Fallback to basic logging if config fails
        logging.basicConfig(level=default_level)


def get_logger(name):
    """
    Get a logger with the specified name
    """
    return logging.getLogger(name)