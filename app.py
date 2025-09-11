import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="FoodWise", page_icon="🍲", layout="wide")

# ---------------------- DATABASE ----------------------
def init_db():
    conn = sqlite3.connect("foodwise.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS favorites (id INTEGER PRIMARY KEY AUTOINCREMENT, recipe TEXT, added_at TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS listings (id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, quantity TEXT, location TEXT, listed_at TEXT)")
    conn.commit()
    conn.close()

init_db()

# ---------------------- HELPERS ----------------------
def save_favorite(recipe):
    conn = sqlite3.connect("foodwise.db")
    c = conn.cursor()
    c.execute("INSERT INTO favorites (recipe, added_at) VALUES (?, ?)", (recipe, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_favorites():
    conn = sqlite3.connect("foodwise.db")
    df = pd.read_sql_query("SELECT * FROM favorites", conn)
    conn.close()
    return df

def remove_favorite(recipe_id):
    conn = sqlite3.connect("foodwise.db")
    c = conn.cursor()
    c.execute("DELETE FROM favorites WHERE id=?", (recipe_id,))
    conn.commit()
    conn.close()

def add_listing(item, quantity, location):
    conn = sqlite3.connect("foodwise.db")
    c = conn.cursor()
    c.execute("INSERT INTO listings (item, quantity, location, listed_at) VALUES (?, ?, ?, ?)", (item, quantity, location, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_listings():
    conn = sqlite3.connect("foodwise.db")
    df = pd.read_sql_query("SELECT * FROM listings", conn)
    conn.close()
    return df

# ---------------------- MAIN APP ----------------------
st.title("🍲 FoodWise – Reduce Food Waste, Share More")

menu = ["Home", "Meal Planner", "Sharing Hub", "Favorites", "About & Deploy"]
choice = st.sidebar.radio("Navigate", menu)

# ---------------------- HOME ----------------------
if choice == "Home":
    st.subheader("AI Recipe Generator (Demo)")
    with st.form(key="recipe_form"):
        ingredients = st.text_area("Enter ingredients (comma separated)")
        generate = st.form_submit_button("Generate Recipes")
    if generate:
        recipes = [f"Recipe with {i.strip()}" for i in ingredients.split(",") if i.strip()]
        if recipes:
            st.write("### Suggested Recipes")
            for i, r in enumerate(recipes):
                st.write(f"- {r}")
                if st.button("Save to Favorites", key=f"fav_{i}"):
                    save_favorite(r)
                    st.success(f"Saved {r} to favorites!")
        else:
            st.warning("No valid ingredients entered.")

# ---------------------- MEAL PLANNER ----------------------
elif choice == "Meal Planner":
    st.subheader("Weekly Meal Planner")
    if 'planner' not in st.session_state:
        st.session_state.planner = {day: [] for day in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]}

    day = st.selectbox("Select a day", list(st.session_state.planner.keys()))
    recipe = st.text_input("Add recipe to this day")
    if st.button("Add to Plan"):
        st.session_state.planner[day].append(recipe)
        st.success(f"Added {recipe} to {day}")

    st.write("### Weekly Plan")
    for d, meals in st.session_state.planner.items():
        st.write(f"**{d}:** {', '.join(meals) if meals else 'No meals yet'}")

# ---------------------- SHARING HUB ----------------------
elif choice == "Sharing Hub":
    st.subheader("Share Extra Food Items")
    with st.form(key="share_form"):
        item = st.text_input("Food Item")
        qty = st.text_input("Quantity")
        loc = st.text_input("Pickup Location")
        submit = st.form_submit_button("List Item")
    if submit:
        add_listing(item, qty, loc)
        st.success("Item listed successfully!")

    st.write("### Available Listings")
    listings = get_listings()
    st.dataframe(listings)

# ---------------------- FAVORITES ----------------------
elif choice == "Favorites":
    st.subheader("Saved Favorite Recipes")
    favs = get_favorites()
    if not favs.empty:
        for _, row in favs.iterrows():
            st.write(f"- {row['recipe']} (added {row['added_at']})")
            if st.button("Remove", key=f"rem_{row['id']}"):
                remove_favorite(row['id'])
                st.experimental_rerun()
    else:
        st.info("No favorites saved yet.")

# ---------------------- ABOUT ----------------------
elif choice == "About & Deploy":
    st.subheader("About FoodWise")
    st.markdown("""
    FoodWise helps reduce food waste through recipe suggestions, meal planning, and community sharing.

    **Deploy Guide:**
    1. Push this file & `requirements.txt` to GitHub.
    2. On [Streamlit Cloud](https://share.streamlit.io), link repo.
    3. Set main file = this script.
    4. Done 🚀
    """)
