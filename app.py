# app.py (Final FoodWise with Restaurant & NGO login)
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit.components.v1 import html

st.set_page_config(page_title="FoodWise", page_icon="🍲", layout="wide")

# --------------------- INITIAL SESSION STATE ---------------------
if 'shared_items' not in st.session_state:
    st.session_state.shared_items = []
if 'favorite_recipes' not in st.session_state:
    st.session_state.favorite_recipes = []
if 'meal_plan' not in st.session_state:
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    meals = ["Breakfast", "Lunch", "Dinner"]
    st.session_state.meal_plan = {day: {meal: "" for meal in meals} for day in days}
if 'restaurant_orders' not in st.session_state:
    st.session_state.restaurant_orders = []
if 'waste_log' not in st.session_state:
    st.session_state.waste_log = []

# simple in-memory users (for demo). keys -> {password, role, display_name}
if 'users' not in st.session_state:
    st.session_state.users = {
        # pre-created demo accounts
        "restro1": {"password": "restro123", "role": "restaurant", "display": "Restro One"},
        "ngo1": {"password": "ngo123", "role": "ngo", "display": "Helping NGO"},
    }

# track current logged-in user
if 'current_user' not in st.session_state:
    st.session_state.current_user = None  # username or None
if 'current_role' not in st.session_state:
    st.session_state.current_role = None  # "restaurant" or "ngo" or None

# flags to avoid immediate loops / messages
if 'action_flag' not in st.session_state:
    st.session_state.action_flag = None

# ---------------------- STYLES & HEADER ----------------------
st.markdown(
    """
    <style>
    .foodwise-hero h1 { color:#FF6F61; font-size: 2.6rem; margin-bottom:0; }
    .foodwise-hero h3 { color:#22C55E; font-weight:600; margin-top:0.15rem; }
    .stButton>button { background:#FF6F61; color:white; border-radius:10px; padding:0.5rem 0.8rem; border:0; }
    .recipe-card { border:1px solid #E2E8F0; border-radius:12px; padding:0.9rem; margin-bottom:0.9rem; }
    </style>
    """, unsafe_allow_html=True
)

st.markdown('<div class="foodwise-hero" style="text-align:center; padding:8px 0 14px 0;">'
            '<h1>🍲 FoodWise</h1>'
            '<h3>Reduce food waste · Restaurant → NGO orders</h3>'
            '</div>', unsafe_allow_html=True)

# ---------------------- NAVIGATION (tabs) ----------------------
tabs = st.tabs(["🏠 Home", "🥘 Recipes", "📅 Planner", "🤝 Sharing", "⭐ Favorites", "📉 Waste", "🔐 Login", "🏬 Orders"])

# ---------------------- HOME ----------------------
with tabs[0]:
    st.markdown("### Welcome to FoodWise")
    st.write("Make the most of your food: generate recipes from leftovers, plan meals, share surplus, and connect restaurants with NGOs.")
    st.write("Demo accounts: restaurant -> `restro1` / `restro123` ; NGO -> `ngo1` / `ngo123`")

