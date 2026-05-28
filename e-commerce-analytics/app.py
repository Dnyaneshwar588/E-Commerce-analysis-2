from __future__ import annotations

import re
import sqlite3
from pathlib import Path
import io

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import ui_components

# Streamlit Page Setup
st.set_page_config(
    page_title="E-commerce Customer Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply global premium SaaS styles
st.markdown(ui_components.CSS_STYLES, unsafe_allow_html=True)

# Project Path Configurations
PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATA_PATHS = [
    PROJECT_ROOT / "dataset" / "Amazon Sale Report.csv",
    PROJECT_ROOT.parent / "Amazon Sale Report.csv",
    PROJECT_ROOT.parent / "dataset" / "Amazon Sale Report.csv",
]


def find_data_file() -> Path | None:
    """Locate the Amazon sales CSV in the project or workspace root."""
    for candidate in DEFAULT_DATA_PATHS:
        if candidate.exists():
            return candidate
    return None


@st.cache_data(show_spinner=False)
def load_sales_data(csv_path_or_buffer, date_column: str | None = None) -> pd.DataFrame:
    """Load and standardize the sales dataset.

    Accepts a file path or a file-like buffer (Streamlit upload).
    """
    # pandas can accept file-like objects directly
    frame = pd.read_csv(csv_path_or_buffer, low_memory=False)

    # Remove columns that are completely empty and normalize column names.
    frame = frame.dropna(axis=1, how="all")
    frame.columns = [re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower()).strip("_") for column in frame.columns]

    rename_map = {
        "order_id": "order_id",
        "date": "order_date",
        "status": "status",
        "fulfilment": "fulfilment",
        "sales_channel": "sales_channel",
        "ship_service_level": "ship_service_level",
        "style": "style",
        "sku": "sku",
        "category": "category",
        "size": "size",
        "asin": "asin",
        "courier_status": "courier_status",
        "qty": "qty",
        "currency": "currency",
        "amount": "amount",
        "ship_city": "ship_city",
        "ship_state": "ship_state",
        "ship_postal_code": "ship_postal_code",
        "ship_country": "ship_country",
        "promotion_ids": "promotion_ids",
        "b2b": "b2b",
        "fulfilled_by": "fulfilled_by",
    }
    frame = frame.rename(columns=rename_map)

    # Keep the columns that drive the dashboard and analytics.
    expected_columns = [
        "order_id",
        "order_date",
        "status",
        "fulfilment",
        "sales_channel",
        "ship_service_level",
        "style",
        "sku",
        "category",
        "size",
        "asin",
        "courier_status",
        "qty",
        "currency",
        "amount",
        "ship_city",
        "ship_state",
        "ship_postal_code",
        "ship_country",
        "promotion_ids",
        "b2b",
        "fulfilled_by",
    ]
    present_columns = [column for column in expected_columns if column in frame.columns]
    frame = frame[present_columns].copy()

    # Standardize text values.
    for column in frame.select_dtypes(include="object").columns:
        frame[column] = frame[column].astype(str).str.strip()
        frame[column] = frame[column].replace({"nan": np.nan, "None": np.nan, "": np.nan})

    frame["status"] = frame.get("status", pd.Series(dtype="object")).fillna("Unknown")
    frame["category"] = frame.get("category", pd.Series(dtype="object")).fillna("Unknown")
    frame["size"] = frame.get("size", pd.Series(dtype="object")).fillna("Unknown")
    frame["ship_city"] = frame.get("ship_city", pd.Series(dtype="object")).fillna("Unknown")
    frame["ship_state"] = frame.get("ship_state", pd.Series(dtype="object")).fillna("Unknown")
    frame["courier_status"] = frame.get("courier_status", pd.Series(dtype="object")).fillna("Unknown")
    frame["currency"] = frame.get("currency", pd.Series(dtype="object")).fillna("INR")
    frame["ship_country"] = frame.get("ship_country", pd.Series(dtype="object")).fillna("IN")
    frame["fulfilled_by"] = frame.get("fulfilled_by", pd.Series(dtype="object")).fillna("Unknown")
    frame["sales_channel"] = frame.get("sales_channel", pd.Series(dtype="object")).fillna("Unknown")
    frame["fulfilment"] = frame.get("fulfilment", pd.Series(dtype="object")).fillna("Unknown")
    frame["ship_service_level"] = frame.get("ship_service_level", pd.Series(dtype="object")).fillna("Unknown")
    frame["style"] = frame.get("style", pd.Series(dtype="object")).fillna("Unknown")
    frame["sku"] = frame.get("sku", pd.Series(dtype="object")).fillna("Unknown")

    # Parse date and numeric fields.
    # If caller provided a specific date column, prefer it
    if date_column and "order_date" not in frame.columns:
        if date_column in frame.columns:
            frame = frame.rename(columns={date_column: "order_date"})
        else:
            # try case-insensitive match
            lower_map = {c.lower(): c for c in frame.columns}
            if date_column.lower() in lower_map:
                actual = lower_map[date_column.lower()]
                frame = frame.rename(columns={actual: "order_date"})
            else:
                # try normalized match (remove non-alphanum)
                def _norm(s: str) -> str:
                    return re.sub(r"[^a-z0-9]+", "", str(s).lower())

                norm_map = {_norm(c): c for c in frame.columns}
                if _norm(date_column) in norm_map:
                    actual = norm_map[_norm(date_column)]
                    frame = frame.rename(columns={actual: "order_date"})

    # Ensure `order_date` exists: try common names or detect the best date-like column
    if "order_date" not in frame.columns:
        # prefer any column containing 'date'
        candidates = [c for c in frame.columns if "date" in c]
        if candidates:
            frame = frame.rename(columns={candidates[0]: "order_date"})
        else:
            # heuristic: find the column with the most parseable datetimes
            best_col = None
            best_count = 0
            for col in frame.columns:
                try:
                    parsed = pd.to_datetime(frame[col], errors="coerce")
                    count = int(parsed.notna().sum())
                    if count > best_count:
                        best_count = count
                        best_col = col
                except Exception:
                    continue
            if best_col is not None and best_count >= max(1, int(0.1 * len(frame))):
                frame = frame.rename(columns={best_col: "order_date"})

    if "order_date" not in frame.columns:
        raise ValueError(f"Could not find a date column to use as 'order_date'. Available columns: {', '.join(frame.columns)}")

    frame["order_date"] = pd.to_datetime(frame["order_date"], errors="coerce")
    frame["qty"] = pd.to_numeric(frame.get("qty"), errors="coerce").fillna(0).astype(int)
    frame["amount"] = pd.to_numeric(frame.get("amount"), errors="coerce").fillna(0.0)
    frame["b2b"] = (
        frame.get("b2b", pd.Series(dtype="object"))
        .astype(str)
        .str.lower()
        .isin(["true", "1", "yes", "y"])
        .astype(int)
    )

    frame = frame.dropna(subset=["order_date"])
    frame["order_date_only"] = frame["order_date"].dt.date
    frame["month"] = frame["order_date"].dt.to_period("M").astype(str)
    frame["weekday"] = frame["order_date"].dt.day_name()
    frame["day_name_short"] = frame["order_date"].dt.strftime("%a")
    frame["is_cancelled"] = frame["status"].str.contains("cancel", case=False, na=False).astype(int)
    frame["is_shipped"] = frame["status"].str.contains("shipped", case=False, na=False).astype(int)
    frame["is_delivered"] = frame["status"].str.contains("delivered", case=False, na=False).astype(int)
    frame["order_value"] = frame["amount"]
    frame["order_year"] = frame["order_date"].dt.year

    return frame


