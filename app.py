import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd

# ---------------------- DB INIT ----------------------
def init_db():
    conn = sqlite3.connect("foodwise.db")
    c = conn.cursor()

    # USERS table (simple login)
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # LISTINGS table
    c.execute("""
    CREATE TABLE IF NOT EXISTS listings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        seller_name TEXT,
        item TEXT,
        quantity TEXT,
        expiry TEXT,
        location TEXT,
        contact TEXT,
        dietary TEXT,
        notes TEXT,
        price TEXT,
        mode TEXT,
        timestamp TEXT
    )
    """)

    # CLAIMS table
    c.execute("""
    CREATE TABLE IF NOT EXISTS claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        consumer_name TEXT,
        listing_id INTEGER,
        claim_time TEXT,
        FOREIGN KEY (listing_id) REFERENCES listings(id)
    )
    """)

    # FAVORITES table
    c.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        recipe TEXT
    )
    """)

    conn.commit()
    conn.close()

# ---------------------- AUTH ----------------------
def signup(username, password, role):
    conn = sqlite3.connect("foodwise.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login(username, password):
    conn = sqlite3.connect("foodwise.db")
    c = conn.cursor()
    c.execute("SELECT id, username, role FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

# ---------------------- MAIN UI ----------------------
def main():
    st.set_page_config(page_title="FoodWise", page_icon="🍲", layout="wide")
    st.title("🍲 FoodWise – Food Waste Reduction & Sharing")

    menu = ["Login", "Signup", "Consumer View", "Seller View", "Favorites"]
    choice = st.sidebar.selectbox("Navigate", menu)

    if choice == "Signup":
        st.subheader("Create Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["consumer", "seller"])
        if st.button("Signup"):
            if signup(username, password, role):
                st.success("Account created successfully! You can now log in.")
            else:
                st.error("Username already exists!")

    elif choice == "Login":
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = login(username, password)
            if user:
                st.session_state["user"] = {"id": user[0], "username": user[1], "role": user[2]}
                st.success(f"Welcome {user[1]}! Role: {user[2]}")
            else:
                st.error("Invalid username or password")

    elif choice == "Seller View":
        st.subheader("🤝 Share or Sell Food")
        if "user" not in st.session_state or st.session_state["user"]["role"] != "seller":
            st.warning("Please login as a seller.")
            return

        seller_name = st.session_state["user"]["username"]
        item = st.text_input("Item name")
        qty = st.text_input("Quantity / units")
        expiry = st.date_input("Expiry date", min_value=datetime.today(), value=datetime.today() + timedelta(days=2))
        location = st.text_input("Location / Area")
        contact = st.text_input("Contact (phone/email)")
        dietary = st.multiselect("Dietary info", ["Vegetarian", "Vegan", "Gluten-free", "Dairy-free", "Contains nuts"])
        notes = st.text_area("Additional notes")
        mode = st.radio("Mode", ["Donate", "Sell"])
        price = st.number_input("Price (₹)", min_value=0, value=0, step=5) if mode == "Sell" else "Free"

        if st.button("Add Listing"):
            conn = sqlite3.connect("foodwise.db")
            c = conn.cursor()
            c.execute("""INSERT INTO listings 
                (seller_name, item, quantity, expiry, location, contact, dietary, notes, price, mode, timestamp) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (seller_name, item, qty, expiry.strftime("%Y-%m-%d"), location, contact, ", ".join(dietary), notes, price, mode, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            st.success("Listing added!")

        # Show seller's listings
        conn = sqlite3.connect("foodwise.db")
        c = conn.cursor()
        c.execute("SELECT * FROM listings WHERE seller_name=?", (seller_name,))
        listings = c.fetchall()
        conn.close()

        if listings:
            st.write("### Your Listings")
            for l in listings:
                st.info(f"{l[2]} - {l[3]} units | {l[5]} | Expires {l[4]} | {l[6]} | {l[7]}")

    elif choice == "Consumer View":
        st.subheader("🛒 Browse Listings")
        conn = sqlite3.connect("foodwise.db")
        c = conn.cursor()
        c.execute("SELECT id, seller_name, item, quantity, expiry, location, contact, dietary, notes, price, mode, timestamp FROM listings ORDER BY id DESC")
        listings = c.fetchall()
        conn.close()

        if listings:
            for l in listings:
                with st.expander(f"{l[2]} ({l[3]}) - {l[10]}"):
                    st.write(f"**Seller:** {l[1]}")
                    st.write(f"**Expiry:** {l[4]}")
                    st.write(f"**Location:** {l[5]}")
                    st.write(f"**Contact:** {l[6]}")
                    st.write(f"**Dietary:** {l[7]}")
                    st.write(f"**Notes:** {l[8]}")
                    st.write(f"**Price:** {l[9]}")
        else:
            st.info("No listings yet!")

    elif choice == "Favorites":
        st.subheader("⭐ Favorite Recipes (Demo)")
        st.write("Feature coming soon!")

# ---------------------- RUN ----------------------
if __name__ == "__main__":
    init_db()
    main()
