import streamlit as st
import pandas as pd
import numpy as np
import json
import os

SAVE_FILE = "financial_model_debug.json"

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
    equipment_list = saved_data.get("equipment", [])
    product_list = saved_data.get("products", [])
    cost_drivers = saved_data.get("cost_drivers", {})

    # Sidebar Navigation
    page = st.sidebar.radio("Navigation", ["Financial Statements", "Manage Equipment", "Manage Products"])

    if page == "Manage Equipment":
        st.header("📋 Equipment List & Management")
        if equipment_list:
            st.dataframe(pd.DataFrame(equipment_list))
        else:
            st.info("No equipment added yet.")

        # Equipment Purchases
        with st.form("equipment_form", clear_on_submit=True):
            eq_name = st.text_input("Equipment Name")
            eq_cost = st.number_input("Cost ($)", min_value=10000, value=500000, step=10000)
            eq_lifetime = st.number_input("Useful Life (years)", min_value=1, value=10, step=1)
            max_capacity = st.number_input("Max Production Capacity (units/year)", min_value=1, value=10000, step=100)
            submit_eq = st.form_submit_button("Add Equipment")

            if submit_eq and eq_name:
                equipment_list.append({"Name": eq_name, "Cost": eq_cost, "Useful Life": eq_lifetime, "Max Capacity": max_capacity})
                save_model(equipment_list, product_list, cost_drivers)
                st.success(f"Equipment '{eq_name}' added successfully!")
                st.experimental_rerun()  # Forces UI to update with saved data
        st.header("⚙️ Set Cost Drivers")

        with st.form("cost_driver_form", clear_on_submit=True):
            eq_type = st.text_input("Equipment Type (e.g., CNC Machine, Laser Cutter)")
            eq_cost_per_unit = st.number_input("Equipment Cost Per Unit ($)", min_value=0.01, value=1.00, step=0.01)
            machinist_cost = st.number_input("Machinist Labor Cost Per Unit ($)", min_value=0.01, value=10.00, step=0.01)
            design_labor_cost = st.number_input("Design Labor Cost Per Unit ($)", min_value=0.01, value=5.00, step=0.01)
            supervision_cost = st.number_input("Supervision Cost Per Unit ($)", min_value=0.01, value=2.00, step=0.01)
            submit_cost = st.form_submit_button("Save Cost Drivers")

        if submit_cost and eq_type:
            cost_drivers[eq_type] = {
                "Equipment Cost Per Unit": eq_cost_per_unit,
                "Machinist Labor": machinist_cost,
                "Design Labor": design_labor_cost,
                "Supervision": supervision_cost
            }
        save_model(equipment_list, product_list, cost_drivers)
        st.success(f"Cost drivers for '{eq_type}' saved successfully!")
        if cost_drivers:
            st.subheader("📊 Existing Cost Drivers")
            st.dataframe(pd.DataFrame(cost_drivers).T)
        else:
            st.info("No cost drivers set yet.")

    elif page == "Manage Products":
        st.header("📦 Product List & Management")
        if product_list:
            st.dataframe(pd.DataFrame(product_list))
        else:
            st.info("No products added yet.")

        # Product Ramp-Up
        with st.form("product_form", clear_on_submit=True):
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
                st.experimental_rerun()  # Ensures new product appears immediately

    elif page == "Financial Statements":
        st.header("📊 Financial Statements")

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

        # Income Statement
        financial_df = pd.DataFrame({"Year": years, "Total Revenue": revenue_forecast, "COGS": cost_forecast})

        for product_name, rev_list in product_revenue_breakdown.items():
            financial_df[product_name + " Revenue"] = rev_list

        financial_df["Gross Profit"] = financial_df["Total Revenue"] - financial_df["COGS"]
        financial_df["Operating Expenses"] = financial_df["COGS"] * 0.20  # Placeholder for OpEx
        financial_df["EBITDA"] = financial_df["Gross Profit"] - financial_df["Operating Expenses"]
        financial_df["Depreciation"] = financial_df["COGS"] * 0.05  # Placeholder for Depreciation
        financial_df["EBIT"] = financial_df["EBITDA"] - financial_df["Depreciation"]
        financial_df["Net Income"] = financial_df["EBIT"] * 0.75  # Assuming 25% Tax

        st.subheader("📊 Income Statement")
        st.dataframe(financial_df.style.format("${:,.0f}"))

        # Balance Sheet & Cash Flow Statement
        st.subheader("📄 Balance Sheet")
        balance_sheet = pd.DataFrame({
            "Year": years,
            "Assets": np.array(financial_df["Total Revenue"]) * 0.6,  # Placeholder assumption
            "Liabilities": np.array(financial_df["Total Revenue"]) * 0.3,  # Placeholder assumption
            "Equity": np.array(financial_df["Total Revenue"]) * 0.3  # Placeholder
        })
        st.dataframe(balance_sheet.style.format("${:,.0f}"))

        st.subheader("💰 Cash Flow Statement")
        cash_flow = pd.DataFrame({
            "Year": years,
            "Operating Cash Flow": financial_df["EBITDA"] * 0.8,  # Placeholder assumption
            "Investing Cash Flow": financial_df["EBITDA"] * -0.2,  # Placeholder assumption
            "Financing Cash Flow": financial_df["EBITDA"] * 0.1  # Placeholder assumption
        })
        st.dataframe(cash_flow.style.format("${:,.0f}"))

if __name__ == "__main__":
    manufacturing_expansion_app()
