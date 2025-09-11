# app.py
import streamlit as st
import sqlite3
import os
import json
import hashlib
import urllib.parse
from datetime import datetime, timedelta
import pandas as pd

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="FoodWise", page_icon="🍲", layout="wide")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "foodwise.db")

# ---------------------- DB HELPERS ----------------------
def get_conn():
    # allow multithreaded access across Streamlit reruns
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    # users
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        role TEXT,
        created_at TEXT
    )
    """)
    # listings
    c.execute("""
    CREATE TABLE IF NOT EXISTS listings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        seller_id INTEGER,
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
        timestamp TEXT
    )
    """)
    # claims
    c.execute("""
    CREATE TABLE IF NOT EXISTS claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        consumer_id INTEGER,
        consumer_name TEXT,
        listing_id INTEGER,
        claim_time TEXT
    )
    """)
    # favorites
    c.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        recipe_json TEXT,
        saved_at TEXT
    )
    """)
    # meal_plans
    c.execute("""
    CREATE TABLE IF NOT EXISTS meal_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plan_json TEXT,
        saved_at TEXT
    )
    """)
    conn.commit()
    conn.close()

# initialize DB at import/run
init_db()

# ---------------------- UTILITIES ----------------------
def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def pretty_ts(ts):
    try:
        return datetime.fromisoformat(ts).strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return ts

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_map_embed(location: str):
    if not location:
        return None
    if "google.com/maps" in location or "maps.app.goo.gl" in location:
        return location
    encoded = urllib.parse.quote_plus(location)
    return f"https://www.google.com/maps?q={encoded}&output=embed"

# ---------------------- SESSION STATE ----------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = None

# ---------------------- AUTH ----------------------
def signup(username: str, password: str, role: str):
    if not username or not password:
        st.error("Username and password required.")
        return False
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                  (username, hash_password(password), role, now_str()))
        conn.commit()
        conn.close()
        st.success("Account created. You can now log in.")
        return True
    except sqlite3.IntegrityError:
        conn.close()
        st.error("Username already exists. Pick another.")
        return False

