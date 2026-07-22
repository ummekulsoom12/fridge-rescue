import streamlit as st
from google import genai
import os
import random

st.set_page_config(page_title="Fridge Rescue", page_icon="🥘", layout="wide")

# ---- Custom styling ----
st.markdown("""
    <style>
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #6b5d52;
        margin-top: 0;
    }
    .recipe-card {
        background-color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid #FFE0D0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# ---- Session state setup ----
if "history" not in st.session_state:
    st.session_state.history = []

# ---- API setup ----
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("API key not found. Please set the GEMINI_API_KEY environment variable.")
    st.stop()

client = genai.Client(api_key=api_key)
MODEL_NAME = "gemini-3.1-flash-lite"

# ---- Sidebar: preferences + history ----
with st.sidebar:
    st.header("⚙️ Your Preferences")
    diet = st.multiselect(
        "Dietary restrictions",
        ["Vegetarian", "Vegan", "No dairy", "No nuts", "Halal", "Low carb"],
    )
    time_limit = st.select_slider(
        "How much time do you have?",
        options=["10 min", "20 min", "30 min", "45+ min"],
        value="20 min"
    )
    spice = st.select_slider(
        "Spice level",
        options=["Mild", "Medium", "Spicy", "Very Spicy"],
        value="Medium"
    )
    servings = st.number_input(
        "How many people are you cooking for?",
        min_value=1,
        max_value=15,
        value=2,
        step=1
    )

    st.markdown("---")
    st.header("📜 Recipe History")
    if not st.session_state.history:
        st.caption("No recipes yet this session.")
    else:
        for i, past in enumerate(reversed(st.session_state.history)):
            with st.expander(f"{past['title']}"):
                st.markdown(past["text"])

# ---- Main hero section ----
st.markdown('<p class="main-title">🥘 Fridge Rescue</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Got random ingredients and no idea what to cook? Tell me what\'s in your fridge, and I\'ll turn it into a real meal.</p>', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    ingredients = st.text_area(
        "What ingredients do you have?",
        placeholder="e.g. eggs, rice, leftover chicken, onion",
        height=100
    )
with col2:
    st.write("")
    st.write("")
    surprise = st.button("🎲 Surprise Me", use_container_width=True)
    generate = st.button("🍳 Rescue My Fridge", type="primary", use_container_width=True)

if surprise:
    pantry_pool = [
        "eggs, spinach, feta cheese", "rice, black beans, corn, lime",
        "pasta, garlic, canned tomatoes", "potatoes, cheese, chives",
        "tofu, soy sauce, broccoli", "leftover roast chicken, tortillas, salsa"
    ]
    ingredients = random.choice(pantry_pool)
    st.info(f"Surprise ingredients: **{ingredients}**")
    generate = True

if generate:
    if not ingredients or not ingredients.strip():
        st.warning("Please enter at least a few ingredients first.")
    else:
        with st.spinner("Cooking up an idea..."):
            prompt = f"""You are a friendly, practical home cooking assistant who is especially
knowledgeable about South Asian and Southeast Asian home cooking (e.g. biryani, pulao, karahi,
khow suey, haleem, nihari, hotpot, curry, fried rice, noodles) as well as familiar everyday dishes.

A user has these ingredients available: {ingredients}.
Dietary restrictions to respect: {', '.join(diet) if diet else 'none'}.
Time available to cook: {time_limit}.
Preferred spice level: {spice}.
Number of people to cook for: {servings}.

Suggest ONE realistic recipe they can make mostly using these ingredients, that fits their time
limit and respects their dietary restrictions. Whenever the ingredients reasonably allow it,
prefer suggesting a recognizable, familiar dish by its real name (for example: chicken biryani,
vegetable pulao, khow suey, beef karahi, egg fried rice, chicken hotpot, lentil curry) rather than
a generic description. If the ingredients don't fit any well-known dish, it's fine to create a
simple original recipe instead.

Scale the ingredient quantities appropriately for {servings} people.

If something essential is missing (like oil, salt, or a basic pantry item), assume they have it.
If a key ingredient is missing, suggest a reasonable substitution.

Format your response with:
- A short, appetizing recipe name as a markdown heading (##) — use the real dish name if applicable
- Ingredients list scaled for {servings} people (mark anything not in their list as 'you may need to add')
- Simple numbered steps
- Keep it friendly and encouraging in tone."""

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            recipe_text = response.text

            title_line = next((line for line in recipe_text.split("\n") if line.strip().startswith("#")), "Your Recipe")
            title_clean = title_line.replace("#", "").strip()

            st.session_state.history.append({"title": title_clean, "text": recipe_text})

            st.markdown('<div class="recipe-card">', unsafe_allow_html=True)
            st.markdown(recipe_text)
            st.markdown('</div>', unsafe_allow_html=True)