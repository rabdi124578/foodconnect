import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests

API_URL = "https://api-inference.huggingface.co/models/gpt2"
headers = {"Authorization": "Bearer YOUR_API_KEY"}  # replace with your token

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

data = query({"inputs": "Once upon a time in Jaipur,"})
print(data)


# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="FoodWise", page_icon="🍲", layout="wide")

# ---------------------- SESSION STATE ----------------------
if 'shared_items' not in st.session_state:
    st.session_state.shared_items = []
if 'favorite_recipes' not in st.session_state:
    st.session_state.favorite_recipes = []
if 'meal_plan' not in st.session_state:
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    meals = ["Breakfast", "Lunch", "Dinner"]
    st.session_state.meal_plan = {day: {meal: "" for meal in meals} for day in days}
if 'ai_recipes' not in st.session_state:
    st.session_state.ai_recipes = []

# ---------------------- THEME / STYLE ----------------------
st.markdown("""
<style>
.foodwise-hero h1 { color:#FF6F61; font-size: 3rem; margin-bottom:0; }
.foodwise-hero h3 { color:#22C55E; font-weight:600; margin-top:0.25rem; }
.foodwise-hero p { font-size:1.05rem; opacity:0.9; }
.stButton>button {
    background:#FF6F61; color:white; border-radius:12px; padding:0.6rem 1rem;
    border:0; font-weight:600; transition: all 0.3s ease;
}
.stButton>button:hover { background:#FF4A3C; transform: scale(1.05); }
.stTextInput>div>div>input, .stNumberInput>div>div>input, textarea { border:2px solid #22C55E; border-radius:10px; }
.pill { display:inline-block; padding:6px 10px; border-radius:999px; background:#F1F5F9; margin-right:8px; margin-bottom:8px; font-size:0.85rem; }
.recipe-card { border: 1px solid #E2E8F0; border-radius:12px; padding:1rem; margin-bottom:1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
.feature-card { background: #F8FAFC; border-radius:12px; padding:1.5rem; margin-bottom:1.5rem; }
</style>
""", unsafe_allow_html=True)

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
    st.markdown('<div class="feature-card">Reduce food waste, save money, and help your community by making the most of your food ingredients.</div>', unsafe_allow_html=True)
    
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
                    items = [x.strip() for x in ingredients_quick.split(",") if x.strip()]
                    base = items[:3] if len(items) >= 3 else items + ["veggies", "spices"][len(items):]
                    st.success("Here are some ideas:")
                    with st.expander("Recipe Suggestions", expanded=True):
                        for name in [f"{base[0].title()} Stir‑Fry", f"{base[0].title()} & {base[1].title()} Fried Rice", f"Hearty {base[0].title()} Soup"]:
                            st.markdown(f"<div class='recipe-card'><h4>🍳 {name}</h4></div>", unsafe_allow_html=True)
                else:
                    st.warning("Please enter at least one ingredient.")
        with col2:
            if st.button("Clear Input", key="clear_btn", use_container_width=True):
                st.session_state.home_ing = ""
                st.experimental_rerun()

# ---------------------- RECIPES ----------------------
# ---------------------- RECIPES (HUGGING FACE VERSION) ----------------------
import requests

# Hugging Face API config
HF_API_URL = "https://api-inference.huggingface.co/models/gpt2"  # change model if you like
HF_API_TOKEN = "YOUR_HF_API_TOKEN"  # replace with your token

headers = {
    "Authorization": f"Bearer {HF_API_TOKEN}"
}

def generate_hf_recipes(prompt):
    payload = {"inputs": prompt, "options": {"wait_for_model": True}}
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            text = data[0]['generated_text'] if isinstance(data, list) else str(data)
            return text
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Exception: {e}"

# ---------------------- RECIPES TAB ----------------------
with tabs[1]:
    st.subheader("🥘 Leftover Recipe Generator")
    st.markdown("Transform your leftover ingredients into delicious meals!")

    c1, c2 = st.columns([2,1])
    with c1:
        ingredients = st.text_input("📝 Enter ingredients (any language)", key="rec_ing", placeholder="e.g., chicken, rice, carrots")
        diet = st.selectbox("Diet preference", ["Any", "Vegetarian", "Vegan", "Gluten-free", "Dairy-free"])
        time_limit = st.slider("Max cooking time (minutes)", 10, 120, 30)
        difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], value="Easy")
        
        if st.button("🔍 Generate AI Recipes", key="ai_rec_btn", use_container_width=True):
            if ingredients.strip():
                prompt = f"""
Generate 3 recipes using these ingredients: {ingredients}.
Diet preference: {diet}.
Max cooking time: {time_limit} minutes.
Difficulty: {difficulty}.
Format as:
Recipe Name:
Ingredients:
Instructions:
Time:
Difficulty:
"""
                recipes_text = generate_hf_recipes(prompt)
                st.session_state.ai_recipes = recipes_text.split("\n\n")  # split by double line break
                st.success("🎉 Here are AI-generated recipes!")

        # Display Hugging Face AI-generated recipes
        if st.session_state.ai_recipes:
            for i, recipe in enumerate(st.session_state.ai_recipes):
                with st.expander(f"AI Recipe {i+1}", expanded=i==0):
                    st.markdown(f"<pre>{recipe}</pre>", unsafe_allow_html=True)
                    if st.button("⭐ Save Recipe", key=f"save_ai_{i}"):
                        st.session_state.favorite_recipes.append({
                            "name": f"AI Recipe {i+1}",
                            "ingredients": "From AI",
                            "instructions": recipe,
                            "time": f"{time_limit} min",
                            "difficulty": difficulty
                        })
                        st.success("Recipe saved to favorites!")

    with c2:
        st.info("💡 Tips for reducing food waste:")
        st.markdown("""
- Store leftovers properly in airtight containers
- Use older ingredients first when cooking
- Freeze leftovers you won't use immediately
- Understand date labels (best before vs use by)
""")
        st.info("🔮 Coming Soon:")
        st.markdown("""
- Nutritional info
- Step-by-step instructions
- AI auto-portion suggestions
""")

