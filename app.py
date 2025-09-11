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
"""
Enhanced FoodWise Streamlit app
- Refactored into functions
- SQLite persistence for listings, favorites, meal_plan
- Modular recipe generation with placeholders for Spoonacular/Edamam API
- Google Maps integration: uses Google Maps Embed API if you provide an API key
  (via st.secrets['GOOGLE_MAPS_API_KEY'] or environment variable 'GOOGLE_MAPS_API_KEY')
- Improved UI layout and interaction

To run:
1. pip install streamlit pandas folium
2. streamlit run FoodWise_streamlit_app_enhanced.py

Set your Google Maps API key (optional, for embed maps):
- Add to ~/.streamlit/secrets.toml:
  GOOGLE_MAPS_API_KEY = "YOUR_KEY_HERE"

If you don't provide a key, the map will show a Folium map (open-source) instead.
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import os
import json
import math
import folium
from streamlit.components.v1 import html

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="FoodWise", page_icon="🍲", layout="wide")
DB_PATH = "foodwise.db"
MAP_ZOOM_DEFAULT = 14

# ---------------------- DATABASE HELPERS ----------------------
@st.experimental_singleton
def get_db_conn(path=DB_PATH):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(conn):
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS shared_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mode TEXT,
                    item TEXT,
                    qty TEXT,
                    expiry TEXT,
                    dietary TEXT,
                    location TEXT,
                    lat REAL,
                    lng REAL,
                    contact TEXT,
                    price TEXT,
                    notes TEXT,
                    date_posted TEXT
                )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS favorite_recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    ingredients TEXT,
                    instructions TEXT,
                    time TEXT,
                    difficulty TEXT,
                    created_at TEXT
                )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS meal_plan (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    day TEXT,
                    meal TEXT,
                    value TEXT
                )""")
    conn.commit()

# ---------------------- UTILITIES ----------------------
@st.cache_data
def parse_ingredients(text):
    return [x.strip() for x in text.split(",") if x.strip()]

def now_date_str():
    return datetime.today().strftime("%Y-%m-%d")

# Map helpers
def get_google_maps_iframe(lat, lng, api_key, zoom=MAP_ZOOM_DEFAULT, width="100%", height=450):
    # Use Google Maps Embed API for a place centered on lat,lng
    if not api_key:
        return None
    src = f"https://www.google.com/maps/embed/v1/view?key={api_key}&center={lat},{lng}&zoom={zoom}&maptype=roadmap"
    iframe = f"<iframe width=\"{width}\" height=\"{height}\" frameborder=0 style=\"border:0\" src=\"{src}\" allowfullscreen></iframe>"
    return iframe

def show_map(lat, lng, label=None, api_key=None, zoom=MAP_ZOOM_DEFAULT, height=400):
    if api_key:
        iframe = get_google_maps_iframe(lat, lng, api_key, zoom=zoom, height=height)
        if iframe:
            html(iframe, height=height)
            return
    # fallback to folium
    m = folium.Map(location=[lat, lng], zoom_start=zoom)
    folium.Marker([lat, lng], popup=label or f"{lat},{lng}").add_to(m)
    html(m._repr_html_(), height=height)

# Optional: geocode address using Google Geocoding API (if key provided)
# Note: network calls will work when the app runs on a machine with internet access.
import requests

def geocode_address(address, api_key=None):
    if not api_key:
        return None
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": api_key}
    try:
        r = requests.get(url, params=params, timeout=8)
        data = r.json()
        if data.get("status") == "OK":
            loc = data["results"][0]["geometry"]["location"]
            return loc["lat"], loc["lng"]
    except Exception:
        return None
    return None

# ---------------------- INIT ----------------------
conn = get_db_conn()
init_db(conn)
cur = conn.cursor()

# ---------------------- STYLES ----------------------
st.markdown(
    """
    <style>
    .foodwise-hero h1 { color:#FF6F61; font-size: 2.6rem; margin-bottom:0; }
    .foodwise-hero h3 { color:#22C55E; font-weight:600; margin-top:0.25rem; }
    .stButton>button { background:#FF6F61; color:white; border-radius:10px; }
    .pill { display:inline-block; padding:6px 10px; border-radius:999px; background:#F1F5F9; margin-right:8px; margin-bottom:8px; font-size:0.85rem; }
    .recipe-card { border: 1px solid #E2E8F0; border-radius:10px; padding:0.8rem; margin-bottom:0.6rem; }
    .feature-card { background: #F8FAFC; border-radius:10px; padding:1rem; margin-bottom:1rem; }
    </style>
    """, unsafe_allow_html=True)

