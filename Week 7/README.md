# Week 7: Clustering and Customer Segmentation

This folder contains the Week 7 clustering assignment for segmenting customers based on purchasing behavior from the Online Retail II dataset.

## Contents

- `Week_7_Clustering_Assignment.ipynb`  
  Main Jupyter notebook with data cleaning, feature engineering, clustering models, validation, and business interpretation.

- `online_retail_II.xlsx`  
  Online Retail II Excel dataset used by the notebook.

## Notebook Topics

The notebook covers:

- Loading and inspecting the UCI Online Retail II dataset
- Cleaning missing customer IDs, cancelled invoices, and invalid quantity or price values
- Creating a customer-level RFM matrix:
  - Recency
  - Frequency
  - Monetary value
- Scaling customer features before clustering
- K-Means clustering with elbow and silhouette analysis
- Comparing random initialization with K-Means++ initialization
- Hierarchical clustering with dendrogram and linkage comparison
- DBSCAN clustering with k-distance plots and parameter experiments
- Cluster validation using Silhouette Score, Davies-Bouldin Index, and Calinski-Harabasz Index
- Comparing clustering methods and choosing a final segmentation
- Writing customer segment profiles, marketing recommendations, and a failure log

## Data

The notebook uses the UCI Online Retail II dataset. The Excel file is included in this folder as:

```text
online_retail_II.xlsx
```

Keep this file in the same folder as the notebook so the data loading cell works correctly.

## Requirements

Use a Python environment with Jupyter and the main data science libraries installed:

```bash
pip install notebook pandas numpy matplotlib seaborn scikit-learn scipy plotly openpyxl
```

The notebook metadata shows Python 3.14.4 was used.

## How to Run

1. Open the notebook in Jupyter Notebook, JupyterLab, or VS Code.
2. Make sure `online_retail_II.xlsx` is in the same folder as the notebook.
3. Run the notebook cells from top to bottom.
4. Review the generated plots, cluster profiles, validation table, business narrative, and failure log.

## Main Result

The final segmentation uses K-Means with `k=4` clusters. The notebook identifies four customer groups:

- Promising Newcomers
- Champions
- At-Risk Customers
- Lost Customers

K-Means was selected because it produced the strongest overall validation results and created balanced, interpretable customer segments for marketing decisions.

## Notes

- One row in the final customer matrix represents one customer.
- Validation metrics are used together with business reasoning, since mathematically clean clusters are not always the most useful for customer segmentation.
- DBSCAN noise points are treated carefully because they still represent real customers.
- The notebook includes a failure log documenting hypotheses that did not work as expected.
