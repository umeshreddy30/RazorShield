# Notebooks

These notebooks are intended for exploratory analysis and model evaluation.
Run them **after** the pipeline has been executed (`python run_pipeline.py`).

## Available Notebooks

### `01_data_exploration.ipynb`

Covers:
- Class balance (RTO vs non-RTO)
- Feature distributions by risk label
- Correlation heatmap
- COD vs prepaid RTO rate comparison
- Temporal patterns (hour, day, festival)

### `02_model_evaluation.ipynb`

Covers:
- PR curves for all three models (LR, RF, LightGBM)
- Confusion matrix visualisation
- Threshold sweep analysis
- SHAP beeswarm plot (feature importance)
- Business impact at different cost assumptions

## How to run

```bash
pip install jupyter
jupyter notebook notebooks/
```