# ---------------------- RECIPES ----------------------
with tabs[1]:
    st.header("Leftover Recipe Generator")
    st.markdown("Enter ingredients (comma-separated). This generator is deterministic (no external APIs).")
    ingredients = st.text_input("Ingredients", key="rec_ing", placeholder="rice, carrot, egg")
    diet = st.selectbox("Diet", ["Any", "Vegetarian", "Vegan", "Gluten-free", "Dairy-free"])
    time_limit = st.slider("Max cook time (min)", 10, 120, 30)
    difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], value="Easy")
    if st.button("Generate Recipes", key="gen_rec"):
        if not ingredients.strip():
            st.warning("Enter some ingredients.")
        else:
            items = [x.strip() for x in ingredients.split(",") if x.strip()]
            base = items[:3] if len(items) >= 3 else items + ["veggies", "spices"][len(items):]
            tag = "" if diet == "Any" else f" · {diet}"
            st.success("Recipes:")
            with st.expander(f"{base[0].title()} Stir-Fry", expanded=True):
                st.markdown(f"**Ingredients:** {', '.join(base[:2])}, soy sauce, garlic, oil  \n**Time:** {max(5, time_limit-10)} min · **{difficulty}{tag}**")
                if st.button("⭐ Save", key=f"save_r_1"):
                    st.session_state.favorite_recipes.append({
                        "name": f"{base[0].title()} Stir-Fry",
                        "ingredients": f"{', '.join(base[:2])}, soy sauce, garlic, oil",
                        "instructions": "1. Heat oil\n2. Add garlic\n3. Stir-fry main ingredient\n4. Serve",
                        "time": f"{max(5, time_limit-10)} mins",
                        "difficulty": difficulty
                    })
                    st.success("Saved.")
            with st.expander(f"{base[0].title()} & {base[1].title()} Wraps"):
                st.markdown(f"**Ingredients:** {', '.join(base[:2])}, tortillas, yogurt  \n**Time:** {time_limit} min · **{difficulty}{tag}**")
                if st.button("⭐ Save", key=f"save_r_2"):
                    st.session_state.favorite_recipes.append({
                        "name": f"{base[0].title()} {base[1].title()} Wraps",
                        "ingredients": f"{', '.join(base[:2])}, tortillas, yogurt",
                        "instructions": "1. Cook and spice\n2. Fill tortillas\n3. Roll & serve",
                        "time": f"{time_limit} mins",
                        "difficulty": difficulty
                    })
                    st.success("Saved.")
            with st.expander(f"Hearty {base[0].title()} Soup"):
                st.markdown(f"**Ingredients:** {', '.join(base)}, broth  \n**Time:** {time_limit+10} min · **{difficulty}{tag}**")
                if st.button("⭐ Save", key=f"save_r_3"):
                    st.session_state.favorite_recipes.append({
                        "name": f"Hearty {base[0].title()} Soup",
                        "ingredients": f"{', '.join(base)}, broth",
                        "instructions": "1. Sauté\n2. Add broth\n3. Simmer\n4. Serve",
                        "time": f"{time_limit+10} mins",
                        "difficulty": difficulty
                    })
                    st.success("Saved.")

# ---------------------- PLANNER ----------------------
with tabs[2]:
    st.header("Weekly Meal Planner")
    days = list(st.session_state.meal_plan.keys())
    cols = st.columns(7)
    for i, day in enumerate(days):
        with cols[i]:
            st.markdown(f"**{day}**")
            for meal in ["Breakfast", "Lunch", "Dinner"]:
                st.session_state.meal_plan[day][meal] = st.text_input(f"{meal}", value=st.session_state.meal_plan[day][meal], key=f"{day}_{meal}")

    st.markdown("### Quantity Calculator")
    dish = st.text_input("Dish name", value="Veg Fried Rice")
    people = st.number_input("People", 1, 100, 4)
    baseline = {"rice (g)": 90, "veggies (g)": 120, "oil (tbsp)": 0.75}
    if st.button("Calculate"):
        rows = []
        for k, v in baseline.items():
            rows.append({"Ingredient": k, "Per person": v, "Total": round(v * people, 2)})
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        st.download_button("Download shopping list", df.to_csv(index=False), "shopping_list.csv", "text/csv")

