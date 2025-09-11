import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import math
import os

# ---------------------- App Constants ----------------------
DB_PATH = "foodwise.db"
PAGE_TITLE = "FoodWise — Reduce Food Waste"
PAGE_ICON = "🍲"

# ---------------------- Helpers: DB ----------------------
def get_conn(path=DB_PATH):
    conn = sqlite3.connect(path, check_same_thread=False)
    return conn

def init_db(conn):
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        ingredients TEXT,
        instructions TEXT,
        time TEXT,
        difficulty TEXT,
        date_added TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS listings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mode TEXT,
        item TEXT,
        qty TEXT,
        expiry TEXT,
        dietary TEXT,
        location TEXT,
        contact TEXT,
        price TEXT,
        notes TEXT,
        date_posted TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS meal_plan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day TEXT,
        meal TEXT,
        value TEXT
    )
    """)

    conn.commit()

# ---------------------- Recipe Generation (simple local logic) ----------------------
def generate_recipes(ingredients, diet="Any", time_limit=30, difficulty="Easy"):
    """Return a list of recipe dicts based on provided ingredients.
    This is simple placeholder logic for hackathon; you can later replace
    with API calls to Spoonacular/Edamam.
    """
    base = [i.strip().lower() for i in ingredients if i.strip()]
    if not base:
        return []

    # Ensure at least two base ingredients for better suggestions
    if len(base) == 1:
        base.append("vegetables")
    if len(base) == 2:
        base.append("rice")

    recipes = []
    # Recipe 1 - Stir fry
    recipes.append({
        "name": f"{base[0].title()} Stir‑Fry",
        "ingredients": ", ".join(base[:2]) + ", oil, garlic, soy sauce",
        "instructions": "1. Heat oil in a pan\n2. Add garlic and sauté\n3. Add main ingredients and stir-fry\n4. Add soy sauce and serve",
        "time": f"{max(10, time_limit-10)} mins",
        "difficulty": difficulty
    })

    # Recipe 2 - Wraps
    recipes.append({
        "name": f"{base[0].title()} & {base[1].title()} Wraps",
        "ingredients": ", ".join(base[:2]) + ", tortillas, spices, yogurt",
        "instructions": "1. Cook filling with spices\n2. Warm tortillas\n3. Fill & roll",
        "time": f"{time_limit} mins",
        "difficulty": difficulty
    })

    # Recipe 3 - Hearty soup
    recipes.append({
        "name": f"Hearty {base[0].title()} Soup",
        "ingredients": ", ".join(base) + ", broth, herbs, potatoes",
        "instructions": "1. Sauté ingredients\n2. Add broth and simmer\n3. Adjust seasoning and serve",
        "time": f"{time_limit+10} mins",
        "difficulty": difficulty
    })

    # Filter by diet (very basic)
    if diet != "Any":
        if diet == "Vegetarian":
            recipes = [r for r in recipes if "chicken" not in r["ingredients"].lower() and "meat" not in r["ingredients"].lower()]
        if diet == "Vegan":
            recipes = [r for r in recipes if all(x not in r["ingredients"].lower() for x in ["yogurt", "egg", "cheese"])]

    return recipes

# ---------------------- Persistence Helpers ----------------------
def save_favorite(conn, recipe):
    c = conn.cursor()
    c.execute(
        "INSERT INTO favorites (name, ingredients, instructions, time, difficulty, date_added) VALUES (?, ?, ?, ?, ?, ?)",
        (recipe["name"], recipe["ingredients"], recipe["instructions"], recipe["time"], recipe["difficulty"], datetime.today().strftime("%Y-%m-%d"))
    )
    conn.commit()

def list_favorites(conn):
    df = pd.read_sql_query("SELECT * FROM favorites ORDER BY date_added DESC", conn)
    return df

def remove_favorite(conn, fav_id):
    c = conn.cursor()
    c.execute("DELETE FROM favorites WHERE id = ?", (fav_id,))
    conn.commit()

def add_listing(conn, listing):
    c = conn.cursor()
    c.execute(
        "INSERT INTO listings (mode, item, qty, expiry, dietary, location, contact, price, notes, date_posted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (listing["mode"], listing["item"], listing["qty"], listing["expiry"], listing["dietary"], listing["location"], listing["contact"], listing["price"], listing["notes"], listing["date_posted"])
    )
    conn.commit()

def list_listings(conn):
    df = pd.read_sql_query("SELECT * FROM listings ORDER BY date_posted DESC", conn)
    return df

def remove_listing(conn, listing_id):
    c = conn.cursor()
    c.execute("DELETE FROM listings WHERE id = ?", (listing_id,))
    conn.commit()

# ---------------------- UI Helpers ----------------------

def write_css():
    st.markdown(
        """
        <style>
        .app-title { text-align:center }
        .pill { display:inline-block; padding:6px 10px; border-radius:999px; background:#F1F5F9; margin-right:8px; margin-bottom:8px; font-size:0.85rem;}
        .recipe-card { border:1px solid #E6EEF3; border-radius:12px; padding:12px; margin-bottom:12px; }
        </style>
        """,
        unsafe_allow_html=True
    )

# ---------------------- App Layout ----------------------
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")
write_css()

# Initialize DB
conn = get_conn()
init_db(conn)

st.markdown("# 🍲 FoodWise")
st.markdown("_Reduce food waste · Save money · Help your community_")
st.markdown("---")

# Top-level tabs
tabs = st.tabs(["Home", "Recipes", "Planner", "Sharing Hub", "Favorites", "About / Deploy"]) 

# ---------------------- HOME ----------------------
with tabs[0]:
    c1, c2 = st.columns([2,1])
    with c1:
        st.header("Welcome to FoodWise")
        st.write("FoodWise helps you transform leftovers into tasty meals, plan portions, and share surplus locally.")
        st.write("Use the tabs to generate recipes, plan your week, or post donations/sales.")

        st.subheader("Quick recipe idea")
        with st.form("quick_recipe", clear_on_submit=True):
            quick_ing = st.text_input("Enter up to 5 ingredients (comma-separated)")
            submitted = st.form_submit_button("Suggest Recipes")
            if submitted:
                ingredients = [x.strip() for x in quick_ing.split(",") if x.strip()]
                recipes = generate_recipes(ingredients)
                if recipes:
                    for r in recipes:
                        st.markdown(f"### {r['name']}")
                        st.markdown(f"**Ingredients:** {r['ingredients']}")
                        st.markdown(f"**Time:** {r['time']}  ·  **Difficulty:** {r['difficulty']}")
                        st.markdown(f"{r['instructions'].replace('\n', '  \n')}")
                else:
                    st.warning("Please enter at least one ingredient.")

    with c2:
        st.subheader("Why FoodWise?")
        st.write("- A large share of food produced goes uneaten each year.\n- Save money by planning and using leftovers.\n- Help others by sharing surplus food.")
        st.subheader("Quick Links")
        st.write("Use the Planner to calculate quantities and the Sharing Hub to post listings.")

# ---------------------- RECIPES ----------------------
with tabs[1]:
    st.header("Leftover Recipe Generator")
    left_col, right_col = st.columns([2,1])

    with left_col:
        with st.form("recipe_form"):
            ingredients_text = st.text_input("Ingredients (comma-separated)")
            diet = st.selectbox("Diet preference", ["Any", "Vegetarian", "Vegan", "Gluten-free", "Dairy-free"])
            time_limit = st.slider("Max cooking time (minutes)", 10, 120, 30)
            difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], value="Easy")
            submit = st.form_submit_button("Generate Recipes")

            if submit:
                ingredients = [x.strip() for x in ingredients_text.split(",") if x.strip()]
                if not ingredients:
                    st.warning("Enter at least one ingredient to generate recipes.")
                else:
                    recipes = generate_recipes(ingredients, diet=diet, time_limit=time_limit, difficulty=difficulty)
                    if not recipes:
                        st.info("No recipes matched your preferences. Try changing diet/time/difficulty.")
                    else:
                        for i, r in enumerate(recipes):
                            with st.expander(f"{r['name']}  ·  {r['time']}  ·  {r['difficulty']}", expanded=(i==0)):
                                st.markdown(f"**Ingredients:** {r['ingredients']}")
                                st.markdown(f"**Instructions:**\n{r['instructions'].replace('\n', '  \n')}")
                                col_a, col_b = st.columns([3,1])
                                with col_a:
                                    st.write("")
                                with col_b:
                                    if st.button("Save to Favorites", key=f"fav_{i}_{r['name']}"):
                                        save_favorite(conn, r)
                                        st.success("Saved to favorites ✅")

    with right_col:
        st.info("Tips for reducing food waste:")
        st.write("- Store leftovers in airtight containers; label with date.\n- Use older ingredients first ('first in, first out').\n- Freeze leftovers you won't use soon.")
        st.write("\nComing soon: API-backed recipes, nutrition facts, step-by-step cooking mode.")

# ---------------------- PLANNER ----------------------
with tabs[2]:
    st.header("Smart Food Planner")
    st.caption("Plan weekly meals and calculate ingredient quantities for a group.")

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    meals = ["Breakfast", "Lunch", "Dinner"]

    # initialize session_state meal_plan
    if 'meal_plan' not in st.session_state:
        st.session_state.meal_plan = {day: {meal: "" for meal in meals} for day in days}

    with st.expander("Weekly planner (click to expand)", expanded=True):
        cols = st.columns(7)
        for i, day in enumerate(days):
            with cols[i]:
                st.markdown(f"**{day}**")
                for meal in meals:
                    st.session_state.meal_plan[day][meal] = st.text_input(f"{day}-{meal}", value=st.session_state.meal_plan[day][meal], key=f"{day}_{meal}")

    st.markdown("---")
    st.subheader("Quantity Calculator")
    with st.form("quantity_form"):
        dish = st.text_input("Dish name", value="Veg Fried Rice")
        people = st.number_input("Number of people", 1, 100, 4, step=1)
        calculate = st.form_submit_button("Calculate quantities")

        if calculate:
            # baseline (demo) values
            baseline = {"rice (g)": 90, "mixed veggies (g)": 120, "oil (tbsp)": 0.75, "spices (tsp)": 1.0, "salt (tsp)": 0.5, "protein (g)": 100}
            rows = []
            for k, v in baseline.items():
                qty = v * people
                rows.append({"Ingredient": k, "Per Person": v, "Total Quantity": round(qty, 2)})

            df = pd.DataFrame(rows)
            st.write(f"**Plan for:** {people} people · **Dish:** {dish}")
            st.dataframe(df, use_container_width=True)
            st.download_button(label="Download Shopping List", data=df.to_csv(index=False), file_name="shopping_list.csv", mime="text/csv")

# ---------------------- SHARING HUB ----------------------
with tabs[3]:
    st.header("Share, Sell, or Donate Surplus")
    st.caption("Post a listing to give away or sell food locally. Listings are saved to a local SQLite DB.")

    mode = st.radio("I want to:", ["Donate", "Sell"], horizontal=True)

    with st.form("listing_form"):
        item = st.text_input("Item name", value="Cooked rice (sealed)")
        qty = st.text_input("Quantity / units", value="2 boxes")
        expiry = st.date_input("Expiry date", min_value=datetime.today(), value=datetime.today() + timedelta(days=2))
        location = st.text_input("Location / Area", value="Campus Block A")
        contact = st.text_input("Contact (phone/email)")
        dietary_info = st.multiselect("Dietary information", ["Vegetarian", "Vegan", "Gluten-free", "Dairy-free", "Contains nuts"])
        notes = st.text_area("Additional notes (optional)")
        price = None
        if mode == "Sell":
            price = st.number_input("Price (₹)", min_value=0, value=50, step=5)

        listing_submitted = st.form_submit_button("Add listing")
        if listing_submitted:
            if not all([item.strip(), qty.strip(), location.strip(), contact.strip()]):
                st.error("Please fill in all required fields: item, qty, location, contact.")
            else:
                listing = {
                    "mode": mode,
                    "item": item.strip(),
                    "qty": qty.strip(),
                    "expiry": expiry.strftime("%Y-%m-%d"),
                    "dietary": ", ".join(dietary_info) if dietary_info else "None",
                    "location": location.strip(),
                    "contact": contact.strip(),
                    "price": f"₹{price}" if price is not None else "Free",
                    "notes": notes.strip(),
                    "date_posted": datetime.today().strftime("%Y-%m-%d")
                }
                add_listing(conn, listing)
                st.success("Listing added successfully! ✅")

    st.markdown("---")
    st.subheader("Current listings")
    listings_df = list_listings(conn)
    if listings_df.empty:
        st.info("No listings yet. Add one above to get started.")
    else:
        for _, row in listings_df.iterrows():
            with st.expander(f"{row['item']} — {row['location']} ({row['mode']})", expanded=False):
                st.write(f"**Quantity:** {row['qty']}")
                st.write(f"**Expiry:** {row['expiry']}")
                st.write(f"**Dietary:** {row['dietary']}")
                st.write(f"**Location:** {row['location']}")
                st.write(f"**Contact:** {row['contact']}")
                st.write(f"**Price:** {row['price']}")
                if row['notes']:
                    st.info(f"Notes: {row['notes']}")
                if st.button("Remove Listing", key=f"remove_listing_{row['id']}"):
                    remove_listing(conn, row['id'])
                    st.experimental_rerun()

# ---------------------- FAVORITES ----------------------
with tabs[4]:
    st.header("Favorite Recipes")
    fav_df = list_favorites(conn)
    if fav_df.empty:
        st.info("You don't have any favorites yet. Save recipes from the Recipes tab.")
    else:
        for _, r in fav_df.iterrows():
            with st.expander(f"{r['name']} · {r['time']} · {r['difficulty']}"):
                st.markdown(f"**Ingredients:** {r['ingredients']}")
                st.markdown(f"**Instructions:**\n{r['instructions'].replace('\n','  \n')}")
                if st.button("Remove from favorites", key=f"remove_fav_{r['id']}"):
                    remove_favorite(conn, r['id'])
                    st.experimental_rerun()

# ---------------------- ABOUT / DEPLOY ----------------------
with tabs[5]:
    st.header("About & Deploy")
    st.markdown("FoodWise — a hackathon-ready MVP to reduce food waste. This version uses a local SQLite DB for persistence.")
    st.markdown("**Next steps / improvements:**")
    st.markdown("- Integrate Spoonacular / Edamam for real recipes and nutrition.\n- Add user authentication and profile pages.\n- Add map-based search for listings and filters.\n- Deploy on Streamlit Cloud / Heroku / Railway and connect to a hosted DB (Postgres).")

    st.markdown("---")
    st.subheader("Deploy notes for GitHub + Streamlit Cloud")
    st.write("1. Create a new GitHub repo and add this file `FoodWise_streamlit.py`.\n2. Add a `requirements.txt` with `streamlit,pandas`.\n3. On Streamlit Cloud, link your GitHub repo and set the main file to `FoodWise_streamlit.py`.\n4. For production, move DB to managed Postgres and update DB connection string.")

# Close DB connection on script end
# (sqlite connection will close when program exits in Streamlit cloud)

