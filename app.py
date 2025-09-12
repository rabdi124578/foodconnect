import streamlit as st
import pandas as pd
import math
from datetime import datetime, timedelta

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

# ---------------------- THEME / STYLE ----------------------
st.markdown(
    """
    <style>
    .foodwise-hero h1 { color:#FF6F61; font-size: 3rem; margin-bottom:0; }
    .foodwise-hero h3 { color:#22C55E; font-weight:600; margin-top:0.25rem; }
    .foodwise-hero p { font-size:1.05rem; opacity:0.9; }
    .stButton>button {
        background:#FF6F61; color:white; border-radius:12px; padding:0.6rem 1rem;
        border:0; font-weight:600; transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background:#FF4A3C; transform: scale(1.05);
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
            '<h3>AI‑Powered Food Waste Reduction & Sharing</h3>'
            '<p>Turn leftovers into recipes, plan meals precisely, and share surplus with your community.</p>'
            '</div>', unsafe_allow_html=True)

# ---------------------- NAV TABS ----------------------
tabs = st.tabs(["🏠 Home", "🥘 Recipes", "📅 Planner", "🤝 Sharing Hub", "⭐ Favorites"])

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
        ingredients_quick = st.text_input("Enter leftovers (comma-separated)", key="home_ing", 
                                         placeholder="e.g., chicken, rice, carrots")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Suggest Recipes", key="home_btn", use_container_width=True):
                if ingredients_quick.strip():
                    items = [x.strip() for x in ingredients_quick.split(",") if x.strip()]
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
                            
                            <div class="recipe-card">
                            <h4>🍚 {base[0].title()} & {base[1].title()} Fried Rice</h4>
                            <p><strong>Ingredients:</strong> {', '.join(base)}, rice, eggs, scallions</p>
                            <p><strong>Time:</strong> 25 minutes | <strong>Difficulty:</strong> Medium</p>
                            </div>
                            
                            <div class="recipe-card">
                            <h4>🍲 Hearty {base[0].title()} Soup</h4>
                            <p><strong>Ingredients:</strong> {', '.join(base)}, broth, herbs, potatoes</p>
                            <p><strong>Time:</strong> 35 minutes | <strong>Difficulty:</strong> Easy</p>
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


import streamlit as st

# ---------------------- RECIPE DATABASE ----------------------
# You can expand this list up to 50+ recipes easily
RECIPE_TEMPLATES = [
    {
        "name": "Quick Stir-Fry",
        "ingredients": "{main}, {secondary}, soy sauce, garlic, oil",
        "instructions": [
            "Heat oil in a pan",
            "Add garlic and sauté",
            "Add {main} and stir fry",
            "Add soy sauce and serve hot"
        ],
        "time_offset": -10
    },
    {
        "name": "{main} {secondary} Wraps",
        "ingredients": "{main}, {secondary}, tortillas, spices, yogurt",
        "instructions": [
            "Cook {main} and {secondary} with spices",
            "Warm tortillas",
            "Fill tortillas with mixture",
            "Add yogurt and roll up"
        ],
        "time_offset": 0
    },
    {
        "name": "Hearty {main} Soup",
        "ingredients": "{main}, {secondary}, {extra}, broth, herbs, potatoes",
        "instructions": [
            "Sauté {main} and veggies",
            "Add broth and potatoes",
            "Simmer for 20 minutes",
            "Add herbs and serve"
        ],
        "time_offset": +5
    },
    {
        "name": "Creamy {main} Pasta",
        "ingredients": "{main}, pasta, cream, cheese, garlic, herbs",
        "instructions": [
            "Boil pasta until al dente",
            "Cook {main} with garlic",
            "Add cream and cheese to pan",
            "Mix pasta and sauce, serve with herbs"
        ],
        "time_offset": +15
    },
    {
        "name": "{main} Fried Rice",
        "ingredients": "{main}, rice, soy sauce, spring onions, egg (optional)",
        "instructions": [
            "Heat oil in wok",
            "Add {main} and stir fry",
            "Add cooked rice and soy sauce",
            "Garnish with spring onions and serve"
        ],
        "time_offset": +5
    },
    {
        "name": "Spicy {main} Curry",
        "ingredients": "{main}, onion, tomato, curry spices, coconut milk",
        "instructions": [
            "Cook onion and tomato with spices",
            "Add {main} and stir well",
            "Pour coconut milk and simmer",
            "Serve with rice or naan"
        ],
        "time_offset": +20
    },
    {
        "name": "{main} Tacos",
        "ingredients": "{main}, tortillas, salsa, lettuce, cheese",
        "instructions": [
            "Cook {main} with spices",
            "Warm tortillas",
            "Fill with {main}, salsa, lettuce, cheese",
            "Serve with lime wedges"
        ],
        "time_offset": 0
    },
    {
        "name": "Cheesy {main} Casserole",
        "ingredients": "{main}, cheese, cream, breadcrumbs, herbs",
        "instructions": [
            "Preheat oven to 180°C",
            "Mix {main} with cream and cheese",
            "Top with breadcrumbs",
            "Bake for 25 minutes"
        ],
        "time_offset": +25
    },
    {
        "name": "{main} {secondary} Salad Bowl",
        "ingredients": "{main}, {secondary}, lettuce, olive oil, dressing",
        "instructions": [
            "Chop {main} and {secondary}",
            "Mix with lettuce and dressing",
            "Top with olive oil",
            "Serve chilled"
        ],
        "time_offset": -5
    },
    {
        "name": "Golden {main} Omelette",
        "ingredients": "Eggs, {main}, onion, spices, cheese",
        "instructions": [
            "Beat eggs with spices",
            "Add {main} and onion",
            "Cook in pan until golden",
            "Sprinkle cheese and fold"
        ],
        "time_offset": -5
    }
    # 👉 Keep adding until you reach 50+ recipes
]

# ---------------------- STREAMLIT UI ----------------------
with st.container():
    st.subheader("🥘 Leftover Recipe Generator")
    st.markdown("Transform your leftover ingredients into delicious meals!")

    c1, c2 = st.columns([2,1])
    with c1:
        ingredients = st.text_input("📝 Ingredients (comma-separated)", key="rec_ing", 
                                   placeholder="e.g., chicken, rice, carrots, potatoes")
        diet = st.selectbox("Diet preference", ["Any", "Vegetarian", "Vegan", "Gluten-free", "Dairy-free"])
        time_limit = st.slider("Max cooking time (minutes)", 10, 120, 30)
        difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], value="Easy")

        if st.button("🔍 Generate Recipes", key="rec_btn", use_container_width=True):
            if ingredients.strip():
                items = [x.strip() for x in ingredients.split(",") if x.strip()]
                if not items:
                    st.warning("Please enter at least one valid ingredient.")
                else:
                    base = items[:3] if len(items) >= 3 else items + ["veggies", "spices"][len(items):]
                    tag = "" if diet=="Any" else f" · {diet}"

                    st.success("🎉 Here are your personalized recipe suggestions!")

                    # Generate all recipes dynamically
                    for i, recipe in enumerate(RECIPE_TEMPLATES, start=1):
                        name = recipe["name"].format(
                            main=base[0].title(),
                            secondary=base[1].title() if len(base) > 1 else "Veggies",
                            extra=base[2].title() if len(base) > 2 else "Spices"
                        )
                        ingredients_text = recipe["ingredients"].format(
                            main=base[0], 
                            secondary=base[1] if len(base) > 1 else "veggies",
                            extra=base[2] if len(base) > 2 else "spices"
                        )
                        instructions_text = "\n".join(
                            [f"{j+1}. {step.format(main=base[0], secondary=base[1] if len(base)>1 else 'veggies')}" 
                             for j, step in enumerate(recipe["instructions"])]
                        )

                        with st.expander(f"{name}", expanded=(i==1)):
                            st.markdown(f"""
                            **Ingredients:** {ingredients_text}  
                            **Instructions:**  
                            {instructions_text}

                            **Time:** {time_limit + recipe['time_offset']} minutes  
                            **Difficulty:** {difficulty}{tag}
                            """)
                            if st.button("⭐ Save Recipe", key=f"save_{i}"):
                                st.session_state.favorite_recipes.append({
                                    "name": name,
                                    "ingredients": ingredients_text,
                                    "instructions": instructions_text,
                                    "time": f"{time_limit + recipe['time_offset']} minutes",
                                    "difficulty": difficulty
                                })
                                st.success("Recipe saved to favorites!")

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
        - API integration with Spoonacular for real recipes  
        - Nutritional information  
        - Step-by-step cooking instructions  
        """)


