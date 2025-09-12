# app.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit.components.v1 import html

st.set_page_config(page_title="FoodWise", page_icon="🍲", layout="wide")

# ---------------------- SESSION STATE INITIALIZATION ----------------------
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
    # each entry: {"item","qty","units","reason","date"}
    st.session_state.waste_log = []

# ---------------------- THEME / STYLE ----------------------
st.markdown(
    """
    <style>
    .foodwise-hero h1 { color:#FF6F61; font-size: 3rem; margin-bottom:0; }
    .foodwise-hero h3 { color:#22C55E; font-weight:600; margin-top:0.25rem; }
    .foodwise-hero p { font-size:1.05rem; opacity:0.9; }
    .stButton>button {
        background:#FF6F61; color:white; border-radius:12px; padding:0.6rem 1rem;
        border:0; font-weight:600; transition: all 0.15s ease;
    }
    .stButton>button:hover {
        background:#FF4A3C; transform: scale(1.03);
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, textarea {
        border:2px solid #22C55E; border-radius:10px;
    }
    .pill { 
        display:inline-block; padding:6px 10px; border-radius:999px; 
        background:#F1F5F9; margin-right:8px; margin-bottom:8px; font-size:0.85rem;
    }
    .recipe-card {
        border: 1px solid #E2E8F0; border-radius:12px; padding:1rem; margin-bottom:1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .feature-card {
        background: #F8FAFC; border-radius:12px; padding:1.5rem; margin-bottom:1.5rem;
    }
    </style>
    """, unsafe_allow_html=True
)

# ---------------------- HEADER ----------------------
st.markdown('<div class="foodwise-hero" style="text-align:center; padding: 10px 0 20px 0;">'
            '<h1>🍲 FoodWise</h1>'
            '<h3>AI-style Recipe Generator · Planner · Sharing · Waste Tracker</h3>'
            '<p>Reduce food waste, help your community, and plan smarter meals.</p>'
            '</div>', unsafe_allow_html=True)

# ---------------------- NAV TABS ----------------------
tabs = st.tabs(["🏠 Home", "🥘 Recipes", "📅 Planner", "🤝 Sharing Hub", "⭐ Favorites", "📉 Waste Tracker", "🏬 Restaurant Orders"])

