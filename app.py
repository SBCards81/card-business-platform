import streamlit as st
import pandas as pd
from datetime import datetime
from urllib.parse import quote_plus

# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------
st.set_page_config(
    page_title="The Juice Card Platform",
    page_icon="🧃",
    layout="wide"
)

JUICE_IMAGE_URL = "https://raw.githubusercontent.com/SBCards81/card-business-platform/main/juice-bg.PNG"

# --------------------------------------------------
# CLEAN STYLING
# --------------------------------------------------
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: #f5efe6;
    }}

    .block-container {{
        max-width: 100% !important;
        padding: 2rem 3rem 2.5rem 3rem !important;
    }}

    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #020617 0%, #111827 60%, #0ea5e9 100%);
        border-right: 4px solid #111827;
    }}

    section[data-testid="stSidebar"] * {{
        color: white !important;
        font-weight: 700;
    }}

    .juice-banner {{
        background:
            linear-gradient(rgba(255,255,255,0.10), rgba(255,255,255,0.10)),
            url('{JUICE_IMAGE_URL}');
        background-size: contain;
        background-position: center;
        background-repeat: no-repeat;
        background-color: #fbf7ef;
        border-radius: 28px;
        min-height: 390px;
        padding: 36px;
        margin-bottom: 28px;
        box-shadow: 0 16px 42px rgba(0,0,0,0.16);
        border: 1px solid rgba(0,0,0,0.08);
    }}

    .banner-title {{
        font-size: 48px;
        font-weight: 950;
        color: #111827;
        margin-bottom: 10px;
    }}

    .banner-subtitle {{
        font-size: 21px;
        color: #111827;
        font-weight: 650;
    }}

    div[data-testid="stMetric"] {{
        background: rgba(255,255,255,0.84);
        padding: 24px;
        border-radius: 22px;
        box-shadow: 0 12px 28px rgba(0,0,0,0.12);
        border-left: 9px solid #f97316;
        min-height: 145px;
    }}

    div[data-testid="stMetricLabel"] {{
        font-size: 18px !important;
        font-weight: 800 !important;
        color: #111827 !important;
    }}

    div[data-testid="stMetricValue"] {{
        font-size: 46px !important;
        font-weight: 950 !important;
        color: #0f172a !important;
    }}

    .section-card {{
        background: rgba(255,255,255,0.92);
        padding: 26px;
        border-radius: 22px;
        box-shadow: 0 10px 28px rgba(0,0,0,0.10);
        margin-bottom: 24px;
        border: 1px solid rgba(0,0,0,0.08);
    }}

    .stButton > button {{
        background-color: #f97316;
        color: white;
        border-radius: 14px;
        min-height: 46px;
        font-weight: 900;
        border: 2px solid #111827;
        font-size: 16px;
    }}

    .stButton > button:hover {{
        background-color: #ea580c;
        color: white;
        border: 2px solid #111827;
    }}

    .stLinkButton > a {{
        background-color: #0ea5e9;
        color: white;
        border-radius: 14px;
        font-weight: 900;
        border: 2px solid #111827;
    }}

    [data-testid="stDataFrame"] {{
        background: rgba(255,255,255,0.9);
        border-radius: 18px;
        padding: 10px;
        box-shadow: 0 10px 24px rgba(0,0,0,0.08);
    }}

    .good {{ color: #15803d; font-weight: 950; font-size: 24px; }}
    .bad {{ color: #dc2626; font-weight: 950; font-size: 24px; }}
    .warn {{ color: #ea580c; font-weight: 950; font-size: 24px; }}

    @media (max-width: 768px) {{
        .block-container {{
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }}
        .banner-title {{
            font-size: 36px;
        }}
        .juice-banner {{
            min-height: 300px;
            padding: 24px;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# DATA SETUP
# --------------------------------------------------
columns = [
    "Card Name", "Year", "Brand/Set", "Player", "Sport", "Category",
    "Card Number", "Parallel/Variation", "Grade", "Purchase Price",
    "Estimated Value", "Target Buy Price", "Sale Price", "Fees", "Shipping",
    "Net Profit", "ROI %", "Customer", "Date Added", "Date Sold", "Status",
    "Image Name", "Notes"
]

if "inventory" not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=columns)
else:
    for col in columns:
        if col not in st.session_state.inventory.columns:
            st.session_state.inventory[col] = None

if "last_estimate" not in st.session_state:
    st.session_state.last_estimate = None

if "last_card" not in st.session_state:
    st.session_state.last_card = {}

# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------
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
    return f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(query)}&LH_Sold=1&LH_Complete=1"


def money(value):
    try:
        return f"${float(value):,.2f}"
    except Exception:
        return "$0.00"


def calculate_net(sale_price, purchase_price, fee_pct, shipping):
    fees = sale_price * (fee_pct / 100)
    net_profit = sale_price - purchase_price - fees - shipping
    roi = (net_profit / purchase_price * 100) if purchase_price > 0 else 0
    return round(fees, 2), round(net_profit, 2), round(roi, 2)


def target_buy_price(est_value, desired_profit, fee_pct, shipping):
    fees = est_value * (fee_pct / 100)
    target = est_value - fees - shipping - desired_profit
    return max(round(target, 2), 0)


def days_old(date_text):
    try:
        added = datetime.strptime(date_text, "%Y-%m-%d")
        return (datetime.now() - added).days
    except Exception:
        return 0


def add_card(card):
    st.session_state.inventory = pd.concat(
        [st.session_state.inventory, pd.DataFrame([card])],
        ignore_index=True
    )

# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------
st.sidebar.markdown("## 🧃 THE JUICE")
st.sidebar.markdown("Built for buying smarter and selling better.")

menu = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard", "Deal Analyzer", "Value Checker", "Add Inventory",
        "Sales Tracker", "Profit Reports", "Inventory Aging", "What’s Working"
    ]
)

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
if menu == "Dashboard":
    df = st.session_state.inventory.copy()

    total_inventory = len(df[df["Status"] == "In Stock"])
    inventory_value = pd.to_numeric(df[df["Status"] == "In Stock"]["Estimated Value"], errors="coerce").fillna(0).sum()
    total_sales = pd.to_numeric(df["Sale Price"], errors="coerce").fillna(0).sum()
    total_net_profit = pd.to_numeric(df["Net Profit"], errors="coerce").fillna(0).sum()
    avg_roi = pd.to_numeric(df[df["Status"] == "Sold"]["ROI %"], errors="coerce").fillna(0).mean()
    if pd.isna(avg_roi):
        avg_roi = 0

    st.markdown(
        """
        <div class="juice-banner">
            <div class="banner-title">📊 Business Dashboard</div>
            <div class="banner-subtitle">Real numbers: inventory value, sales, net profit, and ROI.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)
    row1_col1.metric("Cards in Stock", total_inventory)
    row1_col2.metric("Inventory Value", money(inventory_value))
    row1_col3.metric("Total Sales", money(total_sales))
    row1_col4.metric("Net Profit", money(total_net_profit))

    row2_col1, row2_col2 = st.columns([1, 2.25])
    row2_col1.metric("Average ROI", f"{avg_roi:.1f}%")
    row2_col2.metric("Total Cards Logged", len(df))

    st.markdown("## 📦 Inventory")
    if df.empty:
        st.info("No cards added yet. Start with Deal Analyzer or Value Checker.")
    else:
        show_cols = ["Card Name", "Player", "Brand/Set", "Category", "Purchase Price", "Estimated Value", "Status", "Date Added"]
        st.dataframe(df[show_cols], use_container_width=True, hide_index=True)

# --------------------------------------------------
# DEAL ANALYZER
# --------------------------------------------------
elif menu == "Deal Analyzer":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🔥 Deal Analyzer")
    st.write("Use this before buying a card. It tells you what you can pay and still make money.")
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        estimated_sale = st.number_input("Estimated Sale Price", min_value=0.0, step=0.01, value=100.0)
        asking_price = st.number_input("Seller Asking Price", min_value=0.0, step=0.01, value=50.0)
    with col2:
        fee_pct = st.number_input("Selling Fee %", min_value=0.0, step=0.1, value=13.25)
        shipping = st.number_input("Shipping / Supplies", min_value=0.0, step=0.01, value=5.00)
    with col3:
        desired_profit = st.number_input("Desired Profit", min_value=0.0, step=0.01, value=20.00)

    fees, net_profit, roi = calculate_net(estimated_sale, asking_price, fee_pct, shipping)
    max_buy = target_buy_price(estimated_sale, desired_profit, fee_pct, shipping)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Estimated Fees", money(fees))
    c2.metric("Max Buy Price", money(max_buy))
    c3.metric("Net Profit", money(net_profit))
    c4.metric("ROI", f"{roi:.1f}%")

    if asking_price <= max_buy and net_profit > 0:
        st.markdown('<p class="good">✅ Good deal based on your target profit.</p>', unsafe_allow_html=True)
    elif net_profit > 0:
        st.markdown('<p class="warn">⚠️ Profitable, but below your desired profit target.</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="bad">❌ Bad deal. You would likely lose money.</p>', unsafe_allow_html=True)

    st.divider()
    st.subheader("Optional: Save This Deal to Inventory")
    col_a, col_b = st.columns(2)
    with col_a:
        year = st.text_input("Year", "2024")
        brand = st.text_input("Brand / Set", "Topps Chrome")
        player = st.text_input("Player")
        sport = st.selectbox("Sport", ["Football", "Basketball", "Baseball", "Soccer", "Pokemon", "Other"])
    with col_b:
        category = st.selectbox("Category", ["Rookie QB", "Rookie", "Star", "Prospect", "Autograph", "Patch", "Graded", "Raw", "Other"])
        card_number = st.text_input("Card Number")
        variation = st.text_input("Parallel / Variation")
        grade = st.selectbox("Grade", ["Raw", "PSA 10", "PSA 9", "BGS 9.5", "BGS 9", "SGC 10", "SGC 9.5", "Other"])

    notes = st.text_area("Notes")
    image = st.file_uploader("Upload Card Image", type=["png", "jpg", "jpeg"])
    image_name = image.name if image else ""

    if st.button("Add Deal to Inventory"):
        card_name = build_search_query(year, brand, player, card_number, variation, grade)
        add_card({
            "Card Name": card_name,
            "Year": year,
            "Brand/Set": brand,
            "Player": player,
            "Sport": sport,
            "Category": category,
            "Card Number": card_number,
            "Parallel/Variation": variation,
            "Grade": grade,
            "Purchase Price": asking_price,
            "Estimated Value": estimated_sale,
            "Target Buy Price": max_buy,
            "Sale Price": None,
            "Fees": None,
            "Shipping": None,
            "Net Profit": None,
            "ROI %": None,
            "Customer": None,
            "Date Added": datetime.now().strftime("%Y-%m-%d"),
            "Date Sold": None,
            "Status": "In Stock",
            "Image Name": image_name,
            "Notes": notes
        })
        st.success("Deal added to inventory!")

# --------------------------------------------------
# VALUE CHECKER
# --------------------------------------------------
elif menu == "Value Checker":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🔎 Card Value Checker")
    st.write("Build a precise eBay sold-listings search, enter comps, then save the card.")
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        year = st.text_input("Year", "2024")
        brand = st.text_input("Brand / Set", "Topps Chrome")
        player = st.text_input("Player", "")
        sport = st.selectbox("Sport", ["Football", "Basketball", "Baseball", "Soccer", "Pokemon", "Other"])
        card_number = st.text_input("Card Number", "")
    with col2:
        category = st.selectbox("Category", ["Rookie QB", "Rookie", "Star", "Prospect", "Autograph", "Patch", "Graded", "Raw", "Other"])
        variation = st.text_input("Parallel / Variation", "")
        grade = st.selectbox("Grade", ["Raw", "PSA 10", "PSA 9", "BGS 9.5", "BGS 9", "SGC 10", "SGC 9.5", "Other"])
        purchase_price = st.number_input("Your Purchase Price", min_value=0.0, step=0.01)

    search_query = build_search_query(year, brand, player, card_number, variation, grade)
    if search_query:
        st.info(f"Search phrase: {search_query}")
        st.link_button("Open eBay Sold Listings", ebay_link(search_query))

    st.subheader("Enter Sold Comps")
    comp1, comp2, comp3 = st.columns(3)
    with comp1:
        c1 = st.number_input("Comp 1", min_value=0.0, step=0.01)
    with comp2:
        c2 = st.number_input("Comp 2", min_value=0.0, step=0.01)
    with comp3:
        c3 = st.number_input("Comp 3", min_value=0.0, step=0.01)

    fee_pct = st.number_input("Selling Fee %", min_value=0.0, step=0.1, value=13.25)
    shipping = st.number_input("Shipping / Supplies", min_value=0.0, step=0.01, value=5.00)

    if st.button("Calculate Value"):
        comps = [x for x in [c1, c2, c3] if x > 0]
        if comps:
            estimated = round(sum(comps) / len(comps), 2)
            fees, net_profit, roi = calculate_net(estimated, purchase_price, fee_pct, shipping)
            max_buy = target_buy_price(estimated, 20, fee_pct, shipping)
            st.session_state.last_estimate = estimated
            st.session_state.last_card = {
                "Card Name": search_query,
                "Year": year,
                "Brand/Set": brand,
                "Player": player,
                "Sport": sport,
                "Category": category,
                "Card Number": card_number,
                "Parallel/Variation": variation,
                "Grade": grade,
                "Purchase Price": purchase_price,
                "Estimated Value": estimated,
                "Target Buy Price": max_buy,
                "Fees": fees,
                "Shipping": shipping,
                "Net Profit": net_profit,
                "ROI %": roi
            }
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Estimated Value", money(estimated))
            m2.metric("Est. Fees", money(fees))
            m3.metric("Net Profit", money(net_profit))
            m4.metric("ROI", f"{roi:.1f}%")
        else:
            st.warning("Enter at least one comp.")

    if st.session_state.last_estimate is not None and st.session_state.last_card:
        st.divider()
        st.subheader("Add to Inventory")
        notes = st.text_area("Notes", key="value_notes")
        image = st.file_uploader("Upload Card Image", type=["png", "jpg", "jpeg"], key="value_image")
        image_name = image.name if image else ""
        if st.button("Add to Inventory"):
            card = st.session_state.last_card.copy()
            card.update({
                "Sale Price": None,
                "Customer": None,
                "Date Added": datetime.now().strftime("%Y-%m-%d"),
                "Date Sold": None,
                "Status": "In Stock",
                "Image Name": image_name,
                "Notes": notes
            })
            add_card(card)
            st.success("Card added to inventory!")
            st.session_state.last_estimate = None
            st.session_state.last_card = {}

# --------------------------------------------------
# ADD INVENTORY
# --------------------------------------------------
elif menu == "Add Inventory":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("➕ Add Inventory Manually")
    st.write("Quick entry when you already know the buy price and value.")
    st.markdown('</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        year = st.text_input("Year")
        brand = st.text_input("Brand / Set")
        player = st.text_input("Player")
        sport = st.selectbox("Sport", ["Football", "Basketball", "Baseball", "Soccer", "Pokemon", "Other"])
    with col2:
        category = st.selectbox("Category", ["Rookie QB", "Rookie", "Star", "Prospect", "Autograph", "Patch", "Graded", "Raw", "Other"])
        card_number = st.text_input("Card Number")
        variation = st.text_input("Parallel / Variation")
        grade = st.selectbox("Grade", ["Raw", "PSA 10", "PSA 9", "BGS 9.5", "BGS 9", "SGC 10", "SGC 9.5", "Other"])
    with col3:
        purchase = st.number_input("Purchase Price", min_value=0.0, step=0.01)
        est = st.number_input("Estimated Value", min_value=0.0, step=0.01)
        target = st.number_input("Target Buy Price", min_value=0.0, step=0.01)
    notes = st.text_area("Notes")
    image = st.file_uploader("Upload Card Image", type=["png", "jpg", "jpeg"])
    image_name = image.name if image else ""
    if st.button("Add Card"):
        card_name = build_search_query(year, brand, player, card_number, variation, grade)
        if card_name.strip():
            add_card({
                "Card Name": card_name,
                "Year": year,
                "Brand/Set": brand,
                "Player": player,
                "Sport": sport,
                "Category": category,
                "Card Number": card_number,
                "Parallel/Variation": variation,
                "Grade": grade,
                "Purchase Price": purchase,
                "Estimated Value": est,
                "Target Buy Price": target,
                "Sale Price": None,
                "Fees": None,
                "Shipping": None,
                "Net Profit": None,
                "ROI %": None,
                "Customer": None,
                "Date Added": datetime.now().strftime("%Y-%m-%d"),
                "Date Sold": None,
                "Status": "In Stock",
                "Image Name": image_name,
                "Notes": notes
            })
            st.success("Card added!")
        else:
            st.warning("Enter enough card info to create a card name.")

# --------------------------------------------------
# SALES TRACKER
# --------------------------------------------------
elif menu == "Sales Tracker":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("💵 Sales Tracker")
    st.write("Record the real sale, fees, shipping, net profit, and ROI.")
    st.markdown('</div>', unsafe_allow_html=True)
    df = st.session_state.inventory
    in_stock = df[df["Status"] == "In Stock"]
    if not in_stock.empty:
        card = st.selectbox("Select Card", in_stock["Card Name"])
        selected = df[df["Card Name"] == card].iloc[0]
        purchase_price = float(selected.get("Purchase Price") or 0)
        col1, col2, col3 = st.columns(3)
        with col1:
            price = st.number_input("Sale Price", min_value=0.0, step=0.01)
        with col2:
            fee_pct = st.number_input("Selling Fee %", min_value=0.0, step=0.1, value=13.25)
        with col3:
            shipping = st.number_input("Shipping / Supplies", min_value=0.0, step=0.01, value=5.00)
        customer = st.text_input("Customer")
        fees, net_profit, roi = calculate_net(price, purchase_price, fee_pct, shipping)
        m1, m2, m3 = st.columns(3)
        m1.metric("Fees", money(fees))
        m2.metric("Net Profit", money(net_profit))
        m3.metric("ROI", f"{roi:.1f}%")
        if st.button("Record Sale"):
            idx = df[df["Card Name"] == card].index[0]
            st.session_state.inventory.at[idx, "Sale Price"] = price
            st.session_state.inventory.at[idx, "Fees"] = fees
            st.session_state.inventory.at[idx, "Shipping"] = shipping
            st.session_state.inventory.at[idx, "Net Profit"] = net_profit
            st.session_state.inventory.at[idx, "ROI %"] = roi
            st.session_state.inventory.at[idx, "Customer"] = customer
            st.session_state.inventory.at[idx, "Date Sold"] = datetime.now().strftime("%Y-%m-%d")
            st.session_state.inventory.at[idx, "Status"] = "Sold"
            st.success("Sale recorded!")
    else:
        st.info("No cards available to sell.")

# --------------------------------------------------
# PROFIT REPORTS
# --------------------------------------------------
elif menu == "Profit Reports":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("📈 Profit Reports")
    st.write("See actual net profit after fees and shipping.")
    st.markdown('</div>', unsafe_allow_html=True)
    df = st.session_state.inventory.copy()
    sold = df[df["Status"] == "Sold"].copy()
    if not sold.empty:
        for col in ["Sale Price", "Purchase Price", "Fees", "Shipping", "Net Profit", "ROI %"]:
            sold[col] = pd.to_numeric(sold[col], errors="coerce").fillna(0)
        total_sales = sold["Sale Price"].sum()
        total_profit = sold["Net Profit"].sum()
        avg_roi = sold["ROI %"].mean()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Sales", money(total_sales))
        col2.metric("Net Profit", money(total_profit))
        col3.metric("Average ROI", f"{avg_roi:.1f}%")
        show_cols = ["Card Name", "Player", "Brand/Set", "Purchase Price", "Sale Price", "Fees", "Shipping", "Net Profit", "ROI %", "Customer", "Date Sold"]
        st.dataframe(sold[show_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No sales yet.")

# --------------------------------------------------
# INVENTORY AGING
# --------------------------------------------------
elif menu == "Inventory Aging":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("⏳ Inventory Aging")
    st.write("Find cards that may be sitting too long and tying up cash.")
    st.markdown('</div>', unsafe_allow_html=True)
    df = st.session_state.inventory.copy()
    in_stock = df[df["Status"] == "In Stock"].copy()
    if not in_stock.empty:
        in_stock["Days in Inventory"] = in_stock["Date Added"].apply(days_old)
        in_stock["Action"] = in_stock["Days in Inventory"].apply(lambda d: "Consider lowering price" if d >= 30 else "Hold")
        aged = in_stock.sort_values("Days in Inventory", ascending=False)
        st.dataframe(aged[["Card Name", "Player", "Purchase Price", "Estimated Value", "Days in Inventory", "Action"]], use_container_width=True, hide_index=True)
    else:
        st.info("No in-stock inventory yet.")

# --------------------------------------------------
# WHAT'S WORKING
# --------------------------------------------------
elif menu == "What’s Working":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🧠 What’s Working")
    st.write("Use past sales to see what players, sets, and categories are making money.")
    st.markdown('</div>', unsafe_allow_html=True)
    df = st.session_state.inventory.copy()
    sold = df[df["Status"] == "Sold"].copy()
    if not sold.empty:
        sold["Net Profit"] = pd.to_numeric(sold["Net Profit"], errors="coerce").fillna(0)
        sold["ROI %"] = pd.to_numeric(sold["ROI %"], errors="coerce").fillna(0)
        st.markdown("### Top Players by Net Profit")
        player_perf = sold.groupby("Player", dropna=False).agg(Sales=("Sale Price", "count"), Net_Profit=("Net Profit", "sum"), Avg_ROI=("ROI %", "mean")).reset_index().sort_values("Net_Profit", ascending=False)
        st.dataframe(player_perf, use_container_width=True, hide_index=True)
        st.markdown("### Best Categories")
        cat_perf = sold.groupby("Category", dropna=False).agg(Sales=("Sale Price", "count"), Net_Profit=("Net Profit", "sum"), Avg_ROI=("ROI %", "mean")).reset_index().sort_values("Net_Profit", ascending=False)
        st.dataframe(cat_perf, use_container_width=True, hide_index=True)
        st.markdown("### Best Sets")
        set_perf = sold.groupby("Brand/Set", dropna=False).agg(Sales=("Sale Price", "count"), Net_Profit=("Net Profit", "sum"), Avg_ROI=("ROI %", "mean")).reset_index().sort_values("Net_Profit", ascending=False)
        st.dataframe(set_perf, use_container_width=True, hide_index=True)
    else:
        st.info("Sell a few cards first, then this page will show what is working.")
