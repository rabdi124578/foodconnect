import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import urllib.parse

# ---------------------- DB INIT ----------------------
def init_db():
    conn = sqlite3.connect("foodwise.db")
    c = conn.cursor()

    # USERS table
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

# ---------------------- MAP ----------------------
def get_map_embed(location):
    if "google.com/maps" in location:
        return location
    else:
        encoded = urllib.parse.quote_plus(location)
        return f"https://www.google.com/maps?q={encoded}&output=embed"

# ---------------------- MAIN ----------------------
def main():
    st.set_page_config(page_title="FoodWise", page_icon="🍲", layout="wide")
    st.title("🍲 FoodWise – Food Waste Sharing Platform")

    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is None:
        st.subheader("Login / Signup")
        tab = st.radio("Go to", ["Login", "Signup"], horizontal=True)

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if tab == "Signup":
            role = st.selectbox("Role", ["consumer", "seller"])
            if st.button("Signup"):
                if username.strip() and password.strip():
                    if signup(username.strip(), password.strip(), role):
                        st.success("Account created! Please login now.")
                    else:
                        st.error("Username already exists!")
                else:
                    st.error("Enter username & password")
        else:  # Login
            if st.button("Login"):
                user = login(username.strip(), password.strip())
                if user:
                    st.session_state.user = {"id": user[0], "username": user[1], "role": user[2]}
                    st.success(f"Welcome {user[1]} ({user[2]})")
                else:
                    st.error("Invalid username or password")

        return

    # ---------------------- LOGOUT ----------------------
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.experimental_rerun()

    # ---------------------- DASHBOARD ----------------------
    st.sidebar.success(f"Hello {st.session_state.user['username']} ({st.session_state.user['role']})")
    role = st.session_state.user["role"]

    if role == "seller":
        st.subheader("📦 Seller Dashboard - Share / Sell Food")
        item = st.text_input("Item name")
        qty = st.text_input("Quantity / units")
        expiry = st.date_input("Expiry date", min_value=datetime.today(), value=datetime.today() + timedelta(days=2))
        location = st.text_input("Location / Address / Google Maps Link")
        contact = st.text_input("Contact (phone/email)")
        dietary = st.multiselect("Dietary info", ["Vegetarian","Vegan","Gluten-free","Dairy-free","Contains nuts"])
        notes = st.text_area("Notes")
        mode = st.radio("Mode", ["Donate","Sell"])
        price = st.number_input("Price (₹)", min_value=0, value=50, step=5) if mode=="Sell" else "Free"

        if st.button("Add Listing"):
            conn = sqlite3.connect("foodwise.db")
            c = conn.cursor()
            c.execute("""INSERT INTO listings 
            (seller_name,item,quantity,expiry,location,contact,dietary,notes,price,mode,timestamp)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (st.session_state.user["username"], item, qty, expiry.strftime("%Y-%m-%d"),
             location, contact, ", ".join(dietary), notes, price, mode, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            st.success("Listing added!")

        # Show seller listings & claims
        conn = sqlite3.connect("foodwise.db")
        c = conn.cursor()
        c.execute("SELECT * FROM listings WHERE seller_name=? ORDER BY id DESC", (st.session_state.user["username"],))
        listings = c.fetchall()
        conn.close()

        if listings:
            st.write("### Your Listings")
            for l in listings:
                with st.expander(f"{l[2]} ({l[3]}) - {l[10]}"):
                    st.write(f"**Expiry:** {l[4]}")
                    st.write(f"**Location:** {l[5]}")
                    st.write(f"**Contact:** {l[6]}")
                    st.write(f"**Dietary:** {l[7]}")
                    st.write(f"**Notes:** {l[8]}")
                    st.write(f"**Price:** {l[9]}")
                    # Map
                    st.components.v1.iframe(get_map_embed(l[5]), height=250)

                    # Claims
                    conn = sqlite3.connect("foodwise.db")
                    c = conn.cursor()
                    c.execute("SELECT consumer_name, claim_time FROM claims WHERE listing_id=?", (l[0],))
                    claims = c.fetchall()
                    conn.close()
                    if claims:
                        st.success("Claimed by:")
                        for c_name, c_time in claims:
                            st.write(f"- {c_name} at {c_time}")
                    else:
                        st.info("No claims yet.")

    elif role == "consumer":
        st.subheader("🛒 Consumer Dashboard - Browse & Claim Food")
        conn = sqlite3.connect("foodwise.db")
        c = conn.cursor()
        c.execute("SELECT * FROM listings ORDER BY id DESC")
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
                    st.write(f"**Mode:** {l[10]}")
                    st.components.v1.iframe(get_map_embed(l[5]), height=250)
                    if st.button(f"Claim Food - {l[2]} ({l[0]})"):
                        conn = sqlite3.connect("foodwise.db")
                        c = conn.cursor()
                        c.execute("INSERT INTO claims (consumer_name, listing_id, claim_time) VALUES (?,?,?)",
                                  (st.session_state.user["username"], l[0], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                        conn.close()
                        st.success(f"You claimed {l[2]} from {l[1]}")
        else:
            st.info("No food listings yet!")

# ---------------------- RUN ----------------------
if __name__ == "__main__":
    init_db()
    main()