# ---------------------- PLANNER ----------------------
with tabs[2]:
    st.subheader("📅 Smart Food Planner")
    st.caption("Estimate ingredient quantities based on number of people and plan your meals.")
    
    # Meal planning section
    st.markdown("### 🍽️ Weekly Meal Planner")
    
    # Create a simple weekly planner
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    meals = ["Breakfast", "Lunch", "Dinner"]
    
    planner_cols = st.columns(7)
    for i, day in enumerate(days):
        with planner_cols[i]:
            st.markdown(f"**{day}**")
            for meal in meals:
                st.session_state.meal_plan[day][meal] = st.text_input(
                    f"{meal}", 
                    value=st.session_state.meal_plan[day][meal],
                    key=f"{day}_{meal}"
                )
    
    # Quantity calculator
    st.markdown("### 📊 Quantity Calculator")
    dish = st.text_input("Dish name", value="Veg Fried Rice")
    people = st.number_input("Number of people", 1, 100, 4, step=1)
    
    # Simple baseline per-person grams (demo values)
    baseline = {
        "rice (g)": 90, "mixed veggies (g)": 120, "oil (tbsp)": 0.75, 
        "spices (tsp)": 1.0, "salt (tsp)": 0.5, "protein (g)": 100
    }
    
    if st.button("Calculate quantities", key="plan_btn", use_container_width=True):
        rows = []
        for k, v in baseline.items():
            qty = v * people
            rows.append({"Ingredient": k, "Per Person": v, "Total Quantity": round(qty, 2)})
        
        df = pd.DataFrame(rows)
        st.write(f"**Plan for:** {people} people · **Dish:** {dish}")
        st.dataframe(df, use_container_width=True)
        
        # Shopping list generator
        st.download_button(
            label="📥 Download Shopping List",
            data=df.to_csv(index=False),
            file_name="shopping_list.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.caption("Adjust baseline amounts as needed for your recipes.")

# ---------------------- SHARING HUB ----------------------
with tabs[3]:
    st.subheader("🤝 Share, Sell, or Donate Surplus")
    st.caption("Connect with your community to reduce food waste together")
    
    mode = st.radio("I want to:", ["Donate", "Sell"], horizontal=True)
    
    colA, colB = st.columns(2)
    with colA:
        item = st.text_input("Item name", value="Cooked rice (sealed)")
        qty = st.text_input("Quantity / units", value="2 boxes")
        expiry = st.date_input("Expiry date", min_value=datetime.today(), 
                              value=datetime.today() + timedelta(days=2))
        location = st.text_input("Location / Area", value="Campus Block A")
        contact = st.text_input("Contact (phone/email)", value="example@iitj.ac.in")
    
    with colB:
        dietary_info = st.multiselect("Dietary information", 
                                     ["Vegetarian", "Vegan", "Gluten-free", "Dairy-free", "Contains nuts"])
        notes = st.text_area("Additional notes")
        price = None
        if mode == "Sell":
            price = st.number_input("Price (₹)", min_value=0, value=50, step=5)
    
    if st.button("Add listing", key="share_btn", use_container_width=True):
        # Validate inputs
        if not all([item, qty, location, contact]):
            st.error("Please fill in all required fields")
        else:
            st.session_state.shared_items.append({
                "mode": mode, 
                "item": item, 
                "qty": qty, 
                "expiry": expiry.strftime("%Y-%m-%d"),
                "dietary": ", ".join(dietary_info) if dietary_info else "None",
                "location": location, 
                "contact": contact, 
                "price": price if mode=="Sell" else "Free", 
                "notes": notes,
                "date_posted": datetime.today().strftime("%Y-%m-%d")
            })
            st.success("Listing added successfully! ✅")
    
    if st.session_state.shared_items:
        st.markdown("### 📋 Current Listings")
        
        for i, item in enumerate(st.session_state.shared_items):
            with st.expander(f"{item['item']} - {item['location']} ({item['mode']})", expanded=i==0):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Quantity:** {item['qty']}")
                    st.write(f"**Expiry:** {item['expiry']}")
                    st.write(f"**Dietary:** {item['dietary']}")
                with col2:
                    st.write(f"**Location:** {item['location']}")
                    st.write(f"**Contact:** {item['contact']}")
                    st.write(f"**Price:** {item['price']}")
                
                if item['notes']:
                    st.info(f"**Notes:** {item['notes']}")
                
                if st.button("Remove Listing", key=f"remove_{i}"):
                    st.session_state.shared_items.pop(i)
                    st.experimental_rerun()
        
        st.caption("For production, save to a database (e.g., SQLite/Google Sheet) and add maps/filters.")
    else:
        st.info("No listings yet. Add one above to get started!")

# ---------------------- FAVORITES ----------------------
with tabs[4]:
    st.subheader("⭐ Favorite Recipes")
    
    if st.session_state.favorite_recipes:
        st.success("Your saved recipes:")
        
        for i, recipe in enumerate(st.session_state.favorite_recipes):
            with st.expander(f"{recipe['name']} - {recipe['time']} - {recipe['difficulty']}", expanded=i==0):
                st.write(f"**Ingredients:** {recipe['ingredients']}")
                st.write(f"**Instructions:**")
                st.write(recipe['instructions'].replace('\n', '  \n'))
                
                if st.button("Remove from Favorites", key=f"remove_recipe_{i}"):
                    st.session_state.favorite_recipes.pop(i)
                    st.experimental_rerun()
    else:
        st.info("You haven't saved any recipes yet. Generate some recipes and click the ⭐ button to save them!")
        
        # Add some sample recipes to get started
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
st.markdown("<div style='text-align: center; color: #666;'>"
            "FoodWise ♻️ · Reduce Food Waste · Help Your Community · Save Money"
            "</div>", unsafe_allow_html=True)
