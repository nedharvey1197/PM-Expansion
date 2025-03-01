import streamlit as st
import pandas as pd
import numpy as np
import json
import os

SAVE_FILE = "financial_model.json"

def save_model(equipment_list, product_list):
    data = {
        "equipment": equipment_list,
        "products": product_list
    }
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)

def load_model():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return {"equipment": [], "products": []}

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
    revenue_forecast = []
    cost_forecast = []
    total_production = []

    for year_idx in range(len(years)):
        yearly_revenue = 0
        yearly_cost = 0
        yearly_production = 0

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

    # Process Equipment Financing
    total_equipment_cost = sum([eq["Cost"] for eq in equipment_list])
    depreciation_rate = 1 / max(1, sum([eq["Useful Life"] for eq in equipment_list]) / len(equipment_list)) if equipment_list else 0.10
    depreciation = [total_equipment_cost * depreciation_rate] * len(years)

    # Financial Calculations
    ebitda = [revenue_forecast[i] - cost_forecast[i] for i in range(len(years))]
    ebit = [ebitda[i] - depreciation[i] for i in range(len(years))]
    tax_rate = 0.25
    net_income = [ebit[i] * (1 - tax_rate) for i in range(len(years))]

    # Balance Sheet: Assets, Liabilities, Equity
    assets = [total_equipment_cost + sum(revenue_forecast[:i+1]) - sum(cost_forecast[:i+1]) for i in range(len(years))]
    liabilities = [total_equipment_cost * debt_ratio] * len(years)
    equity = [assets[i] - liabilities[i] for i in range(len(years))]

    # Cash Flow Statement
    operating_cash_flow = [ebitda[i] - (ebitda[i] * 0.10) for i in range(len(years))]
    investing_cash_flow = [-total_equipment_cost] + [0] * (len(years) - 1)
    financing_cash_flow = [liabilities[0] * interest_rate] * len(years)

    # Create DataFrame
    financial_model = pd.DataFrame({
        "Year": years,
        "Revenue": revenue_forecast,
        "Costs": cost_forecast,
        "EBITDA": ebitda,
        "EBIT": ebit,
        "Net Income": net_income,
        "Assets": assets,
        "Liabilities": liabilities,
        "Equity": equity,
        "Operating Cash Flow": operating_cash_flow,
        "Investing Cash Flow": investing_cash_flow,
        "Financing Cash Flow": financing_cash_flow,
        "Equipment Utilization (%)": utilization_rate
    })

    # Display Financial Projections
    st.subheader("Financial Model Projections")
    st.dataframe(financial_model)

    # Visualizations
    st.subheader("Revenue & Cost Growth Over Time")
    st.line_chart(financial_model.set_index("Year")[["Revenue", "Costs"]])

    st.subheader("Equipment Utilization Rate")
    st.line_chart(financial_model.set_index("Year")[["Equipment Utilization (%)"]])

    st.subheader("Cash Flow Analysis")
    st.line_chart(financial_model.set_index("Year")[["Operating Cash Flow", "Investing Cash Flow", "Financing Cash Flow"]])

if __name__ == "__main__":
    manufacturing_expansion_app()