# ---------------------- HOME ----------------------
with tabs[0]:
    st.markdown("### 🌟 Welcome to FoodWise!")
    st.markdown("""
    <div class="feature-card">
    Make the most of your food: generate recipes from leftovers, plan meals, track waste, and connect restaurants with NGOs.
    </div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Why this app?")
        st.write("- Reduce food waste and save money")
        st.write("- Share surplus with local NGOs")
        st.write("- Plan portions so you cook just enough")
    with c2:
        st.subheader("Quick actions")
        quick_ing = st.text_input("Quick ingredients (comma-separated)", key="quick_ing", placeholder="eg. rice, spinach, chicken")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Suggest (Quick)"):
                if quick_ing.strip():
                    items = [x.strip() for x in quick_ing.split(",") if x.strip()]
                    if items:
                        base = items[:3] if len(items) >= 3 else items + ["veggies", "spices"][len(items):]
                        st.success("Quick suggestions:")
                        with st.expander("Ideas", expanded=True):
                            st.markdown(f"<div class='recipe-card'><h4>🍳 {base[0].title()} Stir-Fry</h4>"
                                        f"<p><strong>Ingredients:</strong> {', '.join(base[:2])}, soy sauce, garlic, oil</p>"
                                        f"</div>", unsafe_allow_html=True)
                    else:
                        st.warning("Enter at least one ingredient.")
                else:
                    st.warning("Enter at least one ingredient.")
        with col2:
            if st.button("Clear", key="clear_quick"):
                st.session_state.quick_ing = ""

# ---------------------- RECIPES ----------------------
with tabs[1]:
    st.subheader("🥘 Leftover Recipe Generator")
    st.markdown("Enter your available ingredients and get simple, practical recipes.")
    c1, c2 = st.columns([2,1])
    with c1:
        ingredients = st.text_input("Ingredients (comma-separated)", key="rec_ing", placeholder="e.g., rice, carrot, eggs")
        diet = st.selectbox("Diet preference", ["Any", "Vegetarian", "Vegan", "Gluten-free", "Dairy-free"])
        max_time = st.slider("Max cooking time (minutes)", 10, 120, 30)
        difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], value="Easy")
        if st.button("Generate Recipes"):
            if ingredients.strip():
                items = [x.strip() for x in ingredients.split(",") if x.strip()]
                if not items:
                    st.warning("Please enter valid ingredients.")
                else:
                    # Deterministic heuristic recipe generator (works offline)
                    base = items[:3] if len(items) >= 3 else items + ["veggies", "spices"][len(items):]
                    tag = "" if diet == "Any" else f" · {diet}"
                    st.success("Here are recipes based on your ingredients:")
                    # Recipe cards
                    with st.expander(f"{base[0].title()} Quick Stir-Fry", expanded=True):
                        st.markdown(f"**Ingredients:** {', '.join(base[:2])}, soy sauce, garlic, oil  \n"
                                    f"**Time:** {max_time-10} minutes · **Difficulty:** {difficulty}{tag}")
                        if st.button("⭐ Save Recipe", key="save_gen_1"):
                            st.session_state.favorite_recipes.append({
                                "name": f"{base[0].title()} Quick Stir-Fry",
                                "ingredients": f"{', '.join(base[:2])}, soy sauce, garlic, oil",
                                "instructions": "1. Heat oil\n2. Sauté garlic\n3. Add main ingredient and stir-fry\n4. Add sauce and serve",
                                "time": f"{max_time-10} mins",
                                "difficulty": difficulty
                            })
                            st.success("Saved to favorites.")
                    with st.expander(f"{base[0].title()} & {base[1].title()} Wraps"):
                        st.markdown(f"**Ingredients:** {', '.join(base[:2])}, tortillas, yogurt/spread  \n"
                                    f"**Time:** {max_time} minutes · **Difficulty:** {difficulty}{tag}")
                        if st.button("⭐ Save Recipe", key="save_gen_2"):
                            st.session_state.favorite_recipes.append({
                                "name": f"{base[0].title()} {base[1].title()} Wraps",
                                "ingredients": f"{', '.join(base[:2])}, tortillas, yogurt/spread",
                                "instructions": "1. Cook main ingredients\n2. Warm tortillas\n3. Fill and roll",
                                "time": f"{max_time} mins",
                                "difficulty": difficulty
                            })
                            st.success("Saved to favorites.")
                    with st.expander(f"Hearty {base[0].title()} Soup"):
                        st.markdown(f"**Ingredients:** {', '.join(base)}, broth, herbs  \n"
                                    f"**Time:** {max_time+10} minutes · **Difficulty:** {difficulty}{tag}")
                        if st.button("⭐ Save Recipe", key="save_gen_3"):
                            st.session_state.favorite_recipes.append({
                                "name": f"Hearty {base[0].title()} Soup",
                                "ingredients": f"{', '.join(base)}, broth, herbs",
                                "instructions": "1. Sauté veggies\n2. Add broth and simmer\n3. Season & serve",
                                "time": f"{max_time+10} mins",
                                "difficulty": difficulty
                            })
                            st.success("Saved to favorites.")
            else:
                st.warning("Please enter ingredients.")
    with c2:
        st.info("Tips to reduce waste:")
        st.write("- Use older ingredients first")
        st.write("- Freeze leftovers")
        st.write("- Plan weekly meals")

# ---------------------- PLANNER ----------------------
with tabs[2]:
    st.subheader("📅 Smart Food Planner")
    st.caption("Weekly planner and quantity calculator.")
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    meals = ["Breakfast", "Lunch", "Dinner"]
    planner_cols = st.columns(7)
    for i, day in enumerate(days):
        with planner_cols[i]:
            st.markdown(f"**{day}**")
            for meal in meals:
                st.session_state.meal_plan[day][meal] = st.text_input(
                    f"{meal}", value=st.session_state.meal_plan[day][meal], key=f"{day}_{meal}"
                )
    st.markdown("### 📊 Quantity Calculator")
    dish = st.text_input("Dish name", value="Veg Fried Rice")
    people = st.number_input("Number of people", 1, 100, 4, step=1)
    baseline = {
        "rice (g)": 90, "mixed veggies (g)": 120, "oil (tbsp)": 0.75,
        "spices (tsp)": 1.0, "salt (tsp)": 0.5, "protein (g)": 100
    }
    if st.button("Calculate quantities"):
        rows = []
        for k, v in baseline.items():
            qty = v * people
            rows.append({"Ingredient": k, "Per Person": v, "Total Quantity": round(qty, 2)})
        df = pd.DataFrame(rows)
        st.write(f"**Plan for:** {people} people · **Dish:** {dish}")
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Download Shopping List", df.to_csv(index=False), file_name="shopping_list.csv", mime="text/csv")

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
    with colB:
        dietary_info = st.multiselect("Dietary information", ["Vegetarian", "Vegan", "Gluten-free", "Dairy-free", "Contains nuts"])
        notes = st.text_area("Additional notes")
        price = None
        if mode == "Sell":
            price = st.number_input("Price (₹)", min_value=0, value=50, step=5)
    if st.button("Add listing"):
        if not all([item, qty, location, contact]):
            st.error("Please fill in name, qty, location, and contact.")
        else:
            st.session_state.shared_items.append({
                "mode": mode,
                "item": item, "qty": qty,
                "expiry": expiry.strftime("%Y-%m-%d"),
                "dietary": ", ".join(dietary_info) if dietary_info else "None",
                "location": location, "contact": contact,
                "price": price if mode == "Sell" else "Free",
                "notes": notes, "date_posted": datetime.today().strftime("%Y-%m-%d")
            })
            st.success("Listing added!")
    if st.session_state.shared_items:
        st.markdown("### 📋 Current Listings")
        for i, it in enumerate(st.session_state.shared_items):
            with st.expander(f"{it['item']} - {it['location']} ({it['mode']})", expanded=(i == 0)):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Qty:** {it['qty']}")
                    st.write(f"**Expiry:** {it['expiry']}")
                    st.write(f"**Dietary:** {it['dietary']}")
                with c2:
                    st.write(f"**Location:** {it['location']}")
                    st.write(f"**Contact:** {it['contact']}")
                    st.write(f"**Price:** {it['price']}")
                if it['notes']:
                    st.info(f"Notes: {it['notes']}")
                cols = st.columns([1,1])
                with cols[0]:
                    if st.button("🗺️ Show on Maps", key=f"maps_shared_{i}"):
                        maps_q = it['location'].replace(" ", "+")
                        maps_link = f"https://www.google.com/maps/search/?api=1&query={maps_q}"
                        st.write(f"[Open in Google Maps]({maps_link})")
                with cols[1]:
                    if st.button("Remove", key=f"remove_shared_{i}"):
                        st.session_state.shared_items.pop(i)
                        st.experimental_rerun()
    else:
        st.info("No shared items yet.")

# ---------------------- FAVORITES ----------------------
with tabs[4]:
    st.subheader("⭐ Favorite Recipes")
    if st.session_state.favorite_recipes:
        for i, r in enumerate(st.session_state.favorite_recipes):
            with st.expander(f"{r['name']} — {r.get('time','N/A')} — {r.get('difficulty','')}", expanded=(i == 0)):
                st.write(f"**Ingredients:** {r['ingredients']}")
                st.write("**Instructions:**")
                st.write(r['instructions'].replace("\n", "  \n"))
                cols = st.columns(2)
                with cols[0]:
                    if st.button("Remove", key=f"remove_fav_{i}"):
                        st.session_state.favorite_recipes.pop(i)
                        st.experimental_rerun()
                with cols[1]:
                    st.download_button("📥 Export recipe (txt)", data=f"Name: {r['name']}\nIngredients: {r['ingredients']}\nInstructions:\n{r['instructions']}", file_name=f"{r['name']}.txt")
    else:
        st.info("No favorites yet — save generated recipes using the ⭐ buttons.")

# ---------------------- WASTE TRACKER ----------------------
with tabs[5]:
    st.subheader("📉 Food Waste Tracker")
    st.markdown("Log food you throw away so you can learn and reduce waste over time.")
    w_col1, w_col2 = st.columns(2)
    with w_col1:
        w_item = st.text_input("Item name", key="w_item", value="Cooked rice")
        w_qty = st.number_input("Quantity", min_value=0.0, value=1.0, step=0.1, format="%.2f")
        w_units = st.selectbox("Units", ["kg", "g", "boxes", "units"], index=1)
    with w_col2:
        w_reason = st.selectbox("Reason", ["Overcooked", "Forgotten", "Spoiled", "Leftover not used", "Other"])
        w_date = st.date_input("Date", value=datetime.today())
        if st.button("Log waste"):
            if not w_item.strip() or w_qty <= 0:
                st.error("Enter valid item and quantity.")
            else:
                st.session_state.waste_log.append({
                    "item": w_item.strip(), "qty": w_qty, "units": w_units,
                    "reason": w_reason, "date": w_date.strftime("%Y-%m-%d")
                })
                st.success("Logged.")
    if st.session_state.waste_log:
        dfw = pd.DataFrame(st.session_state.waste_log)
        st.markdown("### Recent waste logs")
        st.dataframe(dfw.sort_values("date", ascending=False), use_container_width=True)
        # Simple aggregate: counts per reason
        reason_counts = dfw.groupby("reason")["qty"].sum().reset_index()
        st.markdown("### Waste by reason (total quantity)")
        st.bar_chart(data=reason_counts.set_index("reason"))
        st.download_button("📥 Export waste log (CSV)", dfw.to_csv(index=False), file_name="waste_log.csv")
    else:
        st.info("No waste logged yet. Start logging to track patterns.")

# ---------------------- RESTAURANT ORDERS ----------------------
with tabs[6]:
    st.subheader("🏬 Restaurant Orders → NGO Confirmation")
    st.markdown("Restaurants post surplus; NGOs view, confirm, and see location on map.")
    colL, colR = st.columns(2)
    with colL:
        st.markdown("### Restaurant: Post an order")
        r_name = st.text_input("Restaurant name", key="r_name", value="My Restaurant")
        r_item = st.text_input("Item / Order details", key="r_item", value="Cooked meals - 20 boxes")
        r_qty = st.text_input("Quantity / units", key="r_qty", value="20 boxes")
        r_pickup_by = st.text_input("Pickup time / window", key="r_pickup", value="Today 6-7 PM")
        r_location = st.text_input("Location (address or 'lat,lng')", key="r_location", value="Campus Block A, Jaipur")
        r_contact = st.text_input("Contact (phone/email)", key="r_contact", value="restro@example.com")
        r_notes = st.text_area("Additional notes", key="r_notes")
        r_price = st.number_input("Suggested price (₹) — optional", min_value=0, value=0, step=5, key="r_price")
        if st.button("📤 Post Order"):
            if not all([r_name.strip(), r_item.strip(), r_location.strip(), r_contact.strip()]):
                st.error("Please fill required fields.")
            else:
                st.session_state.restaurant_orders.append({
                    "restaurant": r_name.strip(),
                    "item": r_item.strip(),
                    "qty": r_qty.strip(),
                    "pickup_by": r_pickup_by.strip(),
                    "location": r_location.strip(),
                    "contact": r_contact.strip(),
                    "notes": r_notes.strip(),
                    "price": r_price if r_price > 0 else "Free",
                    "status": "Available",
                    "date_posted": datetime.today().strftime("%Y-%m-%d")
                })
                st.success("Order posted.")
    with colR:
        st.markdown("### NGO: View & Confirm")
        if st.session_state.restaurant_orders:
            for i, order in enumerate(st.session_state.restaurant_orders):
                with st.expander(f"{order['item']} — {order['restaurant']} ({order['status']})", expanded=(i == 0)):
                    st.write(f"**Qty:** {order['qty']}")
                    st.write(f"**Pickup by:** {order['pickup_by']}")
                    st.write(f"**Contact:** {order['contact']}")
                    st.write(f"**Price:** {order['price']}")
                    if order['notes']:
                        st.info(f"Notes: {order['notes']}")
                    st.write(f"**Posted on:** {order['date_posted']}")
                    maps_query = order['location'].replace(" ", "+")
                    maps_embed_url = f"https://www.google.com/maps?q={maps_query}&output=embed"
                    maps_link = f"https://www.google.com/maps/search/?api=1&query={maps_query}"
                    st.markdown(f"[Open in Google Maps]({maps_link})")
                    iframe_html = f"""
                    <iframe
                      src="{maps_embed_url}"
                      width="100%" height="300" style="border:0;" allowfullscreen="" loading="lazy">
                    </iframe>
                    """
                    html(iframe_html, height=320)
                    cols = st.columns([1,1,1])
                    with cols[0]:
                        if st.button("✅ Confirm (NGO pick-up)", key=f"confirm_{i}"):
                            if order['status'] == "Available":
                                st.session_state.restaurant_orders[i]['status'] = "Confirmed by NGO"
                                st.success("Confirmed — contact restaurant for pickup.")
                                st.experimental_rerun()
                            else:
                                st.warning("Already confirmed/unavailable.")
                    with cols[1]:
                        if st.button("❌ Mark unavailable", key=f"unavail_{i}"):
                            st.session_state.restaurant_orders[i]['status'] = "Unavailable"
                            st.experimental_rerun()
                    with cols[2]:
                        if st.button("🗑️ Remove", key=f"remove_order_{i}"):
                            st.session_state.restaurant_orders.pop(i)
                            st.experimental_rerun()
        else:
            st.info("No restaurant orders yet.")

# ---------------------- FOOTER ----------------------
st.markdown("---")
st.markdown("<div style='text-align:center; color:#666;'>FoodWise ♻️ · Reduce Food Waste · Help Your Community · Save Money</div>", unsafe_allow_html=True)
