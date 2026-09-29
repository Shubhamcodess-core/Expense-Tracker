import pandas as pd
import numpy as np
import yaml
import os
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import logging
from datetime import datetime
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix,
    mean_absolute_error, mean_squared_error, r2_score, classification_report
)
from sklearn.model_selection import learning_curve
import warnings
warnings.filterwarnings('ignore')


class ModelEvaluator:
    """
    Handles evaluation of machine learning models for expense analysis
    """

    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.evaluation_config = config['evaluation']

    def evaluate_models(self, trained_models: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluate all trained models
        """
        self.logger.info("Starting model evaluation")

        # Prepare features and targets
        X, y_classification, y_regression = self._prepare_features_and_targets(df)

        evaluation_results = {}

        # Evaluate classification models
        if 'classification' in trained_models and y_classification is not None:
            self.logger.info("Evaluating classification models")
            evaluation_results['classification'] = self._evaluate_classification_models(
                trained_models['classification'], X, y_classification
            )

        # Evaluate regression models
        if 'regression' in trained_models and y_regression is not None:
            self.logger.info("Evaluating regression models")
            evaluation_results['regression'] = self._evaluate_regression_models(
                trained_models['regression'], X, y_regression
            )

        # Evaluate clustering models
        if 'clustering' in trained_models:
            self.logger.info("Evaluating clustering models")
            evaluation_results['clustering'] = self._evaluate_clustering_models(
                trained_models['clustering'], X
            )

        # Evaluate anomaly detection models
        if 'anomaly_detection' in trained_models:
            self.logger.info("Evaluating anomaly detection models")
            evaluation_results['anomaly_detection'] = self._evaluate_anomaly_detection_models(
                trained_models['anomaly_detection'], X
            )

        self.logger.info("Model evaluation completed")
        return evaluation_results

    def _prepare_features_and_targets(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[pd.Series], Optional[pd.Series]]:
        """
        Prepare features and target variables for evaluation (same as in trainer)
        """
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
        X = X.fillna(0)

        return X, y_classification, y_regression

    def _evaluate_classification_models(self, models: Dict[str, Any], X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        Evaluate classification models
        """
        from sklearn.model_selection import train_test_split

        # Check for label encoder from trained models
        le = None
        for info in models.values():
            if isinstance(info, dict) and info.get('label_encoder') is not None:
                le = info['label_encoder']
                break

        y_eval = pd.Series(le.transform(y), index=y.index) if le is not None and (y.dtype == object or (len(y) > 0 and isinstance(y.iloc[0], str))) else y

        # Split data (same split as used in training for consistency)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_eval,
            test_size=0.2,
            random_state=42,
            stratify=y_eval
        )

        results = {}

        for model_name, model_info in models.items():
            if model_info is None or 'model' not in model_info:
                continue

            try:
                model = model_info['model']
                scaler = model_info.get('scaler')

                # Prepare test data
                if scaler is not None:
                    X_test_scaled = scaler.transform(X_test)
                    y_pred = model.predict(X_test_scaled)
                    y_pred_proba = model.predict_proba(X_test_scaled) if hasattr(model, "predict_proba") else None
                else:
                    y_pred = model.predict(X_test)
                    y_pred_proba = model.predict_proba(X_test) if hasattr(model, "predict_proba") else None

                # Calculate metrics
                metrics = self._calculate_classification_metrics(y_test, y_pred, y_pred_proba)

                # Generate classification report
                class_report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

                # Confusion matrix
                cm = confusion_matrix(y_test, y_pred)

                # Feature importance (if available)
                feature_importance = self._get_feature_importance(model, model_info.get('feature_names', []))

                results[model_name] = {
                    'metrics': metrics,
                    'classification_report': class_report,
                    'confusion_matrix': cm.tolist(),  # Convert to list for JSON serialization
                    'feature_importance': feature_importance,
                    'predictions': y_pred.tolist(),
                    'probabilities': y_pred_proba.tolist() if y_pred_proba is not None else None
                }

                self.logger.info(f"Evaluated {model_name}: Accuracy = {metrics['accuracy']:.4f}")

            except Exception as e:
                self.logger.error(f"Failed to evaluate {model_name}: {e}")
                results[model_name] = {'error': str(e)}

        return results

    def _evaluate_regression_models(self, models: Dict[str, Any], X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        Evaluate regression models
        """
        from sklearn.model_selection import train_test_split

        # Split data (same split as used in training for consistency)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=0.2,
            random_state=42
        )

        results = {}

        for model_name, model_info in models.items():
            if model_info is None or 'model' not in model_info:
                continue

            try:
                model = model_info['model']
                scaler = model_info.get('scaler')

                # Prepare test data
                if scaler is not None:
                    X_test_scaled = scaler.transform(X_test)
                    y_pred = model.predict(X_test_scaled)
                else:
                    y_pred = model.predict(X_test)

                # Calculate metrics
                metrics = self._calculate_regression_metrics(y_test, y_pred)

                # Residuals analysis
                residuals = y_test - y_pred

                # Feature importance (if available)
                feature_importance = self._get_feature_importance(model, model_info.get('feature_names', []))

                results[model_name] = {
                    'metrics': metrics,
                    'residuals': residuals.tolist(),
                    'feature_importance': feature_importance,
                    'predictions': y_pred.tolist(),
                    'actual_values': y_test.tolist()
                }

                self.logger.info(f"Evaluated {model_name}: R² = {metrics['r2']:.4f}")

            except Exception as e:
                self.logger.error(f"Failed to evaluate {model_name}: {e}")
                results[model_name] = {'error': str(e)}

        return results

    def _evaluate_clustering_models(self, models: Dict[str, Any], X: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluate clustering models
        """
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import silhouette_score

        # Scale features for evaluation
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        results = {}

        for model_name, model_info in models.items():
            if model_info is None or 'model' not in model_info:
                continue

            try:
                model = model_info['model']

                # Get cluster labels
                if hasattr(model, 'labels_'):
                    labels = model.labels_
                else:
                    labels = model.predict(X_scaled)

                # Calculate clustering metrics
                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)  # Ignore noise points
                n_noise = list(labels).count(-1) if -1 in labels else 0

                # Silhouette score (only if we have more than 1 cluster and no noise points in pure clustering)
                silhouette_avg = None
                if n_clusters > 1 and n_noise == 0:
                    try:
                        silhouette_avg = silhouette_score(X_scaled, labels)
                    except Exception:
                        silhouette_avg = None  # Silhouette score calculation failed

                results[model_name] = {
                    'n_clusters': n_clusters,
                    'n_noise_points': n_noise,
                    'silhouette_score': silhouette_avg,
                    'labels': labels.tolist(),
                    'algorithm': model_info.get('performance', {}).get('algorithm', model_name)
                }

                self.logger.info(f"Evaluated {model_name}: Clusters = {n_clusters}")

            except Exception as e:
                self.logger.error(f"Failed to evaluate {model_name}: {e}")
                results[model_name] = {'error': str(e)}

        return results

    def _evaluate_anomaly_detection_models(self, models: Dict[str, Any], X: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluate anomaly detection models
        """
        from sklearn.preprocessing import StandardScaler

        # Scale features for evaluation
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        results = {}

        for model_name, model_info in models.items():
            if model_info is None or 'model' not in model_info:
                continue

            try:
                model = model_info['model']

                # Get predictions (-1 for outliers, 1 for inliers)
                if hasattr(model, 'predict'):
                    predictions = model.predict(X_scaled)
                else:
                    # For models that don't have predict method, use decision_function or similar
                    if hasattr(model, 'decision_function'):
                        scores = model.decision_function(X_scaled)
                        # Threshold at 0 for OneClassSVM
                        predictions = np.where(scores >= 0, 1, -1)
                    else:
                        # Fallback: use predict if available
                        predictions = model.predict(X_scaled)

                n_anomalies = sum(predictions == -1)
                anomaly_rate = n_anomalies / len(X)

                results[model_name] = {
                    'n_anomalies': n_anomalies,
                    'anomaly_rate': anomaly_rate,
                    'predictions': predictions.tolist(),
                    'algorithm': model_info.get('performance', {}).get('algorithm', model_name)
                }

                self.logger.info(f"Evaluated {model_name}: Anomalies = {n_anomalies} ({anomaly_rate*100:.2f}%)")

            except Exception as e:
                self.logger.error(f"Failed to evaluate {model_name}: {e}")
                results[model_name] = {'error': str(e)}

        return results

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

        # Add ROC-AUC if probabilities are available
        if y_pred_proba is not None:
            try:
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

    def _get_feature_importance(self, model, feature_names: List[str]) -> Optional[Dict[str, float]]:
        """
        Extract feature importance from model if available
        """
        try:
            importance = None

            # Tree-based models
            if hasattr(model, 'feature_importances_'):
                importance = model.feature_importances_
            # Linear models
            elif hasattr(model, 'coef_'):
                if len(model.coef_.shape) == 1:
                    importance = np.abs(model.coef_)
                else:
                    # For multiclass, take mean of absolute coefficients
                    importance = np.mean(np.abs(model.coef_), axis=0)
            # Other models with feature_importances_
            elif hasattr(model, 'feature_importances_'):
                importance = model.feature_importances_

            if importance is not None and len(feature_names) == len(importance):
                # Create dictionary mapping feature names to importance scores
                feature_importance_dict = {
                    feature_names[i]: float(importance[i])
                    for i in range(len(feature_names))
                }
                # Sort by importance (descending)
                sorted_dict = dict(sorted(feature_importance_dict.items(),
                                        key=lambda x: x[1], reverse=True))
                return sorted_dict

        except Exception as e:
            self.logger.debug(f"Could not extract feature importance: {e}")

        return None

    def save_evaluation_results(self, results: Dict[str, Any], results_dir: str = "reports/"):
        """
        Save evaluation results to disk
        """
        results_path = Path(results_dir)
        results_path.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Saving evaluation results to {results_path}")

        # Save detailed results
        results_file = results_path / "evaluation_results.joblib"
        joblib.dump(results, results_file)
        self.logger.info(f"Saved evaluation results to {results_file}")

        # Also save a summary as JSON for easy reading
        import json
        summary_file = results_path / "evaluation_summary.json"

        # Create a simplified summary
        summary = {}
        for model_type, model_results in results.items():
            summary[model_type] = {}
            for model_name, model_eval in model_results.items():
                if 'error' not in model_eval:
                    if model_type == 'classification':
                        summary[model_type][model_name] = {
                            'accuracy': model_eval.get('metrics', {}).get('accuracy', 0),
                            'precision': model_eval.get('metrics', {}).get('precision', 0),
                            'recall': model_eval.get('metrics', {}).get('recall', 0),
                            'f1_score': model_eval.get('metrics', {}).get('f1_score', 0)
                        }
                    elif model_type == 'regression':
                        summary[model_type][model_name] = {
                            'r2': model_eval.get('metrics', {}).get('r2', 0),
                            'mae': model_eval.get('metrics', {}).get('mae', 0),
                            'rmse': model_eval.get('metrics', {}).get('rmse', 0)
                        }
                    elif model_type == 'clustering':
                        summary[model_type][model_name] = {
                            'n_clusters': model_eval.get('n_clusters', 0),
                            'silhouette_score': model_eval.get('silhouette_score', 0)
                        }
                    elif model_type == 'anomaly_detection':
                        summary[model_type][model_name] = {
                            'anomaly_rate': model_eval.get('anomaly_rate', 0),
                            'n_anomalies': model_eval.get('n_anomalies', 0)
                        }
                else:
                    summary[model_type][model_name] = {'error': model_eval['error']}

        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        self.logger.info(f"Saved evaluation summary to {summary_file}")

    def load_evaluation_results(self, results_dir: str = "reports/") -> Dict[str, Any]:
        """
        Load previously saved evaluation results
        """
        results_path = Path(results_dir)
        results_file = results_path / "evaluation_results.joblib"

        if not results_file.exists():
            raise FileNotFoundError(f"Evaluation results file not found: {results_file}")

        self.logger.info(f"Loading evaluation results from {results_file}")
        results = joblib.load(results_file)
        return results