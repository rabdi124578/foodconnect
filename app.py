import streamlit as st
import sqlite3
import datetime
import urllib.parse

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="FoodWise", page_icon="🍲", layout="wide")

# ---------------------- DATABASE SETUP ----------------------
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

# ---------------------- SESSION STATE ----------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None
if "username" not in st.session_state:
    st.session_state.username = ""
if "favorites" not in st.session_state:
    st.session_state.favorites = []

# ---------------------- FUNCTION: Convert Address to Google Maps Embed ----------------------
def get_map_embed(location):
    if "google.com/maps" in location:  # Direct Google Maps link
        return location
    else:  # Convert address into Google Maps search embed
        import urllib.parse
        encoded_address = urllib.parse.quote_plus(location)
        return f"https://www.google.com/maps?q={encoded_address}&output=embed"

# ---------------------- LOGIN PAGE ----------------------
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align:center;'>🍲 Welcome to FoodWise</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Reduce food waste · Share food · Help community</p>", unsafe_allow_html=True)

    st.markdown("### 🔑 Login / Signup")
    username = st.text_input("Enter your name")
    role = st.radio("Select your role:", ["Seller", "Consumer"], horizontal=True)

    if st.button("Login"):
        if username.strip():
            st.session_state.logged_in = True
            st.session_state.role = role.lower()
            st.session_state.username = username.strip()
            st.experimental_rerun()
        else:
            st.error("Please enter your name before logging in.")

else:
    # ---------------------- SIDEBAR ----------------------
    st.sidebar.success(f"👋 Hello {st.session_state.username} ({st.session_state.role.title()})")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = ""
        st.experimental_rerun()

    # ---------------------- SELLER VIEW ----------------------
    if st.session_state.role == "seller":
        tabs = st.tabs(["🏠 Home", "➕ Add Listing", "📋 My Listings & Claims"])
        
        # Home
        with tabs[0]:
            st.markdown("## 🏠 Home")
            st.write("Welcome to FoodWise! As a **Seller**, you can share surplus food with nearby NGOs/consumers.")
        
        # Add Listing
        with tabs[1]:
            st.markdown("## ➕ Add Food Listing")
            item = st.text_input("🍛 Food Item")
            quantity = st.text_input("📦 Quantity (e.g. 5 plates, 2kg)")
            location = st.text_input("📍 Pickup Location (Address or Google Maps link)")

            if st.button("Submit Listing"):
                if item.strip() and quantity.strip() and location.strip():
                    c.execute("INSERT INTO listings (seller_name, item, quantity, location, timestamp) VALUES (?, ?, ?, ?, ?)", 
                              (st.session_state.username, item, quantity, location, str(datetime.datetime.now())))
                    conn.commit()
                    st.success("✅ Listing added successfully!")
                else:
                    st.error("Please fill all fields.")

        # My Listings & Claims
        with tabs[2]:
            st.markdown("## 📋 My Listings & Claims")
            seller_listings = c.execute("SELECT id, item, quantity, location, timestamp FROM listings WHERE seller_name = ? ORDER BY id DESC", 
                                        (st.session_state.username,)).fetchall()
            if seller_listings:
                for listing_id, item, qty, location, ts in seller_listings:
                    st.markdown(f"### 🍛 {item} ({qty})")
                    st.write(f"📍 Location: {location}")
                    st.write(f"🕒 Posted: {ts}")

                    # Show map
                    map_url = get_map_embed(location)
                    st.components.v1.iframe(map_url, height=250)

                    # Show claims for this listing
                    claims = c.execute("SELECT consumer_name, claim_time FROM claims WHERE listing_id = ?", (listing_id,)).fetchall()
                    if claims:
                        st.success("✅ Claimed by:")
                        for consumer, claim_time in claims:
                            st.write(f"- 👤 {consumer} at {claim_time}")
                    else:
                        st.info("❌ No claims yet.")

                    st.markdown("---")
            else:
                st.info("You have not listed any items yet.")

    # ---------------------- CONSUMER VIEW ----------------------
    elif st.session_state.role == "consumer":
        tabs = st.tabs(["🏠 Home", "🥘 Recipes", "📅 Planner", "🤝 Sharing Hub", "⭐ Favorites"])
        
        # Home
        with tabs[0]:
            st.markdown("## 🏠 Home")
            st.write("Welcome to FoodWise! As a **Consumer**, you can discover recipes, plan meals, and claim food from Sharing Hub.")

        # Recipes
        with tabs[1]:
            st.markdown("## 🥘 Recipes")
            ingredients = st.text_area("Enter ingredients (comma separated):", placeholder="e.g. rice, tomato, onion")
            if st.button("Generate Recipe"):
                if ingredients.strip():
                    st.success(f"Recipe generated using: {ingredients}")
                    if st.button("⭐ Save to Favorites"):
                        st.session_state.favorites.append(f"Recipe with {ingredients}")
                        st.success("Recipe saved to Favorites!")
                else:
                    st.error("Please enter some ingredients.")

        # Planner
        with tabs[2]:
            st.markdown("## 📅 Planner")
            meal = st.text_input("Enter a meal for today:")
            if st.button("Save Plan"):
                st.success(f"Meal Plan saved: {meal}")

        # Sharing Hub (Consumer)
        with tabs[3]:
            st.markdown("## 🤝 Sharing Hub - Consumer")
            st.write("Browse available food listings:")

            listings = c.execute("SELECT id, seller_name, item, quantity, location, timestamp FROM listings ORDER BY id DESC").fetchall()
            if listings:
                for listing_id, seller, item, quantity, location, ts in listings:
                    st.markdown(f"### 🍛 {item} ({quantity})")
                    st.write(f"👤 Seller: {seller}")
                    st.write(f"🕒 Posted on: {ts}")
                    st.write(f"📍 Location: {location}")
                    
                    map_url = get_map_embed(location)
                    st.components.v1.iframe(map_url, height=250)

                    # Claim button
                    if st.button(f"🤝 Claim Food - {listing_id}"):
                        c.execute("INSERT INTO claims (consumer_name, listing_id, claim_time) VALUES (?, ?, ?)",
                                  (st.session_state.username, listing_id, str(datetime.datetime.now())))
                        conn.commit()
                        st.success(f"✅ You claimed {item} from {seller}")
                    
                    st.markdown("---")
            else:
                st.info("No food listings available right now.")

        # Favorites
        with tabs[4]:
            st.markdown("## ⭐ Favorites")
            if st.session_state.favorites:
                for fav in st.session_state.favorites:
                    st.write(f"✅ {fav}")
            else:
                st.info("No favorites saved yet.")