# ---------------------- HEADER ----------------------
st.markdown('<div class="foodwise-hero" style="text-align:center; padding: 8px 0 12px 0;">'
            '<h1>🍲 FoodWise</h1>'
            '<h3>AI‑Powered Food Waste Reduction & Sharing</h3>'
            '<p>Turn leftovers into recipes, plan meals precisely, and share surplus with your community.</p>'
            '</div>', unsafe_allow_html=True)

# ---------------------- NAV ----------------------
tabs = st.tabs(["🏠 Home", "🥘 Recipes", "📅 Planner", "🤝 Sharing Hub", "⭐ Favorites"])

# Load maps API key from secrets or env
MAPS_KEY = None
if "GOOGLE_MAPS_API_KEY" in st.secrets:
    MAPS_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
elif os.getenv("GOOGLE_MAPS_API_KEY"):
    MAPS_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# ---------------------- HOME ----------------------
with tabs[0]:
    st.markdown("### 🌟 Welcome to FoodWise!")
    st.markdown("""
    <div class="feature-card">
    Reduce food waste, save money, and help your community by making the most of your food ingredients.
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1,1])
    with c1:
        st.subheader("Why FoodWise?")
        st.write("- 1/3 of all food produced globally is wasted each year")
        st.write("- The average family throws away ₹50,000 worth of food annually")
        st.write("- FoodWise helps you reduce waste while enjoying delicious meals")

        st.subheader("Key Features")
        st.markdown("• **Leftover Recipe Generator** - Transform ingredients into meals")
        st.markdown("• **Smart Food Planner** - Plan meals and calculate portions")
        st.markdown("• **Food Sharing Hub** - Share surplus with your community")
        st.markdown("• **Favorite Recipes** - Save your go-to recipes")

        st.caption("Built with Streamlit · SQLite · Optional APIs (Spoonacular/Edamam, Maps)")

    with c2:
        st.markdown("**🚀 Quick Start**")
        ingredients_quick = st.text_input("Enter leftovers (comma-separated)", key="home_ing", placeholder="e.g., chicken, rice, carrots")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Suggest Recipes", key="home_btn", use_container_width=True):
                if ingredients_quick.strip():
                    items = parse_ingredients(ingredients_quick)
                    if items:
                        base = items[:3] if len(items) >= 3 else items + ["veggies", "spices"][len(items):]
                        st.success("Here are some ideas:")
                        with st.expander("Recipe Suggestions", expanded=True):
                            st.markdown(f"""
                            <div class="recipe-card">
                            <h4>🍳 {base[0].title()} Stir‑Fry</h4>
                            <p><strong>Ingredients:</strong> {', '.join(base[:2])}, soy sauce, garlic, oil</p>
                            <p><strong>Time:</strong> 20 minutes | <strong>Difficulty:</strong> Easy</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.warning("Please enter at least one ingredient.")
                else:
                    st.warning("Please enter at least one ingredient.")
        with col2:
            if st.button("Clear Input", key="clear_btn", use_container_width=True):
                st.session_state.home_ing = ""
                st.experimental_rerun()

# ---------------------- RECIPES ----------------------
with tabs[1]:
    st.subheader("🥘 Leftover Recipe Generator")
    st.markdown("Transform your leftover ingredients into delicious meals!")

    c1, c2 = st.columns([2,1])
    with c1:
        ingredients = st.text_input("📝 Ingredients (comma-separated)", key="rec_ing", placeholder="e.g., chicken, rice, carrots, potatoes")
        diet = st.selectbox("Diet preference", ["Any", "Vegetarian", "Vegan", "Gluten-free", "Dairy-free"])
        time_limit = st.slider("Max cooking time (minutes)", 10, 120, 30)
        difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], value="Easy")

        if st.button("🔍 Generate Recipes", key="rec_btn", use_container_width=True):
            if ingredients.strip():
                items = parse_ingredients(ingredients)
                if items:
                    base = items[:3] if len(items) >= 3 else items + ["veggies", "spices"][len(items):]
                    tag = "" if diet=="Any" else f" · {diet}"
                    st.success("🎉 Here are your personalized recipe suggestions!")

                    # Show three recipe suggestions and allow saving to DB
                    recipes = [
                        {"name": f"{base[0].title()} Quick Stir‑Fry",
                         "ingredients": f"{', '.join(base[:2])}, soy sauce, garlic, oil",
                         "instructions": "1. Heat oil in a pan\n2. Add garlic and sauté\n3. Add main ingredient and stir fry\n4. Add soy sauce and serve hot",
                         "time": f"{max(5, time_limit-10)} minutes",
                         "difficulty": difficulty
                        },
                        {"name": f"{base[0].title()} {base[1].title()} Wraps",
                         "ingredients": f"{', '.join(base[:2])}, tortillas, spices, yogurt",
                         "instructions": "1. Cook main ingredients with spices\n2. Warm tortillas\n3. Fill tortillas with mixture\n4. Add yogurt and roll up",
                         "time": f"{time_limit} minutes",
                         "difficulty": difficulty
                        },
                        {"name": f"Hearty {base[0].title()} Soup",
                         "ingredients": f"{', '.join(base)}, broth, herbs, potatoes",
                         "instructions": "1. Sauté main ingredients and other veggies\n2. Add broth and potatoes\n3. Simmer for 20 minutes\n4. Add herbs and serve",
                         "time": f"{time_limit+5} minutes",
                         "difficulty": difficulty
                        }
                    ]

                    for idx, r in enumerate(recipes, start=1):
                        with st.expander(f"{r['name']} ({r['time']} · {r['difficulty']})", expanded=idx==1):
                            st.write(f"**Ingredients:** {r['ingredients']}")
                            st.write("**Instructions:**")
                            st.write(r['instructions'].replace('\n', '  \n'))
                            if st.button("⭐ Save Recipe", key=f"save_recipe_{idx}"):
                                cur.execute(
                                    "INSERT INTO favorite_recipes (name, ingredients, instructions, time, difficulty, created_at) VALUES (?,?,?,?,?,?)",
                                    (r['name'], r['ingredients'], r['instructions'], r['time'], r['difficulty'], now_date_str())
                                )
                                conn.commit()
                                st.success("Recipe saved to favorites (DB)!")
                else:
                    st.warning("Please enter at least one valid ingredient.")
            else:
                st.warning("Please enter at least one ingredient.")

    with c2:
        st.info("💡 **Tips for reducing food waste:**")
        st.markdown("""
        - Store leftovers properly in airtight containers
        - Use older ingredients first when cooking
        - Freeze leftovers you won't use immediately
        - Understand date labels (best before vs use by)
        """)
        st.info("🔮 **Coming Soon:**")
        st.markdown("""
        - API integration with Spoonacular for real recipes (placeholder)
        - Nutritional information
        - Step-by-step cooking instructions
        """)

