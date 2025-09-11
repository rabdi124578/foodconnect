import streamlit as st
import sqlite3
from datetime import datetime, timedelta

# ---------------------- INIT DATABASE ----------------------
def init_db():
    conn = sqlite3.connect("foodwise.db")
    c = conn.cursor()

    # Users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # Listings table
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
        price REAL,
        mode TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Claims table
    c.execute("""
    CREATE TABLE IF NOT EXISTS claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_id INTEGER,
        consumer_name TEXT,
        contact TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(listing_id) REFERENCES listings(id)
    )
    """)

    # Favorites table
    c.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        recipe TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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
    except:
        st.error("Username already exists!")
    conn.close()

def login(username, password):
    conn = sqlite3.connect("foodwise.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

# ---------------------- SELLER VIEW ----------------------
def seller_view(username):
    st.subheader("📦 Add New Listing")
    with st.form("add_listing"):
        item = st.text_input("Item")
        quantity = st.text_input("Quantity")
        expiry = st.date_input("Expiry Date")
        location = st.text_input("Pickup Location")
        contact = st.text_input("Contact")
        dietary = st.text_input("Dietary Info")
        notes = st.text_area("Notes")
        price = st.number_input("Price (₹)", min_value=0.0, step=1.0)
        mode = st.selectbox("Mode", ["Donate", "Sell"])
        submitted = st.form_submit_button("Add Listing")

        if submitted:
            conn = sqlite3.connect("foodwise.db")
            c = conn.cursor()
            c.execute("""INSERT INTO listings
                (seller_name, item, quantity, expiry, location, contact, dietary, notes, price, mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (username, item, quantity, str(expiry), location, contact, dietary, notes, price, mode))
            conn.commit()
            conn.close()
            st.success("Listing added successfully!")

    st.subheader("📜 My Listings & Claims")
    conn = sqlite3.connect("foodwise.db")
    c = conn.cursor()
    c.execute("SELECT id, item, quantity, expiry, location, price, mode FROM listings WHERE seller_name=?", (username,))
    listings = c.fetchall()
    for l in listings:
        st.write(f"**{l[1]}** ({l[2]}) | Exp: {l[3]} | ₹{l[5]} | {l[6]} | 📍 {l[4]}")
        c.execute("SELECT consumer_name, contact FROM claims WHERE listing_id=?", (l[0],))
        claims = c.fetchall()
        if claims:
            st.write("  ↳ Claims:")
            for claim in claims:
                st.write(f"     - {claim[0]} ({claim[1]})")
    conn.close()

# ---------------------- CONSUMER VIEW ----------------------
def consumer_view(user_id, username):
    tab1, tab2, tab3, tab4 = st.tabs(["🥗 Recipes", "📅 Meal Planner", "⭐ Favorites", "🍲 Sharing Hub"])

    # Recipes
    with tab1:
        st.subheader("Recipe Generator")
        ingredients = st.text_input("Enter ingredients (comma-separated)")
        if st.button("Generate Recipe"):
            recipe = f"Sample recipe using {ingredients}"
            st.success(recipe)
            if st.button("Save to Favorites"):
                conn = sqlite3.connect("foodwise.db")
                c = conn.cursor()
                c.execute("INSERT INTO favorites (user_id, recipe) VALUES (?, ?)", (user_id, recipe))
                conn.commit()
                conn.close()
                st.info("Saved to favorites!")

    # Meal Planner
    with tab2:
        st.subheader("Weekly Meal Planner")
        days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        for d in days:
            st.text_input(f"{d} Plan")

    # Favorites
    with tab3:
        st.subheader("My Favorites")
        conn = sqlite3.connect("foodwise.db")
        c = conn.cursor()
        c.execute("SELECT recipe FROM favorites WHERE user_id=?", (user_id,))
        favs = c.fetchall()
        for f in favs:
            st.write(f"- {f[0]}")
        conn.close()

    # Sharing Hub
    with tab4:
        st.subheader("Available Food Listings")
        conn = sqlite3.connect("foodwise.db")
        c = conn.cursor()
        c.execute("SELECT id, seller_name, item, quantity, expiry, location, contact, dietary, notes, price, mode, timestamp FROM listings ORDER BY id DESC")
        rows = c.fetchall()
        for r in rows:
            st.write(f"**{r[2]}** ({r[3]}) | Exp: {r[4]} | ₹{r[9]} | {r[10]}")
            st.caption(f"By {r[1]} | 📍 {r[5]} | 📞 {r[6]} | 🥗 {r[7]} | Notes: {r[8]}")
            map_url = f"https://maps.google.com/maps?q={r[5]}&t=&z=13&ie=UTF8&iwloc=&output=embed"
            st.components.v1.iframe(map_url, height=200)
            if st.button(f"Claim {r[2]}", key=r[0]):
                c.execute("INSERT INTO claims (listing_id, consumer_name, contact) VALUES (?, ?, ?)", (r[0], username, "N/A"))
                conn.commit()
                st.success("Claimed successfully!")
        conn.close()

# ---------------------- MAIN ----------------------
def main():
    st.title("🍲 FoodWise")
    menu = ["Login","Signup"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Signup":
        st.subheader("Create New Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["Seller","Consumer"])
        if st.button("Signup"):
            signup(username, password, role)
            st.success("Account created! Please login.")

    elif choice == "Login":
        st.subheader("Login Section")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = login(username, password)
            if user:
                st.success(f"Welcome {user[1]} ({user[3]})")
                if user[3] == "Seller":
                    seller_view(user[1])
                else:
                    consumer_view(user[0], user[1])
            else:
                st.error("Invalid credentials")

if __name__ == "__main__":
    init_db()
    main()
