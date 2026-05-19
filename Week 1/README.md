# Week 1 Assignments

This folder contains the Week 1 assignment work for the Fuse Machines AI Fellowship 2026.

## Files

- `SQL-Assignment.pdf`: Assignment 1, Part 2 for SQL. It includes SQL query tasks related to customers, employees, orders, offices, payments, views, updates, and deletes.
- `Wk_1_Data_Wrangling_HeartAttack(Sulav-Koirala).ipynb`: A Jupyter notebook for the Week 1 data wrangling problem set using heart attack risk data.
- `datasets/`: Dataset folder used by the notebook.

## Notebook Summary

The notebook works with patient data from three CSV files:

- `patient_demographics.csv`
- `clinical_data.csv`
- `lifestyle_factors.csv`

Main tasks covered in the notebook:

- Loading the demographics, clinical, and lifestyle datasets.
- Inspecting the datasets using head, info, describe, and missing value checks.
- Cleaning the blood pressure column by splitting it into systolic and diastolic values.
- Checking for missing values.
- Performing exploratory data analysis on numerical and categorical variables.
- Comparing features with heart attack risk.
- Creating Pearson and Spearman correlation heatmaps.
- Reviewing the target variable distribution.
- Writing a final reflection on the analysis.

## Requirements

The notebook uses the following Python libraries:

- pandas
- numpy
- matplotlib
- seaborn
- scikit-learn

## How to Run

Open the notebook in Jupyter Notebook, JupyterLab, VS Code, or Google Colab.

If running locally, keep the `datasets` folder in the same directory as the notebook so the CSV file paths work correctly.