# ---------------------- PLANNER ----------------------
with tabs[2]:
    st.subheader("📅 Smart Food Planner")
    st.caption("Estimate ingredient quantities based on number of people and plan your meals.")

    # Meal planner UI (saves to DB)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    meals = ["Breakfast", "Lunch", "Dinner"]

    planner_cols = st.columns(7)
    for i, day in enumerate(days):
        with planner_cols[i]:
            st.markdown(f"**{day}**")
            for meal in meals:
                val = st.text_input(f"{meal}", key=f"planner_{day}_{meal}")
                # Save to DB on change
                cur.execute("REPLACE INTO meal_plan (id, day, meal, value) VALUES ((SELECT id FROM meal_plan WHERE day=? AND meal=?), ?, ?, ?)",
                            (day, meal, day, meal, val))
    conn.commit()

    # Quantity calculator
    st.markdown("### 📊 Quantity Calculator")
    dish = st.text_input("Dish name", value="Veg Fried Rice")
    people = st.number_input("Number of people", 1, 100, 4, step=1)

    baseline = {"rice (g)": 90, "mixed veggies (g)": 120, "oil (tbsp)": 0.75, "spices (tsp)": 1.0, "salt (tsp)": 0.5, "protein (g)": 100}

    if st.button("Calculate quantities", key="plan_btn", use_container_width=True):
        rows = []
        for k, v in baseline.items():
            qty = v * people
            rows.append({"Ingredient": k, "Per Person": v, "Total Quantity": round(qty, 2)})
        df = pd.DataFrame(rows)
        st.write(f"**Plan for:** {people} people · **Dish:** {dish}")
        st.dataframe(df, use_container_width=True)
        st.download_button(label="📥 Download Shopping List", data=df.to_csv(index=False), file_name="shopping_list.csv", mime="text/csv", use_container_width=True)

