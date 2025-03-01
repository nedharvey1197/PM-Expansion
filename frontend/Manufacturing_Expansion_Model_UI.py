import streamlit as st
import pandas as pd
import numpy as np
import json
import os

SAVE_FILE = "financial_model_ui.json"

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

    # Expandable Equipment Section
    with st.expander("📋 View & Manage Equipment"):
        if equipment_list:
            st.dataframe(pd.DataFrame(equipment_list))
        else:
            st.info("No equipment added yet.")

    # Expandable Product Section
    with st.expander("📦 View & Manage Products"):
        if product_list:
            st.dataframe(pd.DataFrame(product_list))
        else:
            st.info("No products added yet.")

    # Equipment Purchases
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
    product_revenue_breakdown = {p["Name"]: [] for p in product_list}

    for year_idx in range(len(years)):
        yearly_revenue, yearly_cost, yearly_production = 0, 0, 0

        for product in product_list:
            units_produced = product["Initial Units"] * (1 + product["Growth Rate"]) ** year_idx
            yearly_revenue += units_produced * product["Unit Price"]
            yearly_cost += units_produced * product["Unit Cost"]
            yearly_production += units_produced
            product_revenue_breakdown[product["Name"]].append(units_produced * product["Unit Price"])

        revenue_forecast.append(yearly_revenue)
        cost_forecast.append(yearly_cost)
        total_production.append(yearly_production)

    # Generate Income Statement Format with Revenue Breakdown by Product
    financial_df = pd.DataFrame({"Year": years, "Revenue": revenue_forecast, "COGS": cost_forecast})
    
    # Add product-specific revenue breakdown
    for product_name, rev_list in product_revenue_breakdown.items():
        financial_df[product_name + " Revenue"] = rev_list

    financial_df["Gross Profit"] = financial_df["Revenue"] - financial_df["COGS"]
    financial_df["Operating Expenses"] = financial_df["COGS"] * 0.20  # Placeholder for OpEx
    financial_df["EBITDA"] = financial_df["Gross Profit"] - financial_df["Operating Expenses"]
    financial_df["Depreciation"] = financial_df["COGS"] * 0.05  # Placeholder for Depreciation
    financial_df["EBIT"] = financial_df["EBITDA"] - financial_df["Depreciation"]
    financial_df["Net Income"] = financial_df["EBIT"] * 0.75  # Assuming 25% Tax

    # Display Financial Reports
    st.subheader("📊 Income Statement (with Revenue Breakdown by Product)")
    st.dataframe(financial_df.style.format({"Revenue": "${:,.0f}", "COGS": "${:,.0f}", "Gross Profit": "${:,.0f}",
                                            "Operating Expenses": "${:,.0f}", "EBITDA": "${:,.0f}", "Depreciation": "${:,.0f}",
                                            "EBIT": "${:,.0f}", "Net Income": "${:,.0f}"}))

if __name__ == "__main__":
    manufacturing_expansion_app()
