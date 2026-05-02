import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote_plus
import re

st.set_page_config(page_title="Card Business Platform", layout="wide")

# -----------------------------
# SESSION STORAGE
# -----------------------------
if "inventory" not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=[
        "Card Name", "Year", "Brand/Set", "Player", "Card Number",
        "Parallel/Variation", "Grade", "Serial Number", "Autograph",
        "Rookie Card", "Purchase Price", "Estimated Value", "Sale Price",
        "Customer", "Date Added", "Date Sold", "Status", "Accepted Comps"
    ])

# -----------------------------
# EBAY SOLD COMPS FUNCTIONS
# -----------------------------
def clean_price(price_text):
    match = re.search(r"\$([\d,]+\.?\d*)", price_text)
    if match:
        return float(match.group(1).replace(",", ""))
    return None


def build_search_query(year, brand, player, card_number, variation, grade, serial_number, autograph, rookie):
    parts = [year, brand, player]

    if card_number:
        parts.append(f"#{card_number}" if not str(card_number).startswith("#") else str(card_number))
    if variation:
        parts.append(variation)
    if grade and grade != "Raw":
        parts.append(grade)
    if serial_number:
        parts.append(serial_number)
    if autograph == "Yes":
        parts.append("auto autograph")
    if rookie == "Yes":
        parts.append("rookie RC")

    return " ".join([str(p).strip() for p in parts if str(p).strip()])


def bad_listing(title):
    bad_words = [
        "lot", "lots", "reprint", "digital", "break", "case", "pack", "box",
        "poster", "custom", "or best offer", "pick your", "you pick", "read"
    ]
    title_lower = title.lower()
    return any(word in title_lower for word in bad_words)


def get_ebay_sold_comps(search_query, max_results=12):
    encoded = quote_plus(search_query)
    url = f"https://www.ebay.com/sch/i.html?_nkw={encoded}&LH_Sold=1&LH_Complete=1&_sop=13"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    comps = []

    for item in soup.select(".s-item"):
        title_el = item.select_one(".s-item__title")
        price_el = item.select_one(".s-item__price")
        link_el = item.select_one(".s-item__link")

        if not title_el or not price_el:
            continue

        title = title_el.get_text(" ", strip=True)
        price = clean_price(price_el.get_text(" ", strip=True))
        link = link_el["href"] if link_el and link_el.has_attr("href") else ""

        if not title or title.lower() == "shop on ebay":
            continue
        if price is None:
            continue
        if bad_listing(title):
            continue

        comps.append({
            "Title": title,
            "Sold Price": price,
            "Link": link
        })

        if len(comps) >= max_results:
            break

    return comps


def format_money(value):
    try:
        return f"${float(value):,.2f}"
    except Exception:
        return "$0.00"

# -----------------------------
# APP LAYOUT
# -----------------------------
st.title("Sports Card Business Platform")
st.caption("Track inventory, sales, profits, customers, and eBay sold comps.")

menu = st.sidebar.selectbox(
    "Navigation",
    ["Dashboard", "Add Inventory", "eBay Value Checker", "Sales Tracker", "Profit Reports"]
)

# -----------------------------
# DASHBOARD
# -----------------------------
if menu == "Dashboard":
    st.header("Dashboard")

    df = st.session_state.inventory

    total_inventory = len(df[df["Status"] == "In Stock"])
    total_sales = pd.to_numeric(df["Sale Price"], errors="coerce").fillna(0).sum()
    total_cost = pd.to_numeric(df["Purchase Price"], errors="coerce").fillna(0).sum()
    total_profit = total_sales - pd.to_numeric(df[df["Status"] == "Sold"]["Purchase Price"], errors="coerce").fillna(0).sum()
    estimated_inventory_value = pd.to_numeric(df[df["Status"] == "In Stock"]["Estimated Value"], errors="coerce").fillna(0).sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cards in Stock", total_inventory)
    col2.metric("Inventory Value", format_money(estimated_inventory_value))
    col3.metric("Total Sales", format_money(total_sales))
    col4.metric("Total Profit", format_money(total_profit))

    st.subheader("All Cards")
    st.dataframe(df, use_container_width=True)

# -----------------------------
# ADD INVENTORY
# -----------------------------
elif menu == "Add Inventory":
    st.header("Add New Card")

    with st.form("add_card"):
        col1, col2, col3 = st.columns(3)
        with col1:
            year = st.text_input("Year", placeholder="2024")
            brand = st.text_input("Brand / Set", placeholder="Topps Chrome")
            player = st.text_input("Player", placeholder="CJ Stroud")
            card_number = st.text_input("Card Number", placeholder="150")
        with col2:
            variation = st.text_input("Parallel / Variation", placeholder="Silver Refractor")
            grade = st.selectbox("Grade", ["Raw", "PSA 10", "PSA 9", "BGS 9.5", "BGS 9", "SGC 10", "SGC 9.5", "Other"])
            serial_number = st.text_input("Serial Number", placeholder="/99, /199, 1/1")
            autograph = st.selectbox("Autograph?", ["No", "Yes"])
        with col3:
            rookie = st.selectbox("Rookie Card?", ["No", "Yes"])
            purchase_price = st.number_input("Purchase Price", min_value=0.0, step=0.01)
            estimated_value = st.number_input("Estimated Value", min_value=0.0, step=0.01)

        submitted = st.form_submit_button("Add Card")

        if submitted:
            card_name = build_search_query(year, brand, player, card_number, variation, grade, serial_number, autograph, rookie)

            new_card = {
                "Card Name": card_name,
                "Year": year,
                "Brand/Set": brand,
                "Player": player,
                "Card Number": card_number,
                "Parallel/Variation": variation,
                "Grade": grade,
                "Serial Number": serial_number,
                "Autograph": autograph,
                "Rookie Card": rookie,
                "Purchase Price": purchase_price,
                "Estimated Value": estimated_value,
                "Sale Price": None,
                "Customer": None,
                "Date Added": datetime.now().strftime("%Y-%m-%d"),
                "Date Sold": None,
                "Status": "In Stock",
                "Accepted Comps": ""
            }

            st.session_state.inventory = pd.concat(
                [st.session_state.inventory, pd.DataFrame([new_card])],
                ignore_index=True
            )

            st.success("Card added!")
            st.write("Search name created:", card_name)

