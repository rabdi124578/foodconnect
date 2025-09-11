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
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT,
                  role TEXT)''')
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

# ---------------- SESSION STATE ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = None

# ---------------- LOGIN / SIGNUP ----------------
def signup(username, password, role):
    conn = sqlite3.connect("foodwise.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def login(username, password):
    conn = sqlite3.connect("foodwise.db")
    c = conn.cursor()
    c.execute("SELECT username, role FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

# ---------------- MAP EMBED ----------------
def get_map_embed(location):
    if "google.com/maps" in location:
        return location
    else:
        encoded = urllib.parse.quote_plus(location)
        return f"https://www.google.com/maps?q={encoded}&output=embed"

# ---------------- MAIN ----------------
def main():
    if not st.session_state.logged_in:
        st.title("🍲 FoodWise Login / Signup")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        role = st.radio("Role", ["Seller", "Consumer"], horizontal=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login"):
                user = login(username.strip(), password.strip())
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = user[0]
                    st.session_state.role = user[1]
                    st.experimental_rerun()
                else:
                    st.error("Invalid credentials")
        with col2:
            if st.button("Signup"):
                success = signup(username.strip(), password.strip(), role)
                if success:
                    st.success("Account created! You can login now.")
                else:
                    st.error("Username already exists")
    else:
        st.sidebar.success(f"👋 Hello {st.session_state.username} ({st.session_state.role})")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = None
            st.experimental_rerun()
        
        if st.session_state.role.lower() == "seller":
            seller_view()
        else:
            consumer_view()

# ---------------- SELLER VIEW ----------------
def seller_view():
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
def consumer_view():
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
            if st.button(f"Claim Food - {listing_id}"):
                conn = sqlite3.connect("foodwise.db")
                c = conn.cursor()
                c.execute("INSERT INTO claims (consumer_name, listing_id, claim_time) VALUES (?, ?, ?)",
                          (st.session_state.username, listing_id, str(datetime.datetime.now())))
                conn.commit()
                conn.close()
                st.success(f"✅ You claimed {item} from {seller}")
            st.markdown("---")
    else:
        st.info("No food listings yet")

# ---------------- RUN ----------------
if __name__ == "__main__":
    main()
