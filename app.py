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

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def build_search_query(year, brand, player, card_number, variation, grade):
    parts = [year, brand, player]

    if card_number:
        parts.append(f"#{card_number}")
    if variation:
        parts.append(variation)
    if grade and grade != "Raw":
        parts.append(grade)

    return " ".join([str(p) for p in parts if p])

def ebay_link(query):
    encoded = quote_plus(query)
    return f"https://www.ebay.com/sch/i.html?_nkw={encoded}&LH_Sold=1&LH_Complete=1"

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
    df = st.session_state.inventory

    total_inventory = len(df[df["Status"] == "In Stock"])
    total_sales = df["Sale Price"].fillna(0).sum()
    total_profit = (df["Sale Price"].fillna(0) - df["Purchase Price"].fillna(0)).sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Cards in Stock", total_inventory)
    col2.metric("Total Sales", f"${total_sales:.2f}")
    col3.metric("Total Profit", f"${total_profit:.2f}")

    st.dataframe(df)

# -----------------------------
# VALUE CHECKER (NEW RELIABLE VERSION)
# -----------------------------
elif menu == "Value Checker":
    st.header("Card Value Checker")

    year = st.text_input("Year", "2024")
    brand = st.text_input("Brand/Set", "Topps Chrome")
    player = st.text_input("Player", "")
    card_number = st.text_input("Card Number", "")
    variation = st.text_input("Parallel/Variation", "")
    grade = st.selectbox("Grade", ["Raw", "PSA 10", "PSA 9", "BGS 9.5"])

    purchase_price = st.number_input("Your Purchase Price", 0.0)

    search_query = build_search_query(year, brand, player, card_number, variation, grade)

    if player:
        link = ebay_link(search_query)

        st.subheader("Step 1: Check eBay comps")
        st.link_button("Open eBay Sold Listings", link)

        st.subheader("Step 2: Enter 3 real sold prices")
        comp1 = st.number_input("Comp 1", 0.0)
        comp2 = st.number_input("Comp 2", 0.0)
        comp3 = st.number_input("Comp 3", 0.0)

        if st.button("Calculate Value"):
            comps = [comp1, comp2, comp3]
            comps = [c for c in comps if c > 0]

            if len(comps) >= 1:
                estimated = sum(comps) / len(comps)
                profit = estimated - purchase_price

                st.success(f"Estimated Value: ${estimated:.2f}")
                st.write(f"Potential Profit: ${profit:.2f}")

                if st.button("Add to Inventory"):
                    new_row = {
                        "Card Name": search_query,
                        "Purchase Price": purchase_price,
                        "Estimated Value": round(estimated, 2),
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

                    st.success("Card added to inventory!")

            else:
                st.warning("Enter at least one comp")

# -----------------------------
# ADD INVENTORY
# -----------------------------
elif menu == "Add Inventory":
    st.header("Add Card")

    name = st.text_input("Card Name")
    purchase = st.number_input("Purchase Price", 0.0)
    est = st.number_input("Estimated Value", 0.0)

    if st.button("Add"):
        new_row = {
            "Card Name": name,
            "Purchase Price": purchase,
            "Estimated Value": est,
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

        st.success("Added!")

# -----------------------------
# SALES
# -----------------------------
elif menu == "Sales Tracker":
    df = st.session_state.inventory
    in_stock = df[df["Status"] == "In Stock"]

    if not in_stock.empty:
        card = st.selectbox("Select Card", in_stock["Card Name"])
        price = st.number_input("Sale Price", 0.0)
        customer = st.text_input("Customer")

        if st.button("Record Sale"):
            idx = df[df["Card Name"] == card].index[0]

            st.session_state.inventory.at[idx, "Sale Price"] = price
            st.session_state.inventory.at[idx, "Customer"] = customer
            st.session_state.inventory.at[idx, "Date Sold"] = datetime.now().strftime("%Y-%m-%d")
            st.session_state.inventory.at[idx, "Status"] = "Sold"

            st.success("Sale recorded!")

# -----------------------------
# PROFITS
# -----------------------------
elif menu == "Profit Reports":
    df = st.session_state.inventory
    sold = df[df["Status"] == "Sold"].copy()

    if not sold.empty:
        sold["Profit"] = sold["Sale Price"] - sold["Purchase Price"]
        st.dataframe(sold)
        st.success(f"Total Profit: ${sold['Profit'].sum():.2f}")
    else:
        st.info("No sales yet")
