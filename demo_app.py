from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title='Restaurant Revenue Intelligence', layout="wide"
)

# Load data
DATA_PATH = Path('data/pos_sample.csv')

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

df = load_data()

# -------- HEADER & BRANDING --------

st.title('🍽️ Restaurant Margin & menu Intelligence')
st.caption(
    'Automated POS Transaction Analytics & Marketing Lif Audit (Demo: Last 30 Days)'
)
st.markdown('---')

# -------- TOP KPI METRICS --------
total_revenue = df['gross_sales'].sum()
total_cogs = df['gross_cost'].sum()
total_gross_profit = df['gross_profit'].sum()
food_cost_pct = (total_cogs / total_revenue) * 100
total_orders = df['ticket_id'].nunique()

TARGET_FOOD_COST = 32.0
variance = food_cost_pct - TARGET_FOOD_COST

col1, col2, col3, col4 = st.columns(4)
col1.metric('Total Revenue', f'R {total_revenue:,.2f}')
col2.metric('Gross Profit', f'R {total_gross_profit:,.2f}')
col3.metric(
    'Food Cost %',
    f'{food_cost_pct:.2f}%',
    delta=f'{variance:+.2f}% vs target (32%)',
    delta_color='inverse'
)
col4.metric('Total Guest Checks', f'{total_orders:,}')

st.markdown('---')

# -------- TABS --------
tab1, tab2, tab3 = st.tabs([
    '📊 Menu Engineering Matrix',
    '🎯 Marketing Campaign Impact',
    '📝 Actionable Recommendations',
])

