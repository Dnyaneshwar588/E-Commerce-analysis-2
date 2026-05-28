# Amazon Sales Analytics Dashboard

A resume-ready, business-oriented analytics project built with **Python, SQL, and Streamlit**. This dashboard cleans the Amazon sales dataset, loads it into SQLite, and exposes interactive insights for sales, customers, regions, products, and fulfillment.

## Executive Summary

This project analyzes Amazon order data to help a business understand where revenue comes from, which products and regions perform best, and where operational leakage occurs through cancellations or courier issues. It combines data cleaning, SQL-based aggregation, and an interactive dashboard to turn raw CSV data into decision-ready insights.

## Problem Statement

The raw sales file contains transaction-level records but no business summary. The goal is to answer practical questions such as:

- Which categories and products drive the most revenue?
- Which states and cities generate the strongest demand?
- How do B2B and non-B2B orders differ?
- Where are orders being cancelled or delayed?
- Which periods show sales growth or slowdown?

## Why This Project Matters

- It demonstrates an end-to-end analytics workflow, not just chart creation.
- It is suitable for placement interviews because every metric can be explained in business language.
- It shows SQL, Python, and dashboarding in one portfolio-ready project.

## Features

- Interactive Streamlit dashboard with sidebar filters
- Date, state, and category filters
- KPI cards for revenue, orders, order value, and cancellation rate
- Sales analysis: revenue trend, daily orders, category sales, top products
- Customer and business analysis: B2B vs Non-B2B, status mix, purchasing trends, sales growth
- Regional analysis: state-wise sales, city-wise orders, top-performing regions
- Product analysis: size demand, category performance, quantity analysis
- Delivery analysis: shipped vs cancelled, courier status, fulfillment performance
- SQL-backed aggregation layer for all analytics views
- Data cleaning and preprocessing pipeline

## Project Structure

```text
Amazon-Sales-Analytics/
│
├── dataset/
├── notebooks/
├── sql/
├── app.py
├── requirements.txt
└── README.md
```

## Dataset

Place `Amazon Sale Report.csv` inside `dataset/`.

The app also looks for the file in the workspace root, so it works in the current environment without extra setup.

## How to Run

1. Create and activate a Python environment.
2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Launch the dashboard:

```bash
streamlit run app.py
```

## SQL Usage

The project includes reusable SQL examples in `sql/analytics.sql`. The Streamlit app uses SQLite in memory and runs all aggregates from SQL queries.

## Analytical Focus

- Revenue and sales growth analysis
- Customer segment comparison
- Regional performance and demand concentration
- Product mix and size demand
- Fulfillment quality and cancellation pressure

## Business Insights You Can Present

- Which category generates the highest revenue
- Which state and city are the strongest demand centers
- Whether B2B orders contribute meaningful volume
- How cancellation and courier issues affect revenue
- Which months show growth or seasonal weakness

