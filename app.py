import streamlit as st
import pandas as pd
from datetime import datetime
from urllib.parse import quote_plus

st.set_page_config(
    page_title="SB Cards Business Platform",
    page_icon="🃏",
    layout="wide"
)

# -----------------------------
# CUSTOM STYLING
# -----------------------------
st.markdown("""
<style>
    .main {
        background-color: #f6f7fb;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .app-header {
        background: linear-gradient(135deg, #111827 0%, #1f2937 45%, #2563eb 100%);
        padding: 28px;
        border-radius: 22px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 12px 35px rgba(0,0,0,0.16);
    }

    .app-header h1 {
        margin: 0;
        font-size: 42px;
        font-weight: 800;
        letter-spacing: -1px;
    }

    .app-header p {
        margin-top: 8px;
        font-size: 17px;
        color: #dbeafe;
    }

    .section-card {
        background: white;
        padding: 24px;
        border-radius: 20px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
        border: 1px solid #e5e7eb;
        margin-bottom: 20px;
    }

    .small-muted {
        color: #6b7280;
        font-size: 14px;
    }

    .step-badge {
        display: inline-block;
        background: #dbeafe;
        color: #1d4ed8;
        padding: 6px 12px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 10px;
    }

    .profit-positive {
        color: #16a34a;
        font-weight: 800;
        font-size: 22px;
    }

    .profit-negative {
        color: #dc2626;
        font-weight: 800;
        font-size: 22px;
    }

    div[data-testid="stMetric"] {
        background: white;
        padding: 18px;
        border-radius: 18px;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
        border: 1px solid #e5e7eb;
    }

    .stButton > button {
        border-radius: 12px;
        height: 44px;
        font-weight: 700;
    }

    .stLinkButton > a {
        border-radius: 12px;
        font-weight: 700;
    }

    section[data-testid="stSidebar"] {
        background: #111827;
    }

    section[data-testid="stSidebar"] * {
        color: white;
    }
</style>
""", unsafe_allow_html=True)

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


def money(value):
    try:
        return f"${float(value):,.2f}"
    except Exception:
        return "$0.00"

