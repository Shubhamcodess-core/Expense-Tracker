# Machine Learning Expense Analyzer
A comprehensive machine learning project for personal expense analysis and prediction.

## Project Overview
This project implements machine learning algorithms to analyze spending patterns, categorize expenses automatically, and predict future expenses based on historical data. It covers the complete machine learning lifecycle from data preprocessing to model deployment.

## Features
- Expense categorization using supervised learning
- Expense amount prediction using regression models
- Spending pattern analysis and clustering
- Financial anomaly detection
- Interactive visualizations
- Model performance evaluation and comparison
- Exportable reports and predictions

## Technical Stack
- **Language**: Python 3.8+
- **Libraries**: 
  - Data Processing: pandas, numpy
  - Machine Learning: scikit-learn, xgboost, lightgbm
  - Visualization: matplotlib, seaborn, plotly
  - Utilities: joblib, yaml, tqdm

## Project Structure
```
ML_Expense_Analyzer/
├── data/                    # Data storage directory
│   ├── raw/                 # Raw expense data
│   ├── processed/           # Cleaned and processed data
│   └── external/            # External data sources
├── models/                  # Trained model storage
├── notebooks/               # Jupyter notebooks for exploration
├── src/                     # Source code
│   ├── __init__.py
│   ├── data/                # Data processing modules
│   ├── features/            # Feature engineering
│   ├── models/              # Model training and evaluation
│   └── utils/               # Utility functions
├── reports/                 # Generated reports and visualizations
├── requirements.txt         # Python dependencies
├── config.yaml              # Configuration file
└── main.py                  # Main execution script
```

## Installation
```bash
# Clone the repository
git clone <repository-url>
cd ML_Expense_Analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage
```bash
# Run the complete ML pipeline
python main.py

# Or run specific modules
python -m src.data.preprocess
python -m src.models.train
python -m src.models.evaluate
```

## Machine Learning Components
1. **Expense Categorization** (Classification)
   - Algorithms: Random Forest, XGBoost, SVM, Neural Networks
   - Features: amount, time features, merchant descriptions, historical patterns
   - Target: Expense category (Food, Transport, Entertainment, etc.)

2. **Expense Prediction** (Regression)
   - Algorithms: Linear Regression, Ridge, Lasso, Gradient Boosting
   - Features: historical spending, seasonality, economic indicators
   - Target: Future expense amounts

3. **Spending Clustering** (Unsupervised Learning)
   - Algorithm: K-Means, DBSCAN
   - Purpose: Identify spending patterns and user segments

4. **Anomaly Detection**
   - Algorithms: Isolation Forest, One-Class SVM
   - Purpose: Detect unusual or fraudulent transactions

## Data Requirements
The system expects expense data in CSV format with the following columns:
- date: Transaction date (YYYY-MM-DD)
- amount: Transaction amount (numeric)
- category: Expense category (for supervised learning)
- description/note: Transaction description
- currency: Transaction currency (optional)
- payment_method: How the transaction was made (optional)

## Model Performance
Reports include:
- Accuracy, Precision, Recall, F1-score (for classification)
- MAE, MSE, RMSE, R² (for regression)
- Confusion matrices
- Learning curves
- Feature importance analysis

## Future Enhancements
- Deep learning models for sequential spending patterns
- Integration with banking APIs for real-time data
- Web dashboard for interactive visualization
- Deployable API for expense prediction service
- Natural language processing for transaction descriptions