# -----------------------------
# EBAY VALUE CHECKER
# -----------------------------
elif menu == "eBay Value Checker":
    st.header("eBay Sold Comps Value Checker")
    st.write("Enter exact card details. The app searches eBay sold listings, filters obvious bad matches, then lets you accept the comps that look right.")

    col1, col2, col3 = st.columns(3)
    with col1:
        year = st.text_input("Year", placeholder="2024")
        brand = st.text_input("Brand / Set", placeholder="Topps Chrome")
        player = st.text_input("Player", placeholder="CJ Stroud")
        card_number = st.text_input("Card Number", placeholder="150")
    with col2:
        variation = st.text_input("Parallel / Variation", placeholder="Silver Refractor")
        grade = st.selectbox("Grade", ["Raw", "PSA 10", "PSA 9", "BGS 9.5", "BGS 9", "SGC 10", "SGC 9.5", "Other"], key="checker_grade")
        serial_number = st.text_input("Serial Number", placeholder="/99, /199, 1/1")
        autograph = st.selectbox("Autograph?", ["No", "Yes"], key="checker_auto")
    with col3:
        rookie = st.selectbox("Rookie Card?", ["No", "Yes"], key="checker_rookie")
        purchase_price = st.number_input("Purchase Price if adding to inventory", min_value=0.0, step=0.01)

    search_query = build_search_query(year, brand, player, card_number, variation, grade, serial_number, autograph, rookie)
    st.info(f"eBay search phrase: {search_query}")

    if st.button("Find eBay Sold Comps"):
        if not player or not brand:
            st.warning("At minimum, enter Brand/Set and Player.")
        else:
            with st.spinner("Searching eBay sold listings..."):
                st.session_state.comps = get_ebay_sold_comps(search_query)
                st.session_state.last_search_query = search_query

    if "comps" in st.session_state and st.session_state.comps:
        st.subheader("Review Comps")
        st.write("Check only the listings that truly match the card.")

        accepted_prices = []
        accepted_titles = []

        for i, comp in enumerate(st.session_state.comps):
            with st.container(border=True):
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.write(f"**{comp['Title']}**")
                    st.write(f"Sold Price: **{format_money(comp['Sold Price'])}**")
                    if comp["Link"]:
                        st.link_button("Open eBay Listing", comp["Link"])
                with col_b:
                    accept = st.checkbox("Accept", key=f"accept_comp_{i}")
                    if accept:
                        accepted_prices.append(comp["Sold Price"])
                        accepted_titles.append(f"{comp['Title']} - {format_money(comp['Sold Price'])}")

        if accepted_prices:
            estimated_value = sum(accepted_prices) / len(accepted_prices)
            st.success(f"Estimated Value from Accepted Comps: {format_money(estimated_value)}")

            if st.button("Add This Card to Inventory"):
                new_card = {
                    "Card Name": st.session_state.last_search_query,
                    "Year": year,
                    "Brand/Set": brand,
                    "Player": player,
                    "Card Number": card_number,
                    "Parallel/Variation": variation,
                    "Grade": grade,
                    "Serial Number": serial_number,
                    "Autograph": autograph,
                    "Rookie Card": rookie,
                    "Purchase Price": purchase_price,
                    "Estimated Value": round(estimated_value, 2),
                    "Sale Price": None,
                    "Customer": None,
                    "Date Added": datetime.now().strftime("%Y-%m-%d"),
                    "Date Sold": None,
                    "Status": "In Stock",
                    "Accepted Comps": " | ".join(accepted_titles)
                }

                st.session_state.inventory = pd.concat(
                    [st.session_state.inventory, pd.DataFrame([new_card])],
                    ignore_index=True
                )
                st.success("Card added to inventory with accepted eBay comps!")
        else:
            st.warning("No comps accepted yet. Check the matching listings above.")

    elif "comps" in st.session_state:
        st.error("No sold comps found. Try fewer words or check spelling.")

# -----------------------------
# SALES TRACKER
# -----------------------------
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
        sold["Margin %"] = sold.apply(
            lambda row: round((row["Profit"] / row["Sale Price"] * 100), 2) if row["Sale Price"] else 0,
            axis=1
        )

        st.dataframe(sold, use_container_width=True)

        total_profit = sold["Profit"].sum()
        st.success(f"Total Profit: {format_money(total_profit)}")
    else:
        st.info("No sales yet.")