@st.cache_resource
def get_master_connection(csv_path_or_buffer, date_column: str | None = None) -> tuple[pd.DataFrame, sqlite3.Connection]:
    """Create a single master SQLite database connection on startup to avoid expensive file writes.

    Accepts either a path-like, a file-like buffer, or a pre-loaded DataFrame.
    """
    if isinstance(csv_path_or_buffer, pd.DataFrame):
        frame = csv_path_or_buffer.copy()
    else:
        frame = load_sales_data(csv_path_or_buffer, date_column=date_column)
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    analytics_frame = frame.copy()
    analytics_frame["order_date"] = analytics_frame["order_date"].dt.strftime("%Y-%m-%d")
    analytics_frame.to_sql("amazon_sales_raw", connection, index=False, if_exists="replace")
    return frame, connection


def update_filtered_view(
    connection: sqlite3.Connection,
    start_date,
    end_date,
    selected_states,
    selected_categories,
    selected_statuses,
    selected_fulfillments
):
    """Recreate the 'amazon_sales' SQLite VIEW based on selected filters, optimizing performance."""
    cursor = connection.cursor()
    cursor.execute("DROP VIEW IF EXISTS amazon_sales")
    
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    query = f"""
    CREATE VIEW amazon_sales AS
    SELECT * FROM amazon_sales_raw
    WHERE order_date BETWEEN '{start_str}' AND '{end_str}'
    """
    
    if selected_states:
        escaped_states = [s.replace("'", "''") for s in selected_states]
        states_str = ",".join(f"'{s}'" for s in escaped_states)
        query += f" AND ship_state IN ({states_str})"
    
    if selected_categories:
        escaped_cats = [c.replace("'", "''") for c in selected_categories]
        cats_str = ",".join(f"'{c}'" for c in escaped_cats)
        query += f" AND category IN ({cats_str})"
        
    if selected_statuses:
        escaped_stats = [s.replace("'", "''") for s in selected_statuses]
        stats_str = ",".join(f"'{s}'" for s in escaped_stats)
        query += f" AND status IN ({stats_str})"
        
    if selected_fulfillments:
        escaped_fulls = [f.replace("'", "''") for f in selected_fulfillments]
        fulls_str = ",".join(f"'{f}'" for f in escaped_fulls)
        query += f" AND fulfilment IN ({fulls_str})"
        
    cursor.execute(query)
    connection.commit()


def run_query(connection: sqlite3.Connection, query: str) -> pd.DataFrame:
    """Run a SQL query and return a dataframe."""
    return pd.read_sql_query(query, connection)


def currency_format(value: float) -> str:
    return f"₹{value:,.2f}"


