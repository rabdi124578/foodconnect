# app.py
import streamlit as st
import sqlite3
import datetime
import urllib.parse

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="FoodWise", page_icon="🍲", layout="wide")

# ---------------- DATABASE INIT ----------------
def init_db():
    conn = sqlite3.connect("foodwise.db")
    c = conn.cursor()
    # Listings table
    c.execute('''CREATE TABLE IF NOT EXISTS listings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  seller_name TEXT,
                  item TEXT,
                  quantity TEXT,
                  location TEXT,
                  timestamp TEXT)''')
    # Claims table
    c.execute('''CREATE TABLE IF NOT EXISTS claims
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  consumer_name TEXT,
                  listing_id INTEGER,
                  claim_time TEXT,
                  FOREIGN KEY (listing_id) REFERENCES listings(id))''')
    conn.commit()
    conn.close()

init_db()  # Ensure DB is ready

# ---------------- MAP EMBED ----------------
def get_map_embed(location):
    if "google.com/maps" in location:
        return location
    else:
        encoded = urllib.parse.quote_plus(location)
        return f"https://www.google.com/maps?q={encoded}&output=embed"

# ---------------- SESSION STATE ----------------
if "username" not in st.session_state:
    st.session_state.username = "Guest"  # default username

# ---------------- MAIN ----------------
st.title("🍲 FoodWise - Login-Free Version")

st.text_input("Enter your name:", key="username")

role = st.radio("Select your role:", ["Seller", "Consumer"], horizontal=True)

# ---------------- SELLER VIEW ----------------
if role == "Seller":
    st.header("🏠 Seller Dashboard")
    st.subheader("➕ Add Listing")
    item = st.text_input("Food Item")
    quantity = st.text_input("Quantity (e.g., 2kg, 5 plates)")
    location = st.text_input("Pickup Location (Address or Google Maps link)")
    if st.button("Submit Listing"):
        if item and quantity and location:
            conn = sqlite3.connect("foodwise.db")
            c = conn.cursor()
            c.execute("INSERT INTO listings (seller_name, item, quantity, location, timestamp) VALUES (?, ?, ?, ?, ?)",
                      (st.session_state.username, item, quantity, location, str(datetime.datetime.now())))
            conn.commit()
            conn.close()
            st.success("Listing added successfully!")
        else:
            st.error("Fill all fields")
    
    st.subheader("📋 My Listings & Claims")
    conn = sqlite3.connect("foodwise.db")
    c = conn.cursor()
    seller_listings = c.execute("SELECT id, item, quantity, location, timestamp FROM listings WHERE seller_name=? ORDER BY id DESC",
                                (st.session_state.username,)).fetchall()
    conn.close()
    if seller_listings:
        for listing_id, item, qty, loc, ts in seller_listings:
            st.markdown(f"### {item} ({qty})")
            st.write(f"📍 {loc}")
            st.write(f"🕒 {ts}")
            st.components.v1.iframe(get_map_embed(loc), height=250)
            conn = sqlite3.connect("foodwise.db")
            c = conn.cursor()
            claims = c.execute("SELECT consumer_name, claim_time FROM claims WHERE listing_id=?", (listing_id,)).fetchall()
            conn.close()
            if claims:
                st.success("✅ Claimed by:")
                for cons, t in claims:
                    st.write(f"- {cons} at {t}")
            else:
                st.info("❌ No claims yet")
            st.markdown("---")
    else:
        st.info("No listings yet")

# ---------------- CONSUMER VIEW ----------------
else:
    st.header("🏠 Consumer Dashboard")
    conn = sqlite3.connect("foodwise.db")
    c = conn.cursor()
    listings = c.execute("SELECT id, seller_name, item, quantity, location, timestamp FROM listings ORDER BY id DESC").fetchall()
    conn.close()
    if listings:
        for listing_id, seller, item, qty, loc, ts in listings:
            st.markdown(f"### {item} ({qty})")
            st.write(f"👤 Seller: {seller}")
            st.write(f"📍 {loc}")
            st.write(f"🕒 {ts}")
            st.components.v1.iframe(get_map_embed(loc), height=250)
            consumer_name = st.session_state.username
            if st.button(f"Claim Food - {listing_id}"):
                conn = sqlite3.connect("foodwise.db")
                c = conn.cursor()
                c.execute("INSERT INTO claims (consumer_name, listing_id, claim_time) VALUES (?, ?, ?)",
                          (consumer_name, listing_id, str(datetime.datetime.now())))
                conn.commit()
                conn.close()
                st.success(f"✅ You claimed {item} from {seller}")
            st.markdown("---")
    else:
        st.info("No food listings yet")