# --- TAB 1: MENU MATRIX ---
with tab1:
    st.subheader('Dish Profitability vs. Volume Quadrants')
    st.write(
        'Every dish classified by sales popularity against contribution margin'
    )

    item_summary = (
        df.groupby(['item_name', 'category'])
        .agg(
            units_sold=('quantity', 'sum'),
            avg_unit_price=('unit_price', 'mean'),
            avg_unit_cost=('unit_cost', 'mean'),
            total_revenue=('gross_sales', 'sum'),
            total_profit=('gross_profit', 'sum')
        )
        .reset_index()
    )

    item_summary['unit_margin'] = (
        item_summary['avg_unit_price'] - item_summary['avg_unit_cost']
    )

    median_units = item_summary['units_sold'].median()
    median_margin = item_summary['unit_margin'].median()

    def assign_quadrant(row):
        if (
            row['units_sold'] >= median_units and row['unit_margin'] >= median_margin
        ):
            return '⭐ Star (High Profit / High Vol)'
        elif (
            row['units_sold'] >= median_units and row['unit_margin'] < median_margin
        ):
            return '🐎 Workhorse (Low Profit / High Vol)'
        elif(
            row['units_sold'] < median_units and row['unit_margin'] >= median_margin
        ):
            return '🧩 Puzzle (High Profit / Low Vol)'
        else:
            return '🐕 Dog (Low Profit / Low Vol)'

    item_summary['Quadrant'] = item_summary.apply(assign_quadrant, axis=1)
    item_summary['plot_size'] = item_summary['total_profit'].clip(lower=1)

    fig =px.scatter(
        item_summary,
        x='units_sold',
        y='unit_margin',
        hover_name='item_name',
        color='Quadrant',
        size='plot_size',
        hover_data=['category', 'avg_unit_price', 'total_profit'],
        color_discrete_map={
            '⭐ Star (High Profit / High Vol)': '#2ecc71',
            '🐎 Workhorse (Low Profit / High Vol)': '#3498db',
            '🧩 Puzzle (High Profit / Low Vol)': '#f39c12',
            '🐕 Dog (Low Profit / Low Vol)': '#e74c3c',
        },
    )

    fig.add_vline(
        x=median_units, line_dash='dash', line_color='grey', annotation_text='Avg Vol'
    )
    fig.add_hline(
        y=median_margin,
        line_dash='dash',
        line_color='gray',
        annotation_text='Avg Margin',
    )

    fig.update_layout(
        height=500,
        xaxis_title='Total Units Sold (Popularity)',
        yaxis_title='Unit Margin (Rands Profit / Plate)',
        xaxis=dict(
            range=[
                item_summary['units_sold'].min() - 30,
                item_summary['units_sold'].max() + 30,
            ]
        )
    )

    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: MARKETING IMPACT (TECBOT`S FEATURE) ---

with tab2:
    st.subheader('Digital Agency Campaign Yield')
    st.info(
        'Demonstrates real item sales during a 7-day social ad campaign featuring the Truffle Rigatoni'
    )

    pasta_df = df[df['item_name'] == 'Truffle Wild Mushroom Rigatoni'].copy()

    campaign_days = pasta_df[pasta_df['campaign_active'] == True]['timestamp'].dt.date.nunique() or 7
    normal_days = pasta_df[pasta_df['campaign_active'] == False]['timestamp'].dt.date.nunique() or 23

    campaign_units = pasta_df[pasta_df['campaign_active'] == True]['quantity'].sum()
    normal_units = pasta_df[pasta_df['campaign_active'] == False]['quantity'].sum()

    daily_avg_campaign = campaign_units / campaign_days
    daily_avg_normal = normal_units / normal_days
    uplift_pct = ((daily_avg_campaign - daily_avg_normal) / daily_avg_normal) * 100

    campaign_summary = pd.DataFrame({
        'Period': ['Normal Operations', 'Active Campaign'],
        'daily_avg': [daily_avg_normal, daily_avg_campaign]
    })

    fig_bar = px.bar(
        campaign_summary,
        x='Period',
        y='daily_avg',
        color='Period',
        text_auto='.1f',
        title='Daily Sales Velocity: Truffle Rigatoni (Units / Day)',
        color_discrete_sequence=['#95a5a6', '#2ecc71'],
    )
    fig_bar.update_layout(yaxis_title="Average Plates Sold per Day", showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Baseline Daily Sales", f"{daily_avg_normal:.1f} plates / day")
    col_m2.metric(
        "Campaign Daily Sales",
        f"{daily_avg_campaign:.1f} plates / day",
        delta=f"+{uplift_pct:.0f}% Direct Item Uplift"
    )

# --- TAB 3: RECOMMENDATIONS ---
with tab3:
    st.subheader("Automated Operational Action Plan")

    # Find the top representative dish for each category
    workhorses = item_summary[item_summary['Quadrant'].str.contains('Workhorse')].sort_values(by='units_sold',
                                                                                              ascending=False)
    puzzles = item_summary[item_summary['Quadrant'].str.contains('Puzzle')].sort_values(by='unit_margin',
                                                                                        ascending=False)
    dogs = item_summary[item_summary['Quadrant'].str.contains('Dog')].sort_values(by='units_sold', ascending=True)

    top_workhorse = workhorses.iloc[0] if not workhorses.empty else None
    top_puzzle = puzzles.iloc[0] if not puzzles.empty else None
    top_dog = dogs.iloc[0] if not dogs.empty else None

    rec_md = ""

    if top_workhorse is not None:
        rec_md += f"""
    1. **Reprice / Re-portion High Volume ('Workhorse'):**
       * **{top_workhorse['item_name']}** sells heavily ({top_workhorse['units_sold']:,} units) but carries a lower unit margin (R{top_workhorse['unit_margin']:.2f}). 
       * A modest R15 price adjustment or portion re-costing would recover approximately **R{top_workhorse['units_sold'] * 15:,.2f}** in direct monthly gross profit.
    """

    if top_puzzle is not None:
        rec_md += f"""
    2. **Promote Untapped Profit Potential ('Puzzle'):**
       * **{top_puzzle['item_name']}** has an exceptional margin of **R{top_puzzle['unit_margin']:.2f} per plate**, but only sold {top_puzzle['units_sold']:,} units.
       * High-priority candidate for social media ad pushes and server upsell bonuses to drive volume into the Star quadrant.
    """

    if top_dog is not None:
        rec_md += f"""
    3. **Eliminate or Rework Underperformers ('Dog'):**
       * **{top_dog['item_name']}** sold only {top_dog['units_sold']:,} units and yields a weak margin of R{top_dog['unit_margin']:.2f}.
       * Candidates like this contribute negligible profit while tying up walk-in fridge storage and risking ingredient spoilage.
    """

    st.markdown(rec_md)