# ---------------------- SHARING (basic) ----------------------
with tabs[3]:
    st.header("Share / Sell / Donate")
    mode = st.radio("I want to:", ["Donate", "Sell"])
    colA, colB = st.columns(2)
    with colA:
        s_item = st.text_input("Item name", "Cooked rice (sealed)")
        s_qty = st.text_input("Quantity", "2 boxes")
        s_expiry = st.date_input("Expiry", min_value=datetime.today(), value=datetime.today() + timedelta(days=2))
        s_location = st.text_input("Location", "Campus Block A")
        s_contact = st.text_input("Contact", "example@iitj.ac.in")
    with colB:
        s_diet = st.multiselect("Dietary", ["Vegetarian", "Vegan", "Gluten-free", "Contains nuts"])
        s_notes = st.text_area("Notes")
        s_price = 0
        if mode == "Sell":
            s_price = st.number_input("Price (₹)", min_value=0, value=50)
    if st.button("Add listing", key="add_listing"):
        if not all([s_item.strip(), s_qty.strip(), s_location.strip(), s_contact.strip()]):
            st.error("Fill required fields.")
        else:
            st.session_state.shared_items.append({
                "mode": mode, "item": s_item, "qty": s_qty,
                "expiry": s_expiry.strftime("%Y-%m-%d"),
                "dietary": ", ".join(s_diet) if s_diet else "None",
                "location": s_location, "contact": s_contact,
                "price": s_price if mode == "Sell" else "Free",
                "notes": s_notes, "posted": datetime.today().strftime("%Y-%m-%d")
            })
            st.success("Listing added.")
    if st.session_state.shared_items:
        st.markdown("### Current listings")
        for i, it in enumerate(st.session_state.shared_items):
            with st.expander(f"{it['item']} — {it['location']} ({it['mode']})", expanded=(i == 0)):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"Qty: {it['qty']}")
                    st.write(f"Expiry: {it['expiry']}")
                    st.write(f"Dietary: {it['dietary']}")
                with c2:
                    st.write(f"Location: {it['location']}")
                    st.write(f"Contact: {it['contact']}")
                    st.write(f"Price: {it['price']}")
                if it['notes']:
                    st.info(it['notes'])
                if st.button("Remove", key=f"remove_share_{i}"):
                    st.session_state.shared_items.pop(i)
                    st.experimental_rerun()
    else:
        st.info("No listings yet.")

# ---------------------- FAVORITES ----------------------
with tabs[4]:
    st.header("Favorites")
    if st.session_state.favorite_recipes:
        for i, r in enumerate(st.session_state.favorite_recipes):
            with st.expander(f"{r['name']} — {r.get('time','')}"):
                st.write("Ingredients:", r['ingredients'])
                st.write("Instructions:")
                st.write(r['instructions'])
                cols = st.columns([1,1])
                with cols[0]:
                    if st.button("Remove", key=f"rmfav_{i}"):
                        st.session_state.favorite_recipes.pop(i)
                        st.experimental_rerun()
                with cols[1]:
                    st.download_button("Export (txt)", data=f"Name: {r['name']}\nIngredients: {r['ingredients']}\n\n{r['instructions']}", file_name=f"{r['name']}.txt")
    else:
        st.info("No favorites yet.")

# ---------------------- WASTE TRACKER ----------------------
with tabs[5]:
    st.header("Food Waste Tracker")
    w_col1, w_col2 = st.columns(2)
    with w_col1:
        w_item = st.text_input("Item", key="w_item", value="Cooked rice")
        w_qty = st.number_input("Quantity", min_value=0.0, value=1.0, step=0.1)
        w_units = st.selectbox("Units", ["kg", "g", "boxes", "units"])
    with w_col2:
        w_reason = st.selectbox("Reason", ["Overcooked", "Forgotten", "Spoiled", "Leftover not used", "Other"])
        w_date = st.date_input("Date", value=datetime.today())
        if st.button("Log waste"):
            if not w_item.strip() or w_qty <= 0:
                st.error("Valid item & quantity required.")
            else:
                st.session_state.waste_log.append({
                    "item": w_item.strip(), "qty": w_qty, "units": w_units,
                    "reason": w_reason, "date": w_date.strftime("%Y-%m-%d")
                })
                st.success("Logged.")
    if st.session_state.waste_log:
        dfw = pd.DataFrame(st.session_state.waste_log)
        st.dataframe(dfw.sort_values("date", ascending=False), use_container_width=True)
        st.download_button("Export waste CSV", dfw.to_csv(index=False), file_name="waste_log.csv")
    else:
        st.info("No waste logged yet.")

