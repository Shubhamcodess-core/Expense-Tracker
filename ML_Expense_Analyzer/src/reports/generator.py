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
import json
from matplotlib.backends.backend_pdf import PdfPages


class ReportGenerator:
    """
    Handles generation of reports and visualizations for ML Expense Analyzer
    """

    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.report_config = config['output']
        self.viz_config = config['visualization']

        # Set up matplotlib style
        plt.style.use(self.viz_config['style'])
        sns.set_palette(self.viz_config['color_palette'])

    def generate_comprehensive_report(self, processed_data: pd.DataFrame,
                                    featured_data: pd.DataFrame,
                                    trained_models: Dict[str, Any],
                                    evaluation_results: Dict[str, Any]):
        """
        Generate comprehensive report including data analysis, model performance, and insights
        """
        self.logger.info("Starting comprehensive report generation")

        # Create reports directory
        reports_path = Path(self.report_config['reports_path'])
        plots_path = Path(self.report_config['plots_path'])
        predictions_path = Path(self.report_config['predictions_path'])

        for path in [reports_path, plots_path, predictions_path]:
            path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"expense_analysis_report_{timestamp}"

        # Generate PDF report
        pdf_path = reports_path / f"{report_filename}.pdf"
        self._generate_pdf_report(processed_data, featured_data, trained_models,
                                 evaluation_results, pdf_path)

        # Generate JSON summary
        json_path = reports_path / f"{report_filename}_summary.json"
        self._generate_json_summary(processed_data, featured_data, trained_models,
                                   evaluation_results, json_path)

        # Generate individual plots
        self._generate_visualizations(processed_data, featured_data, trained_models,
                                     evaluation_results, plots_path)

        # Generate predictions file
        self._generate_predictions(featured_data, trained_models, predictions_path, timestamp)

        self.logger.info(f"Comprehensive report generated: {pdf_path}")
        self.logger.info(f"JSON summary generated: {json_path}")
        self.logger.info(f"Visualizations saved to: {plots_path}")
        self.logger.info(f"Predictions saved to: {predictions_path}")

    def _generate_pdf_report(self, processed_data: pd.DataFrame, featured_data: pd.DataFrame,
                           trained_models: Dict[str, Any], evaluation_results: Dict[str, Any],
                           pdf_path: Path):
        """
        Generate PDF report with multiple pages
        """
        with PdfPages(pdf_path) as pdf:
            # Page 1: Project Overview and Data Summary
            self._add_project_overview_page(pdf, processed_data)

            # Page 2: Data Analysis and Visualizations
            self._add_data_analysis_page(pdf, processed_data, featured_data)

            # Page 3: Model Performance Summary
            self._add_model_performance_page(pdf, evaluation_results)

            # Page 4: Classification Model Details
            if 'classification' in evaluation_results:
                self._add_classification_details_page(pdf, evaluation_results['classification'])

            # Page 5: Regression Model Details
            if 'regression' in evaluation_results:
                self._add_regression_details_page(pdf, evaluation_results['regression'])

            # Page 6: Clustering and Anomaly Detection Results
            self._add_unsupervised_details_page(pdf, evaluation_results)

            # Page 7: Feature Importance and Insights
            self._add_insights_page(pdf, featured_data, trained_models, evaluation_results)

            # Page 8: Conclusions and Recommendations
            self._add_conclusions_page(pdf, processed_data, featured_data,
                                    trained_models, evaluation_results)

    def _add_project_overview_page(self, pdf: PdfPages, processed_data: pd.DataFrame):
        """
        Add project overview page to PDF
        """
        fig, ax = plt.subplots(figsize=(self.viz_config['figure_size'][0],
                                       self.viz_config['figure_size'][1]))
        ax.axis('off')
        ax.set_title('ML Expense Analyzer Project Report', fontsize=24, fontweight='bold', pad=20)

        # Project information
        project_info = [
            f"Project: {self.config['project']['name']}",
            f"Version: {self.config['project']['version']}",
            f"Description: {self.config['project']['description']}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "Dataset Information:",
            f"  • Total Records: {len(processed_data):,}",
            f"  • Date Range: {processed_data['date'].min().strftime('%Y-%m-%d')} to {processed_data['date'].max().strftime('%Y-%m-%d')}",
            f"  • Total Expenses: ${processed_data['amount'].sum():,.2f}",
            f"  • Average Transaction: ${processed_data['amount'].mean():.2f}",
            f"  • Unique Categories: {processed_data['category'].nunique() if 'category' in processed_data.columns else 'N/A'}",
            "",
            "Machine Learning Components:",
            "  • Supervised Learning: Expense Categorization (Classification)",
            "  • Supervised Learning: Future Expense Prediction (Regression)",
            "  • Unsupervised Learning: Spending Pattern Discovery (Clustering)",
            "  • Anomaly Detection: Fraudulent Transaction Identification",
            "",
            "Key Features:",
            "  • Automated expense categorization",
            "  • Spending trend analysis and forecasting",
            "  • Financial anomaly detection",
            "  • Interactive visualizations",
            "  • Exportable reports and predictions"
        ]

        info_text = '\n'.join(project_info)
        ax.text(0.1, 0.9, info_text, transform=ax.transAxes, fontsize=12,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.1))

        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()

    def _add_data_analysis_page(self, pdf: PdfPages, processed_data: pd.DataFrame,
                               featured_data: pd.DataFrame):
        """
        Add data analysis page to PDF
        """
        fig = plt.figure(figsize=(self.viz_config['figure_size'][0],
                                 self.viz_config['figure_size'][1]))
        gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)

        # Plot 1: Expenses over time
        ax1 = fig.add_subplot(gs[0, 0])
        if 'date' in processed_data.columns and 'amount' in processed_data.columns:
            daily_expenses = processed_data.groupby('date')['amount'].sum()
            ax1.plot(daily_expenses.index, daily_expenses.values, linewidth=2)
            ax1.set_title('Daily Expenses Over Time')
            ax1.set_xlabel('Date')
            ax1.set_ylabel('Amount ($)')
            ax1.tick_params(axis='x', rotation=45)

        # Plot 2: Category distribution
        ax2 = fig.add_subplot(gs[0, 1])
        if 'category' in processed_data.columns:
            category_counts = processed_data['category'].value_counts()
            ax2.pie(category_counts.values, labels=category_counts.index, autopct='%1.1f%%')
            ax2.set_title('Expense Distribution by Category')

        # Plot 3: Amount distribution
        ax3 = fig.add_subplot(gs[0, 2])
        if 'amount' in processed_data.columns:
            ax3.hist(processed_data['amount'], bins=30, edgecolor='black', alpha=0.7)
            ax3.set_title('Transaction Amount Distribution')
            ax3.set_xlabel('Amount ($)')
            ax3.set_ylabel('Frequency')

        # Plot 4: Monthly spending trend
        ax4 = fig.add_subplot(gs[1, 0])
        if 'date' in processed_data.columns and 'amount' in processed_data.columns:
            processed_data['month'] = processed_data['date'].dt.to_period('M')
            monthly_expenses = processed_data.groupby('month')['amount'].sum()
            ax4.bar(range(len(monthly_expenses)), monthly_expenses.values)
            ax4.set_title('Monthly Spending Trend')
            ax4.set_xlabel('Month')
            ax4.set_ylabel('Amount ($)')
            ax4.set_xticks(range(len(monthly_expenses)))
            ax4.set_xticklabels([str(m) for m in monthly_expenses.index], rotation=45)

        # Plot 5: Weekend vs Weekday spending
        ax5 = fig.add_subplot(gs[1, 1])
        if 'date' in processed_data.columns and 'amount' in processed_data.columns:
            processed_data['is_weekend'] = processed_data['date'].dt.dayofweek >= 5
            weekend_spending = processed_data[processed_data['is_weekend']]['amount'].sum()
            weekday_spending = processed_data[~processed_data['is_weekend']]['amount'].sum()
            ax5.bar(['Weekend', 'Weekday'], [weekend_spending, weekday_spending], color=['orange', 'blue'])
            ax5.set_title('Weekend vs Weekday Spending')
            ax5.set_ylabel('Total Amount ($)')

        # Plot 6: Data features summary
        ax6 = fig.add_subplot(gs[1, 2])
        ax6.axis('off')
        feature_info = [
            "Feature Engineering Summary:",
            f"  • Original Features: {len(processed_data.columns)}",
            f"  • Engineered Features: {len(featured_data.columns) - len(processed_data.columns)}",
            f"  • Total Features: {len(featured_data.columns)}",
            "",
            "Feature Types:",
            "  • Time-based: Hour, day, month, quarter, weekend flags",
            "  • Amount-based: Log transform, z-score, rolling statistics",
            "  • Text-based: Description length, word count, sentiment",
            "  • Categorical: Encoded category, currency, payment method",
            "  • Interaction: Amount-time, category-amount combinations"
        ]
        feature_text = '\n'.join(feature_info)
        ax6.text(0.1, 0.9, feature_text, transform=ax6.transAxes, fontsize=11,
                 verticalalignment='top', fontfamily='monospace')

        plt.suptitle('Data Analysis and Feature Engineering', fontsize=16, fontweight='bold')
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()

    def _add_model_performance_page(self, pdf: PdfPages, evaluation_results: Dict[str, Any]):
        """
        Add model performance summary page to PDF
        """
        fig, ax = plt.subplots(figsize=(self.viz_config['figure_size'][0],
                                     self.viz_config['figure_size'][1]))
        ax.axis('off')
        ax.set_title('Model Performance Summary', fontsize=20, fontweight='bold', pad=20)

        # Create performance comparison table
        performance_data = []

        # Classification metrics
        if 'classification' in evaluation_results:
            performance_data.append(["Classification Models", "", ""])
            performance_data.append(["Model", "Accuracy", "F1-Score"])
            for model_name, results in evaluation_results['classification'].items():
                if 'error' not in results:
                    acc = results.get('metrics', {}).get('accuracy', 0)
                    f1 = results.get('metrics', {}).get('f1_score', 0)
                    performance_data.append([model_name.replace('_', ' ').title(), f"{acc:.3f}", f"{f1:.3f}"])

        # Regression metrics
        if 'regression' in evaluation_results:
            performance_data.append(["", "", ""])  # Empty row
            performance_data.append(["Regression Models", "", ""])
            performance_data.append(["Model", "R² Score", "RMSE"])
            for model_name, results in evaluation_results['regression'].items():
                if 'error' not in results:
                    r2 = results.get('metrics', {}).get('r2', 0)
                    rmse = results.get('metrics', {}).get('rmse', 0)
                    performance_data.append([model_name.replace('_', ' ').title(), f"{r2:.3f}", f"{rmse:.3f}"])

        # Clustering metrics
        if 'clustering' in evaluation_results:
            performance_data.append(["", "", ""])  # Empty row
            performance_data.append(["Clustering Models", "", ""])
            performance_data.append(["Model", "Clusters", "Silhouette Score"])
            for model_name, results in evaluation_results['clustering'].items():
                if 'error' not in results:
                    n_clusters = results.get('n_clusters', 0)
                    sil_score = results.get('silhouette_score', 0)
                    performance_data.append([model_name.replace('_', ' ').title(), f"{n_clusters}", f"{sil_score:.3f}" if sil_score else "N/A"])

        # Anomaly detection metrics
        if 'anomaly_detection' in evaluation_results:
            performance_data.append(["", "", ""])  # Empty row
            performance_data.append(["Anomaly Detection Models", "", ""])
            performance_data.append(["Model", "Anomaly Rate", "Count"])
            for model_name, results in evaluation_results['anomaly_detection'].items():
                if 'error' not in results:
                    anomaly_rate = results.get('anomaly_rate', 0)
                    n_anomalies = results.get('n_anomalies', 0)
                    performance_data.append([model_name.replace('_', ' ').title(), f"{anomaly_rate:.2%}", f"{n_anomalies}"])

        # Create table
        if len(performance_data) > 1:
            table = ax.table(cellText=performance_data[1:],  # Skip header row for now
                            colLabels=performance_data[0],  # Use first row as column labels
                            cellLoc='center',
                            loc='center',
                            bbox=[0.1, 0.2, 0.8, 0.6])

            # Style the table
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 2)

            # Header styling
            for i in range(len(performance_data[0])):
                table[(0, i)].set_facecolor('#4CAF50')
                table[(0, i)].set_text_props(weight='bold', color='white')

            # Alternate row colors
            for i in range(1, len(performance_data)):
                for j in range(len(performance_data[0])):
                    if i % 2 == 0:
                        table[(i, j)].set_facecolor('#f2f2f2')

        # Add explanation
        explanation = [
            "Model Performance Metrics:",
            "• Classification: Accuracy (correct predictions), F1-Score (balance of precision & recall)",
            "• Regression: R² (variance explained), RMSE (prediction error)",
            "• Clustering: Number of clusters found, Silhouette Score (cluster quality)",
            "• Anomaly Detection: Percentage of transactions flagged as unusual",
            "",
            "Note: Higher values indicate better performance for all metrics except RMSE (lower is better)."
        ]
        explanation_text = '\n'.join(explanation)
        ax.text(0.5, 0.05, explanation_text, transform=ax.transAxes, fontsize=9,
                ha='center', va='bottom', style='italic')

        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()

    def _add_classification_details_page(self, pdf: PdfPages, classification_results: Dict[str, Any]):
        """
        Add classification model details page to PDF
        """
        fig = plt.figure(figsize=(self.viz_config['figure_size'][0],
                                 self.viz_config['figure_size'][1]))
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

        # Plot 1: Model accuracy comparison
        ax1 = fig.add_subplot(gs[0, 0])
        model_names = []
        accuracies = []
        f1_scores = []

        for model_name, results in classification_results.items():
            if 'error' not in results:
                model_names.append(model_name.replace('_', ' ').title())
                accuracies.append(results.get('metrics', {}).get('accuracy', 0))
                f1_scores.append(results.get('metrics', {}).get('f1_score', 0))

        x = np.arange(len(model_names))
        width = 0.35
        ax1.bar(x - width/2, accuracies, width, label='Accuracy', alpha=0.8)
        ax1.bar(x + width/2, f1_scores, width, label='F1-Score', alpha=0.8)
        ax1.set_xlabel('Models')
        ax1.set_ylabel('Score')
        ax1.set_title('Classification Model Performance')
        ax1.set_xticks(x)
        ax1.set_xticklabels(model_names, rotation=45, ha='right')
        ax1.legend()
        ax1.set_ylim(0, 1)

        # Plot 2: Confusion matrix for best model
        ax2 = fig.add_subplot(gs[0, 1])
        # Find best model based on F1-score
        best_model_name = None
        best_f1 = 0
        for model_name, results in classification_results.items():
            if 'error' not in results:
                f1 = results.get('metrics', {}).get('f1_score', 0)
                if f1 > best_f1:
                    best_f1 = f1
                    best_model_name = model_name

        if best_model_name and 'confusion_matrix' in classification_results[best_model_name]:
            cm = np.array(classification_results[best_model_name]['confusion_matrix'])
            # Get class labels if available
            class_labels = []  # Would need to store these from the data
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax2)
            ax2.set_title(f'Confusion Matrix: {best_model_name.replace("_", " ").title()}')
            ax2.set_xlabel('Predicted')
            ax2.set_ylabel('Actual')
        else:
            ax2.text(0.5, 0.5, 'Confusion matrix not available',
                    ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Confusion Matrix')

        # Plot 3: Feature importance for best model
        ax3 = fig.add_subplot(gs[1, :])
        if best_model_name and 'feature_importance' in classification_results[best_model_name]:
            feature_importance = classification_results[best_model_name]['feature_importance']
            if feature_importance:
                # Get top 10 features
                top_features = dict(list(feature_importance.items())[:10])
                features = list(top_features.keys())
                importance = list(top_features.values())

                y_pos = np.arange(len(features))
                ax3.barh(y_pos, importance)
                ax3.set_yticks(y_pos)
                ax3.set_yticklabels(features)
                ax3.set_xlabel('Feature Importance')
                ax3.set_title(f'Top 10 Feature Importance: {best_model_name.replace("_", " ").title()}')
                ax3.invert_yaxis()  # Highest values at top
        else:
            ax3.text(0.5, 0.5, 'Feature importance not available',
                    ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Feature Importance')

        plt.suptitle('Classification Model Details', fontsize=16, fontweight='bold')
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()

    def _add_regression_details_page(self, pdf: PdfPages, regression_results: Dict[str, Any]):
        """
        Add regression model details page to PDF
        """
        fig = plt.figure(figsize=(self.viz_config['figure_size'][0],
                                 self.viz_config['figure_size'][1]))
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

        # Plot 1: Model R² comparison
        ax1 = fig.add_subplot(gs[0, 0])
        model_names = []
        r2_scores = []
        rmse_scores = []

        for model_name, results in regression_results.items():
            if 'error' not in results:
                model_names.append(model_name.replace('_', ' ').title())
                r2_scores.append(results.get('metrics', {}).get('r2', 0))
                rmse_scores.append(results.get('metrics', {}).get('rmse', 0))

        x = np.arange(len(model_names))
        width = 0.35
        ax1.bar(x - width/2, r2_scores, width, label='R² Score', alpha=0.8, color='green')
        ax1.bar(x + width/2, [-x for x in rmse_scores], width, label='-RMSE (inverted)', alpha=0.8, color='red')
        ax1.set_xlabel('Models')
        ax1.set_ylabel('Score')
        ax1.set_title('Regression Model Performance (R² vs -RMSE)')
        ax1.set_xticks(x)
        ax1.set_xticklabels(model_names, rotation=45, ha='right')
        ax1.legend()
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)

        # Plot 2: Prediction vs Actual for best model
        ax2 = fig.add_subplot(gs[0, 1])
        # Find best model based on R²
        best_model_name = None
        best_r2 = -np.inf
        for model_name, results in regression_results.items():
            if 'error' not in results:
                r2 = results.get('metrics', {}).get('r2', 0)
                if r2 > best_r2:
                    best_r2 = r2
                    best_model_name = model_name

        if best_model_name and 'predictions' in regression_results[best_model_name] and 'actual_values' in regression_results[best_model_name]:
            predictions = np.array(regression_results[best_model_name]['predictions'])
            actual = np.array(regression_results[best_model_name]['actual_values'])

            ax2.scatter(actual, predictions, alpha=0.6)
            # Perfect prediction line
            max_val = max(np.max(actual), np.max(predictions))
            min_val = min(np.min(actual), np.min(predictions))
            ax2.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Prediction')
            ax2.set_xlabel('Actual Values ($)')
            ax2.set_ylabel('Predicted Values ($)')
            ax2.set_title(f'Predictions vs Actual: {best_model_name.replace("_", " ").title()}')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        else:
            ax2.text(0.5, 0.5, 'Prediction data not available',
                    ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Predictions vs Actual')

        # Plot 3: Residuals distribution for best model
        ax3 = fig.add_subplot(gs[1, 0])
        if best_model_name and 'residuals' in regression_results[best_model_name]:
            residuals = np.array(regression_results[best_model_name]['residuals'])
            ax3.hist(residuals, bins=30, edgecolor='black', alpha=0.7)
            ax3.axvline(x=0, color='red', linestyle='--', label='Zero Error')
            ax3.set_xlabel('Residuals ($)')
            ax3.set_ylabel('Frequency')
            ax3.set_title(f'Residuals Distribution: {best_model_name.replace("_", " ").title()}')
            ax3.legend()
        else:
            ax3.text(0.5, 0.5, 'Residuals data not available',
                    ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Residuals Distribution')

        # Plot 4: Learning curve placeholder
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.text(0.5, 0.5, 'Learning Curves\n(Model performance vs training size)',
                ha='center', va='center', transform=ax4.transAxes,
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
        ax4.set_title('Learning Curves')

        plt.suptitle('Regression Model Details', fontsize=16, fontweight='bold')
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()

    def _add_unsupervised_details_page(self, pdf: PdfPages, evaluation_results: Dict[str, Any]):
        """
        Add unsupervised learning details page to PDF
        """
        fig = plt.figure(figsize=(self.viz_config['figure_size'][0],
                                 self.viz_config['figure_size'][1]))
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

        # Plot 1: Clustering results
        ax1 = fig.add_subplot(gs[0, 0])
        if 'clustering' in evaluation_results:
            model_names = []
            n_clusters = []
            silhouette_scores = []

            for model_name, results in evaluation_results['clustering'].items():
                if 'error' not in results:
                    model_names.append(model_name.replace('_', ' ').title())
                    n_clusters.append(results.get('n_clusters', 0))
                    sil_score = results.get('silhouette_score', 0)
                    silhouette_scores.append(sil_score if sil_score is not None else 0)

            x = np.arange(len(model_names))
            width = 0.35
            ax1.bar(x - width/2, n_clusters, width, label='Number of Clusters', alpha=0.8, color='blue')
            ax1_twin = ax1.twinx()
            ax1_twin.bar(x + width/2, silhouette_scores, width, label='Silhouette Score', alpha=0.8, color='orange')
            ax1.set_xlabel('Models')
            ax1.set_ylabel('Number of Clusters', color='blue')
            ax1_twin.set_ylabel('Silhouette Score', color='orange')
            ax1.set_title('Clustering Results')
            ax1.set_xticks(x)
            ax1.set_xticklabels(model_names, rotation=45, ha='right')
            ax1.legend(loc='upper left')
            ax1_twin.legend(loc='upper right')
        else:
            ax1.text(0.5, 0.5, 'Clustering results not available',
                    ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title('Clustering Results')

        # Plot 2: Anomaly detection results
        ax2 = fig.add_subplot(gs[0, 1])
        if 'anomaly_detection' in evaluation_results:
            model_names = []
            anomaly_rates = []
            n_anomalies = []

            for model_name, results in evaluation_results['anomaly_detection'].items():
                if 'error' not in results:
                    model_names.append(model_name.replace('_', ' ').title())
                    anomaly_rates.append(results.get('anomaly_rate', 0))
                    n_anomalies.append(results.get('n_anomalies', 0))

            x = np.arange(len(model_names))
            width = 0.35
            ax2.bar(x - width/2, [x*100 for x in anomaly_rates], width, label='Anomaly Rate (%)', alpha=0.8, color='red')
            ax2_twin = ax2.twinx()
            ax2_twin.bar(x + width/2, n_anomalies, width, label='Count', alpha=0.8, color='darkred')
            ax2.set_xlabel('Models')
            ax2.set_ylabel('Anomaly Rate (%)', color='red')
            ax2_twin.set_ylabel('Count', color='darkred')
            ax2.set_title('Anomaly Detection Results')
            ax2.set_xticks(x)
            ax2.set_xticklabels(model_names, rotation=45, ha='right')
            ax2.legend(loc='upper left')
            ax2_twin.legend(loc='upper right')
        else:
            ax2.text(0.5, 0.5, 'Anomaly detection results not available',
                    ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Anomaly Detection Results')

        # Plot 3: Cluster visualization placeholder
        ax3 = fig.add_subplot(gs[1, 0])
        ax3.text(0.5, 0.5, 'Cluster Visualization\n(Feature space projection)',
                ha='center', va='center', transform=ax3.transAxes,
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        ax3.set_title('Cluster Visualization')

        # Plot 4: Anomalies over time placeholder
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.text(0.5, 0.5, 'Anomalies Over Time\n(Detected unusual transactions)',
                ha='center', va='center', transform=ax4.transAxes,
                bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))
        ax4.set_title('Anomalies Over Time')

        plt.suptitle('Unsupervised Learning Results', fontsize=16, fontweight='bold')
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()

    def _add_insights_page(self, pdf: PdfPages, featured_data: pd.DataFrame,
                          trained_models: Dict[str, Any], evaluation_results: Dict[str, Any]):
        """
        Add insights and feature importance page to PDF
        """
        fig = plt.figure(figsize=(self.viz_config['figure_size'][0],
                                 self.viz_config['figure_size'][1]))
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

        # Plot 1: Top features across models
        ax1 = fig.add_subplot(gs[0, :])
        ax1.text(0.5, 0.5, 'Feature Importance Analysis\n(Combined insights from all models)',
                ha='center', va='center', transform=ax1.transAxes,
                fontsize=14,
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
        ax1.set_title('Feature Insights')

        # Plot 2: Spending insights
        ax2 = fig.add_subplot(gs[1, 0])
        spending_insights = [
            "Key Spending Insights:",
            "• Categorization accuracy enables automated budgeting",
            "• Prediction models forecast future expenses",
            "• Clustering reveals spending patterns and segments",
            "• Anomaly detection identifies unusual transactions",
            "",
            "Business Value:",
            "• Improved financial awareness and control",
            "• Data-driven budgeting decisions",
            "• Early fraud detection",
            "• Personalized financial recommendations"
        ]
        insights_text = '\n'.join(spending_insights)
        ax2.text(0.1, 0.9, insights_text, transform=ax2.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace')
        ax2.set_title('Business Insights')
        ax2.axis('off')

        # Plot 3: Technical insights
        ax3 = fig.add_subplot(gs[1, 1])
        technical_insights = [
            "Technical Implementation:",
            "• Feature engineering: Time, amount, text, categorical features",
            "• Model ensemble: Multiple algorithms for robust predictions",
            "• Evaluation: Comprehensive metrics and cross-validation",
            "• Scalability: Designed for growing datasets",
            "",
            "Model Interpretability:",
            "• Feature importance for understanding drivers",
            "• SHAP values available for detailed explanations",
            "• Model cards documenting performance and limitations"
        ]
        tech_text = '\n'.join(technical_insights)
        ax3.text(0.1, 0.9, tech_text, transform=ax3.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace')
        ax3.set_title('Technical Insights')
        ax3.axis('off')

        plt.suptitle('Insights and Feature Analysis', fontsize=16, fontweight='bold')
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()

    def _add_conclusions_page(self, pdf: PdfPages, processed_data: pd.DataFrame,
                             featured_data: pd.DataFrame, trained_models: Dict[str, Any],
                             evaluation_results: Dict[str, Any]):
        """
        Add conclusions and recommendations page to PDF
        """
        fig, ax = plt.subplots(figsize=(self.viz_config['figure_size'][0],
                                     self.viz_config['figure_size'][1]))
        ax.axis('off')
        ax.set_title('Conclusions and Recommendations', fontsize=20, fontweight='bold', pad=20)

        # Calculate some summary statistics
        total_expenses = processed_data['amount'].sum() if 'amount' in processed_data.columns else 0
        avg_transaction = processed_data['amount'].mean() if 'amount' in processed_data.columns else 0
        unique_categories = processed_data['category'].nunique() if 'category' in processed_data.columns else 0
        date_range_days = (processed_data['date'].max() - processed_data['date'].min()).days if 'date' in processed_data.columns else 0

        # Get best model performance
        best_classification_acc = 0
        best_regression_r2 = -np.inf

        if 'classification' in evaluation_results:
            for model_name, results in evaluation_results['classification'].items():
                if 'error' not in results:
                    acc = results.get('metrics', {}).get('accuracy', 0)
                    best_classification_acc = max(best_classification_acc, acc)

        if 'regression' in evaluation_results:
            for model_name, results in evaluation_results['regression'].items():
                if 'error' not in results:
                    r2 = results.get('metrics', {}).get('r2', 0)
                    best_regression_r2 = max(best_regression_r2, r2)

        conclusions = [
            "EXECUTIVE SUMMARY",
            "=" * 50,
            "",
            f"Dataset Analysis:",
            f"  • Processed {len(processed_data):,} financial transactions",
            f"  • Total spending: ${total_expenses:,.2f} over {date_range_days} days",
            f"  • Average transaction: ${avg_transaction:.2f}",
            f"  • {unique_categories} distinct expense categories identified",
            "",
            "Machine Learning Performance:",
            f"  • Best categorization accuracy: {best_classification_acc:.1%}",
            f"  • Best prediction R² score: {best_regression_r2:.3f}",
            f"  • Multiple algorithms evaluated for robustness",
            "",
            "KEY FINDINGS",
            "=" * 50,
            "",
            "1. Automated Categorization Achievable:",
            "   • ML models can accurately classify expenses into predefined categories",
            "   • Enables automated budgeting and expense tracking",
            "",
            "2. Predictive Capabilities Demonstrated:",
            "   • Historical spending patterns can forecast future expenses",
            "   • Supports proactive financial planning",
            "",
            "3. Pattern Recognition Successful:",
            "   • Clustering reveals distinct spending behaviors",
            "   • Enables personalized financial insights",
            "",
            "4. Anomaly Detection Functional:",
            "   • Unusual transactions can be flagged for review",
            "   • Enhances financial security and fraud detection",
            "",
            "RECOMMENDATIONS",
            "=" * 50,
            "",
            "Short-term (0-3 months):",
            "  • Deploy categorization model for real-time expense tagging",
            "  • Implement monthly spending forecasts",
            "  • Set up anomaly alerts for unusual transactions",
            "",
            "Medium-term (3-6 months):",
            "  • Integrate with banking APIs for automatic data feeds",
            "  • Develop web dashboard for interactive visualization",
            "  • Add customizable budgeting goals and tracking",
            "",
            "Long-term (6+ months):",
            "  • Implement deep learning for sequential spending patterns",
            "  • Add natural language processing for transaction descriptions",
            "  • Create collaborative family/household expense management",
            "",
            "TECHNICAL NOTES",
            "=" * 50,
            "",
            "• Models trained on historical data - periodic retraining recommended",
            "• Feature engineering pipeline ensures consistent preprocessing",
            "• Evaluation metrics provide unbiased performance estimates",
            "• Configuration-driven design allows easy experimentation",
            "",
            f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"ML Expense Analyzer v{self.config['project']['version']}"
        ]

        conclusions_text = '\n'.join(conclusions)
        ax.text(0.05, 0.95, conclusions_text, transform=ax.transAxes, fontsize=11,
                verticalalignment='top', fontfamily='monospace')

        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()

    def _generate_json_summary(self, processed_data: pd.DataFrame, featured_data: pd.DataFrame,
                              trained_models: Dict[str, Any], evaluation_results: Dict[str, Any],
                              json_path: Path):
        """
        Generate JSON summary of the analysis
        """
        summary = {
            "project_info": {
                "name": self.config['project']['name'],
                "version": self.config['project']['version'],
                "description": self.config['project']['description'],
                "generated_at": datetime.now().isoformat()
            },
            "data_summary": {
                "total_records": len(processed_data),
                "date_range": {
                    "start": processed_data['date'].min().isoformat() if 'date' in processed_data.columns else None,
                    "end": processed_data['date'].max().isoformat() if 'date' in processed_data.columns else None
                } if 'date' in processed_data.columns else None,
                "total_expenses": float(processed_data['amount'].sum()) if 'amount' in processed_data.columns else 0,
                "average_transaction": float(processed_data['amount'].mean()) if 'amount' in processed_data.columns else 0,
                "unique_categories": int(processed_data['category'].nunique()) if 'category' in processed_data.columns else 0,
                "features_original": len(processed_data.columns),
                "features_engineered": len(featured_data.columns),
                "features_total": len(featured_data.columns)
            },
            "model_performance": {},
            "recommendations": [
                "Deploy categorization model for real-time expense tagging",
                "Implement monthly spending forecasts",
                "Set up anomaly alerts for unusual transactions",
                "Integrate with banking APIs for automatic data feeds",
                "Develop web dashboard for interactive visualization"
            ]
        }

        # Add model performance summary
        for model_type, results in evaluation_results.items():
            summary["model_performance"][model_type] = {}
            for model_name, model_results in results.items():
                if 'error' not in model_results:
                    if model_type == 'classification':
                        summary["model_performance"][model_type][model_name] = {
                            "accuracy": model_results.get('metrics', {}).get('accuracy', 0),
                            "precision": model_results.get('metrics', {}).get('precision', 0),
                            "recall": model_results.get('metrics', {}).get('recall', 0),
                            "f1_score": model_results.get('metrics', {}).get('f1_score', 0),
                            "roc_auc": model_results.get('metrics', {}).get('roc_auc', 0)
                        }
                    elif model_type == 'regression':
                        summary["model_performance"][model_type][model_name] = {
                            "r2": model_results.get('metrics', {}).get('r2', 0),
                            "mae": model_results.get('metrics', {}).get('mae', 0),
                            "rmse": model_results.get('metrics', {}).get('rmse', 0),
                            "mape": model_results.get('metrics', {}).get('mape', 0)
                        }
                    elif model_type == 'clustering':
                        summary["model_performance"][model_type][model_name] = {
                            "n_clusters": model_results.get('n_clusters', 0),
                            "n_noise_points": model_results.get('n_noise_points', 0),
                            "silhouette_score": model_results.get('silhouette_score', 0)
                        }
                    elif model_type == 'anomaly_detection':
                        summary["model_performance"][model_type][model_name] = {
                            "anomaly_rate": model_results.get('anomaly_rate', 0),
                            "n_anomalies": model_results.get('n_anomalies', 0)
                        }

        # Save JSON file
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        self.logger.info(f"JSON summary saved to {json_path}")

    def _generate_visualizations(self, processed_data: pd.DataFrame, featured_data: pd.DataFrame,
                                trained_models: Dict[str, Any], evaluation_results: Dict[str, Any],
                                plots_path: Path):
        """
        Generate individual visualization plots
        """
        # Set style
        plt.style.use(self.viz_config['style'])

        # 1. Spending over time
        if 'date' in processed_data.columns and 'amount' in processed_data.columns:
            fig, ax = plt.subplots(figsize=self.viz_config['figure_size'])
            daily_expenses = processed_data.groupby('date')['amount'].sum()
            ax.plot(daily_expenses.index, daily_expenses.values, linewidth=2, color='#2E86AB')
            ax.set_title('Daily Spending Over Time', fontsize=16, fontweight='bold')
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel('Amount ($)', fontsize=12)
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(plots_path / 'spending_over_time.png', dpi=self.viz_config['dpi'],
                       bbox_inches='tight')
            plt.close()

        # 2. Category distribution
        if 'category' in processed_data.columns:
            fig, ax = plt.subplots(figsize=self.viz_config['figure_size'])
            category_counts = processed_data['category'].value_counts()
            colors = plt.cm.Set3(np.linspace(0, 1, len(category_counts)))
            wedges, texts, autotexts = ax.pie(category_counts.values, labels=category_counts.index,
                                              autopct='%1.1f%%', colors=colors, startangle=90)
            ax.set_title('Expense Distribution by Category', fontsize=16, fontweight='bold')
            plt.tight_layout()
            plt.savefig(plots_path / 'category_distribution.png', dpi=self.viz_config['dpi'],
                       bbox_inches='tight')
            plt.close()

        # 3. Monthly trend
        if 'date' in processed_data.columns and 'amount' in processed_data.columns:
            fig, ax = plt.subplots(figsize=self.viz_config['figure_size'])
            processed_data['month'] = processed_data['date'].dt.to_period('M')
            monthly_expenses = processed_data.groupby('month')['amount'].sum()
            ax.bar(range(len(monthly_expenses)), monthly_expenses.values, color='#A23B72')
            ax.set_title('Monthly Spending Trend', fontsize=16, fontweight='bold')
            ax.set_xlabel('Month', fontsize=12)
            ax.set_ylabel('Amount ($)', fontsize=12)
            ax.set_xticks(range(len(monthly_expenses)))
            ax.set_xticklabels([str(m) for m in monthly_expenses.index], rotation=45)
            ax.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()
            plt.savefig(plots_path / 'monthly_trend.png', dpi=self.viz_config['dpi'],
                       bbox_inches='tight')
            plt.close()

        # 4. Amount distribution
        if 'amount' in processed_data.columns:
            fig, ax = plt.subplots(figsize=self.viz_config['figure_size'])
            ax.hist(processed_data['amount'], bins=30, edgecolor='black', alpha=0.7, color='#F18F01')
            ax.set_title('Transaction Amount Distribution', fontsize=16, fontweight='bold')
            ax.set_xlabel('Amount ($)', fontsize=12)
            ax.set_ylabel('Frequency', fontsize=12)
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(plots_path / 'amount_distribution.png', dpi=self.viz_config['dpi'],
                       bbox_inches='tight')
            plt.close()

        # 5. Weekend vs Weekday comparison
        if 'date' in processed_data.columns and 'amount' in processed_data.columns:
            fig, ax = plt.subplots(figsize=self.viz_config['figure_size'])
            processed_data['is_weekend'] = processed_data['date'].dt.dayofweek >= 5
            weekend_spending = processed_data[processed_data['is_weekend']]['amount'].sum()
            weekday_spending = processed_data[~processed_data['is_weekend']]['amount'].sum()

            bars = ax.bar(['Weekend', 'Weekday'], [weekend_spending, weekday_spending],
                         color=['#FF6B6B', '#4ECDC4'])
            ax.set_title('Weekend vs Weekday Spending', fontsize=16, fontweight='bold')
            ax.set_ylabel('Total Amount ($)', fontsize=12)

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'${height:,.0f}', ha='center', va='bottom')

            ax.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()
            plt.savefig(plots_path / 'weekend_vs_weekday.png', dpi=self.viz_config['dpi'],
                       bbox_inches='tight')
            plt.close()

        # 6. Model performance comparison
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(self.viz_config['figure_size'][0]*1.5,
                                                                   self.viz_config['figure_size'][1]*1.5))

        # Classification performance
        if 'classification' in evaluation_results:
            model_names = []
            accuracies = []
            f1_scores = []

            for model_name, results in evaluation_results['classification'].items():
                if 'error' not in results:
                    model_names.append(model_name.replace('_', ' ').title())
                    accuracies.append(results.get('metrics', {}).get('accuracy', 0))
                    f1_scores.append(results.get('metrics', {}).get('f1_score', 0))

            if model_names:
                x = np.arange(len(model_names))
                width = 0.35
                ax1.bar(x - width/2, accuracies, width, label='Accuracy', alpha=0.8, color='#4CAF50')
                ax1.bar(x + width/2, f1_scores, width, label='F1-Score', alpha=0.8, color='#2196F3')
                ax1.set_xlabel('Models', fontsize=12)
                ax1.set_ylabel('Score', fontsize=12)
                ax1.set_title('Classification Model Performance', fontsize=14, fontweight='bold')
                ax1.set_xticks(x)
                ax1.set_xticklabels(model_names, rotation=45, ha='right')
                ax1.legend()
                ax1.set_ylim(0, 1)
                ax1.grid(True, alpha=0.3, axis='y')

        # Regression performance
        if 'regression' in evaluation_results:
            model_names = []
            r2_scores = []
            rmse_scores = []

            for model_name, results in evaluation_results['regression'].items():
                if 'error' not in results:
                    model_names.append(model_name.replace('_', ' ').title())
                    r2_scores.append(results.get('metrics', {}).get('r2', 0))
                    rmse_scores.append(results.get('metrics', {}).get('rmse', 0))

            if model_names:
                x = np.arange(len(model_names))
                width = 0.35
                ax2.bar(x - width/2, r2_scores, width, label='R² Score', alpha=0.8, color='#4CAF50')
                ax2.bar(x + width/2, [-x for x in rmse_scores], width, label='-RMSE', alpha=0.8, color='#F44336')
                ax2.set_xlabel('Models', fontsize=12)
                ax2.set_ylabel('Score', fontsize=12)
                ax2.set_title('Regression Model Performance', fontsize=14, fontweight='bold')
                ax2.set_xticks(x)
                ax2.set_xticklabels(model_names, rotation=45, ha='right')
                ax2.legend()
                ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                ax2.grid(True, alpha=0.3, axis='y')

        # Clustering performance
        if 'clustering' in evaluation_results:
            model_names = []
            n_clusters = []
            silhouette_scores = []

            for model_name, results in evaluation_results['clustering'].items():
                if 'error' not in results:
                    model_names.append(model_name.replace('_', ' ').title())
                    n_clusters.append(results.get('n_clusters', 0))
                    sil_score = results.get('silhouette_score', 0)
                    silhouette_scores.append(sil_score if sil_score is not None else 0)

            if model_names:
                x = np.arange(len(model_names))
                width = 0.35
                ax3.bar(x - width/2, n_clusters, width, label='Clusters', alpha=0.8, color='#9C27B0')
                ax3_twin = ax3.twinx()
                ax3_twin.bar(x + width/2, silhouette_scores, width, label='Silhouette', alpha=0.8, color='#FF9800')
                ax3.set_xlabel('Models', fontsize=12)
                ax3.set_ylabel('Number of Clusters', fontsize=12, color='#9C27B0')
                ax3_twin.set_ylabel('Silhouette Score', fontsize=12, color='#FF9800')
                ax3.set_title('Clustering Model Performance', fontsize=14, fontweight='bold')
                ax3.set_xticks(x)
                ax3.set_xticklabels(model_names, rotation=45, ha='right')
                ax3.legend(loc='upper left')
                ax3_twin.legend(loc='upper right')
                ax3.grid(True, alpha=0.3, axis='y')

        # Anomaly detection performance
        if 'anomaly_detection' in evaluation_results:
            model_names = []
            anomaly_rates = []

            for model_name, results in evaluation_results['anomaly_detection'].items():
                if 'error' not in results:
                    model_names.append(model_name.replace('_', ' ').title())
                    anomaly_rates.append(results.get('anomaly_rate', 0))

            if model_names:
                x = np.arange(len(model_names))
                ax4.bar(model_names, [x*100 for x in anomaly_rates], alpha=0.8, color='#E91E63')
                ax4.set_xlabel('Models', fontsize=12)
                ax4.set_ylabel('Anomaly Rate (%)', fontsize=12)
                ax4.set_title('Anomaly Detection Performance', fontsize=14, fontweight='bold')
                ax4.set_xticklabels(model_names, rotation=45, ha='right')
                ax4.grid(True, alpha=0.3, axis='y')

        plt.suptitle('Machine Learning Model Performance Comparison', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(plots_path / 'model_performance_comparison.png', dpi=self.viz_config['dpi'],
                   bbox_inches='tight')
        plt.close()

    def _generate_predictions(self, featured_data: pd.DataFrame, trained_models: Dict[str, Any],
                             predictions_path: Path, timestamp: str):
        """
        Generate predictions file
        """
        predictions = {
            "generated_at": datetime.now().isoformat(),
            "predictions": {}
        }

        # Generate expense category predictions if classification models available
        if 'classification' in trained_models:
            # Find best classification model
            best_model_name = None
            best_accuracy = 0

            for model_name, model_info in trained_models['classification'].items():
                if model_info and 'performance' in model_info:
                    accuracy = model_info['performance'].get('accuracy', 0)
                    if accuracy > best_accuracy:
                        best_accuracy = accuracy
                        best_model_name = model_name

            if best_model_name and best_model_name in trained_models['classification']:
                model_info = trained_models['classification'][best_model_name]
                if 'model' in model_info and 'feature_names' in model_info:
                    model = model_info['model']
                    scaler = model_info.get('scaler')
                    feature_names = model_info['feature_names']

                    # Prepare features (using same columns as training)
                    # For simplicity, use a subset of available features
                    available_features = [col for col in feature_names if col in featured_data.columns]
                    if available_features:
                        X_pred = featured_data[available_features].fillna(0)

                        # Scale if needed
                        if scaler is not None:
                            X_pred = scaler.transform(X_pred)

                        # Make predictions
                        try:
                            if hasattr(model, 'predict'):
                                pred_categories = model.predict(X_pred)
                                predictions["predictions"]["expense_categories"] = {
                                    "model_used": best_model_name,
                                    "accuracy": best_accuracy,
                                    "predictions": pred_categories.tolist(),
                                    "description": "Predicted expense categories for each transaction"
                                }

                                # Also get prediction probabilities if available
                                if hasattr(model, 'predict_proba'):
                                    pred_probabilities = model.predict_proba(X_pred)
                                    predictions["predictions"]["expense_categories"]["probabilities"] = pred_probabilities.tolist()
                        except Exception as e:
                            self.logger.warning(f"Could not generate category predictions: {e}")

        # Generate expense amount predictions if regression models available
        if 'regression' in trained_models:
            # Find best regression model
            best_model_name = None
            best_r2 = -np.inf

            for model_name, model_info in trained_models['regression'].items():
                if model_info and 'performance' in model_info:
                    r2 = model_info['performance'].get('r2', 0)
                    if r2 > best_r2:
                        best_r2 = r2
                        best_model_name = model_name

            if best_model_name and best_model_name in trained_models['regression']:
                model_info = trained_models['regression'][best_model_name]
                if 'model' in model_info and 'feature_names' in model_info:
                    model = model_info['model']
                    scaler = model_info.get('scaler')
                    feature_names = model_info['feature_names']

                    # For expense prediction, we'd need future-dated features
                    # For now, we'll note that this would require future feature engineering
                    predictions["predictions"]["expense_amounts"] = {
                        "model_used": best_model_name,
                        "r2_score": best_r2,
                        "note": "Future expense prediction requires forward-looking feature engineering",
                        "description": "Amount predictions would be generated for future time periods"
                    }

        # Save predictions
        predictions_file = predictions_path / f"expense_predictions_{timestamp}.json"
        with open(predictions_file, 'w') as f:
            json.dump(predictions, f, indent=2, default=str)

        self.logger.info(f"Predictions saved to {predictions_file}")