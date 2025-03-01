import streamlit as st
import pandas as pd
import numpy as np
import json
import os

SAVE_FILE = "financial_model.json"  # Ensuring the original data file name remains

# Function to save and load data
def save_model(equipment_list, product_list, product_costs):
    data = {"equipment": equipment_list, "products": product_list, "product_costs": product_costs}
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_model():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return {"equipment": [], "products": [], "product_costs": {}}

def manufacturing_expansion_app():
    st.title("Manufacturing Financial Model")

    st.sidebar.header("User Inputs")

    # Load saved data if available
    saved_data = load_model()
    equipment_list = saved_data["equipment"]
    product_list = saved_data["products"]
    product_costs = saved_data["product_costs"]

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
                save_model(equipment_list, product_list, product_costs)
                st.success(f"Equipment '{eq_name}' added successfully!")

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
            growth_rate = st.slider("Annual Production Growth (%)", min_value=1, max_value=50, value=10) / 100
            selected_equipment = st.multiselect("Select Equipment Used", [eq["Name"] for eq in equipment_list])

            # Cost Drivers for Each Equipment Selected
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
                
                product_costs[product_name] = {
                    "Equipment Costs": equipment_cost_inputs,
                    "Machinist Labor": {"Cost Per Hour": machinist_cost_per_hour, "Hours Per Unit": machinist_hours_per_unit},
                    "Design Labor": {"Cost Per Hour": design_cost_per_hour, "Hours Per Unit": design_hours_per_unit},
                    "Supervision": {"Cost Per Hour": supervision_cost_per_hour, "Hours Per Unit": supervision_hours_per_unit}
                }

                save_model(equipment_list, product_list, product_costs)
                st.success(f"Product '{product_name}' and cost drivers added successfully!")

if __name__ == "__main__":
    manufacturing_expansion_app()
