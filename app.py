import streamlit as st
from google import genai
from PIL import Image
from supabase import create_client
import os
import random

st.set_page_config(page_title="Fridge Rescue", page_icon="🥘", layout="wide")

# ---- Custom styling ----
st.markdown("""
    <style>
    .main-title { font-size: 3rem; font-weight: 800; margin-bottom: 0; }
    .subtitle { font-size: 1.1rem; color: #6b5d52; margin-top: 0; }
    .recipe-card {
        background-color: #FFFFFF; padding: 1.5rem; border-radius: 16px;
        border: 1px solid #FFE0D0; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# ---- API setup ----
gemini_key = os.environ.get("GEMINI_API_KEY")
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

if not gemini_key or not supabase_url or not supabase_key:
    st.error("Missing environment variables. Please set GEMINI_API_KEY, SUPABASE_URL, and SUPABASE_KEY.")
    st.stop()

client = genai.Client(api_key=gemini_key)
MODEL_NAME = "gemini-3.1-flash-lite"
supabase = create_client(supabase_url, supabase_key)

# ---- Helper functions ----
def save_recipe(title, content, ingredients_text):
    supabase.table("recipes").insert({
        "title": title,
        "content": content,
        "ingredients": ingredients_text,
        "is_favorite": False
    }).execute()

def get_recent_recipes(limit=5):
    result = supabase.table("recipes").select("*").order("created_at", desc=True).limit(limit).execute()
    return result.data

def get_favorites():
    result = supabase.table("recipes").select("*").eq("is_favorite", True).order("created_at", desc=True).execute()
    return result.data

def mark_favorite(recipe_id):
    supabase.table("recipes").update({"is_favorite": True}).eq("id", recipe_id).execute()

# ---- Sidebar: preferences + history + favorites ----
with st.sidebar:
    st.header("⚙️ Your Preferences")
    diet = st.multiselect("Dietary restrictions", ["Vegetarian", "Vegan", "No dairy", "No nuts", "Halal", "Low carb"])
    time_limit = st.select_slider("How much time do you have?", options=["10 min", "20 min", "30 min", "45+ min"], value="20 min")
    spice = st.select_slider("Spice level", options=["Mild", "Medium", "Spicy", "Very Spicy"], value="Medium")
    servings = st.number_input("How many people are you cooking for?", min_value=1, max_value=15, value=2, step=1)

    st.markdown("---")
    st.header("⭐ Favorites")
    favorites = get_favorites()
    if not favorites:
        st.caption("No favorites saved yet.")
    else:
        for fav in favorites:
            with st.expander(fav["title"]):
                st.markdown(fav["content"])

    st.markdown("---")
    st.header("📜 Recent History")
    recent = get_recent_recipes(limit=5)
    if not recent:
        st.caption("No recipes yet.")
    else:
        for r in recent:
            with st.expander(r["title"]):
                st.markdown(r["content"])
                if not r["is_favorite"]:
                    if st.button(f"⭐ Save as Favorite", key=f"fav_{r['id']}"):
                        mark_favorite(r["id"])
                        st.rerun()

# ---- Main hero section ----
st.markdown('<p class="main-title">🥘 Fridge Rescue</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Got random ingredients and no idea what to cook? Tell me what\'s in your fridge, and I\'ll turn it into a real meal.</p>', unsafe_allow_html=True)

# ---- Image-based ingredient detection ----
st.subheader("📸 Or upload a photo of your fridge/pantry")
uploaded_image = st.file_uploader("Upload a photo", type=["jpg", "jpeg", "png"])

if "detected_ingredients" not in st.session_state:
    st.session_state.detected_ingredients = ""

if uploaded_image is not None:
    st.image(uploaded_image, width=250)
    if st.button("🔍 Detect Ingredients from Photo"):
        with st.spinner("Looking at your photo..."):
            img = Image.open(uploaded_image)
            vision_prompt = "List only the edible food ingredients you can clearly see in this image, as a simple comma-separated list. Do not include any explanation, just the list."
            vision_response = client.models.generate_content(model=MODEL_NAME, contents=[vision_prompt, img])
            st.session_state.detected_ingredients = vision_response.text.strip()
            st.success(f"Detected: {st.session_state.detected_ingredients}")

# ---- Ingredient input + buttons ----
col1, col2 = st.columns([3, 1])
with col1:
    ingredients = st.text_area(
        "What ingredients do you have?",
        value=st.session_state.detected_ingredients,
        placeholder="e.g. eggs, rice, leftover chicken, onion",
        height=100
    )
with col2:
    st.write("")
    st.write("")
    surprise = st.button("🎲 Surprise Me", use_container_width=True)
    recommend = st.button("✨ Recommend For Me", use_container_width=True)
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

# ---- Personalized recommendation (based on favorites) ----
if recommend:
    favs = get_favorites()
    if not favs:
        st.warning("Save a few favorites first so I can learn your taste!")
    else:
        with st.spinner("Thinking of something you'd love..."):
            fav_titles = ", ".join([f["title"] for f in favs])
            fav_ingredients = ", ".join([f["ingredients"] or "" for f in favs])
            rec_prompt = f"""Based on a user's favorite past recipes: {fav_titles},
and ingredients they've enjoyed before: {fav_ingredients},
suggest ONE new recipe idea in a similar style/cuisine/flavor profile that they haven't tried yet.
Time available: {time_limit}. Servings: {servings}. Spice level: {spice}.
Dietary restrictions: {', '.join(diet) if diet else 'none'}.

Format with:
- A short recipe name as a markdown heading (##)
- Ingredients list
- Simple numbered steps
- A one-line note explaining why it fits their taste based on their favorites."""

            response = client.models.generate_content(model=MODEL_NAME, contents=rec_prompt)
            recipe_text = response.text
            title_line = next((l for l in recipe_text.split("\n") if l.strip().startswith("#")), "Recommended Recipe")
            title_clean = title_line.replace("#", "").strip()

            save_recipe(title_clean, recipe_text, "(personalized recommendation)")

            st.markdown('<div class="recipe-card">', unsafe_allow_html=True)
            st.markdown(recipe_text)
            st.markdown('</div>', unsafe_allow_html=True)

# ---- Main recipe generation ----
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

            response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
            recipe_text = response.text

            title_line = next((l for l in recipe_text.split("\n") if l.strip().startswith("#")), "Your Recipe")
            title_clean = title_line.replace("#", "").strip()

            save_recipe(title_clean, recipe_text, ingredients)

            st.markdown('<div class="recipe-card">', unsafe_allow_html=True)
            st.markdown(recipe_text)
            st.markdown('</div>', unsafe_allow_html=True)