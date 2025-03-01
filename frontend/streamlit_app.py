import streamlit as st
import pandas as pd
import numpy as np
import json
import os

SAVE_FILE = "financial_model_data.json"  # Ensuring the original data file name remains

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
    st.title("Manufacturing Financial Model")
    
     # Sidebar Navigation
    st.sidebar.header("Navigation")
    page = st.sidebar.radio("Select a Page", ["Financial Statements", "Manage Equipment", "Manage Products"])

    st.sidebar.header("User Inputs")
    # User Input Fields
    initial_revenue = st.sidebar.number_input("Initial Annual Revenue ($)", min_value=0, value=0, step=50000)
    initial_costs = st.sidebar.number_input("Initial Annual Costs ($)", min_value=0, value=0, step=50000)
    annual_revenue_growth = st.sidebar.slider("Annual Revenue Growth (%)", min_value=1, max_value=50, value=15) / 100
    annual_cost_growth = st.sidebar.slider("Annual Cost Growth (%)", min_value=1, max_value=50, value=10) / 100

    # Financing Inputs
    debt_ratio = st.sidebar.slider("Debt Financing Ratio (%)", min_value=0, max_value=100, value=50) / 100
    interest_rate = st.sidebar.slider("Annual Interest Rate (%)", min_value=1, max_value=20, value=10) / 100

    # Load saved data if available
    saved_data = load_model()
    equipment_list = saved_data["equipment"]
    product_list = saved_data["products"]
    cost_drivers = saved_data["cost_drivers"]

   

    if page == "Manage Equipment":
        st.header("📋 Equipment List & Management")
        if equipment_list:
            for i, eq in enumerate(equipment_list):
                col1, col2 = st.columns([2,2])  # Adjust width for button alignment
                with col1:
                    st.write(f"🔹 {eq['Name']} - Cost: ${eq['Cost']:,.2f}")
                with col2:
                    if st.button(f"❌ Remove", key=f"del_eq_{i}"):
                        del equipment_list[i]
                        save_model(equipment_list, product_list, cost_drivers)
                        st.experimental_rerun()  # Refresh UI
        else:
            st.info("No equipment added yet.")

        # Equipment Purchases
        st.header("📋 Add Equipment")
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

    elif page == "Manage Products":
        st.header("📦 Product List & Management")
        if product_list:
            for i, prod in enumerate(product_list):
                col1, col2 = st.columns([2, 2])  # Adjust width for button alignment
                with col1:
                    st.write(f"🛠 {prod['Name']} - Price: ${prod['Unit Price']:,.2f}")
                with col2:
                    if st.button(f"❌ Remove", key=f"del_prod_{i}"):
                        del product_list[i]
                        save_model(equipment_list, product_list, cost_drivers)
                        st.experimental_rerun()  # Refresh UI
        else:
            st.info("No products added yet.")

        # Product Ramp-Up
        st.header("📋 Add New Product")
        with st.form("product_form", clear_on_submit=True):
            product_name = st.text_input("Product Name")
            initial_units = st.number_input("Initial Production Volume (units/year)", min_value=1, value=1000, step=100)
            unit_price = st.number_input("Unit Selling Price ($)", min_value=1, value=100, step=1)
            growth_rate = st.slider("Annual Production Growth (%)", min_value=1, max_value=50, value=10) / 100
            selected_equipment = st.multiselect("Select Equipment Used", [eq["Name"] for eq in equipment_list])

            # Cost Drivers for Each Equipment Selected
            st.header("📋 Enter Cost Drivers Equipment")
            equipment_cost_inputs = {}
            for eq_name in selected_equipment:
                st.subheader(f"⚙️ Cost Drivers for {eq_name}")
                cost_per_hour = st.number_input(f"{eq_name} - Cost Per Hour ($)", min_value=0.01, value=50.00, step=0.01)
                hours_per_unit = st.number_input(f"{eq_name} - Hours Per Unit Produced", min_value=0.01, value=1.00, step=0.01)
                equipment_cost_inputs[eq_name] = {"Cost Per Hour": cost_per_hour, "Hours Per Unit": hours_per_unit}

            # Labor & Supervision Costs
            st.subheader("👷 Labor & Supervision Costs")
            machinist_cost_per_hour = st.number_input("Machinist Labor Cost Per Hour ($)", min_value=0.01, value=30.00, step=0.01)
            machinist_hours_per_unit = st.number_input("Machinist Hours Per Unit", min_value=0.01, value=2.00, step=0.01)
            design_cost_per_hour = st.number_input("Design Labor Cost Per Hour ($)", min_value=0.01, value=40.00, step=0.01)
            design_hours_per_unit = st.number_input("Design Hours Per Unit", min_value=0.01, value=1.00, step=0.01)
            supervision_cost_per_hour = st.number_input("Supervision Cost Per Hour ($)", min_value=0.01, value=20.00, step=0.01)
            supervision_hours_per_unit = st.number_input("Supervision Hours Per Unit", min_value=0.01, value=0.50, step=0.01)

            submit_product = st.form_submit_button("Add Product & Cost Drivers")

            if submit_product and product_name:
                product_list.append({"Name": product_name, "Initial Units": initial_units, "Unit Price": unit_price, "Growth Rate": growth_rate})
                
                cost_drivers[product_name] = {
                    "Equipment Costs": equipment_cost_inputs,
                    "Machinist Labor": {"Cost Per Hour": machinist_cost_per_hour, "Hours Per Unit": machinist_hours_per_unit},
                    "Design Labor": {"Cost Per Hour": design_cost_per_hour, "Hours Per Unit": design_hours_per_unit},
                    "Supervision": {"Cost Per Hour": supervision_cost_per_hour, "Hours Per Unit": supervision_hours_per_unit}
                }

                save_model(equipment_list, product_list, cost_drivers)
                st.success(f"Product '{product_name}' and cost drivers added successfully!")
                
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
        st.dataframe(financial_df.style.format("${:,.0f}"), use_container_width=True)

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