def calculate_rfm(df, end_date):
    """Calculate RFM metrics and assign customer segments."""
    rfm = df.groupby("ship_postal_code").agg(
        recency=("order_date", lambda x: (end_date - x.max().date()).days),
        frequency=("order_id", "nunique"),
        monetary=("amount", "sum")
    ).reset_index()
    
    if rfm.empty:
        return rfm
        
    # Rank scores from 1 to 5 (higher is better for frequency/monetary, lower is better for recency)
    rfm["r_score"] = pd.qcut(rfm["recency"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    
    rfm["rfm_score"] = rfm["r_score"].astype(str) + rfm["f_score"].astype(str) + rfm["m_score"].astype(str)
    
    def assign_segment(row):
        r, f, m = row["r_score"], row["f_score"], row["m_score"]
        if r >= 4 and f >= 4:
            return "Champions"
        elif r >= 3 and f >= 3:
            return "Loyal Customers"
        elif r >= 4 and f < 3:
            return "New / Promising"
        elif r < 3 and f >= 3:
            return "At Risk"
        else:
            return "Lost / Hibernating"
            
    rfm["segment"] = rfm.apply(assign_segment, axis=1)
    return rfm


# Allow users to upload their own CSV via the sidebar (overrides default file)
uploaded_file = st.sidebar.file_uploader("Upload your sales CSV (optional)", type=["csv"], help="Upload a CSV file to analyze. If not provided, the sample dataset will be used.")

# Load Master Connection (uploaded file takes precedence over bundled sample)
if uploaded_file is not None:
    # Preview the uploaded file to let the user pick the date column
    try:
        uploaded_file.seek(0)
    except Exception:
        pass
    preview_df = pd.read_csv(uploaded_file, nrows=5)
    cols = preview_df.columns.tolist()
    # choose a sensible default (first column containing 'date')
    default_idx = 0
    for i, c in enumerate(cols):
        if "date" in c.lower():
            default_idx = i
            break
    selected_date_col = st.sidebar.selectbox("Select date column for analysis", options=cols, index=default_idx, help="Pick the column that contains the order date/time")
    try:
        uploaded_file.seek(0)
    except Exception:
        pass
    raw_data, connection = get_master_connection(uploaded_file, date_column=selected_date_col)
else:
    DATA_PATH = find_data_file()

    if DATA_PATH is None:
        st.error("No dataset found. Upload a CSV via the sidebar or place 'Amazon Sale Report.csv' in e-commerce-analytics/dataset/.")
        st.stop()

    # Initialize data and sqlite db connection from default file
    raw_data, connection = get_master_connection(str(DATA_PATH))

min_date = raw_data["order_date"].min().date()
max_date = raw_data["order_date"].max().date()

# Sidebar Setup
with st.sidebar:
    st.markdown("<h2 style='text-align: center; margin-top: 1rem; margin-bottom: 1.5rem;'>📊 Navigation</h2>", unsafe_allow_html=True)
    
    page = st.radio(
        label="Select Section",
        options=[
            "Executive Summary",
            "Sales Analytics",
            "Customer Segment (RFM)",
            "Affinity & Promotions",
            "Sales Forecasting",
            "Geographic Analysis",
            "Product Analysis",
            "Operations & Fulfillment",
            "SQL Playground",
            "About Project"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("<br><h3 style='margin-bottom: 0.5rem;'>⚙️ Data Filters</h3>", unsafe_allow_html=True)
    
    # 1. Date filter
    with st.expander("📅 Date Range Filter", expanded=True):
        selected_date = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        
        if isinstance(selected_date, (tuple, list)):
            if len(selected_date) == 2:
                start_date, end_date = selected_date
            elif len(selected_date) == 1:
                start_date = selected_date[0]
                end_date = selected_date[0]
            else:
                start_date, end_date = min_date, max_date
        else:
            start_date = selected_date if selected_date else min_date
            end_date = selected_date if selected_date else max_date

    # 2. Geographic & Category filters
    with st.expander("📍 Geographic & Category", expanded=False):
        state_options = sorted(raw_data["ship_state"].fillna("Unknown").unique().tolist())
        category_options = sorted(raw_data["category"].fillna("Unknown").unique().tolist())

        selected_states = st.multiselect("State", options=state_options, default=state_options[:10] if len(state_options) > 10 else state_options)
        selected_categories = st.multiselect("Category", options=category_options, default=category_options)

    # 3. Status & Fulfillment filters
    with st.expander("📦 Order & Fulfillment", expanded=False):
        status_options = sorted(raw_data["status"].fillna("Unknown").unique().tolist())
        fulfillment_options = sorted(raw_data["fulfilment"].fillna("Unknown").unique().tolist())
        
        selected_statuses = st.multiselect("Order Status", options=status_options, default=status_options)
        selected_fulfillments = st.multiselect("Fulfillment Type", options=fulfillment_options, default=fulfillment_options)

# Filter raw dataframe in pandas
filtered_data = raw_data[
    (raw_data["order_date"].dt.date >= start_date)
    & (raw_data["order_date"].dt.date <= end_date)
    & (raw_data["ship_state"].isin(selected_states) if selected_states else True)
    & (raw_data["category"].isin(selected_categories) if selected_categories else True)
    & (raw_data["status"].isin(selected_statuses) if selected_statuses else True)
    & (raw_data["fulfilment"].isin(selected_fulfillments) if selected_fulfillments else True)
].copy()

# Dynamic view update in SQLite
update_filtered_view(
    connection,
    start_date,
    end_date,
    selected_states,
    selected_categories,
    selected_statuses,
    selected_fulfillments
)
filtered_connection = connection

if filtered_data.empty:
    st.warning("No data matches the selected filters. Please adjust filters in the sidebar.")
    st.stop()

# Layout Headers
ui_components.render_header(
    title=f"E-commerce Customer Analytics - {page}",
    subtitle="Interactive E-Commerce Business Analytics, Customer Segmentations, and SQL Aggregations."
)

# Shared Query Executions
metrics_query = """
SELECT
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(amount) AS total_revenue,
    AVG(amount) AS avg_order_value,
    SUM(is_cancelled) * 1.0 / COUNT(*) AS cancellation_rate,
    SUM(is_shipped) * 1.0 / COUNT(*) AS shipped_rate,
    SUM(b2b) * 1.0 / COUNT(*) AS b2b_share
FROM amazon_sales;
"""
metrics = run_query(filtered_connection, metrics_query).iloc[0]

# Month over month growth calculation
latest_month = run_query(
    filtered_connection,
    """
    SELECT month, SUM(amount) AS revenue
    FROM (
        SELECT strftime('%Y-%m', order_date) AS month, amount
        FROM amazon_sales
    )
    GROUP BY month
    ORDER BY month;
    """,
)
if not latest_month.empty:
    latest_month["growth_pct"] = latest_month["revenue"].pct_change() * 100

if latest_month.empty:
    growth_text = "N/A"
else:
    growth_value = latest_month["growth_pct"].dropna().iloc[-1] if latest_month["growth_pct"].notna().any() else 0.0
    growth_text = f"{growth_value:+.1f}% MoM"

# Setup basic query aggregations used in multiple tabs
category_sales = run_query(
    filtered_connection,
    "SELECT category, SUM(amount) AS revenue, SUM(qty) AS qty FROM amazon_sales GROUP BY category ORDER BY revenue DESC;"
)
state_sales = run_query(
    filtered_connection,
    "SELECT ship_state, COUNT(*) AS orders, SUM(amount) AS revenue FROM amazon_sales GROUP BY ship_state ORDER BY revenue DESC;"
)

top_category_val = category_sales.iloc[0]['category'] if not category_sales.empty else "N/A"
top_state_val = state_sales.iloc[0]['ship_state'] if not state_sales.empty else "N/A"

# ==========================================
# PAGE 1: EXECUTIVE SUMMARY
# ==========================================
if page == "Executive Summary":
    st.markdown("<div class='section-title'>Key Performance Indicators</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        ui_components.render_metric_card(
            title="Total Revenue",
            value=currency_format(metrics["total_revenue"] or 0),
            subtext=f"Growth: {growth_text}",
            icon_emoji="💳",
            border_color="#6366f1"
        )
    with col2:
        ui_components.render_metric_card(
            title="Total Orders",
            value=f"{int(metrics['total_orders'] or 0):,}",
            subtext=f"B2B Share: {metrics['b2b_share']*100:.1f}%",
            icon_emoji="📦",
            border_color="#10b981"
        )
    with col3:
        ui_components.render_metric_card(
            title="Avg. Order Value",
            value=currency_format(metrics["avg_order_value"] or 0),
            subtext=f"Avg Qty: {filtered_data['qty'].mean():.2f} per order",
            icon_emoji="📈",
            border_color="#f59e0b"
        )

    col4, col5, col6 = st.columns(3)
    with col4:
        ui_components.render_metric_card(
            title="Cancellation Rate",
            value=f"{(metrics['cancellation_rate'] or 0) * 100:.1f}%",
            subtext=f"Shipped Rate: {metrics['shipped_rate']*100:.1f}%",
            icon_emoji="⚠️",
            border_color="#ef4444"
        )
    with col5:
        top_cat_rev = currency_format(category_sales.iloc[0]['revenue']) if not category_sales.empty else "₹0.00"
        ui_components.render_metric_card(
            title="Top Category",
            value=top_category_val,
            subtext=f"Revenue: {top_cat_rev}",
            icon_emoji="👕",
            border_color="#8b5cf6"
        )
    with col6:
        top_state_rev = currency_format(state_sales.iloc[0]['revenue']) if not state_sales.empty else "₹0.00"
        ui_components.render_metric_card(
            title="Top State",
            value=top_state_val,
            subtext=f"Revenue: {top_state_rev}",
            icon_emoji="📍",
            border_color="#06b6d4"
        )

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Render Dynamic Business Insights
    insights = [
        f"<strong>Top Revenue Category:</strong> <em>{top_category_val}</em> generates the highest revenue in the selected segment ({top_cat_rev}). Prioritize inventory allocation and procurement for this category.",
        f"<strong>Regional Revenue Core:</strong> <em>{top_state_val}</em> leads geographic demand, contributing <em>{top_state_rev}</em>. Channel marketing campaigns and regional warehousing structures directly to this hub.",
        f"<strong>Order Loss Leakage:</strong> Cancellation rate is currently at <em>{(metrics['cancellation_rate'] or 0) * 100:.1f}%</em>. Regions with high cancellation ratios require immediate carrier checks and fulfillment audits to minimize lost sales.",
        f"<strong>B2B Wholesale Contribution:</strong> B2B orders represent <em>{metrics['b2b_share']*100:.1f}%</em> of transactions. Introducing high-volume tiered packages can further capitalize on these wholesale buyers.",
        "<strong>Strategic Planning:</strong> Focus on cross-selling high-affinity product pairs (like Western Dresses + Tops) and run localized customer retention programs based on risk segments in the RFM dashboard."
    ]
    ui_components.render_insights_box(insights)

    # Executive Overview Chart Grid
    left, right = st.columns(2)
    with left:
        monthly_sales = run_query(
            filtered_connection,
            "SELECT strftime('%Y-%m', order_date) AS month, SUM(amount) AS revenue FROM amazon_sales GROUP BY month ORDER BY month;"
        )
        monthly_chart = px.line(monthly_sales, x="month", y="revenue", markers=True, title="Monthly Revenue Trend (Overview)")
        monthly_chart.update_layout(height=350, xaxis_title="Month", yaxis_title="Revenue (INR)")
        st.plotly_chart(ui_components.apply_plotly_style(monthly_chart), use_container_width=True)

    with right:
        region_chart = px.scatter(
            state_sales.head(15),
            x="orders",
            y="revenue",
            size="revenue",
            color="ship_state",
            hover_name="ship_state",
            title="Revenue vs Orders Concentration by Top States",
            size_max=30,
        )
        region_chart.update_layout(height=350, xaxis_title="Orders count", yaxis_title="Revenue (INR)")
        st.plotly_chart(ui_components.apply_plotly_style(region_chart), use_container_width=True)

# ==========================================
# PAGE 2: SALES ANALYTICS
# ==========================================
elif page == "Sales Analytics":
    ui_components.render_info_card(
        "Sales Trend Overview",
        "Monitor revenue trends across months and days. Assess category performances and top selling products to plan cash flow and seasonal campaigns."
    )
    
    monthly_sales = run_query(
        filtered_connection,
        "SELECT strftime('%Y-%m', order_date) AS month, SUM(amount) AS revenue, COUNT(*) AS orders FROM amazon_sales GROUP BY month ORDER BY month;"
    )
    daily_orders = run_query(
        filtered_connection,
        "SELECT order_date, COUNT(*) AS orders, SUM(amount) AS revenue FROM amazon_sales GROUP BY order_date ORDER BY order_date;"
    )
    top_products = run_query(
        filtered_connection,
        "SELECT style, sku, SUM(amount) AS revenue, SUM(qty) AS qty, COUNT(*) AS orders FROM amazon_sales GROUP BY style, sku ORDER BY revenue DESC LIMIT 10;"
    )

    left, right = st.columns(2)
    with left:
        monthly_chart = px.line(monthly_sales, x="month", y="revenue", markers=True, title="Monthly Sales Trend")
        monthly_chart.update_layout(height=420, xaxis_title="Month", yaxis_title="Revenue")
        st.plotly_chart(ui_components.apply_plotly_style(monthly_chart), use_container_width=True)

    with right:
        daily_chart = px.line(daily_orders, x="order_date", y="orders", title="Daily Order Trend")
        daily_chart.update_layout(height=420, xaxis_title="Date", yaxis_title="Orders")
        st.plotly_chart(ui_components.apply_plotly_style(daily_chart), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        category_chart = px.bar(
            category_sales,
            x="revenue",
            y="category",
            orientation="h",
            title="Category-wise Sales Distribution",
            text_auto=".2s",
        )
        category_chart.update_layout(height=450, yaxis_title="Category", xaxis_title="Revenue")
        st.plotly_chart(ui_components.apply_plotly_style(category_chart), use_container_width=True)

    with c2:
        top_products_chart = px.bar(
            top_products,
            x="revenue",
            y="style",
            orientation="h",
            color="qty",
            color_continuous_scale="Blues",
            title="Top 10 Selling Product Styles",
            hover_data=["sku", "orders"],
        )
        top_products_chart.update_layout(height=450, yaxis_title="Style Code", xaxis_title="Revenue")
        st.plotly_chart(ui_components.apply_plotly_style(top_products_chart), use_container_width=True)

    if not latest_month.empty:
        growth_chart = latest_month.copy()
        growth_chart["month_label"] = growth_chart["month"]
        growth_fig = go.Figure()
        growth_fig.add_trace(go.Bar(x=growth_chart["month_label"], y=growth_chart["revenue"], name="Revenue", marker_color="#6366f1"))
        growth_fig.add_trace(go.Scatter(x=growth_chart["month_label"], y=growth_chart["growth_pct"], name="MoM Growth %", yaxis="y2", mode="lines+markers", line=dict(color="#ef4444", width=3)))
        growth_fig.update_layout(
            title="Sales Growth Trend (MoM %)",
            height=420,
            xaxis_title="Month",
            yaxis=dict(title="Revenue (INR)"),
            yaxis2=dict(title="Growth %", overlaying="y", side="right", showgrid=False),
        )
        st.plotly_chart(ui_components.apply_plotly_style(growth_fig), use_container_width=True)
        
    st.markdown("<div class='section-title'>Sales Category Details</div>", unsafe_allow_html=True)
    ui_components.render_styled_dataframe(category_sales, numeric_cols=['qty'], currency_cols=['revenue'])

# ==========================================
# PAGE 3: CUSTOMER SEGMENT (RFM)
# ==========================================
elif page == "Customer Segment (RFM)":
    ui_components.render_info_card(
        "RFM (Recency, Frequency, Monetary) Customer Segmentation",
        "Analyze regional customer value groupings. Target re-engagement campaigns to 'At Risk' locations and cross-sell premium offerings to high-spending 'Champions'."
    )
    
    rfm_df = calculate_rfm(filtered_data, end_date)
    
    if rfm_df.empty:
        st.warning("Not enough data in the current filter range to calculate RFM segmentation.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            ui_components.render_metric_card("Unique Customer Hubs", f"{rfm_df['ship_postal_code'].nunique():,}", "Unique Postal Codes", "#6366f1")
        with c2:
            ui_components.render_metric_card("Top RFM Segment", rfm_df['segment'].value_counts().index[0], "Highest count segment", "#10b981")
        with c3:
            ui_components.render_metric_card("Avg Customer Spend", currency_format(rfm_df['monetary'].mean()), "Mean customer lifetime value", "#f59e0b")
        
        col_l, col_r = st.columns(2)
        
        with col_l:
            seg_counts = rfm_df['segment'].value_counts().reset_index()
            seg_counts.columns = ['Segment', 'Customers']
            fig_seg = px.bar(
                seg_counts, 
                x='Customers', 
                y='Segment', 
                orientation='h',
                title='Customer Count by Segment',
                color='Segment',
            )
            fig_seg.update_layout(height=420)
            st.plotly_chart(ui_components.apply_plotly_style(fig_seg), use_container_width=True)
            
        with col_r:
            fig_scatter = px.scatter(
                rfm_df,
                x='recency',
                y='frequency',
                size='monetary',
                color='segment',
                hover_name='ship_postal_code',
                title='RFM Customer Distribution (Bubble size = Monetary Spend)',
                labels={'recency': 'Recency (Days since last order)', 'frequency': 'Frequency (Unique Orders)'},
                size_max=35,
            )
            fig_scatter.update_layout(height=420)
            st.plotly_chart(ui_components.apply_plotly_style(fig_scatter), use_container_width=True)
        
        st.markdown("<div class='section-title'>Segment Details & Averages</div>", unsafe_allow_html=True)
        seg_raw = rfm_df.groupby('segment').agg(
            customers=('ship_postal_code', 'count'),
            avg_recency=('recency', 'mean'),
            avg_frequency=('frequency', 'mean'),
            avg_monetary=('monetary', 'mean')
        ).reset_index()
        seg_raw.columns = ['Segment', 'Customer Count', 'Avg Recency (Days)', 'Avg Frequency (Orders)', 'Avg Spend (INR)']
        ui_components.render_styled_dataframe(seg_raw, numeric_cols=['Customer Count', 'Avg Recency (Days)', 'Avg Frequency (Orders)'], currency_cols=['Avg Spend (INR)'])

# ==========================================
# PAGE 4: AFFINITY & PROMOTIONS
# ==========================================
elif page == "Affinity & Promotions":
    ui_components.render_info_card(
        "Market Basket & Affinity Associations",
        "Discovers product categories commonly purchased in the same transaction. This analysis guides bundle pricing, package discounts, and web design placements."
    )
    
    order_item_counts = filtered_data.groupby('order_id')['category'].nunique()
    multi_item_orders = order_item_counts[order_item_counts > 1].index
    
    if len(multi_item_orders) == 0:
        st.info("No orders in the filtered range contain multiple different product categories. Showing Category sales distribution instead.")
        fig_fallback = px.bar(category_sales, x='category', y='qty', title="Product Quantity Sold by Category")
        st.plotly_chart(ui_components.apply_plotly_style(fig_fallback), use_container_width=True)
    else:
        basket_data = filtered_data[filtered_data['order_id'].isin(multi_item_orders)]
        pairs = pd.merge(
            basket_data[['order_id', 'category']],
            basket_data[['order_id', 'category']],
            on='order_id'
        )
        pairs = pairs[pairs['category_x'] < pairs['category_y']]
        pair_counts = pairs.groupby(['category_x', 'category_y']).size().reset_index(name='count')
        pair_counts = pair_counts.sort_values(by='count', ascending=False)
        
        col_bl, col_br = st.columns(2)
        with col_bl:
            fig_pairs = px.bar(
                pair_counts.head(10),
                x='count',
                y=pair_counts.head(10).apply(lambda r: f"{r['category_x']} + {r['category_y']}", axis=1),
                orientation='h',
                title='Top 10 Product Category Bundles Co-purchased',
                labels={'y': 'Product Pair', 'count': 'Number of Co-occurrences'},
                text_auto=True
            )
            fig_pairs.update_layout(height=420)
            st.plotly_chart(ui_components.apply_plotly_style(fig_pairs), use_container_width=True)
            
        with col_br:
            categories_list = sorted(filtered_data['category'].unique().tolist())
            matrix_df = pd.DataFrame(0, index=categories_list, columns=categories_list)
            for _, row in pair_counts.iterrows():
                matrix_df.at[row['category_x'], row['category_y']] = row['count']
                matrix_df.at[row['category_y'], row['category_x']] = row['count']
                
            fig_heat = px.imshow(
                matrix_df,
                text_auto=True,
                title='Product Category Affinity Heatmap',
                color_continuous_scale='Blues',
                labels=dict(x="Category", y="Category", color="Co-occurrences")
            )
            fig_heat.update_layout(height=420)
            st.plotly_chart(ui_components.apply_plotly_style(fig_heat), use_container_width=True)
        
        st.markdown("<div class='section-title'>Bundle Recommendations</div>", unsafe_allow_html=True)
        if not pair_counts.empty:
            rec_html = "<ul style='margin-top:0; padding-left:1.2rem;'>"
            for idx, row in pair_counts.head(3).iterrows():
                rec_html += f"<li style='margin-bottom:0.5rem;'><strong>Cross-sell opportunity:</strong> Customers buying <em>{row['category_x']}</em> frequently purchase <em>{row['category_y']}</em> (Co-occurred {row['count']} times). Recommend placing these in recommended bundles or offer a multi-buy discount.</li>"
            rec_html += "</ul>"
            st.markdown(rec_html, unsafe_allow_html=True)
            
            st.markdown("<div class='section-title'>Top Co-Purchased Combinations Details</div>", unsafe_allow_html=True)
            ui_components.render_styled_dataframe(pair_counts.head(15), numeric_cols=['count'])

    # Promotional ROI Section
    st.markdown("<br><hr>", unsafe_allow_html=True)
    ui_components.render_info_card(
        "Promotional ROI Analysis",
        "Determine if campaigns are driving profitable orders or eroding margins. Evaluate items per order and cancellation trends for promotional vs organic shoppers."
    )
    
    promo_data = filtered_data.copy()
    promo_data['has_promo'] = promo_data['promotion_ids'].notna() & (promo_data['promotion_ids'].astype(str) != 'nan') & (promo_data['promotion_ids'].astype(str) != '')
    
    promo_segment = promo_data.groupby('has_promo').agg(
        orders=('order_id', 'nunique'),
        revenue=('amount', 'sum'),
        qty=('qty', 'sum'),
        cancellations=('is_cancelled', 'sum')
    ).reset_index()
    
    if not promo_segment.empty:
        promo_segment['aov'] = promo_segment['revenue'] / promo_segment['orders']
        promo_segment['items_per_order'] = promo_segment['qty'] / promo_segment['orders']
        promo_segment['cancellation_rate'] = promo_segment['cancellations'] / promo_segment['orders']
        promo_segment['segment_label'] = promo_segment['has_promo'].map({True: 'Promotional Orders', False: 'Organic/Standard Orders'})
        
        pcol1, pcol2 = st.columns(2)
        with pcol1:
            fig_promo_rev = px.pie(
                promo_segment,
                names='segment_label',
                values='revenue',
                title='Revenue Contribution: Promo vs Organic',
                hole=0.45
            )
            fig_promo_rev.update_layout(height=420)
            st.plotly_chart(ui_components.apply_plotly_style(fig_promo_rev), use_container_width=True)
            
        with pcol2:
            fig_promo_aov = px.bar(
                promo_segment,
                x='segment_label',
                y='aov',
                title='Average Order Value (AOV) Comparison',
                color='segment_label',
                color_discrete_sequence=['#f59e0b', '#6366f1'],
                text_auto='.2f',
                labels={'aov': 'Average Order Value (INR)', 'segment_label': ''}
            )
            fig_promo_aov.update_layout(height=420)
            st.plotly_chart(ui_components.apply_plotly_style(fig_promo_aov), use_container_width=True)
        
        st.markdown("<div class='section-title'>Operational Metric Comparison</div>", unsafe_allow_html=True)
        promo_disp_df = promo_segment.copy()
        promo_disp_df['cancellation_rate'] = promo_disp_df['cancellation_rate'] * 100
        promo_disp_df = promo_disp_df[['segment_label', 'orders', 'revenue', 'aov', 'items_per_order', 'cancellation_rate']]
        promo_disp_df.columns = ['Order Segment', 'Total Orders', 'Total Revenue', 'Avg Order Value (AOV)', 'Avg Qty per Order', 'Cancellation Rate']
        ui_components.render_styled_dataframe(
            promo_disp_df, 
            numeric_cols=['Total Orders', 'Avg Qty per Order'], 
            currency_cols=['Total Revenue', 'Avg Order Value (AOV)'],
            pct_cols=['Cancellation Rate']
        )
        
        st.markdown("<div class='section-title'>Top Performing Campaigns</div>", unsafe_allow_html=True)
        promo_series = promo_data['promotion_ids'].dropna().astype(str)
        promo_series = promo_series[(promo_series != 'nan') & (promo_series != '')]
        if not promo_series.empty:
            promo_exploded = promo_series.str.split(',').explode().str.strip()
            top_promos = promo_exploded.value_counts().head(10).reset_index()
            top_promos.columns = ['Promotion Campaign Code', 'Orders Attributed']
            
            fig_campaign = px.bar(
                top_promos,
                x='Orders Attributed',
                y='Promotion Campaign Code',
                orientation='h',
                title='Top 10 Campaigns by Volume',
                color='Orders Attributed',
                color_continuous_scale='Sunsetdark'
            )
            fig_campaign.update_layout(height=420)
            st.plotly_chart(ui_components.apply_plotly_style(fig_campaign), use_container_width=True)
            
            st.markdown("<div class='section-title'>Campaign Code Counts</div>", unsafe_allow_html=True)
            ui_components.render_styled_dataframe(top_promos, numeric_cols=['Orders Attributed'])
        else:
            st.write("No campaign codes recorded in this segment.")
    else:
        st.write("No promotional data recorded in this segment.")

# ==========================================
# PAGE 5: SALES FORECASTING
# ==========================================
elif page == "Sales Forecasting":
    ui_components.render_info_card(
        "30-Day Sales Forecasting",
        "Calculated using daily transaction volume modeled with a linear trend and weekly seasonality index. Shaded region indicates the 95% confidence interval."
    )
    
    daily_sales = filtered_data.groupby('order_date_only')['amount'].sum().reset_index()
    daily_sales.columns = ['date', 'revenue']
    daily_sales['date'] = pd.to_datetime(daily_sales['date'])
    daily_sales = daily_sales.sort_values(by='date')
    
    if len(daily_sales) < 15:
        st.warning("Insufficient data history in this date range. Please select a larger date range (at least 15 active days) in the sidebar to perform sales forecasting.")
    else:
        daily_sales['time_index'] = np.arange(len(daily_sales))
        x = daily_sales['time_index']
        y = daily_sales['revenue']
        
        beta, alpha = np.polyfit(x, y, 1)
        
        daily_sales['dayofweek'] = daily_sales['date'].dt.dayofweek
        mean_rev = daily_sales['revenue'].mean()
        if mean_rev > 0:
            seasonal_factors = daily_sales.groupby('dayofweek')['revenue'].mean() / mean_rev
        else:
            seasonal_factors = pd.Series(1.0, index=np.arange(7))
            
        residuals = y - (alpha + beta * x)
        std_error = np.std(residuals)
        
        last_date = daily_sales['date'].max()
        forecast_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=30)
        forecast_time_index = np.arange(len(daily_sales), len(daily_sales) + 30)
        
        trend_forecast = alpha + beta * forecast_time_index
        
        forecast_dayofweek = forecast_dates.dayofweek
        season_multipliers = forecast_dayofweek.map(seasonal_factors).fillna(1.0).values
        
        final_forecast = np.clip(trend_forecast * season_multipliers, 0, None)
        lower_bound = np.clip(final_forecast - 1.96 * std_error, 0, None)
        upper_bound = final_forecast + 1.96 * std_error
        
        historical_df = daily_sales[['date', 'revenue']].copy()
        historical_df['Type'] = 'Historical Sales'
        historical_df['Lower Bound'] = np.nan
        historical_df['Upper Bound'] = np.nan
        
        forecast_df = pd.DataFrame({
            'date': forecast_dates,
            'revenue': final_forecast,
            'Type': 'Forecasted Sales (Next 30 Days)',
            'Lower Bound': lower_bound,
            'Upper Bound': upper_bound
        })
        
        combined_forecast_df = pd.concat([historical_df, forecast_df], ignore_index=True)
        
        fig_fore = go.Figure()
        
        fig_fore.add_trace(go.Scatter(
            x=historical_df['date'],
            y=historical_df['revenue'],
            mode='lines+markers',
            name='Historical Revenue',
            line=dict(color='#6366f1', width=2),
            marker=dict(size=4)
        ))
        
        fig_fore.add_trace(go.Scatter(
            x=forecast_df['date'],
            y=forecast_df['revenue'],
            mode='lines+markers',
            name='Forecasted Revenue (With Weekly Seasonality)',
            line=dict(color='#ef4444', width=2, dash='dash'),
            marker=dict(size=4)
        ))
        
        fig_fore.add_trace(go.Scatter(
            x=forecast_df['date'],
            y=forecast_df['Upper Bound'],
            mode='lines',
            line=dict(width=0),
            showlegend=False,
            name='Confidence Band Upper'
        ))
        
        fig_fore.add_trace(go.Scatter(
            x=forecast_df['date'],
            y=forecast_df['Lower Bound'],
            mode='lines',
            fill='tonexty',
            fillcolor='rgba(239, 68, 68, 0.12)',
            line=dict(width=0),
            name='95% Prediction Confidence Interval'
        ))
        
        fig_fore.update_layout(
            title='30-Day Revenue Trend Projection',
            xaxis_title='Date',
            yaxis_title='Revenue (INR)',
            hovermode='x unified',
            height=460
        )
        st.plotly_chart(ui_components.apply_plotly_style(fig_fore), use_container_width=True)
        
        st.markdown("<div class='section-title'>Forecasted Metrics Summary</div>", unsafe_allow_html=True)
        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            ui_components.render_metric_card("Projected 30-Day Revenue", currency_format(final_forecast.sum()), "Sum of 30-day forecast", "#6366f1")
        with fcol2:
            ui_components.render_metric_card("Projected Daily Average", currency_format(final_forecast.mean()), "Average daily revenue projection", "#10b981")
        with fcol3:
            ui_components.render_metric_card("Projected Trend Direction", "UPWARD 📈" if beta > 0 else "DOWNWARD 📉", f"Slope (beta): {beta:+.2f}", "#f59e0b")
        
        st.markdown("<div class='section-title'>Projected 30-Day Daily Forecast Details</div>", unsafe_allow_html=True)
        forecast_table = pd.DataFrame({
            'Date': forecast_dates.strftime('%Y-%m-%d'),
            'Projected Revenue': final_forecast,
            'Confidence Lower Range': lower_bound,
            'Confidence Upper Range': upper_bound
        })
        ui_components.render_styled_dataframe(forecast_table, currency_cols=['Projected Revenue', 'Confidence Lower Range', 'Confidence Upper Range'])

# ==========================================
# PAGE 6: GEOGRAPHIC ANALYSIS
# ==========================================
elif page == "Geographic Analysis":
    ui_components.render_info_card(
        "Regional Performance Matrix",
        "Explore which states and cities generate high demand. Allocate logistic assets and local marketing campaigns where revenue concentration is high."
    )
    
    city_orders = run_query(
        filtered_connection,
        "SELECT ship_city, COUNT(*) AS orders, SUM(amount) AS revenue FROM amazon_sales GROUP BY ship_city ORDER BY orders DESC LIMIT 15;"
    )

    e, f = st.columns(2)
    with e:
        state_chart = px.bar(
            state_sales.head(15),
            x="revenue",
            y="ship_state",
            orientation="h",
            title="State-wise Revenue Distribution (Top 15)",
            text_auto=".2s",
        )
        state_chart.update_layout(height=450, xaxis_title="Revenue", yaxis_title="State")
        st.plotly_chart(ui_components.apply_plotly_style(state_chart), use_container_width=True)

    with f:
        city_chart = px.bar(
            city_orders,
            x="orders",
            y="ship_city",
            orientation="h",
            title="City-wise Order Volume (Top 15)",
            text_auto=True,
        )
        city_chart.update_layout(height=450, xaxis_title="Orders", yaxis_title="City")
        st.plotly_chart(ui_components.apply_plotly_style(city_chart), use_container_width=True)

    region_chart = px.scatter(
        state_sales.head(20),
        x="orders",
        y="revenue",
        size="revenue",
        color="ship_state",
        hover_name="ship_state",
        title="Geographic Revenue Concentration Scatter Map",
        size_max=35,
    )
    region_chart.update_layout(height=430, xaxis_title="Orders Count", yaxis_title="Revenue")
    st.plotly_chart(ui_components.apply_plotly_style(region_chart), use_container_width=True)
    
    st.markdown("<div class='section-title'>Top 15 States Sales Ranking</div>", unsafe_allow_html=True)
    ui_components.render_styled_dataframe(state_sales.head(15), numeric_cols=['orders'], currency_cols=['revenue'])

# ==========================================
# PAGE 7: PRODUCT ANALYSIS
# ==========================================
elif page == "Product Analysis":
    ui_components.render_info_card(
        "Product Performance Insights",
        "Examine size distribution and category quantity outputs to align clothing apparel supply with buyer sizing patterns."
    )
    
    size_demand = run_query(
        filtered_connection,
        "SELECT size, SUM(qty) AS qty, SUM(amount) AS revenue FROM amazon_sales GROUP BY size ORDER BY qty DESC;"
    )

    g, h = st.columns(2)
    with g:
        size_chart = px.bar(
            size_demand,
            x="size",
            y="qty",
            title="Size-wise Product Demand",
            text_auto=True,
        )
        size_chart.update_layout(height=420, xaxis_title="Product Size", yaxis_title="Quantity Sold")
        st.plotly_chart(ui_components.apply_plotly_style(size_chart), use_container_width=True)

    with h:
        category_perf_chart = px.scatter(
            category_sales,
            x="qty",
            y="revenue",
            size="revenue",
            color="category",
            title="Product Category Performance Map",
            hover_name="category",
        )
        category_perf_chart.update_layout(height=420, xaxis_title="Quantity Sold", yaxis_title="Revenue (INR)")
        st.plotly_chart(ui_components.apply_plotly_style(category_perf_chart), use_container_width=True)

    quantity_fig = px.histogram(
        filtered_data,
        x="qty",
        nbins=20,
        title="Items Per Order Frequency (Quantity Distribution)",
    )
    quantity_fig.update_layout(height=400, xaxis_title="Quantity In Single Transaction", yaxis_title="Order Frequency")
    st.plotly_chart(ui_components.apply_plotly_style(quantity_fig), use_container_width=True)
    
    st.markdown("<div class='section-title'>Product Size-wise Demand Table</div>", unsafe_allow_html=True)
    ui_components.render_styled_dataframe(size_demand, numeric_cols=['qty'], currency_cols=['revenue'])

# ==========================================
# PAGE 8: OPERATIONS & FULFILLMENT
# ==========================================
elif page == "Operations & Fulfillment":
    ui_components.render_info_card(
        "Operations & Shipping Health Check",
        "Track courier status and FBA (Fulfilled by Amazon) vs Easy-Ship fulfillment ratios. Identify logistics delays or high cancellation channels."
    )
    
    courier_status = run_query(
        filtered_connection,
        "SELECT courier_status, COUNT(*) AS orders, SUM(amount) AS revenue FROM amazon_sales GROUP BY courier_status ORDER BY orders DESC;"
    )
    fulfilment_performance = run_query(
        filtered_connection,
        "SELECT fulfilment, status, COUNT(*) AS orders, SUM(amount) AS revenue FROM amazon_sales GROUP BY fulfilment, status ORDER BY orders DESC;"
    )

    i, j = st.columns(2)
    with i:
        fulfillment_mix = run_query(
            filtered_connection,
            """
            SELECT CASE
                WHEN is_cancelled = 1 THEN 'Cancelled'
                WHEN is_shipped = 1 THEN 'Shipped'
                WHEN is_delivered = 1 THEN 'Delivered'
                ELSE 'Other'
            END AS delivery_group,
            COUNT(*) AS orders,
            SUM(amount) AS revenue
            FROM amazon_sales
            GROUP BY delivery_group
            ORDER BY orders DESC;
            """,
        )

        fulfillment_chart = px.pie(
            fulfillment_mix,
            names="delivery_group",
            values="orders",
            hole=0.45,
            title="Fulfillment Group Mix Status",
        )
        fulfillment_chart.update_layout(height=420)
        st.plotly_chart(ui_components.apply_plotly_style(fulfillment_chart), use_container_width=True)

    with j:
        courier_chart = px.bar(
            courier_status,
            x="courier_status",
            y="orders",
            color="revenue",
            color_continuous_scale="Viridis",
            title="Courier Handover Status Metrics",
            text_auto=True,
        )
        courier_chart.update_layout(height=420, xaxis_title="Courier status", yaxis_title="Orders")
        st.plotly_chart(ui_components.apply_plotly_style(courier_chart), use_container_width=True)

    fulfillment_breakdown = px.bar(
        fulfilment_performance,
        x="fulfilment",
        y="orders",
        color="status",
        barmode="group",
        title="Fulfillment Method vs Order Status Performance",
        text_auto=True,
    )
    fulfillment_breakdown.update_layout(height=430, xaxis_title="Fulfillment Type", yaxis_title="Orders")
    st.plotly_chart(ui_components.apply_plotly_style(fulfillment_breakdown), use_container_width=True)
    
    st.markdown("<div class='section-title'>Courier Status Summary</div>", unsafe_allow_html=True)
    ui_components.render_styled_dataframe(courier_status, numeric_cols=['orders'], currency_cols=['revenue'])

# ==========================================
# PAGE 9: SQL PLAYGROUND
# ==========================================
elif page == "SQL Playground":
    st.markdown("<div class='section-title'>SQL Query Playground</div>", unsafe_allow_html=True)
    st.markdown(
        """
        Write custom SQL queries against the loaded in-memory SQLite database table <code>amazon_sales</code>.
        Use this tool to explore schema columns or write custom aggregates for presentation.
        """,
        unsafe_allow_html=True
    )
    
    sqcol_l, sqcol_r = st.columns([3, 1])
    with sqcol_r:
        st.markdown("##### 📋 Schema Guide")
        schema_info = run_query(connection, "PRAGMA table_info(amazon_sales_raw);")
        if not schema_info.empty:
            schema_summary = schema_info[['name', 'type']]
            st.dataframe(schema_summary, height=350, use_container_width=True, hide_index=True)
        else:
            st.info("Schema not loaded yet.")
            
    with sqcol_l:
        default_q = """SELECT category, 
       SUM(qty) AS total_quantity, 
       SUM(amount) AS total_revenue 
FROM amazon_sales 
GROUP BY category 
ORDER BY total_revenue DESC;"""
        
        query_input = st.text_area("SQL Code", value=default_q, height=180)
        run_btn = st.button("🚀 Run Query", key="sql_run_btn")
        
        if run_btn:
            try:
                res_df = pd.read_sql_query(query_input, connection)
                st.success(f"Query returned {len(res_df)} rows")
                st.dataframe(res_df, use_container_width=True)
                
                csv_data = res_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export Result to CSV",
                    data=csv_data,
                    file_name="custom_query_results.csv",
                    mime="text/csv",
                    key="sql_download_btn"
                )
                
                if len(res_df) > 0 and len(res_df.columns) >= 2:
                    st.markdown("<div class='section-title'>Visualizer Builder</div>", unsafe_allow_html=True)
                    num_cols = res_df.select_dtypes(include=[np.number]).columns.tolist()
                    cat_cols = res_df.select_dtypes(exclude=[np.number]).columns.tolist()
                    
                    if num_cols and cat_cols:
                        vcol1, vcol2, vcol3 = st.columns(3)
                        ctype = vcol1.selectbox("Chart Type", ["Bar Chart", "Line Chart", "Scatter Plot"], key="sql_chart_type")
                        xcol = vcol2.selectbox("X Axis (Categorical)", cat_cols, key="sql_xcol")
                        ycol = vcol3.selectbox("Y Axis (Numeric)", num_cols, key="sql_ycol")
                        
                        if ctype == "Bar Chart":
                            fig_sql = px.bar(res_df, x=xcol, y=ycol, title=f"{ycol} by {xcol}", color=xcol)
                        elif ctype == "Line Chart":
                            fig_sql = px.line(res_df, x=xcol, y=ycol, title=f"{ycol} by {xcol}", markers=True)
                        else:
                            fig_sql = px.scatter(res_df, x=xcol, y=ycol, title=f"{ycol} vs {xcol}", color=xcol, size=ycol if ycol in res_df.columns else None)
                            
                        st.plotly_chart(ui_components.apply_plotly_style(fig_sql), use_container_width=True)
                    else:
                        st.info("To use the visualizer, your query must return at least one numeric column and one categorical/date column.")
            except Exception as e:
                st.error(f"SQL Error: {str(e)}")

# ==========================================
# PAGE 10: ABOUT PROJECT
# ==========================================
elif page == "About Project":
    st.markdown("<div class='section-title'>Project Technical Specifications</div>", unsafe_allow_html=True)
    
    col_ab1, col_ab2 = st.columns(2)
    with col_ab1:
        st.markdown(
            """
            ### 📌 Architecture Overview
            This application is designed as a **portfolio-ready analytics platform** demonstrating modern dashboard architecture:
            
            1. **Pandas Preprocessing Layer**: Initial ingestion reads raw dataset CSVs, removes empty columns, standardizes field labels to snake_case, and structures clean date/numerical values.
            2. **SQL Aggregation Engine**: Rather than running heavy Pandas calculations on every reload, the application loads the cleaned dataset into an **in-memory SQLite3 connection**. Filters dynamically drop and recreate a SQL `VIEW` (`amazon_sales`) inside the engine. The dashboard visualizations and query sandbox fetch metrics directly from the SQL views.
            3. **Interactive Visualizations**: Uses customized **Plotly Express** layouts matching SaaS dashboard design systems (Outfit typography, clean grids, curated responsive colors).
            4. **Analytics Algorithms**: Includes RFM Customer segmentation, Market Basket Analysis co-occurrences, Promotional ROI audits, and a 30-day Time Series Forecasting model.
            """,
            unsafe_allow_html=True
        )
    with col_ab2:
        st.markdown(
            """
            ### 💡 Interview Questions Cheat Sheet (Decision Science & Analyst Roles)
            Prepare to answer these questions during case studies or placement runs (e.g. Mu Sigma, ZS Associates):
            
            * **Q: Why utilize SQLite views for filtering instead of standard Pandas queries?**
              * *A: Speed and separation of concerns. A database view processes query restrictions in C-compiled SQLite, which avoids multiple copies of data frames in Python memory. This replicates a production cloud database environment where queries hit structured tables instead of direct memory objects.*
            * **Q: How does the Market Basket Analysis work?**
              * *A: It identifies transactions containing multiple distinct categories. It creates a self-join SQL equivalent that pairs combinations and returns co-occurrence frequency counts to discover purchase affinities (e.g., Tops and Dresses being bought together).*
            * **Q: What modeling is used in the Sales Forecast?**
              * *A: A combined additive model using a linear trend line ($\alpha + \beta x$) combined with a day-of-week seasonal multiplier. This captures both the growth trajectory and weekly customer purchase seasonality.*
            """,
            unsafe_allow_html=True
        )

# Render Global Footer
ui_components.render_footer()