def login(username: str, password: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, username, role FROM users WHERE username=? AND password_hash=?", (username, hash_password(password)))
    row = c.fetchone()
    conn.close()
    if row:
        st.session_state.logged_in = True
        st.session_state.user_id = row[0]
        st.session_state.username = row[1]
        st.session_state.role = row[2]
        return True
    else:
        return False

def logout():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = ""
    st.session_state.role = None
    st.experimental_rerun()

# ---------------------- UI COMPONENTS ----------------------
st.markdown("""
    <style>
    .stButton>button { background:#FF6F61; color:white; border-radius:8px; }
    .recipe-card { border:1px solid #E2E8F0; padding:10px; border-radius:8px; margin-bottom:8px; }
    </style>
""", unsafe_allow_html=True)

def login_ui():
    st.markdown("<h2 style='text-align:center;'>🍲 FoodWise</h2>", unsafe_allow_html=True)
    st.write("Reduce food waste · Share food · Help your community")
    with st.form("login_form", clear_on_submit=False):
        cols = st.columns([2,1])
        username = cols[0].text_input("Username", key="login_username")
        password = cols[1].text_input("Password", type="password", key="login_password")
        role_choice = st.radio("Role (for signup)", ["Seller", "Consumer"], index=1, horizontal=True)
        submitted = st.form_submit_button("Login / Signup")
    if submitted:
        if username and password:
            # try login
            success = login(username.strip(), password)
            if success:
                st.success(f"Welcome back, {st.session_state.username} ({st.session_state.role})")
                st.experimental_rerun()
            else:
                # prompt to signup
                if st.button("Create new account with entered credentials"):
                    signup(username.strip(), password, role_choice)
        else:
            st.error("Please enter username and password.")

# ---------------------- SELLER VIEW ----------------------
def seller_view():
    st.sidebar.success(f"👋 {st.session_state.username} (Seller)")
    if st.sidebar.button("Logout"):
        logout()

    tabs = st.tabs(["🏠 Home", "➕ Add Listing", "📋 My Listings & Claims"])
    # Home
    with tabs[0]:
        st.header("Seller Home")
        st.write("Share surplus food with your community.")
        st.info("Use clear pickup location (address or Google Maps link).")
    # Add Listing
    with tabs[1]:
        st.header("➕ Add Listing")
        colA, colB = st.columns(2)
        with colA:
            item = st.text_input("Item name", key="s_item")
            quantity = st.text_input("Quantity (e.g., 2 boxes)", key="s_qty")
            expiry = st.date_input("Expiry date", value=datetime.today() + timedelta(days=2), min_value=datetime.today(), key="s_expiry")
            mode = st.radio("Mode", ["Donate", "Sell"], horizontal=True, key="s_mode")
            price = None
            if mode == "Sell":
                price = st.number_input("Price (₹)", min_value=0.0, value=50.0, step=5.0, key="s_price")
        with colB:
            location = st.text_input("Pickup location (address or Google Maps link)", key="s_location")
            contact = st.text_input("Contact (phone/email)", key="s_contact")
            dietary = st.multiselect("Dietary info", ["Vegetarian", "Vegan", "Gluten-free", "Dairy-free", "Contains nuts"], key="s_dietary")
            notes = st.text_area("Notes / Packaging / Pickup instructions", key="s_notes", height=100)
        if st.button("Add listing", key=f"add_listing_{st.session_state.user_id}"):
            if not all([item.strip(), quantity.strip(), location.strip(), contact.strip()]):
                st.error("Please fill item, quantity, location and contact.")
            else:
                conn = get_conn()
                c = conn.cursor()
                c.execute("""INSERT INTO listings
                             (seller_id, seller_name, item, quantity, expiry, location, contact, dietary, notes, price, mode, timestamp)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                          (st.session_state.user_id, st.session_state.username, item.strip(), quantity.strip(), expiry.strftime("%Y-%m-%d"),
                           location.strip(), contact.strip(), ", ".join(dietary) if dietary else "None", notes.strip(),
                           float(price) if price is not None else None, mode, now_str()))
                conn.commit()
                conn.close()
                st.success("Listing added successfully!")
                st.experimental_rerun()
    # My Listings & Claims
    with tabs[2]:
        st.header("📋 My Listings & Claims")
        conn = get_conn()
        c = conn.cursor()
        try:
            c.execute("SELECT id, item, quantity, expiry, location, contact, dietary, notes, price, mode, timestamp FROM listings WHERE seller_id=? ORDER BY id DESC", (st.session_state.user_id,))
            rows = c.fetchall()
        except sqlite3.OperationalError:
            rows = []
        conn.close()
        if not rows:
            st.info("You have no listings yet.")
        else:
            for r in rows:
                lid, item, qty, expiry, loc, contact, dietary, notes, price, mode, ts = r
                st.markdown(f"### 🍛 {item} ({qty})")
                st.write(f"🕒 Posted: {pretty_ts(ts)} · Expires: {expiry} · Mode: {mode} · Price: {price if price is not None else 'Free'}")
                st.write(f"📍 {loc}")
                map_url = get_map_embed(loc)
                if map_url:
                    try:
                        st.components.v1.iframe(map_url, height=230)
                    except Exception:
                        st.write("Map preview unavailable.")
                st.write(f"📞 Contact: {contact}")
                st.write(f"🥗 Dietary: {dietary}")
                if notes:
                    st.info(f"Notes: {notes}")
                # show claims
                conn2 = get_conn()
                c2 = conn2.cursor()
                c2.execute("SELECT consumer_name, claim_time FROM claims WHERE listing_id = ? ORDER BY id DESC", (lid,))
                claims = c2.fetchall()
                conn2.close()
                if claims:
                    st.success("Claims:")
                    for consumer_name, claim_time in claims:
                        st.write(f"- 👤 {consumer_name} at {pretty_ts(claim_time)}")
                else:
                    st.info("No claims yet.")
                if st.button("Remove Listing", key=f"remove_{lid}"):
                    conn3 = get_conn()
                    c3 = conn3.cursor()
                    c3.execute("DELETE FROM listings WHERE id=?", (lid,))
                    c3.execute("DELETE FROM claims WHERE listing_id=?", (lid,))
                    conn3.commit()
                    conn3.close()
                    st.success("Listing removed.")
                    st.experimental_rerun()
                st.markdown("---")

# ---------------------- CONSUMER VIEW ----------------------
def consumer_view():
    st.sidebar.success(f"👋 {st.session_state.username} (Consumer)")
    if st.sidebar.button("Logout"):
        logout()

    tabs = st.tabs(["🏠 Home", "🥘 Recipes", "📅 Planner", "🤝 Sharing Hub", "⭐ Favorites"])
    # Home
    with tabs[0]:
        st.header("Welcome!")
        st.write("Find recipes from leftovers, plan meals, and claim shared food nearby.")
        quick_ing = st.text_input("Quick find recipes - ingredients (comma separated)", key="quick_ing")
        if st.button("Suggest recipes", key=f"quick_btn_{st.session_state.user_id}"):
            if quick_ing.strip():
                items = [x.strip() for x in quick_ing.split(",") if x.strip()]
                base = items[:3] if items else ["veggies"]
                with st.expander("Recipe ideas"):
                    st.write(f"1) {base[0].title()} Stir-fry with {', '.join(base[1:]) or 'spices'}")
                    st.write(f"2) {base[0].title()} Fried Rice")
                    st.write(f"3) Hearty {base[0].title()} Soup")
            else:
                st.warning("Enter at least one ingredient.")
    # Recipes
    with tabs[1]:
        st.header("Leftover Recipe Generator")
        c1, c2 = st.columns([2,1])
        with c1:
            ingredients = st.text_input("Ingredients (comma-separated)", key="rec_ing")
            diet = st.selectbox("Diet preference", ["Any", "Vegetarian", "Vegan", "Gluten-free", "Dairy-free"], key="rec_diet")
            time_limit = st.slider("Max cooking time (minutes)", 10, 120, 30, key="rec_time")
            difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], value="Easy", key="rec_diff")
            if st.button("Generate recipes", key=f"gen_rec_{st.session_state.user_id}"):
                if not ingredients.strip():
                    st.warning("Please enter ingredients.")
                else:
                    items = [x.strip() for x in ingredients.split(",") if x.strip()]
                    base = items[:3] if items else ["veggies"]
                    tag = "" if diet == "Any" else f" · {diet}"
                    st.success("Here are suggestions:")
                    recipes = []
                    r1 = {
                        "name": f"{base[0].title()} Quick Stir-Fry",
                        "ingredients": ", ".join(base[:2]) + ", soy sauce, garlic, oil",
                        "instructions": "1. Heat oil.\n2. Add garlic and sauté.\n3. Add main ingredients and stir fry.\n4. Add soy sauce and serve hot.",
                        "time": f"{max(5, time_limit-10)} minutes",
                        "difficulty": difficulty
                    }
                    r2 = {
                        "name": f"{base[0].title()} & {base[1].title() if len(base)>1 else 'Veg'} Wraps",
                        "ingredients": ", ".join(base[:2]) + ", tortillas, spices, yogurt",
                        "instructions": "1. Cook main ingredients with spices.\n2. Warm tortillas.\n3. Fill and roll.",
                        "time": f"{time_limit} minutes",
                        "difficulty": difficulty
                    }
                    r3 = {
                        "name": f"Hearty {base[0].title()} Soup",
                        "ingredients": ", ".join(base) + ", broth, herbs, potatoes",
                        "instructions": "1. Sauté ingredients.\n2. Add broth and potatoes.\n3. Simmer 20 mins.\n4. Add herbs and serve.",
                        "time": f"{time_limit+5} minutes",
                        "difficulty": difficulty
                    }
                    recipes = [r1, r2, r3]
                    for idx, r in enumerate(recipes, start=1):
                        with st.expander(f"{r['name']} · {r['time']} · {r['difficulty']}", expanded=(idx==1)):
                            st.write("**Ingredients:**", r["ingredients"])
                            st.write("**Instructions:**")
                            st.write(r["instructions"].replace("\n", "  \n"))
                            if st.button("⭐ Save Recipe", key=f"save_{st.session_state.user_id}_{idx}"):
                                conn = get_conn()
                                c = conn.cursor()
                                c.execute("INSERT INTO favorites (user_id, recipe_json, saved_at) VALUES (?, ?, ?)",
                                          (st.session_state.user_id, json.dumps(r), now_str()))
                                conn.commit()
                                conn.close()
                                st.success("Saved to Favorites!")
        with c2:
            st.info("Tips to reduce food waste:")
            st.markdown("""
            - Store leftovers in airtight containers
            - Use older ingredients first
            - Freeze leftovers you won't use
            - Learn date labels (best before vs use by)
            """)
    # Planner
    with tabs[2]:
        st.header("Smart Food Planner")
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        meals = ["Breakfast", "Lunch", "Dinner"]
        # load latest plan for user
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT plan_json FROM meal_plans WHERE user_id = ? ORDER BY id DESC LIMIT 1", (st.session_state.user_id,))
        row = c.fetchone()
        conn.close()
        if row:
            plan = json.loads(row[0])
        else:
            plan = {d: {m: "" for m in meals} for d in days}
        planner_cols = st.columns(7)
        for i, day in enumerate(days):
            with planner_cols[i]:
                st.markdown(f"**{day}**")
                for meal in meals:
                    key = f"planner_{st.session_state.user_id}_{day}_{meal}"
                    plan[day][meal] = st.text_input(meal, value=plan[day].get(meal, ""), key=key)
        if st.button("Save Weekly Plan", key=f"save_plan_{st.session_state.user_id}"):
            conn = get_conn()
            c = conn.cursor()
            c.execute("INSERT INTO meal_plans (user_id, plan_json, saved_at) VALUES (?, ?, ?)",
                      (st.session_state.user_id, json.dumps(plan), now_str()))
            conn.commit()
            conn.close()
            st.success("Plan saved.")
        st.markdown("### Quantity Calculator")
        dish = st.text_input("Dish name", value="Veg Fried Rice", key=f"dish_{st.session_state.user_id}")
        people = st.number_input("Number of people", 1, 100, 4, step=1, key=f"people_{st.session_state.user_id}")
        baseline = {"rice (g)": 90, "mixed veggies (g)": 120, "oil (tbsp)": 0.75, "spices (tsp)": 1.0, "salt (tsp)": 0.5, "protein (g)": 100}
        if st.button("Calculate quantities", key=f"calc_{st.session_state.user_id}"):
            rows = []
            for k, v in baseline.items():
                qty = v * people
                rows.append({"Ingredient": k, "Per Person": v, "Total Quantity": round(qty, 2)})
            df = pd.DataFrame(rows)
            st.write(f"**Plan for:** {people} people · **Dish:** {dish}")
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Shopping List", data=csv, file_name="shopping_list.csv", mime="text/csv")
    # Sharing Hub
    with tabs[3]:
        st.header("Sharing Hub")
        conn = get_conn()
        c = conn.cursor()
        try:
            c.execute("SELECT id, seller_name, item, quantity, expiry, location, contact, dietary, notes, price, mode, timestamp FROM listings ORDER BY id DESC")
            listings = c.fetchall()
        except sqlite3.OperationalError:
            listings = []
        conn.close()
        if not listings:
            st.info("No listings available.")
        else:
            for row in listings:
                lid, seller_name, item, qty, expiry, loc, contact, dietary, notes, price, mode, ts = row
                st.markdown(f"### 🍛 {item} ({qty})")
                st.write(f"👤 Seller: {seller_name} · 🕒 Posted: {pretty_ts(ts)} · Expires: {expiry}")
                st.write(f"📍 {loc}")
                map_url = get_map_embed(loc)
                if map_url:
                    try:
                        st.components.v1.iframe(map_url, height=220)
                    except Exception:
                        st.write("Map preview not available.")
                st.write(f"🥗 Dietary: {dietary} · 📞 Contact: {contact} · Price: {price if price is not None else 'Free'} · Mode: {mode}")
                if notes:
                    st.info(f"Notes: {notes}")
                if st.button("🤝 Claim Food", key=f"claim_{st.session_state.user_id}_{lid}"):
                    conn2 = get_conn()
                    c2 = conn2.cursor()
                    c2.execute("SELECT id FROM claims WHERE listing_id = ? AND consumer_id = ?", (lid, st.session_state.user_id))
                    exists = c2.fetchone()
                    if exists:
                        st.warning("You already claimed this listing.")
                    else:
                        c2.execute("INSERT INTO claims (consumer_id, consumer_name, listing_id, claim_time) VALUES (?, ?, ?, ?)",
                                   (st.session_state.user_id, st.session_state.username, lid, now_str()))
                        conn2.commit()
                        st.success(f"You claimed {item}. Contact {seller_name} at {contact} to coordinate pickup.")
                    conn2.close()
                st.markdown("---")
    # Favorites
    with tabs[4]:
        st.header("Favorite Recipes")
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id, recipe_json, saved_at FROM favorites WHERE user_id = ? ORDER BY id DESC", (st.session_state.user_id,))
        favs = c.fetchall()
        conn.close()
        if not favs:
            st.info("You haven't saved any recipes yet.")
        else:
            for fid, recipe_json, saved_at in favs:
                r = json.loads(recipe_json)
                with st.expander(f"{r['name']} · {r['time']} · {r['difficulty']}", expanded=True):
                    st.write("**Ingredients:**", r["ingredients"])
                    st.write("**Instructions:**")
                    st.write(r["instructions"].replace("\n", "  \n"))
                    st.write(f"Saved: {pretty_ts(saved_at)}")
                    if st.button("Remove from Favorites", key=f"remove_{fid}_{st.session_state.user_id}"):
                        conn2 = get_conn()
                        c2 = conn2.cursor()
                        c2.execute("DELETE FROM favorites WHERE id = ?", (fid,))
                        conn2.commit()
                        conn2.close()
                        st.success("Removed from favorites.")
                        st.experimental_rerun()

# ---------------------- MAIN ----------------------
def main():
    st.title("FoodWise ♻️")
    if not st.session_state.logged_in:
        login_ui()
        return
    # route by role
    if st.session_state.role == "Seller":
        seller_view()
    elif st.session_state.role == "Consumer":
        consumer_view()
    else:
        st.error("Unknown role. Please logout and login again.")
        if st.button("Logout"):
            logout()

# ---------------------- START ----------------------
if __name__ == "__main__":
    main()
