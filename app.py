# app.py - FoodWise (Multi-Page Professional Dashboard)
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from streamlit.components.v1 import html

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="FoodWise", page_icon="🍲", layout="wide")
DB_PATH = "orders.db"

# ---------------------- DATABASE HELPERS ----------------------
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant TEXT,
            food_item TEXT,
            quantity INTEGER,
            expiry DATETIME,
            ngo TEXT,
            status TEXT DEFAULT 'Available'
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------------- CUSTOM STYLING ----------------------
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #1f1c2c, #928dab);
        color: #ffffff;
        font-family: 'Segoe UI', sans-serif;
    }
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
    }
    h1, h2, h3 {
        color: #f8f9fa;
        font-weight: 600;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    div.stButton > button {
        background: linear-gradient(90deg, #ff416c, #ff4b2b);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6em 1.2em;
        font-size: 1em;
        font-weight: bold;
        transition: 0.3s;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    }
    div.stButton > button:hover {
        background: linear-gradient(90deg, #ff4b2b, #ff416c);
        transform: scale(1.05);
    }
    .stMarkdown, .stDataFrame, .stTable {
        background: rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    }
    input, textarea {
        border-radius: 10px !important;
        border: 1px solid #ddd !important;
        padding: 10px !important;
        font-size: 1em !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 2em;
        font-weight: bold;
        color: #00e6e6;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------- PAGE NAVIGATION ----------------------
st.sidebar.title("🍽️ FoodWise Navigation")
page = st.sidebar.radio("Go to", ["🏠 Dashboard", "🍴 Restaurant Panel", "🏢 NGO Panel"])

# ---------------------- DASHBOARD PAGE ----------------------
if page == "🏠 Dashboard":
    st.title("🍲 FoodWise - Smart Food Saving Platform")

    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Orders", "1,245", "+12%")
    with col2:
        st.metric("NGOs Connected", "56", "+4")
    with col3:
        st.metric("Restaurants Listed", "132", "+8")

    st.markdown("---")
    st.subheader("📊 Platform Overview")
    st.markdown(
        "FoodWise connects **restaurants with surplus food** to **NGOs helping the needy**, "
        "reducing food waste and fighting hunger at the same time."
    )

# ---------------------- RESTAURANT PANEL ----------------------
elif page == "🍴 Restaurant Panel":
    st.title("🍴 Restaurant Panel - Manage Food Listings")

    with st.form("add_order"):
        restaurant = st.text_input("Restaurant Name")
        food_item = st.text_input("Food Item")
        quantity = st.number_input("Quantity", min_value=1, step=1)
        expiry = st.date_input("Expiry Date", min_value=datetime.today())
        ngo = st.text_input("NGO (Optional)")

        submitted = st.form_submit_button("➕ Add Food Listing")
        if submitted and restaurant and food_item:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO orders (restaurant, food_item, quantity, expiry, ngo, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (restaurant, food_item, quantity, expiry, ngo, "Available"))
            conn.commit()
            conn.close()
            st.success("✅ Food listing added successfully!")

    st.markdown("---")
    st.subheader("📦 Current Listings")
    conn = get_conn()
    df = pd.read_sql("SELECT restaurant, food_item, quantity, expiry, status FROM orders", conn)
    conn.close()
    if not df.empty:
        st.dataframe(df)
    else:
        st.info("No listings yet.")

# ---------------------- NGO PANEL ----------------------
elif page == "🏢 NGO Panel":
    st.title("🏢 NGO Panel - Request Surplus Food")

    conn = get_conn()
    df = pd.read_sql("SELECT id, restaurant, food_item, quantity, expiry, status FROM orders WHERE status='Available'", conn)

    if not df.empty:
        st.dataframe(df)

        selected_id = st.number_input("Enter Order ID to Request", min_value=1, step=1)
        ngo_name = st.text_input("Your NGO Name")

        if st.button("📥 Request Food"):
            if ngo_name:
                cur = conn.cursor()
                cur.execute("UPDATE orders SET ngo=?, status='Requested' WHERE id=?", (ngo_name, selected_id))
                conn.commit()
                st.success("✅ Request sent successfully!")
            else:
                st.error("⚠️ Please enter NGO name before requesting.")
    else:
        st.info("No available surplus food right now.")

    conn.close()

# ---------------------- FOOTER ----------------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color: #ddd;'>Made with ❤️ for SharkTank @ JNU</p>", 
    unsafe_allow_html=True
)