# -----------------------------
# HEADER
# -----------------------------
st.markdown("""
<div class="app-header">
    <h1>🃏 SB Cards Business Platform</h1>
    <p>Price smarter. Track inventory. Record sales. Build a real card-flipping business.</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("## 🃏 SB Cards")
st.sidebar.markdown("Track the business like a pro.")

menu = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Value Checker", "Add Inventory", "Sales Tracker", "Profit Reports"]
)

# -----------------------------
# DASHBOARD
# -----------------------------
if menu == "Dashboard":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("📊 Business Dashboard")
    st.write("A quick snapshot of inventory, sales, and profit.")
    st.markdown('</div>', unsafe_allow_html=True)

    df = st.session_state.inventory

    total_inventory = len(df[df["Status"] == "In Stock"])
    total_sales = pd.to_numeric(df["Sale Price"], errors="coerce").fillna(0).sum()
    sold_cost = pd.to_numeric(df[df["Status"] == "Sold"]["Purchase Price"], errors="coerce").fillna(0).sum()
    total_profit = total_sales - sold_cost
    inventory_value = pd.to_numeric(df[df["Status"] == "In Stock"]["Estimated Value"], errors="coerce").fillna(0).sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cards in Stock", total_inventory)
    col2.metric("Inventory Value", money(inventory_value))
    col3.metric("Total Sales", money(total_sales))
    col4.metric("Total Profit", money(total_profit))

    st.markdown("### 📦 Inventory")
    if df.empty:
        st.info("No cards added yet. Start with the Value Checker or Add Inventory page.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

# -----------------------------
# VALUE CHECKER
# -----------------------------
elif menu == "Value Checker":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🔎 Card Value Checker")
    st.write("Build a precise eBay sold-listings search, enter real comps, and save the card to inventory.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<span class="step-badge">STEP 1</span>', unsafe_allow_html=True)
    st.markdown("### Enter Card Details")

    col1, col2 = st.columns(2)

    with col1:
        year = st.text_input("Year", "2024")
        brand = st.text_input("Brand / Set", "Topps Chrome")
        player = st.text_input("Player", "")
        card_number = st.text_input("Card Number", "")

    with col2:
        variation = st.text_input("Parallel / Variation", "")
        grade = st.selectbox("Grade", ["Raw", "PSA 10", "PSA 9", "BGS 9.5", "BGS 9", "SGC 10", "SGC 9.5", "Other"])
        purchase_price = st.number_input("Your Purchase Price", min_value=0.0, step=0.01)

    search_query = build_search_query(year, brand, player, card_number, variation, grade)

    st.markdown('<span class="step-badge">STEP 2</span>', unsafe_allow_html=True)
    st.markdown("### Check Sold Listings")

    if search_query:
        st.info(f"Search phrase: {search_query}")
        st.link_button("Open eBay Sold Listings", ebay_link(search_query))

    st.markdown('<span class="step-badge">STEP 3</span>', unsafe_allow_html=True)
    st.markdown("### Enter Sold Comps")

    comp_col1, comp_col2, comp_col3 = st.columns(3)
    with comp_col1:
        comp1 = st.number_input("Comp 1", min_value=0.0, step=0.01)
    with comp_col2:
        comp2 = st.number_input("Comp 2", min_value=0.0, step=0.01)
    with comp_col3:
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

            st.success(f"Estimated Value: {money(estimated)}")
            if profit >= 0:
                st.markdown(f'<p class="profit-positive">Potential Profit: {money(profit)}</p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p class="profit-negative">Potential Loss: {money(profit)}</p>', unsafe_allow_html=True)
        else:
            st.warning("Enter at least one comp.")

    if st.session_state.last_estimate is not None:
        st.divider()
        st.markdown('<span class="step-badge">STEP 4</span>', unsafe_allow_html=True)
        st.markdown("### Add to Inventory")

        review1, review2, review3 = st.columns(3)
        review1.metric("Card", st.session_state.last_card_name[:28] + "..." if len(st.session_state.last_card_name) > 28 else st.session_state.last_card_name)
        review2.metric("Cost", money(st.session_state.last_purchase_price))
        review3.metric("Est. Value", money(st.session_state.last_estimate))

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
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("➕ Add Card Manually")
    st.write("Use this for quick inventory entry when you already know the value.")
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        name = st.text_input("Card Name")
    with col2:
        purchase = st.number_input("Purchase Price", min_value=0.0, step=0.01)
    with col3:
        est = st.number_input("Estimated Value", min_value=0.0, step=0.01)

    if st.button("Add Card"):
        if name.strip():
            add_card_to_inventory(name, purchase, est)
            st.success("Card added!")
        else:
            st.warning("Enter a card name.")

# -----------------------------
# SALES TRACKER
# -----------------------------
elif menu == "Sales Tracker":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("💵 Sales Tracker")
    st.write("Record who bought the card and how much they paid.")
    st.markdown('</div>', unsafe_allow_html=True)

    df = st.session_state.inventory
    in_stock = df[df["Status"] == "In Stock"]

    if not in_stock.empty:
        card = st.selectbox("Select Card", in_stock["Card Name"])
        col1, col2 = st.columns(2)
        with col1:
            price = st.number_input("Sale Price", min_value=0.0, step=0.01)
        with col2:
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
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("📈 Profit Reports")
    st.write("See which cards made money and how profitable the business is.")
    st.markdown('</div>', unsafe_allow_html=True)

    df = st.session_state.inventory
    sold = df[df["Status"] == "Sold"].copy()

    if not sold.empty:
        sold["Sale Price"] = pd.to_numeric(sold["Sale Price"], errors="coerce").fillna(0)
        sold["Purchase Price"] = pd.to_numeric(sold["Purchase Price"], errors="coerce").fillna(0)
        sold["Profit"] = sold["Sale Price"] - sold["Purchase Price"]
        sold["Margin %"] = sold.apply(
            lambda row: round((row["Profit"] / row["Sale Price"] * 100), 2) if row["Sale Price"] else 0,
            axis=1
        )

        total_profit = sold["Profit"].sum()
        total_sales = sold["Sale Price"].sum()
        avg_margin = sold["Margin %"].mean()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Sales", money(total_sales))
        col2.metric("Total Profit", money(total_profit))
        col3.metric("Average Margin", f"{avg_margin:.1f}%")

        st.dataframe(sold, use_container_width=True, hide_index=True)
    else:
        st.info("No sales yet.")
