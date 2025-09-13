# app.py - FoodWise 
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from streamlit.components.v1 import html

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="FoodWise", page_icon="🍲", layout="wide")
DB_PATH = "orders.db"

# ---------------------- DATABASE HELPERS ----------------------
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    # Create table with columns for NGO info as well
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        restaurant TEXT,
        username TEXT,
        item TEXT,
        qty TEXT,
        pickup TEXT,
        location TEXT,
        contact TEXT,
        notes TEXT,
        price TEXT,
        status TEXT,
        posted_on TEXT,
        confirmed_by TEXT,
        confirmed_on TEXT,
        ngo_contact TEXT,
        ngo_location TEXT
    )
    """)
    conn.commit()

    # Ensure extra columns exist (migration-friendly)
    c.execute("PRAGMA table_info(orders)")
    cols = [r[1] for r in c.fetchall()]
    needed = {
        "confirmed_by": "TEXT",
        "confirmed_on": "TEXT",
        "ngo_contact": "TEXT",
        "ngo_location": "TEXT"
    }
    for col, coltype in needed.items():
        if col not in cols:
            # add missing column
            c.execute(f"ALTER TABLE orders ADD COLUMN {col} {coltype}")
    conn.commit()
    conn.close()

def insert_order(order):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO orders (restaurant, username, item, qty, pickup, location, contact, notes, price, status, posted_on)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order["restaurant"], order["username"], order["item"], order["qty"], order["pickup"],
        order["location"], order["contact"], order["notes"], order["price"], order["status"], order["posted_on"]
    ))
    conn.commit()
    conn.close()

def fetch_orders(filter_clause=None, params=()):
    conn = get_conn()
    c = conn.cursor()
    q = "SELECT * FROM orders"
    if filter_clause:
        q += f" WHERE {filter_clause}"
    q += " ORDER BY id DESC"
    c.execute(q, params)
    rows = c.fetchall()
    conn.close()
    return rows

def update_order_status(order_id, new_status, confirmed_by=None, ngo_contact=None, ngo_location=None):
    conn = get_conn()
    c = conn.cursor()
    if confirmed_by or ngo_contact or ngo_location:
        c.execute("""
            UPDATE orders
            SET status=?, confirmed_by=?, confirmed_on=?, ngo_contact=?, ngo_location=?
            WHERE id=?
        """, (new_status, confirmed_by or "", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ngo_contact or "", ngo_location or "", order_id))
    else:
        c.execute("UPDATE orders SET status=? WHERE id=?", (new_status, order_id))
    conn.commit()
    conn.close()

def remove_order(order_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM orders WHERE id=?", (order_id,))
    conn.commit()
    conn.close()

# initialize DB
init_db()

# ---------------------- SESSION / IN-MEMORY USERS ----------------------
if 'users' not in st.session_state:
    st.session_state.users = {
        # demo users: username -> {password, role, display, contact, location}
        "restro1": {"password": "restro123", "role": "restaurant", "display": "Restro One", "contact": "9876500000", "location": "Campus Block A"},
        "restro2": {"password": "restro234", "role": "restaurant", "display": "Tasty Corner", "contact": "9876501111", "location": "Block B"},
        "ngo1": {"password": "ngo123", "role": "ngo", "display": "Helping NGO", "contact": "9998800000", "location": "NGO Center"},
        "ngo2": {"password": "ngo234", "role": "ngo", "display": "Care Foundation", "contact": "9998801111", "location": "Welfare Hub"},
    }

if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'current_role' not in st.session_state:
    st.session_state.current_role = None
if 'msg_flag' not in st.session_state:
    st.session_state.msg_flag = None
if 'favorite_recipes' not in st.session_state:
    st.session_state.favorite_recipes = []
if 'shared_items' not in st.session_state:
    st.session_state.shared_items = []
if 'waste_log' not in st.session_state:
    st.session_state.waste_log = []
if 'meal_plan' not in st.session_state:
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    meals = ["Breakfast", "Lunch", "Dinner"]
    st.session_state.meal_plan = {day: {meal: "" for meal in meals} for day in days}

# ---------------------- STYLES & HEADER ----------------------
st.markdown("""
    <style>
    .foodwise-hero h1 { color:#FF6F61; font-size:2.4rem; margin-bottom:0; }
    .foodwise-hero h3 { color:#22C55E; font-weight:600; margin-top:0.15rem; }
    .stButton>button { background:#FF6F61; color:white; border-radius:10px; padding:0.45rem 0.8rem; border:0; }
    .recipe-card { border:1px solid #E2E8F0; border-radius:10px; padding:0.8rem; margin-bottom:0.9rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="foodwise-hero" style="text-align:center; padding:8px 0 12px 0;">'
            '<h1>🍲 FoodWise</h1>'
            '<h3>Leftovers → Recipes · Planner · Sharing · Restaurant ↔ NGO</h3>'
            '</div>', unsafe_allow_html=True)

# ---------------------- NAV TABS ----------------------
tabs = st.tabs(["🏠 Home", "🥘 Recipes", "📅 Planner", "🤝 Sharing", "⭐ Favorites", "📉 Waste", "🔐 Login", "🏬 Orders"])

# ---------------------- HOME ----------------------
with tabs[0]:
    st.markdown("### Welcome back to FoodWise")
    st.write("Features: Leftover recipe generator, weekly planner, favorites, waste tracker, and a persistent Restaurant↔NGO orders system.")
    st.write("To share orders across devices: host this app on one server (Streamlit Cloud / Render / Railway) so both laptops use the same orders.db on the server.")

# ---------------------- RECIPES ----------------------
with tabs[1]:
    st.header("Leftover Recipe Generator")
    ingredients = st.text_input("Ingredients (comma-separated)", key="rec_ing", placeholder="e.g., rice, carrot, egg")
    diet = st.selectbox("Diet preference", ["Any", "Vegetarian", "Vegan", "Gluten-free", "Dairy-free"])
    max_time = st.slider("Max cooking time (min)", 10, 120, 30)
    difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], value="Easy")
    if st.button("Generate Recipes", key="gen_rec"):
        if not ingredients.strip():
            st.warning("Please enter at least one ingredient.")
        else:
            items = [it.strip() for it in ingredients.split(",") if it.strip()]
            base = items[:3] if len(items) >= 3 else items + ["veggies", "spices"][len(items):]
            tag = "" if diet == "Any" else f" · {diet}"
            st.success("Suggested recipes:")
            with st.expander(f"{base[0].title()} Stir-Fry", expanded=True):
                st.markdown(f"Ingredients: {', '.join(base[:2])}, soy sauce, garlic, oil  \n*Time:* {max(5, max_time-10)} min · {difficulty}{tag}")
                if st.button("⭐ Save Recipe", key="save_recipe_1"):
                    st.session_state.favorite_recipes.append({
                        "name": f"{base[0].title()} Stir-Fry",
                        "ingredients": f"{', '.join(base[:2])}, soy sauce, garlic, oil",
                        "instructions": "1. Heat oil\n2. Sauté garlic\n3. Add main ingredient and stir-fry\n4. Serve",
                        "time": f"{max(5, max_time-10)} mins",
                        "difficulty": difficulty
                    })
                    st.success("Saved to favorites.")
            with st.expander(f"{base[0].title()} {base[1].title()} Wraps"):
                st.markdown(f"Ingredients: {', '.join(base[:2])}, tortillas, yogurt  \n*Time:* {max_time} min · {difficulty}{tag}")
                if st.button("⭐ Save Recipe", key="save_recipe_2"):
                    st.session_state.favorite_recipes.append({
                        "name": f"{base[0].title()} {base[1].title()} Wraps",
                        "ingredients": f"{', '.join(base[:2])}, tortillas, yogurt",
                        "instructions": "1. Cook & spice\n2. Fill tortillas\n3. Roll & serve",
                        "time": f"{max_time} mins",
                        "difficulty": difficulty
                    })
                    st.success("Saved to favorites.")
            with st.expander(f"Hearty {base[0].title()} Soup"):
                st.markdown(f"Ingredients: {', '.join(base)}, broth  \n*Time:* {max_time+10} min · {difficulty}{tag}")
                if st.button("⭐ Save Recipe", key="save_recipe_3"):
                    st.session_state.favorite_recipes.append({
                        "name": f"Hearty {base[0].title()} Soup",
                        "ingredients": f"{', '.join(base)}, broth",
                        "instructions": "1. Sauté\n2. Add broth\n3. Simmer\n4. Serve",
                        "time": f"{max_time+10} mins",
                        "difficulty": difficulty
                    })
                    st.success("Saved to favorites.")

# ---------------------- PLANNER ----------------------
with tabs[2]:
    st.header("Weekly Meal Planner")
    days = list(st.session_state.meal_plan.keys())
    cols = st.columns(7)
    for i, day in enumerate(days):
        with cols[i]:
            st.markdown(f"{day}")
            for meal in ["Breakfast", "Lunch", "Dinner"]:
                st.session_state.meal_plan[day][meal] = st.text_input(f"{meal}", value=st.session_state.meal_plan[day][meal], key=f"{day}_{meal}")
    st.markdown("### Quantity Calculator")
    dish = st.text_input("Dish name", value="Veg Fried Rice")
    people = st.number_input("Number of people", 1, 100, 4)
    baseline = {"rice (g)": 90, "mixed veggies (g)": 120, "oil (tbsp)": 0.75, "spices (tsp)": 1.0}
    if st.button("Calculate quantities", key="calc_qty"):
        rows = []
        for k, v in baseline.items():
            rows.append({"Ingredient": k, "Per Person": v, "Total Quantity": round(v * people, 2)})
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        st.download_button("Download shopping list (CSV)", df.to_csv(index=False), file_name="shopping_list.csv", mime="text/csv")

# ---------------------- SHARING (basic) ----------------------
with tabs[3]:
    st.header("Share / Sell / Donate (Local)")
    mode = st.radio("I want to:", ["Donate", "Sell"], horizontal=True, key="share_mode")
    left, right = st.columns(2)
    with left:
        s_item = st.text_input("Item name", value="Cooked rice (sealed)", key="s_item")
        s_qty = st.text_input("Quantity / units", value="2 boxes", key="s_qty")
        s_expiry = st.date_input("Expiry date", min_value=datetime.today(), value=datetime.today() + timedelta(days=2), key="s_expiry")
        s_location = st.text_input("Location / Area", value="Campus Block A", key="s_location")
        s_contact = st.text_input("Contact (phone/email)", value="example@iitj.ac.in", key="s_contact")
    with right:
        s_diet = st.multiselect("Dietary information", ["Vegetarian", "Vegan", "Gluten-free", "Dairy-free", "Contains nuts"], key="s_diet")
        s_notes = st.text_area("Additional notes", key="s_notes")
        s_price = 0
        if mode == "Sell":
            s_price = st.number_input("Price (₹)", min_value=0, value=50, key="s_price")
    if st.button("Add listing", key="add_listing"):
        if not all([s_item.strip(), s_qty.strip(), s_location.strip(), s_contact.strip()]):
            st.error("Please fill all required fields (item, qty, location, contact).")
        else:
            st.session_state.shared_items.append({
                "mode": mode,
                "item": s_item.strip(),
                "qty": s_qty.strip(),
                "expiry": s_expiry.strftime("%Y-%m-%d"),
                "dietary": ", ".join(s_diet) if s_diet else "None",
                "location": s_location.strip(),
                "contact": s_contact.strip(),
                "price": s_price if mode == "Sell" else "Free",
                "notes": s_notes.strip(),
                "date_posted": datetime.today().strftime("%Y-%m-%d")
            })
            st.success("Sharing listing added (local session).")

    if st.session_state.shared_items:
        st.markdown("### Local shared items")
        for i, it in enumerate(st.session_state.shared_items):
            with st.expander(f"{it['item']} — {it['location']} ({it['mode']})", expanded=(i==0)):
                st.write(f"Qty: {it['qty']}")
                st.write(f"Expiry: {it['expiry']}")
                st.write(f"Dietary: {it['dietary']}")
                st.write(f"Contact: {it['contact']}")
                if it['notes']:
                    st.info(it['notes'])
                if st.button("Remove", key=f"remove_shared_{i}"):
                    st.session_state.shared_items.pop(i)
                    st.experimental_rerun()
    else:
        st.info("No local shared items yet. Use the form above to add.")

# ---------------------- FAVORITES ----------------------
with tabs[4]:
    st.header("Favorite Recipes")
    if not st.session_state.favorite_recipes:
        st.info("No favorites yet. Save recipes from the generator.")
    else:
        for i, r in enumerate(st.session_state.favorite_recipes):
            with st.expander(f"{r['name']} — {r.get('time','')}"):
                st.write("Ingredients:", r['ingredients'])
                st.write("Instructions:")
                st.write(r['instructions'])
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Remove", key=f"rmfav_{i}"):
                        st.session_state.favorite_recipes.pop(i)
                        st.experimental_rerun()
                with c2:
                    st.download_button("Export recipe (txt)", data=f"Name: {r['name']}\nIngredients: {r['ingredients']}\n\n{r['instructions']}", file_name=f"{r['name']}.txt")

# ---------------------- WASTE TRACKER ----------------------
with tabs[5]:
    st.header("Food Waste Tracker")
    w_col1, w_col2 = st.columns(2)
    with w_col1:
        w_item = st.text_input("Item name", key="w_item", value="Cooked rice")
        w_qty = st.number_input("Quantity", min_value=0.0, value=1.0, step=0.1, key="w_qty")
        w_units = st.selectbox("Units", ["kg", "g", "boxes", "units"], key="w_units")
    with w_col2:
        w_reason = st.selectbox("Reason", ["Overcooked", "Forgotten", "Spoiled", "Leftover not used", "Other"], key="w_reason")
        w_date = st.date_input("Date", value=datetime.today(), key="w_date")
        if st.button("Log waste", key="log_waste"):
            if not w_item.strip() or w_qty <= 0:
                st.error("Enter valid item and quantity.")
            else:
                st.session_state.waste_log.append({
                    "item": w_item.strip(),
                    "qty": w_qty,
                    "units": w_units,
                    "reason": w_reason,
                    "date": w_date.strftime("%Y-%m-%d")
                })
                st.success("Logged.")
    if st.session_state.waste_log:
        dfw = pd.DataFrame(st.session_state.waste_log)
        st.markdown("### Recent waste logs")
        st.dataframe(dfw.sort_values("date", ascending=False), use_container_width=True)
        st.download_button("Export waste log CSV", dfw.to_csv(index=False), file_name="waste_log.csv", mime="text/csv")
    else:
        st.info("No waste logged yet.")

# ---------------------- LOGIN ----------------------
with tabs[6]:
    st.header("Login / Register (demo)")
    st.write("Demo accounts: restaurant -> restro1 / restro123 ; NGO -> ngo1 / ngo123")
    col1, col2 = st.columns(2)
    with col1:
        role_choice = st.selectbox("Role", ["restaurant", "ngo"], key="login_role")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", key="btn_login"):
            if not username or not password:
                st.error("Enter username and password.")
            else:
                users = st.session_state.users
                if username in users and users[username]["password"] == password and users[username]["role"] == role_choice:
                    st.session_state.current_user = username
                    st.session_state.current_role = role_choice
                    st.session_state.msg_flag = "logged_in"
                    st.success(f"Logged in as {users[username].get('display', username)} ({role_choice})")
                else:
                    st.error("Invalid credentials or role mismatch.")
    with col2:
        if st.button("Logout", key="btn_logout"):
            st.session_state.current_user = None
            st.session_state.current_role = None
            st.success("Logged out.")

    st.markdown("---")
    st.subheader("Register (demo, stored in-memory)")
    r_user = st.text_input("New username", key="reg_user")
    r_pass = st.text_input("New password", type="password", key="reg_pass")
    r_role = st.selectbox("Register role", ["restaurant", "ngo"], key="reg_role")
    r_display = st.text_input("Display name (optional)", key="reg_disp")
    if st.button("Register", key="btn_reg"):
        if not r_user or not r_pass:
            st.error("Enter username and password.")
        elif r_user in st.session_state.users:
            st.error("Username already exists.")
        else:
            st.session_state.users[r_user] = {"password": r_pass, "role": r_role, "display": r_display or r_user, "contact": "", "location": ""}
            st.success(f"Registered {r_user} as {r_role}. Now login from above.")

# ---------------------- ORDERS (SQLite-backed) ----------------------
with tabs[7]:
    st.header("🏬 Restaurant ↔ NGO Orders (Persistent)")
    st.write("Restaurants must login as role=restaurant to post. NGOs must login as role=ngo to view & confirm.")
    left, right = st.columns(2)

    # Restaurant posting area
    with left:
        st.subheader("Restaurant: Post Order")
        if st.session_state.current_role != "restaurant":
            st.info("Login as a restaurant to post orders.")
        else:
            posted_by = st.session_state.current_user
            rest_display = st.session_state.users.get(posted_by, {}).get("display", posted_by)

            # ------------------- NEW SECTION: show my existing orders -------------------
            my_orders = fetch_orders("username=?", (posted_by,))
            if my_orders:
                st.markdown("### My Posted Orders")
                for row in my_orders:
                    # columns indices:
                    # 0:id,1:restaurant,2:username,3:item,4:qty,5:pickup,6:location,7:contact,8:notes,9:price,10:status,11:posted_on,12:confirmed_by,13:confirmed_on,14:ngo_contact,15:ngo_location
                    oid = row[0]
                    restaurant_name = row[1]
                    username = row[2]
                    item = row[3]
                    qty = row[4]
                    pickup = row[5]
                    location = row[6]
                    contact = row[7]
                    notes = row[8]
                    price = row[9]
                    status = row[10]
                    posted_on = row[11]
                    confirmed_by = row[12] if len(row) > 12 else ""
                    confirmed_on = row[13] if len(row) > 13 else ""
                    ngo_contact = row[14] if len(row) > 14 else ""
                    ngo_location = row[15] if len(row) > 15 else ""

                    with st.expander(f"{item} — {status}", expanded=False):
                        st.write(f"Qty: {qty}")
                        st.write(f"Pickup: {pickup}")
                        st.write(f"Location: {location}")
                        st.write(f"Contact: {contact}")
                        st.write(f"Price: {price}")
                        st.write(f"Posted on: {posted_on}")
                        if notes:
                            st.info(f"Notes: {notes}")
                        st.write(f"Status: {status}")
                        if confirmed_by:
                            st.success(f"✅ Confirmed by {confirmed_by} on {confirmed_on}")
                            if ngo_contact:
                                st.write(f"📞 NGO Contact: {ngo_contact}")
                            if ngo_location:
                                st.write(f"📍 NGO Location: {ngo_location}")
                        c1, c2 = st.columns([1,1])
                        with c1:
                            if st.button("🗑 Remove Order", key=f"remove_order_{oid}"):
                                remove_order(oid)
                                st.success("Order removed.")
                                st.experimental_rerun()
                        with c2:
                            # allow restaurant to mark unavailable if desired
                            if st.button("❌ Mark Unavailable", key=f"rest_unavail_{oid}"):
                                if status != "Unavailable":
                                    update_order_status(oid, "Unavailable")
                                    st.success("Marked unavailable.")
                                else:
                                    st.info("Already unavailable.")
            else:
                st.info("No orders posted yet.")
            # ------------------- END NEW SECTION -------------------

            # -------- Existing Post form (unchanged) --------
            ro_item = st.text_input("Item / details", key="ro_item", value="Cooked meals - 20 boxes")
            ro_qty = st.text_input("Quantity / units", key="ro_qty", value="20 boxes")
            ro_pickup = st.text_input("Pickup time / window", key="ro_pickup", value="Today 6-7 PM")
            ro_location = st.text_input("Location (address or lat,lng)", key="ro_location", value="Campus Block A, Jaipur")
            ro_contact = st.text_input("Contact (phone/email)", key="ro_contact", value="restro@example.com")
            ro_notes = st.text_area("Notes (optional)", key="ro_notes")
            ro_price = st.number_input("Suggested price (0 = free)", min_value=0, value=0, key="ro_price")
            if st.button("Post Order", key="post_order_btn"):
                if not ro_item.strip() or not ro_location.strip() or not ro_contact.strip():
                    st.error("Fill item, location, and contact.")
                else:
                    order = {
                        "restaurant": rest_display,
                        "username": posted_by,
                        "item": ro_item.strip(),
                        "qty": ro_qty.strip(),
                        "pickup": ro_pickup.strip(),
                        "location": ro_location.strip(),
                        "contact": ro_contact.strip(),
                        "notes": ro_notes.strip(),
                        "price": str(ro_price) if ro_price > 0 else "Free",
                        "status": "Available",
                        "posted_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    insert_order(order)
                    st.success("Order posted. NGOs can now view & confirm.")
                    st.session_state.msg_flag = "order_posted"

    # NGO view & confirm area
    with right:
        st.subheader("NGO: View & Confirm Orders")
        if st.session_state.current_role != "ngo":
            st.info("Login as an NGO to view and confirm orders.")
        else:
            orders = fetch_orders()  # all orders
            stat_filter = st.selectbox("Filter by status", ["All", "Available", "Confirmed", "Unavailable"], index=0, key="stat_filter")
            if stat_filter == "All":
                filtered = orders
            else:
                # status column index is 10
                filtered = [r for r in orders if r[10] == stat_filter]

            if not filtered:
                st.info("No orders match the filter.")
            else:
                for row in filtered:
                    # columns indices:
                    # 0:id,1:restaurant,2:username,3:item,4:qty,5:pickup,6:location,7:contact,8:notes,9:price,10:status,11:posted_on,12:confirmed_by,13:confirmed_on,14:ngo_contact,15:ngo_location
                    oid = row[0]
                    restaurant = row[1]
                    username = row[2]
                    item = row[3]
                    qty = row[4]
                    pickup = row[5]
                    location = row[6]
                    contact = row[7]
                    notes = row[8]
                    price = row[9]
                    status = row[10]
                    posted_on = row[11]
                    confirmed_by = row[12]
                    confirmed_on = row[13]
                    ngo_contact = row[14] if len(row) > 14 else ""
                    ngo_location = row[15] if len(row) > 15 else ""

                    with st.expander(f"{item} — {restaurant} ({status})", expanded=False):
                        st.write(f"Qty: {qty}")
                        st.write(f"Pickup: {pickup}")
                        st.write(f"Contact: {contact}")
                        st.write(f"Price: {price}")
                        st.write(f"Posted on: {posted_on}")
                        if notes:
                            st.info(f"Notes: {notes}")
                        if confirmed_by:
                            st.write(f"Confirmed by: {confirmed_by} on {confirmed_on}")
                            if ngo_contact:
                                st.write(f"NGO Contact: {ngo_contact}")
                            if ngo_location:
                                st.write(f"NGO Location: {ngo_location}")

                        # Map link + embed
                        try:
                            maps_q = location.replace(" ", "+")
                            maps_link = f"https://www.google.com/maps/search/?api=1&query={maps_q}"
                            st.markdown(f"[Open in Google Maps]({maps_link})")
                            iframe_html = f'<iframe src="https://www.google.com/maps?q={maps_q}&output=embed" width="100%" height="220" style="border:0;" allowfullscreen="" loading="lazy"></iframe>'
                            html(iframe_html, height=240)
                        except Exception:
                            st.write("Map unavailable for this location.")

                        c1, c2, c3 = st.columns([1,1,1])
                        with c1:
                            if st.button("✅ Confirm (Pick-up)", key=f"confirm_{oid}"):
                                if status == "Available":
                                    ngo_username = st.session_state.current_user
                                    ngo_info = st.session_state.users.get(ngo_username, {})
                                    ngo_contact_val = ngo_info.get("contact", "")
                                    ngo_location_val = ngo_info.get("location", "")
                                    # store human-friendly display name if available
                                    confirmed_by_display = ngo_info.get("display", ngo_username)
                                    update_order_status(oid, "Confirmed", confirmed_by=confirmed_by_display, ngo_contact=ngo_contact_val, ngo_location=ngo_location_val)
                                    st.success("Order confirmed. Contact restaurant for pickup.")
                                else:
                                    st.warning("Order not available to confirm.")
                        with c2:
                            if st.button("❌ Mark Unavailable", key=f"unavail_{oid}"):
                                if status != "Unavailable":
                                    update_order_status(oid, "Unavailable")
                                    st.success("Marked unavailable.")
                                else:
                                    st.info("Already unavailable.")
                        with c3:
                            # removal allowed only by restaurant owner (not shown here)
                            st.write("")

    # small UX message area
    if st.session_state.msg_flag == "order_posted":
        st.info("Order successfully posted (persisted to database).")
        st.session_state.msg_flag = None
    if st.session_state.msg_flag == "logged_in":
        st.session_state.msg_flag = None

# ---------------------- SHOW LOGIN STATE & FOOTER ----------------------
st.markdown("---")
if st.session_state.current_user:
    display = st.session_state.users.get(st.session_state.current_user, {}).get("display", st.session_state.current_user)
    st.write(f"Logged in as {display} · role: {st.session_state.current_role}")
else:
    st.write("Not logged in.")

st.markdown("<div style='text-align:center; color:#666; padding:8px 0;'>FoodWise ♻ · Orders persisted to SQLite (orders.db). Host on a server to share between devices.</div>", unsafe_allow_html=True)