# ---------------------- LOGIN (Restaurant & NGO) ----------------------
with tabs[6]:
    st.header("Login / Register")
    st.markdown("Choose your role and login. Demo accounts: restro1/restro123 (restaurant), ngo1/ngo123 (ngo).")
    role = st.selectbox("Role", ["restaurant", "ngo"], index=0, key="login_role")
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
    with col2:
        if st.button("Login", key="btn_login"):
            if not username or not password:
                st.error("Enter username & password.")
            else:
                users = st.session_state.users
                if username in users and users[username]['password'] == password and users[username]['role'] == role:
                    st.session_state.current_user = username
                    st.session_state.current_role = role
                    st.success(f"Logged in as {users[username]['display'] or username} ({role})")
                else:
                    st.error("Invalid credentials or role mismatch.")
        if st.button("Logout", key="btn_logout"):
            st.session_state.current_user = None
            st.session_state.current_role = None
            st.success("Logged out.")
    st.markdown("---")
    st.markdown("**Register (demo, stored in-session)**")
    r_user = st.text_input("New username", key="reg_user")
    r_pass = st.text_input("New password", type="password", key="reg_pass")
    r_role = st.selectbox("Register role", ["restaurant", "ngo"], key="reg_role")
    r_display = st.text_input("Display name", key="reg_disp")
    if st.button("Register", key="btn_reg"):
        if not r_user or not r_pass:
            st.error("Enter username and password.")
        elif r_user in st.session_state.users:
            st.error("Username exists.")
        else:
            st.session_state.users[r_user] = {"password": r_pass, "role": r_role, "display": r_display or r_user}
            st.success(f"Registered {r_user} as {r_role}. Now login from above.")

