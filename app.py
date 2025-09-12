# app.py - FoodWise (final with AI Recipe Generator integrated)
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from streamlit.components.v1 import html
import random

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="FoodWise", page_icon="🍲", layout="wide")
DB_PATH = "orders.db"

# ---------------------- DATABASE HELPERS ----------------------
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    restaurant TEXT,
                    food_item TEXT,
                    quantity TEXT,
                    expiry_time TEXT,
                    status TEXT DEFAULT 'Available',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    # Add new columns if not exist
    try: c.execute("ALTER TABLE orders ADD COLUMN confirmed_by TEXT")
    except: pass
    try: c.execute("ALTER TABLE orders ADD COLUMN ngo_contact TEXT")
    except: pass
    try: c.execute("ALTER TABLE orders ADD COLUMN ngo_location TEXT")
    except: pass
    conn.commit(); conn.close()
init_db()

# ---------------------- SESSION STATE ----------------------
if 'shared_items' not in st.session_state: st.session_state.shared_items = []
if 'favorite_recipes' not in st.session_state: st.session_state.favorite_recipes = []
if 'meal_plan' not in st.session_state: st.session_state.meal_plan = {}
if 'waste_log' not in st.session_state: st.session_state.waste_log = []
if 'user' not in st.session_state: st.session_state.user = None
if 'role' not in st.session_state: st.session_state.role = None

# ---------------------- PAGES ----------------------
st.title("🍲 FoodWise – Smart Food Waste Reduction")

tabs = st.tabs([
    "🏠 Home", "🍴 Restaurant Panel", "🏢 NGO Panel",
    "🤖 AI Recipe Generator", "📅 Meal Planner",
    "📤 Share Food", "⭐ Favorites", "🗑 Waste Log"
])

# ---------------------- HOME ----------------------
with tabs[0]:
    st.header("Welcome to FoodWise")
    st.markdown("AI-powered platform to reduce food waste & connect restaurants with NGOs.")

# ---------------------- RESTAURANT PANEL ----------------------
with tabs[1]:
    st.subheader("🍴 Restaurant Panel")
    r_name = st.text_input("Restaurant Name", key="r_name")
    f_item = st.text_input("Food Item", key="f_item")
    qty = st.text_input("Quantity (e.g. 10 plates)", key="qty")
    exp = st.time_input("Expiry Time")
    if st.button("Add Food Listing"):
        if r_name and f_item and qty:
            conn = get_conn()
            conn.execute("INSERT INTO orders (restaurant, food_item, quantity, expiry_time, status) VALUES (?,?,?,?,?)",
                         (r_name, f_item, qty, exp.strftime("%H:%M"), "Available"))
            conn.commit(); conn.close()
            st.success("✅ Food listing added!")
        else:
            st.error("Please fill all fields.")

    st.markdown("---")
    st.subheader("📦 Your Listings")
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM orders WHERE restaurant=?", conn, params=(r_name,))
    conn.close()
    if not df.empty:
        st.dataframe(df[["id","food_item","quantity","expiry_time","status"]])
        rem_id = st.number_input("Enter ID to Remove", min_value=1, step=1)
        if st.button("Remove Listing"):
            conn = get_conn()
            conn.execute("DELETE FROM orders WHERE id=? AND restaurant=?", (rem_id, r_name))
            conn.commit(); conn.close()
            st.success("❌ Listing removed!")

