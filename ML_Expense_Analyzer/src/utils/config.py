import yaml
import os
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file
    """
    config_file = Path(config_path)

    if not config_file.exists():
        # Return default configuration if file doesn't exist
        return get_default_config()

    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        raise RuntimeError(f"Failed to load configuration from {config_path}: {e}")


def get_default_config() -> Dict[str, Any]:
    """
    Return default configuration
    """
    return {
        "project": {
            "name": "ML Expense Analyzer",
            "version": "1.0.0",
            "description": "Machine Learning project for personal expense analysis and prediction"
        },
        "data": {
            "raw_path": "data/raw/",
            "processed_path": "data/processed/",
            "external_path": "data/external/",
            "required_columns": ["date", "amount", "category", "description"],
            "optional_columns": ["currency", "payment_method", "merchant"],
            "date_format": "%Y-%m-%d",
            "base_currency": "USD"
        },
        "models": {
            "model_path": "models/",
            "classification": {
                "algorithms": ["random_forest", "xgboost", "lightgbm", "svm", "neural_network"],
                "test_size": 0.2,
                "random_state": 42,
                "cross_validation_folds": 5
            },
            "regression": {
                "algorithms": ["linear_regression", "ridge", "lasso", "gradient_boosting", "xgboost_regressor"],
                "test_size": 0.2,
                "random_state": 42,
                "cross_validation_folds": 5
            },
            "clustering": {
                "algorithms": ["kmeans", "dbscan"],
                "n_clusters_range": [2, 10]
            },
            "anomaly_detection": {
                "algorithms": ["isolation_forest", "one_class_svm"],
                "contamination": 0.1
            }
        },
        "visualization": {
            "figure_size": [12, 8],
            "style": "seaborn-v0_8",
            "color_palette": "husl",
            "save_format": ["png", "svg", "pdf"],
            "dpi": 300,
            "interactive": True,
            "theme": "plotly_white"
        },
        "evaluation": {
            "classification_metrics": ["accuracy", "precision", "recall", "f1-score", "roc_auc"],
            "regression_metrics": ["mae", "mse", "rmse", "r2", "mape"],
            "alpha": 0.05
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file_path": "logs/project.log"
        },
        "output": {
            "reports_path": "reports/",
            "plots_path": "reports/plots/",
            "predictions_path": "reports/predictions/"
        },
        "features": {
            "time_features": ["hour", "day_of_week", "day_of_month", "month", "quarter", "is_weekend", "is_month_start", "is_month_end"],
            "amount_features": ["log_amount", "amount_zscore", "rolling_mean_7d", "rolling_std_7d", "expense_ratio_to_income"],
            "text_features": ["tfidf", "word_embeddings", "sentiment_score"],
            "categorical_encoding": ["onehot", "label", "target"]
        }
    }


def save_config(config: Dict[str, Any], config_path: str = "config.yaml"):
    """
    Save configuration to YAML file
    """
    config_file = Path(config_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)

    with open(config_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)