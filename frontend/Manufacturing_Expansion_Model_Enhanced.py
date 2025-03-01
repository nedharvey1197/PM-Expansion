import streamlit as st
import pandas as pd
import numpy as np
import json
import os

SAVE_FILE = "financial_model_enhanced.json"

# Function to save and load data
def save_model(equipment_list, product_list, cost_drivers):
    data = {"equipment": equipment_list, "products": product_list, "cost_drivers": cost_drivers}
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_model():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return {"equipment": [], "products": [], "cost_drivers": {}}

def manufacturing_expansion_app():
    st.title("Manufacturing Financial Model")

    st.sidebar.header("User Inputs")

    # Load saved data if available
    saved_data = load_model()
    equipment_list = saved_data["equipment"]
    product_list = saved_data["products"]
    cost_drivers = saved_data["cost_drivers"]

    # Financial Assumptions
    initial_revenue = st.sidebar.number_input("Initial Annual Revenue ($)", min_value=1000000, value=5000000, step=100000)
    initial_costs = st.sidebar.number_input("Initial Annual Costs ($)", min_value=1000000, value=3000000, step=100000)
    annual_revenue_growth = st.sidebar.slider("Annual Revenue Growth (%)", min_value=1, max_value=50, value=15) / 100
    annual_cost_growth = st.sidebar.slider("Annual Cost Growth (%)", min_value=1, max_value=50, value=10) / 100

    # Equipment Costs & Utilization
    st.sidebar.subheader("Equipment Purchases")

    with st.sidebar.form("equipment_form", clear_on_submit=True):
        eq_name = st.text_input("Equipment Name")
        eq_cost = st.number_input("Cost ($)", min_value=10000, value=500000, step=10000)
        eq_lifetime = st.number_input("Useful Life (years)", min_value=1, value=10, step=1)
        max_capacity = st.number_input("Max Production Capacity (units/year)", min_value=1, value=10000, step=100)
        submit_eq = st.form_submit_button("Add Equipment")

        if submit_eq and eq_name:
            equipment_list.append({"Name": eq_name, "Cost": eq_cost, "Useful Life": eq_lifetime, "Max Capacity": max_capacity})
            save_model(equipment_list, product_list, cost_drivers)
            st.success(f"Equipment '{eq_name}' added successfully!")

    # Cost Drivers Per Unit (Labor, Equipment, Overhead)
    st.sidebar.subheader("Cost Drivers")

    with st.sidebar.form("cost_driver_form", clear_on_submit=True):
        eq_type = st.text_input("Equipment Type")
        eq_cost_per_unit = st.number_input("Equipment Cost Per Unit ($)", min_value=0.01, value=1.00, step=0.01)
        machinist_cost = st.number_input("Machinist Labor Cost Per Unit ($)", min_value=0.01, value=10.00, step=0.01)
        design_labor_cost = st.number_input("Design Labor Cost Per Unit ($)", min_value=0.01, value=5.00, step=0.01)
        supervision_cost = st.number_input("Supervision Cost Per Unit ($)", min_value=0.01, value=2.00, step=0.01)
        submit_cost = st.form_submit_button("Set Cost Drivers")

        if submit_cost and eq_type:
            cost_drivers[eq_type] = {
                "Equipment Cost Per Unit": eq_cost_per_unit,
                "Machinist Labor": machinist_cost,
                "Design Labor": design_labor_cost,
                "Supervision": supervision_cost
            }
            save_model(equipment_list, product_list, cost_drivers)
            st.success(f"Cost drivers for '{eq_type}' set successfully!")

    # Product Ramp-Up
    st.sidebar.subheader("Product Lines")

    with st.sidebar.form("product_form", clear_on_submit=True):
        product_name = st.text_input("Product Name")
        initial_units = st.number_input("Initial Production Volume (units/year)", min_value=1, value=1000, step=100)
        unit_price = st.number_input("Unit Selling Price ($)", min_value=1, value=100, step=1)
        unit_cost = st.number_input("Unit Production Cost ($)", min_value=1, value=50, step=1)
        growth_rate = st.slider("Annual Production Growth (%)", min_value=1, max_value=50, value=10) / 100
        submit_product = st.form_submit_button("Add Product")

        if submit_product and product_name:
            product_list.append({"Name": product_name, "Initial Units": initial_units, "Unit Price": unit_price, "Unit Cost": unit_cost, "Growth Rate": growth_rate})
            save_model(equipment_list, product_list, cost_drivers)
            st.success(f"Product '{product_name}' added successfully!")

    # Financial Projections
    years = np.arange(2025, 2030)
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

    # Generate Income Statement Format
    financial_df = pd.DataFrame({
        "Year": years,
        "Revenue": revenue_forecast,
        "COGS": cost_forecast,
        "Gross Profit": np.array(revenue_forecast) - np.array(cost_forecast),
        "Operating Expenses": np.array(cost_forecast) * 0.20,  # Placeholder for OpEx
        "EBITDA": np.array(revenue_forecast) - np.array(cost_forecast) - (np.array(cost_forecast) * 0.20),
        "Depreciation": np.array(cost_forecast) * 0.05,  # Placeholder for Depreciation
        "EBIT": np.array(revenue_forecast) - np.array(cost_forecast) - (np.array(cost_forecast) * 0.20) - (np.array(cost_forecast) * 0.05),
        "Net Income": (np.array(revenue_forecast) - np.array(cost_forecast) - (np.array(cost_forecast) * 0.20) - (np.array(cost_forecast) * 0.05)) * 0.75  # 25% Tax
    })

    # Display Financial Reports
    st.subheader("📊 Income Statement")
    st.dataframe(financial_df.style.format({"Revenue": "${:,.0f}", "COGS": "${:,.0f}", "Gross Profit": "${:,.0f}",
                                            "Operating Expenses": "${:,.0f}", "EBITDA": "${:,.0f}", "Depreciation": "${:,.0f}",
                                            "EBIT": "${:,.0f}", "Net Income": "${:,.0f}"}))

if __name__ == "__main__":
    manufacturing_expansion_app()
