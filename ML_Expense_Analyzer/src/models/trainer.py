import pandas as pd
import numpy as np
import yaml
import os
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import logging
from datetime import datetime
import joblib
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge, Lasso
from sklearn.svm import SVC, SVR
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.cluster import KMeans, DBSCAN
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    mean_absolute_error, mean_squared_error, r2_score
)
import xgboost as xgb
import lightgbm as lgb


class ModelTrainer:
    """
    Handles training of machine learning models for expense analysis
    """

    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.models_config = config['models']
        self.trained_models = {}
        self.model_performance = {}

    def train_all_models(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Train all types of models (classification, regression, clustering, anomaly detection)
        """
        self.logger.info("Starting model training for all model types")

        # Prepare features and targets
        X, y_classification, y_regression = self._prepare_features_and_targets(df)

        # Train classification models (expense categorization)
        if y_classification is not None:
            self.logger.info("Training classification models")
            self.trained_models['classification'] = self._train_classification_models(X, y_classification)

        # Train regression models (expense prediction)
        if y_regression is not None:
            self.logger.info("Training regression models")
            self.trained_models['regression'] = self._train_regression_models(X, y_regression)

        # Train clustering models (spending patterns)
        self.logger.info("Training clustering models")
        self.trained_models['clustering'] = self._train_clustering_models(X)

        # Train anomaly detection models
        self.logger.info("Training anomaly detection models")
        self.trained_models['anomaly_detection'] = self._train_anomaly_detection_models(X)

        self.logger.info("Model training completed")
        return self.trained_models

    def _prepare_features_and_targets(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[pd.Series], Optional[pd.Series]]:
        """
        Prepare features and target variables for modeling
        """
        self.logger.info("Preparing features and targets")

        # Create a copy to avoid modifying original data
        df_model = df.copy()

        # Define feature columns (exclude non-feature columns)
        exclude_columns = [
            'date',  # We'll use engineered time features instead
            'description',  # Raw text - we use engineered text features
        ]

        # Identify target columns if they exist
        y_classification = None
        y_regression = None

        if 'category' in df_model.columns:
            y_classification = df_model['category'].copy()
            exclude_columns.extend([col for col in df_model.columns if col == 'category' or col.startswith('category_')])

        # For regression, we'll use amount as target
        if 'amount' in df_model.columns:
            y_regression = df_model['amount'].copy()
            exclude_columns.extend([col for col in df_model.columns if col == 'amount' or col.startswith('amount_') or col == 'log_amount'])

        # Get feature columns (keep numeric only)
        feature_columns = [col for col in df_model.columns if col not in exclude_columns]
        X = df_model[feature_columns].select_dtypes(include=[np.number]).copy()

        # Handle missing values in features
        X = X.fillna(X.mean(numeric_only=True))  # Simple imputation for numeric columns
        # For simplicity, fill with 0 for remaining NaNs
        X = X.fillna(0)

        self.logger.info(f"Prepared features: {X.shape[1]} columns, {X.shape[0]} samples")
        if y_classification is not None:
            self.logger.info(f"Classification target: {len(y_classification.unique())} classes")
        if y_regression is not None:
            self.logger.info(f"Regression target: {y_regression.name}")

        return X, y_classification, y_regression

    def _train_classification_models(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        Train classification models for expense categorization
        """
        self.logger.info("Training classification models")

        # Encode string labels if needed
        label_encoder = None
        if y.dtype == object or (len(y) > 0 and isinstance(y.iloc[0], str)):
            label_encoder = LabelEncoder()
            y_encoded = pd.Series(label_encoder.fit_transform(y), index=y.index)
        else:
            y_encoded = y

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded,
            test_size=self.models_config['classification']['test_size'],
            random_state=self.models_config['classification']['random_state'],
            stratify=y_encoded
        )

        # Scale features for some models
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        models = {}
        model_performance = {}

        # Define models to train
        model_configs = {
            'random_forest': RandomForestClassifier(
                n_estimators=100,
                random_state=self.models_config['classification']['random_state'],
                n_jobs=-1
            ),
            'xgboost': xgb.XGBClassifier(
                n_estimators=100,
                random_state=self.models_config['classification']['random_state'],
                eval_metric='logloss'
            ),
            'lightgbm': lgb.LGBMClassifier(
                n_estimators=100,
                random_state=self.models_config['classification']['random_state'],
                verbose=-1
            ),
            'svm': SVC(
                probability=True,
                random_state=self.models_config['classification']['random_state']
            ),
            'neural_network': MLPClassifier(
                hidden_layer_sizes=(100, 50),
                max_iter=500,
                random_state=self.models_config['classification']['random_state']
            )
        }

        # Train each model
        for name, model in model_configs.items():
            try:
                self.logger.info(f"Training {name}...")

                # Use scaled data for SVM and Neural Network, original for tree-based
                if name in ['svm', 'neural_network']:
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                    y_pred_proba = model.predict_proba(X_test_scaled) if hasattr(model, "predict_proba") else None
                else:
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                    y_pred_proba = model.predict_proba(X_test) if hasattr(model, "predict_proba") else None

                # Calculate performance metrics
                performance = self._calculate_classification_metrics(y_test, y_pred, y_pred_proba)
                model_performance[name] = performance

                # Store model and scaler (if used)
                models[name] = {
                    'model': model,
                    'scaler': scaler if name in ['svm', 'neural_network'] else None,
                    'label_encoder': label_encoder,
                    'performance': performance,
                    'feature_names': list(X.columns)
                }

                self.logger.info(f"{name} - Accuracy: {performance['accuracy']:.4f}")

            except Exception as e:
                self.logger.error(f"Failed to train {name}: {e}")
                continue

        # Store performance for later use
        self.model_performance['classification'] = model_performance

        return models

    def _train_regression_models(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        Train regression models for expense prediction
        """
        self.logger.info("Training regression models")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=self.models_config['regression']['test_size'],
            random_state=self.models_config['regression']['random_state']
        )

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        models = {}
        model_performance = {}

        # Define models to train
        model_configs = {
            'linear_regression': Ridge(alpha=1.0, random_state=self.models_config['regression']['random_state']),
            'ridge': Ridge(alpha=1.0, random_state=self.models_config['regression']['random_state']),
            'lasso': Lasso(alpha=0.1, random_state=self.models_config['regression']['random_state']),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=100,
                random_state=self.models_config['regression']['random_state']
            ),
            'xgboost_regressor': xgb.XGBRegressor(
                n_estimators=100,
                random_state=self.models_config['regression']['random_state']
            )
        }

        # Train each model
        for name, model in model_configs.items():
            try:
                self.logger.info(f"Training {name}...")

                # Use scaled data for linear models, original for tree-based
                if name in ['linear_regression', 'ridge', 'lasso']:
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                else:
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)

                # Calculate performance metrics
                performance = self._calculate_regression_metrics(y_test, y_pred)
                model_performance[name] = performance

                # Store model and scaler (if used)
                models[name] = {
                    'model': model,
                    'scaler': scaler if name in ['linear_regression', 'ridge', 'lasso'] else None,
                    'performance': performance,
                    'feature_names': list(X.columns)
                }

                self.logger.info(f"{name} - R²: {performance['r2']:.4f}")

            except Exception as e:
                self.logger.error(f"Failed to train {name}: {e}")
                continue

        # Store performance for later use
        self.model_performance['regression'] = model_performance

        return models

    def _train_clustering_models(self, X: pd.DataFrame) -> Dict[str, Any]:
        """
        Train clustering models for spending pattern analysis
        """
        self.logger.info("Training clustering models")

        # Scale features for clustering
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        models = {}

        # Define models to train
        model_configs = {
            'kmeans': KMeans(
                n_clusters=5,
                random_state=self.models_config['clustering']['random_state'] if 'random_state' in self.models_config['clustering'] else 42,
                n_init=10
            ),
            'dbscan': DBSCAN(
                eps=0.5,
                min_samples=5
            )
        }

        # Train each model
        for name, model in model_configs.items():
            try:
                self.logger.info(f"Training {name}...")

                model.fit(X_scaled)
                labels = model.labels_

                # Calculate clustering metrics (silhouette score would need additional computation)
                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)  # Ignore noise points if present
                n_noise = list(labels).count(-1) if -1 in labels else 0

                performance = {
                    'n_clusters': n_clusters,
                    'n_noise_points': n_noise,
                    'algorithm': name
                }

                # Store model and scaler
                models[name] = {
                    'model': model,
                    'scaler': scaler,
                    'performance': performance,
                    'feature_names': list(X.columns),
                    'labels': labels
                }

                self.logger.info(f"{name} - Clusters: {n_clusters}, Noise points: {n_noise}")

            except Exception as e:
                self.logger.error(f"Failed to train {name}: {e}")
                continue

        return models

    def _train_anomaly_detection_models(self, X: pd.DataFrame) -> Dict[str, Any]:
        """
        Train anomaly detection models for fraud detection
        """
        self.logger.info("Training anomaly detection models")

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        models = {}

        # Define models to train
        contamination = self.models_config['anomaly_detection']['contamination']
        model_configs = {
            'isolation_forest': IsolationForest(
                contamination=contamination,
                random_state=42,
                n_jobs=-1
            ),
            'one_class_svm': OneClassSVM(
                nu=contamination,
                kernel="rbf",
                gamma='scale'
            )
        }

        # Train each model
        for name, model in model_configs.items():
            try:
                self.logger.info(f"Training {name}...")

                model.fit(X_scaled)
                # Predict: -1 for outliers, 1 for inliers
                predictions = model.predict(X_scaled)
                n_anomalies = sum(predictions == -1)

                performance = {
                    'n_anomalies': n_anomalies,
                    'anomaly_rate': n_anomalies / len(X),
                    'algorithm': name
                }

                # Store model and scaler
                models[name] = {
                    'model': model,
                    'scaler': scaler,
                    'performance': performance,
                    'feature_names': list(X.columns),
                    'predictions': predictions
                }

                self.logger.info(f"{name} - Anomalies detected: {n_anomalies} ({n_anomalies/len(X)*100:.2f}%)")

            except Exception as e:
                self.logger.error(f"Failed to train {name}: {e}")
                continue

        return models

    def _calculate_classification_metrics(self, y_true, y_pred, y_pred_proba=None) -> Dict[str, float]:
        """
        Calculate classification performance metrics
        """
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y_true, y_pred, average='weighted', zero_division=0),
            'f1_score': f1_score(y_true, y_pred, average='weighted', zero_division=0)
        }

        # Add ROC-AUC if probabilities are available and it's a binary or multiclass problem
        if y_pred_proba is not None:
            try:
                # For multiclass, we need to compute ROC-AUC OvR or OvO
                if len(np.unique(y_true)) == 2:
                    # Binary case
                    metrics['roc_auc'] = roc_auc_score(y_true, y_pred_proba[:, 1])
                else:
                    # Multiclass case
                    metrics['roc_auc'] = roc_auc_score(y_true, y_pred_proba, multi_class='ovr', average='weighted')
            except Exception as e:
                self.logger.warning(f"Could not compute ROC-AUC: {e}")
                metrics['roc_auc'] = 0.0

        return metrics

    def _calculate_regression_metrics(self, y_true, y_pred) -> Dict[str, float]:
        """
        Calculate regression performance metrics
        """
        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true, y_pred)

        # Mean Absolute Percentage Error (avoid division by zero)
        mape = np.mean(np.abs((y_true - y_pred) / np.where(y_true != 0, y_true, 1e-8))) * 100

        return {
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'r2': r2,
            'mape': mape
        }

    def save_models(self, models: Dict[str, Any] = None, model_dir: str = "models/"):
        """
        Save trained models to disk
        """
        if models is None:
            models = self.trained_models

        model_path = Path(model_dir)
        model_path.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Saving models to {model_path}")

        for model_type, model_dict in models.items():
            if model_dict is None:
                continue

            for model_name, model_info in model_dict.items():
                if model_info is None or 'model' not in model_info:
                    continue

                # Create filename
                filename = f"{model_type}_{model_name}.joblib"
                filepath = model_path / filename

                # Save model and associated preprocessing objects
                save_dict = {
                    'model': model_info['model'],
                    'scaler': model_info.get('scaler'),
                    'performance': model_info.get('performance'),
                    'feature_names': model_info.get('feature_names'),
                    'model_type': model_type,
                    'model_name': model_name
                }

                # Add type-specific information
                if 'labels' in model_info:
                    save_dict['labels'] = model_info['labels']
                if 'predictions' in model_info:
                    save_dict['predictions'] = model_info['predictions']

                joblib.dump(save_dict, filepath)
                self.logger.info(f"Saved {model_type}/{model_name} to {filepath}")

        # Also save performance metrics
        performance_file = model_path / "model_performance.joblib"
        joblib.dump(self.model_performance, performance_file)
        self.logger.info(f"Saved model performance to {performance_file}")

    def load_models(self, model_dir: str = "models/") -> Dict[str, Any]:
        """
        Load previously trained models from disk
        """
        model_path = Path(model_dir)

        if not model_path.exists():
            raise FileNotFoundError(f"Model directory not found: {model_path}")

        self.logger.info(f"Loading models from {model_path}")

        models = {}
        model_types = ['classification', 'regression', 'clustering', 'anomaly_detection']

        for model_type in model_types:
            models[model_type] = {}
            # Look for saved model files
            model_files = list(model_path.glob(f"{model_type}_*.joblib"))

            for model_file in model_files:
                try:
                    # Extract model name from filename
                    model_name = model_file.stem.replace(f"{model_type}_", "")

                    # Load model data
                    model_data = joblib.load(model_file)

                    # Reconstruct model info dictionary
                    model_info = {
                        'model': model_data['model'],
                        'scaler': model_data.get('scaler'),
                        'performance': model_data.get('performance'),
                        'feature_names': model_data.get('feature_names'),
                        'model_type': model_data.get('model_type'),
                        'model_name': model_data.get('model_name')
                    }

                    # Add type-specific information
                    if 'labels' in model_data:
                        model_info['labels'] = model_data['labels']
                    if 'predictions' in model_data:
                        model_info['predictions'] = model_data['predictions']

                    models[model_type][model_name] = model_info
                    self.logger.info(f"Loaded {model_type}/{model_name} from {model_file}")

                except Exception as e:
                    self.logger.error(f"Failed to load model from {model_file}: {e}")
                    continue

        # Load performance metrics if available
        performance_file = model_path / "model_performance.joblib"
        if performance_file.exists():
            try:
                self.model_performance = joblib.load(performance_file)
                self.logger.info(f"Loaded model performance from {performance_file}")
            except Exception as e:
                self.logger.warning(f"Failed to load model performance: {e}")

        return models