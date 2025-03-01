import streamlit as st
import pandas as pd
import numpy as np
import json
import os

SAVE_FILE = "financial_model.json"

# Function to save and load data
def save_model(equipment_list, product_list):
    data = {"equipment": equipment_list, "products": product_list}
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)

def load_model():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return {"equipment": [], "products": []}

def generate_swot_analysis(revenue_forecast, cost_forecast, utilization_rate):
    strengths, weaknesses, opportunities, threats = [], [], [], []

    # Strengths
    if max(utilization_rate) < 80:
        strengths.append("Capacity available for expansion")
    if max(revenue_forecast) / max(cost_forecast) > 1.5:
        strengths.append("Strong revenue-to-cost ratio")

    # Weaknesses
    if min(utilization_rate) > 90:
        weaknesses.append("High equipment utilization may lead to bottlenecks")
    if min(revenue_forecast) / min(cost_forecast) < 1:
        weaknesses.append("Revenue barely covers costs in early years")

    # Opportunities
    if max(revenue_forecast) > 2 * min(revenue_forecast):
        opportunities.append("Strong revenue growth potential")
    if min(utilization_rate) < 50:
        opportunities.append("Potential to add more production capacity")

    # Threats
    if min(revenue_forecast) < min(cost_forecast):
        threats.append("Potential losses in early years")
    if max(utilization_rate) > 95:
        threats.append("Risk of overcapacity and downtime issues")

    return strengths, weaknesses, opportunities, threats

def investor_sanity_check(revenue_forecast, cost_forecast, utilization_rate):
    score = 100

    # Penalize overly optimistic growth assumptions
    if max(revenue_forecast) / min(revenue_forecast) > 5:
        score -= 15

    # Penalize high utilization with no extra investment
    if max(utilization_rate) > 95:
        score -= 10

    # Penalize revenue/cost ratio being too low
    if min(revenue_forecast) / min(cost_forecast) < 1:
        score -= 20

    # Ensure score stays between 0-100%
    score = max(0, min(score, 100))

    return score

def export_to_excel(financial_model):
    file_path = "financial_report.xlsx"
    financial_model.to_excel(file_path, index=False)
    return file_path

def manufacturing_expansion_app():
    st.title("Manufacturing Expansion Financial Model")

    st.sidebar.header("User Inputs")

    # Load saved data if available
    saved_data = load_model()
    equipment_list = saved_data["equipment"]
    product_list = saved_data["products"]

    # User Input Fields
    initial_revenue = st.sidebar.number_input("Initial Annual Revenue ($)", min_value=1000000, value=5000000, step=100000)
    initial_costs = st.sidebar.number_input("Initial Annual Costs ($)", min_value=1000000, value=3000000, step=100000)
    annual_revenue_growth = st.sidebar.slider("Annual Revenue Growth (%)", min_value=1, max_value=50, value=15) / 100
    annual_cost_growth = st.sidebar.slider("Annual Cost Growth (%)", min_value=1, max_value=50, value=10) / 100

    # Financing Inputs
    debt_ratio = st.sidebar.slider("Debt Financing Ratio (%)", min_value=0, max_value=100, value=50) / 100
    interest_rate = st.sidebar.slider("Annual Interest Rate (%)", min_value=1, max_value=20, value=10) / 100

    # Equipment Financing Options
    st.sidebar.subheader("Equipment Purchases")

    with st.sidebar.form("equipment_form", clear_on_submit=True):
        eq_name = st.text_input("Equipment Name")
        eq_cost = st.number_input("Cost ($)", min_value=10000, value=500000, step=10000)
        eq_lifetime = st.number_input("Useful Life (years)", min_value=1, value=10, step=1)
        max_capacity = st.number_input("Max Production Capacity (units/year)", min_value=1, value=10000, step=100)
        financing_type = st.selectbox(
            "Financing Method",
            ["Cash Purchase", "Short-Term Debt", "Long-Term Debt", "$1 Buyout Lease", "FMV Lease"]
        )
        submit_eq = st.form_submit_button("Add Equipment")

        if submit_eq and eq_name:
            equipment_list.append({
                "Name": eq_name,
                "Cost": eq_cost,
                "Useful Life": eq_lifetime,
                "Max Capacity": max_capacity,
                "Financing": financing_type
            })
            save_model(equipment_list, product_list)

    # Product Ramp-Up Forecasting
    st.sidebar.subheader("Product Lines")

    with st.sidebar.form("product_form", clear_on_submit=True):
        product_name = st.text_input("Product Name")
        initial_units = st.number_input("Initial Production Volume (units/year)", min_value=1, value=1000, step=100)
        unit_price = st.number_input("Unit Selling Price ($)", min_value=1, value=100, step=1)
        unit_cost = st.number_input("Unit Production Cost ($)", min_value=1, value=50, step=1)
        growth_rate = st.slider("Annual Production Growth (%)", min_value=1, max_value=50, value=10) / 100
        submit_product = st.form_submit_button("Add Product")

        if submit_product and product_name:
            product_list.append({
                "Name": product_name,
                "Initial Units": initial_units,
                "Unit Price": unit_price,
                "Unit Cost": unit_cost,
                "Growth Rate": growth_rate
            })
            save_model(equipment_list, product_list)

    # Define time horizon
    years = np.arange(2025, 2030)

    # Compute Revenue, Cost, and Utilization based on product ramp-up
    revenue_forecast, cost_forecast, total_production = [], [], []

    for year_idx in range(len(years)):
        yearly_revenue, yearly_cost, yearly_production = 0, 0, 0

        for product in product_list:
            units_produced = product["Initial Units"] * (1 + product["Growth Rate"]) ** year_idx
            yearly_revenue += units_produced * product["Unit Price"]
            yearly_cost += units_produced * product["Unit Cost"]
            yearly_production += units_produced

        revenue_forecast.append(yearly_revenue)
        cost_forecast.append(yearly_cost)
        total_production.append(yearly_production)

    # Equipment Utilization
    total_capacity = sum([eq["Max Capacity"] for eq in equipment_list])
    utilization_rate = [(total_production[i] / total_capacity) * 100 if total_capacity > 0 else 0 for i in range(len(years))]

    # SWOT Analysis
    strengths, weaknesses, opportunities, threats = generate_swot_analysis(revenue_forecast, cost_forecast, utilization_rate)

    # Investor Sanity Check
    believability_score = investor_sanity_check(revenue_forecast, cost_forecast, utilization_rate)

    # Export Financial Report
    financial_model = pd.DataFrame({
        "Year": years,
        "Revenue": revenue_forecast,
        "Costs": cost_forecast,
        "Equipment Utilization (%)": utilization_rate
    })
    report_path = export_to_excel(financial_model)

    # Display Download Button
    st.subheader("Download Financial Report")
    st.download_button(label="Download Report (Excel)", data=open(report_path, "rb"), file_name="Financial_Report.xlsx", mime="application/vnd.ms-excel")

if __name__ == "__main__":
    manufacturing_expansion_app()
