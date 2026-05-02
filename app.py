import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Card Business Platform", layout="wide")

# Initialize inventory
if "inventory" not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=[
        "Card Name", "Purchase Price", "Estimated Value",
        "Sale Price", "Customer", "Date Added",
        "Date Sold", "Status"
    ])

st.title("Sports Card Business Platform")

menu = st.sidebar.selectbox(
    "Navigation",
    ["Dashboard", "Add Inventory", "Sales Tracker", "Profit Reports"]
)

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.header("Dashboard")

    df = st.session_state.inventory

    total_inventory = len(df[df["Status"] == "In Stock"])
    total_sales = df["Sale Price"].fillna(0).sum()
    total_profit = (df["Sale Price"].fillna(0) - df["Purchase Price"].fillna(0)).sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Cards in Stock", total_inventory)
    col2.metric("Total Sales", f"${total_sales:.2f}")
    col3.metric("Total Profit", f"${total_profit:.2f}")

    st.subheader("All Cards")
    st.dataframe(df, use_container_width=True)

# ---------------- ADD INVENTORY ----------------
elif menu == "Add Inventory":
    st.header("Add New Card")

    with st.form("add_card"):
        card_name = st.text_input("Card Name")
        purchase_price = st.number_input("Purchase Price", min_value=0.0, step=0.01)
        estimated_value = st.number_input("Estimated Value", min_value=0.0, step=0.01)

        submitted = st.form_submit_button("Add Card")

        if submitted:
            new_card = {
                "Card Name": card_name,
                "Purchase Price": purchase_price,
                "Estimated Value": estimated_value,
                "Sale Price": None,
                "Customer": None,
                "Date Added": datetime.now().strftime("%Y-%m-%d"),
                "Date Sold": None,
                "Status": "In Stock"
            }

            st.session_state.inventory = pd.concat(
                [st.session_state.inventory, pd.DataFrame([new_card])],
                ignore_index=True
            )

            st.success("Card added!")

# ---------------- SALES TRACKER ----------------
elif menu == "Sales Tracker":
    st.header("Record a Sale")

    df = st.session_state.inventory
    in_stock = df[df["Status"] == "In Stock"]

    if not in_stock.empty:
        card_selected = st.selectbox("Select Card", in_stock["Card Name"])
        sale_price = st.number_input("Sale Price", min_value=0.0, step=0.01)
        customer = st.text_input("Customer Name")

        if st.button("Record Sale"):
            idx = df[df["Card Name"] == card_selected].index[0]

            st.session_state.inventory.at[idx, "Sale Price"] = sale_price
            st.session_state.inventory.at[idx, "Customer"] = customer
            st.session_state.inventory.at[idx, "Date Sold"] = datetime.now().strftime("%Y-%m-%d")
            st.session_state.inventory.at[idx, "Status"] = "Sold"

            st.success("Sale recorded!")

    else:
        st.info("No cards available to sell.")

# ---------------- PROFIT REPORTS ----------------
elif menu == "Profit Reports":
    st.header("Profit Reports")

    df = st.session_state.inventory
    sold = df[df["Status"] == "Sold"].copy()

    if not sold.empty:
        sold["Profit"] = sold["Sale Price"] - sold["Purchase Price"]

        st.dataframe(sold, use_container_width=True)

        total_profit = sold["Profit"].sum()
        st.success(f"Total Profit: ${total_profit:.2f}")
    else:
        st.info("No sales yet.")