# ---------------------- ORDERS (Restaurant posts & NGO confirms) ----------------------
with tabs[7]:
    st.header("Restaurant → NGO Orders")
    st.markdown("Restaurants must login with role=restaurant to post orders. NGOs must login with role=ngo to confirm.")
    left, right = st.columns(2)

    # --- LEFT: Restaurant posting (only if logged in as restaurant) ---
    with left:
        st.subheader("Restaurant: Post Order")
        if st.session_state.current_role != "restaurant":
            st.info("Please login as a restaurant to post orders.")
        else:
            posted_by = st.session_state.current_user
            rest_display = st.session_state.users.get(posted_by, {}).get("display", posted_by)
            ro_item = st.text_input("Item / details", key="ro_item", value="Cooked meals - 20 boxes")
            ro_qty = st.text_input("Quantity", key="ro_qty", value="20 boxes")
            ro_pickup = st.text_input("Pickup window", key="ro_pickup", value="Today 6-7 PM")
            ro_location = st.text_input("Location (address or lat,lng)", key="ro_location", value="Campus Block A, Jaipur")
            ro_contact = st.text_input("Contact", key="ro_contact", value="restro@example.com")
            ro_notes = st.text_area("Notes (optional)", key="ro_notes")
            ro_price = st.number_input("Suggested price (0=free)", min_value=0, value=0, key="ro_price")
            if st.button("Post Order", key="btn_post_order"):
                if not ro_item.strip() or not ro_location.strip() or not ro_contact.strip():
                    st.error("Fill item, location, and contact.")
                else:
                    st.session_state.restaurant_orders.append({
                        "id": f"ord_{len(st.session_state.restaurant_orders)+1}",
                        "restaurant": rest_display,
                        "username": posted_by,
                        "item": ro_item.strip(),
                        "qty": ro_qty.strip(),
                        "pickup": ro_pickup.strip(),
                        "location": ro_location.strip(),
                        "contact": ro_contact.strip(),
                        "notes": ro_notes.strip(),
                        "price": ro_price if ro_price > 0 else "Free",
                        "status": "Available",
                        "posted_on": datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
                        "confirmed_by": None,
                        "confirmed_on": None
                    })
                    st.success("Order posted — NGOs can view & confirm it.")
                    st.session_state.action_flag = "posted_order"  # non-looping feedback

    # --- RIGHT: NGO view & confirm (only if logged in as ngo) ---
    with right:
        st.subheader("NGO: View & Confirm")
        if st.session_state.current_role != "ngo":
            st.info("Please login as an NGO to view & confirm orders.")
        else:
            ngo_user = st.session_state.current_user
            if not st.session_state.restaurant_orders:
                st.info("No orders posted yet.")
            else:
                for idx, order in enumerate(st.session_state.restaurant_orders):
                    with st.expander(f"{order['item']} — {order['restaurant']} ({order['status']})", expanded=(idx == 0)):
                        st.write(f"**Qty:** {order['qty']}")
                        st.write(f"**Pickup:** {order['pickup']}")
                        st.write(f"**Contact:** {order['contact']}")
                        st.write(f"**Price:** {order['price']}")
                        if order['notes']:
                            st.info(order['notes'])
                        st.write(f"Posted on: {order['posted_on']}")
                        # Maps: address -> embed
                        maps_q = order['location'].replace(" ", "+")
                        maps_link = f"https://www.google.com/maps/search/?api=1&query={maps_q}"
                        st.markdown(f"[Open in Google Maps]({maps_link})")
                        iframe = f"""<iframe src="https://www.google.com/maps?q={maps_q}&output=embed" width="100%" height="240" style="border:0;" allowfullscreen="" loading="lazy"></iframe>"""
                        html(iframe, height=260)
                        cols = st.columns([1,1,1])
                        with cols[0]:
                            if st.button("✅ Confirm (Pick-up)", key=f"confirm_{order['id']}"):
                                # prevent confirming already confirmed orders
                                if order['status'] == "Available":
                                    st.session_state.restaurant_orders[idx]['status'] = "Confirmed"
                                    st.session_state.restaurant_orders[idx]['confirmed_by'] = ngo_user
                                    st.session_state.restaurant_orders[idx]['confirmed_on'] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                                    st.success("Confirmed — contact restaurant for pickup.")
                                    # no rerun loop; just set flag for UI
                                    st.session_state.action_flag = "confirmed_order"
                                else:
                                    st.warning("Order already confirmed or unavailable.")
                        with cols[1]:
                            if st.button("❌ Mark Unavailable", key=f"unavail_{order['id']}"):
                                st.session_state.restaurant_orders[idx]['status'] = "Unavailable"
                                st.session_state.action_flag = "marked_unavailable"
                                st.success("Marked unavailable.")
                        with cols[2]:
                            # allow removal only by restaurant who posted or an admin (not implemented)
                            can_remove = (st.session_state.current_role == "restaurant" and st.session_state.current_user == order.get("username"))
                            if can_remove:
                                if st.button("🗑️ Remove (owner)", key=f"rm_{order['id']}"):
                                    st.session_state.restaurant_orders.pop(idx)
                                    st.success("Removed.")
                                    st.experimental_rerun()

# ---------------------- Small UX: show current login state ----------------------
st.markdown("---")
if st.session_state.current_user:
    display = st.session_state.users.get(st.session_state.current_user, {}).get("display", st.session_state.current_user)
    st.write(f"Logged in as **{display}** · role: **{st.session_state.current_role}**")
else:
    st.write("Not logged in.")

# ---------------------- FOOTER ----------------------
st.markdown("<div style='text-align:center; color:#666; padding:8px 0;'>FoodWise ♻️ · Demo — all data stored in session only</div>", unsafe_allow_html=True)