# ---------------------- SHARING HUB ----------------------
with tabs[3]:
    st.subheader("🤝 Share, Sell, or Donate Surplus")
    st.caption("Connect with your community to reduce food waste together")

    mode = st.radio("I want to:", ["Donate", "Sell"], horizontal=True)
    colA, colB = st.columns(2)
    with colA:
        item = st.text_input("Item name", value="Cooked rice (sealed)")
        qty = st.text_input("Quantity / units", value="2 boxes")
        expiry = st.date_input("Expiry date", min_value=datetime.today(), value=datetime.today() + timedelta(days=2))
        location = st.text_input("Location / Area", value="Campus Block A")
        contact = st.text_input("Contact (phone/email)", value="example@iitj.ac.in")
        # Optional: allow manual lat/lng
        lat = st.text_input("Latitude (optional)", value="")
        lng = st.text_input("Longitude (optional)", value="")
    with colB:
        dietary_info = st.multiselect("Dietary information", ["Vegetarian", "Vegan", "Gluten-free", "Dairy-free", "Contains nuts"]) 
        notes = st.text_area("Additional notes")
        price = None
        if mode == "Sell":
            price = st.number_input("Price (₹)", min_value=0, value=50, step=5)

    if st.button("Add listing", key="share_btn", use_container_width=True):
        if not all([item, qty, location, contact]):
            st.error("Please fill in all required fields")
        else:
            # Try geocoding if no lat/lng provided
            lat_val = None
            lng_val = None
            try:
                lat_val = float(lat) if lat.strip() else None
                lng_val = float(lng) if lng.strip() else None
            except Exception:
                lat_val = None
                lng_val = None

            if lat_val is None or lng_val is None:
                geocoded = geocode_address(location, MAPS_KEY)
                if geocoded:
                    lat_val, lng_val = geocoded

            cur.execute(
                "INSERT INTO shared_items (mode, item, qty, expiry, dietary, location, lat, lng, contact, price, notes, date_posted) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (mode, item, qty, expiry.strftime("%Y-%m-%d"), ", ".join(dietary_info) if dietary_info else "None", location, lat_val, lng_val, contact, (price if mode=="Sell" else "Free"), notes, now_date_str())
            )
            conn.commit()
            st.success("Listing added successfully! ✅")

    # Show listings from DB
    cur.execute("SELECT * FROM shared_items ORDER BY id DESC")
    rows = cur.fetchall()
    if rows:
        st.markdown("### 📋 Current Listings")
        for r in rows:
            with st.expander(f"{r['item']} - {r['location']} ({r['mode']}) - Posted {r['date_posted']}", expanded=False):
                col1, col2 = st.columns([2,1])
                with col1:
                    st.write(f"**Quantity:** {r['qty']}")
                    st.write(f"**Expiry:** {r['expiry']}")
                    st.write(f"**Dietary:** {r['dietary']}")
                    if r['notes']:
                        st.info(f"**Notes:** {r['notes']}")
                with col2:
                    st.write(f"**Location:** {r['location']}")
                    st.write(f"**Contact:** {r['contact']}")
                    st.write(f"**Price:** {r['price']}")
                    if r['lat'] and r['lng']:
                        if st.button(f"Show on map ({r['item']})", key=f"map_{r['id']}"):
                            show_map(r['lat'], r['lng'], label=r['item'], api_key=MAPS_KEY)
                    else:
                        st.write("No coordinates available. You can add latitude/longitude when creating a listing.")

                    if st.button("Remove Listing", key=f"remove_{r['id']}"):
                        cur.execute("DELETE FROM shared_items WHERE id=?", (r['id'],))
                        conn.commit()
                        st.experimental_rerun()
    else:
        st.info("No listings yet. Add one above to get started!")

# ---------------------- FAVORITES ----------------------
with tabs[4]:
    st.subheader("⭐ Favorite Recipes")
    cur.execute("SELECT * FROM favorite_recipes ORDER BY id DESC")
    favs = cur.fetchall()
    if favs:
        st.success("Your saved recipes:")
        for r in favs:
            with st.expander(f"{r['name']} - {r['time']} - {r['difficulty']}"):
                st.write(f"**Ingredients:** {r['ingredients']}")
                st.write("**Instructions:**")
                st.write(r['instructions'].replace('\n', '  \n'))
                if st.button("Remove from Favorites", key=f"remove_recipe_{r['id']}"):
                    cur.execute("DELETE FROM favorite_recipes WHERE id=?", (r['id'],))
                    conn.commit()
                    st.experimental_rerun()
    else:
        st.info("You haven't saved any recipes yet. Generate some recipes and click the ⭐ button to save them!")
        with st.expander("View sample recipes"):
            st.markdown("""
            **🍳 Veggie Stir-Fry**  
            **Ingredients:** mixed veggies, soy sauce, garlic, oil  
            **Instructions:**  
            1. Heat oil in a pan  
            2. Add garlic and sauté  
            3. Add veggies and stir fry  
            4. Add soy sauce and serve hot  
            
            **Time:** 20 minutes · **Difficulty:** Easy
            """)

# ---------------------- FOOTER ----------------------
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>FoodWise ♻️ · Reduce Food Waste · Help Your Community · Save Money</div>", unsafe_allow_html=True)
