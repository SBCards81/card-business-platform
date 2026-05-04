import streamlit as st
import pandas as pd
from datetime import datetime
from urllib.parse import quote_plus

st.set_page_config(page_title="Card Business Platform", layout="wide")

# -----------------------------
# SESSION STORAGE
# -----------------------------
if "inventory" not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=[
        "Card Name", "Purchase Price", "Estimated Value",
        "Sale Price", "Customer", "Date Added",
        "Date Sold", "Status"
    ])

if "last_estimate" not in st.session_state:
    st.session_state.last_estimate = None

if "last_card_name" not in st.session_state:
    st.session_state.last_card_name = ""

if "last_purchase_price" not in st.session_state:
    st.session_state.last_purchase_price = 0.0

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def build_search_query(year, brand, player, card_number, variation, grade):
    parts = [year, brand, player]

    if card_number:
        parts.append(f"#{card_number}" if not str(card_number).startswith("#") else str(card_number))
    if variation:
        parts.append(variation)
    if grade and grade != "Raw":
        parts.append(grade)

    return " ".join([str(p).strip() for p in parts if str(p).strip()])


def ebay_link(query):
    encoded = quote_plus(query)
    return f"https://www.ebay.com/sch/i.html?_nkw={encoded}&LH_Sold=1&LH_Complete=1"


def add_card_to_inventory(card_name, purchase_price, estimated_value):
    new_row = {
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
        [st.session_state.inventory, pd.DataFrame([new_row])],
        ignore_index=True
    )

# -----------------------------
# APP
# -----------------------------
st.title("Sports Card Business Platform")

menu = st.sidebar.selectbox(
    "Navigation",
    ["Dashboard", "Value Checker", "Add Inventory", "Sales Tracker", "Profit Reports"]
)

# -----------------------------
# DASHBOARD
# -----------------------------
if menu == "Dashboard":
    st.header("Dashboard")
    df = st.session_state.inventory

    total_inventory = len(df[df["Status"] == "In Stock"])
    total_sales = pd.to_numeric(df["Sale Price"], errors="coerce").fillna(0).sum()
    sold_cost = pd.to_numeric(df[df["Status"] == "Sold"]["Purchase Price"], errors="coerce").fillna(0).sum()
    total_profit = total_sales - sold_cost
    inventory_value = pd.to_numeric(df[df["Status"] == "In Stock"]["Estimated Value"], errors="coerce").fillna(0).sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cards in Stock", total_inventory)
    col2.metric("Inventory Value", f"${inventory_value:.2f}")
    col3.metric("Total Sales", f"${total_sales:.2f}")
    col4.metric("Total Profit", f"${total_profit:.2f}")

    st.subheader("Inventory")
    st.dataframe(df, use_container_width=True)

# -----------------------------
# VALUE CHECKER
# -----------------------------
elif menu == "Value Checker":
    st.header("Card Value Checker")
    st.write("Use the eBay sold-listings link, enter real sold comps, then add the card to inventory.")

    col1, col2 = st.columns(2)

    with col1:
        year = st.text_input("Year", "2024")
        brand = st.text_input("Brand/Set", "Topps Chrome")
        player = st.text_input("Player", "")
        card_number = st.text_input("Card Number", "")

    with col2:
        variation = st.text_input("Parallel/Variation", "")
        grade = st.selectbox("Grade", ["Raw", "PSA 10", "PSA 9", "BGS 9.5", "BGS 9", "SGC 10", "SGC 9.5", "Other"])
        purchase_price = st.number_input("Your Purchase Price", min_value=0.0, step=0.01)

    search_query = build_search_query(year, brand, player, card_number, variation, grade)

    if search_query:
        st.info(f"Search phrase: {search_query}")
        st.link_button("Open eBay Sold Listings", ebay_link(search_query))

    st.subheader("Enter Sold Comps")
    comp1 = st.number_input("Comp 1", min_value=0.0, step=0.01)
    comp2 = st.number_input("Comp 2", min_value=0.0, step=0.01)
    comp3 = st.number_input("Comp 3", min_value=0.0, step=0.01)

    if st.button("Calculate Value"):
        comps = [comp1, comp2, comp3]
        comps = [c for c in comps if c > 0]

        if len(comps) >= 1:
            estimated = round(sum(comps) / len(comps), 2)
            profit = round(estimated - purchase_price, 2)

            st.session_state.last_estimate = estimated
            st.session_state.last_card_name = search_query
            st.session_state.last_purchase_price = purchase_price

            st.success(f"Estimated Value: ${estimated:.2f}")
            st.write(f"Potential Profit: ${profit:.2f}")
        else:
            st.warning("Enter at least one comp.")

    if st.session_state.last_estimate is not None:
        st.divider()
        st.subheader("Ready to Add")
        st.write(f"Card: **{st.session_state.last_card_name}**")
        st.write(f"Purchase Price: **${st.session_state.last_purchase_price:.2f}**")
        st.write(f"Estimated Value: **${st.session_state.last_estimate:.2f}**")

        if st.button("Add to Inventory"):
            add_card_to_inventory(
                st.session_state.last_card_name,
                st.session_state.last_purchase_price,
                st.session_state.last_estimate
            )
            st.success("Card added to inventory!")
            st.session_state.last_estimate = None
            st.session_state.last_card_name = ""
            st.session_state.last_purchase_price = 0.0

# -----------------------------
# ADD INVENTORY
# -----------------------------
elif menu == "Add Inventory":
    st.header("Add Card Manually")

    name = st.text_input("Card Name")
    purchase = st.number_input("Purchase Price", min_value=0.0, step=0.01)
    est = st.number_input("Estimated Value", min_value=0.0, step=0.01)

    if st.button("Add"):
        if name.strip():
            add_card_to_inventory(name, purchase, est)
            st.success("Card added!")
        else:
            st.warning("Enter a card name.")

# -----------------------------
# SALES TRACKER
# -----------------------------
elif menu == "Sales Tracker":
    st.header("Record a Sale")

    df = st.session_state.inventory
    in_stock = df[df["Status"] == "In Stock"]

    if not in_stock.empty:
        card = st.selectbox("Select Card", in_stock["Card Name"])
        price = st.number_input("Sale Price", min_value=0.0, step=0.01)
        customer = st.text_input("Customer")

        if st.button("Record Sale"):
            idx = df[df["Card Name"] == card].index[0]

            st.session_state.inventory.at[idx, "Sale Price"] = price
            st.session_state.inventory.at[idx, "Customer"] = customer
            st.session_state.inventory.at[idx, "Date Sold"] = datetime.now().strftime("%Y-%m-%d")
            st.session_state.inventory.at[idx, "Status"] = "Sold"

            st.success("Sale recorded!")
    else:
        st.info("No cards available to sell.")

# -----------------------------
# PROFIT REPORTS
# -----------------------------
elif menu == "Profit Reports":
    st.header("Profit Reports")

    df = st.session_state.inventory
    sold = df[df["Status"] == "Sold"].copy()

    if not sold.empty:
        sold["Sale Price"] = pd.to_numeric(sold["Sale Price"], errors="coerce").fillna(0)
        sold["Purchase Price"] = pd.to_numeric(sold["Purchase Price"], errors="coerce").fillna(0)
        sold["Profit"] = sold["Sale Price"] - sold["Purchase Price"]
        st.dataframe(sold, use_container_width=True)
        st.success(f"Total Profit: ${sold['Profit'].sum():.2f}")
    else:
        st.info("No sales yet.")