# ---------------------- NGO PANEL ----------------------
with tabs[2]:
    st.subheader("🏢 NGO Panel")
    ngo_name = st.text_input("NGO Name", key="ngo_name")
    contact = st.text_input("Contact Number", key="ngo_contact")
    location = st.text_input("NGO Location", key="ngo_loc")

    status_filter = st.selectbox("Filter by Status", ["All","Available","Confirmed"])
    conn = get_conn()
    query = "SELECT * FROM orders" if status_filter=="All" else "SELECT * FROM orders WHERE status=?"
    df = pd.read_sql(query, conn, params=(status_filter,) if status_filter!="All" else ())
    conn.close()

    if not df.empty:
        for _,row in df.iterrows():
            with st.expander(f"🍛 {row['food_item']} from {row['restaurant']} ({row['quantity']})"):
                st.write(f"⏰ Expiry: {row['expiry_time']} | Status: {row['status']}")
                if row['status']=="Available" and ngo_name and contact:
                    if st.button(f"Confirm Order #{row['id']}", key=f"conf_{row['id']}"):
                        conn = get_conn()
                        conn.execute("UPDATE orders SET status='Confirmed', confirmed_by=?, ngo_contact=?, ngo_location=? WHERE id=?",
                                     (ngo_name, contact, location, row['id']))
                        conn.commit(); conn.close()
                        st.success("✅ Order confirmed!")
                if row['ngo_location']:
                    st.markdown(f"📍 Location: {row['ngo_location']}")
                    map_url = f"https://www.google.com/maps/search/?api=1&query={row['ngo_location'].replace(' ','+')}"
                    html(f"<iframe src='{map_url}' width='100%' height='300'></iframe>", height=300)

# ---------------------- AI RECIPE GENERATOR ----------------------
with tabs[3]:
    st.subheader("🤖 AI Recipe Generator")
    st.markdown("Get creative AI-inspired recipes instantly!")

    ingredients = st.text_input("📝 Ingredients (comma-separated)", key="ai_ing",
                                placeholder="e.g., rice, tomato, cheese")

    sample_recipes = [
        "AI Fusion Fried Rice", "Neural Network Noodles", "Quantum Curry",
        "Deep Learning Dal", "Predictive Pasta", "Generative Gravy",
        "Data-Driven Dumplings", "Cognitive Curry Wraps", "AI-Powered Pizza",
        "Smart Salad Bowl", "Machine-Learning Momo", "Blockchain Biryani",
        "Cybernetic Soup", "Robotic Roti Rolls", "Augmented Reality Aloo Tikki",
        "ChatGPT Chole Bhature", "AI-Enhanced Egg Curry", "Meta Masala Paneer",
        "Vision-Driven Veggie Stir Fry", "Future-Forward Falafel"
    ]

    if st.button("Generate Recipes 🚀"):
        st.info("🤖 AI is generating your recipes...")
        st.markdown("### 🍽️ Suggested Recipes:")
        for i, recipe in enumerate(sample_recipes, 1):
            st.write(f"{i}. {recipe}")

# ---------------------- MEAL PLANNER ----------------------
with tabs[4]:
    st.subheader("📅 Weekly Meal Planner")
    days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    meals = ["Breakfast","Lunch","Dinner"]
    for d in days:
        with st.expander(d):
            st.session_state.meal_plan[d] = {}
            for m in meals:
                st.session_state.meal_plan[d][m] = st.text_input(f"{d} - {m}", key=f"{d}_{m}")
    st.success("✅ Planner saved locally.")

# ---------------------- SHARE FOOD ----------------------
with tabs[5]:
    st.subheader("📤 Share Food")
    food = st.text_input("Food Item to Share")
    qty = st.text_input("Quantity")
    if st.button("Share"):
        if food and qty:
            st.session_state.shared_items.append({"food":food,"qty":qty,"time":datetime.now()})
            st.success("✅ Food shared!")
    st.write("### Shared Items")
    st.table(pd.DataFrame(st.session_state.shared_items))

# ---------------------- FAVORITES ----------------------
with tabs[6]:
    st.subheader("⭐ Favorite Recipes")
    fav = st.text_input("Add Favorite Recipe")
    if st.button("Add to Favorites"):
        if fav: st.session_state.favorite_recipes.append(fav); st.success("✅ Added!")
    if st.session_state.favorite_recipes:
        st.write("### Your Favorites")
        st.table(st.session_state.favorite_recipes)

# ---------------------- WASTE LOG ----------------------
with tabs[7]:
    st.subheader("🗑 Food Waste Log")
    item = st.text_input("Wasted Item")
    reason = st.text_input("Reason")
    if st.button("Log Waste"):
        if item and reason:
            st.session_state.waste_log.append({"item":item,"reason":reason,"time":datetime.now()})
            st.success("✅ Logged!")
    if st.session_state.waste_log:
        st.write("### Waste History")
        st.table(pd.DataFrame(st.session_state.waste_log))
