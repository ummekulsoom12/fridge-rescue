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
    .subtitle { font-size: 1.1rem; color: #6b5d52; margin-top: 0; margin-bottom: 1.5rem; }
    .recipe-card {
        background-color: #FFFFFF; padding: 1.5rem; border-radius: 16px;
        border: 1px solid #FFE0D0; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-top: 1rem;
    }
    .section-hint {
        background-color: #FFF3EC; padding: 0.9rem 1.2rem; border-radius: 12px;
        border-left: 4px solid #FF6B4A; margin-bottom: 1.2rem; color: #6b5d52;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 48px; border-radius: 10px 10px 0 0; padding: 0 20px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# ---- API setup ----
gemini_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
supabase_url = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

if not gemini_key or not supabase_url or not supabase_key:
    st.error("Missing environment variables. Please set GEMINI_API_KEY, SUPABASE_URL, and SUPABASE_KEY.")
    st.stop()

client = genai.Client(api_key=gemini_key)
MODEL_NAME = "gemini-3.1-flash-lite"
supabase = create_client(supabase_url, supabase_key)

if "detected_ingredients" not in st.session_state:
    st.session_state.detected_ingredients = ""
if "manual_ingredients" not in st.session_state:
    st.session_state.manual_ingredients = ""

# ---- Helper functions ----
def save_recipe(title, content, ingredients_text):
    result = supabase.table("recipes").insert({
        "title": title, "content": content,
        "ingredients": ingredients_text, "is_favorite": False
    }).execute()
    return result.data[0]["id"]

def get_recent_recipes(limit=10):
    return supabase.table("recipes").select("*").order("created_at", desc=True).limit(limit).execute().data

def get_favorites():
    return supabase.table("recipes").select("*").eq("is_favorite", True).order("created_at", desc=True).execute().data

def mark_favorite(recipe_id):
    supabase.table("recipes").update({"is_favorite": True}).eq("id", recipe_id).execute()

def build_recipe_prompt(ingredients, diet, time_limit, spice, servings):
    return f"""You are a friendly, practical home cooking assistant who is especially
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

def generate_and_display(ingredients, diet, time_limit, spice, servings):
    with st.spinner("Cooking up an idea..."):
        prompt = build_recipe_prompt(ingredients, diet, time_limit, spice, servings)
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        recipe_text = response.text
        title_line = next((l for l in recipe_text.split("\n") if l.strip().startswith("#")), "Your Recipe")
        title_clean = title_line.replace("#", "").strip()
        recipe_id = save_recipe(title_clean, recipe_text, ingredients)

        st.session_state.last_recipe_id = recipe_id
        st.session_state.last_recipe_text = recipe_text
        st.session_state.last_recipe_saved_as_fav = False

def render_last_recipe(location):
    if "last_recipe_id" in st.session_state and st.session_state.last_recipe_id:
        st.markdown('<div class="recipe-card">', unsafe_allow_html=True)
        st.markdown(st.session_state.last_recipe_text)

        if st.session_state.get("last_recipe_saved_as_fav"):
            st.success("Saved to your Favorites! ⭐")
        else:
            if st.button("⭐ Save as Favorite", key=f"savefav_{location}_{st.session_state.last_recipe_id}"):
                mark_favorite(st.session_state.last_recipe_id)
                st.session_state.last_recipe_saved_as_fav = True
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# ---- Sidebar: ONLY preferences ----
with st.sidebar:
    st.header("⚙️ Your Preferences")
    st.caption("Applied to every recipe, no matter how you enter ingredients.")
    diet = st.multiselect("Dietary restrictions", ["Vegetarian", "Vegan", "No dairy", "No nuts", "Halal", "Low carb"])
    time_limit = st.select_slider("How much time do you have?", options=["10 min", "20 min", "30 min", "45+ min"], value="20 min")
    spice = st.select_slider("Spice level", options=["Mild", "Medium", "Spicy", "Very Spicy"], value="Medium")
    servings = st.number_input("How many people are you cooking for?", min_value=1, max_value=15, value=2, step=1)

# ---- Hero ----
st.markdown('<p class="main-title">🥘 Fridge Rescue</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Got random ingredients and no idea what to cook? Pick how you want to tell me what you have.</p>', unsafe_allow_html=True)

# ---- Tabs ----
tab_cook, tab_photo, tab_foryou, tab_recipes = st.tabs(
    ["🍳 Cook Now", "📸 Snap & Cook", "✨ For You", "📖 My Recipes"]
)

# ===== TAB 1: Cook Now =====
with tab_cook:
    st.markdown('<div class="section-hint">Type what you have, or hit Surprise Me if you\'d rather not decide.</div>', unsafe_allow_html=True)

    ingredients = st.text_area(
        "What ingredients do you have?",
        value=st.session_state.manual_ingredients,
        placeholder="e.g. eggs, rice, leftover chicken, onion",
        height=100,
        key="cook_now_input"
    )

    col1, col2 = st.columns(2)
    with col1:
        surprise = st.button("🎲 Surprise Me", use_container_width=True)
    with col2:
        generate = st.button("🍳 Rescue My Fridge", type="primary", use_container_width=True)

    if surprise:
        pantry_pool = [
            "eggs, spinach, feta cheese", "rice, black beans, corn, lime",
            "pasta, garlic, canned tomatoes", "potatoes, cheese, chives",
            "tofu, soy sauce, broccoli", "leftover roast chicken, tortillas, salsa"
        ]
        ingredients = random.choice(pantry_pool)
        st.info(f"Surprise ingredients: **{ingredients}**")
        generate_and_display(ingredients, diet, time_limit, spice, servings)
    elif generate:
        if not ingredients or not ingredients.strip():
            st.warning("Please enter at least a few ingredients first.")
        else:
            generate_and_display(ingredients, diet, time_limit, spice, servings)

    render_last_recipe("cook")
# ===== TAB 2: Snap & Cook =====
with tab_photo:
    st.markdown('<div class="section-hint">Upload a photo of your fridge or pantry, and I\'ll figure out what\'s in it for you.</div>', unsafe_allow_html=True)

    uploaded_image = st.file_uploader("Upload a photo", type=["jpg", "jpeg", "png"])

    if uploaded_image is not None:
        img_col, btn_col = st.columns([1, 2])
        with img_col:
            st.image(uploaded_image, width=250)
        with btn_col:
            st.write("")
            if st.button("🔍 Detect Ingredients from Photo"):
                with st.spinner("Looking at your photo..."):
                    img = Image.open(uploaded_image)
                    vision_prompt = "List only the edible food ingredients you can clearly see in this image, as a simple comma-separated list. Do not include any explanation, just the list."
                    vision_response = client.models.generate_content(model=MODEL_NAME, contents=[vision_prompt, img])
                    st.session_state.detected_ingredients = vision_response.text.strip()

    if st.session_state.detected_ingredients:
        st.success(f"Detected: {st.session_state.detected_ingredients}")
        edited = st.text_area("Edit detected ingredients if needed:", value=st.session_state.detected_ingredients, height=80)
        if st.button("🍳 Rescue My Fridge (from photo)", type="primary"):
            generate_and_display(edited, diet, time_limit, spice, servings)

    render_last_recipe("photo")
# ===== TAB 3: For You =====
with tab_foryou:
    st.markdown('<div class="section-hint">Once you\'ve saved a few favorites, I\'ll use them to suggest something new that matches your taste.</div>', unsafe_allow_html=True)

    favs = get_favorites()
    if not favs:
        st.info("You haven't saved any favorites yet — go save a few recipes you love in **My Recipes**, then come back here!")
    else:
        st.caption(f"Based on {len(favs)} saved favorite(s): " + ", ".join([f["title"] for f in favs]))
        if st.button("✨ Recommend Something For Me", type="primary"):
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
                recipe_id = save_recipe(title_clean, recipe_text, "(personalized recommendation)")

                st.session_state.last_recipe_id = recipe_id
                st.session_state.last_recipe_text = recipe_text
                st.session_state.last_recipe_saved_as_fav = False

    render_last_recipe("foryou")
# ===== TAB 4: My Recipes =====
with tab_recipes:
    fav_col, hist_col = st.columns(2)

    with fav_col:
        st.subheader("⭐ Favorites")
        favorites = get_favorites()
        if not favorites:
            st.caption("No favorites saved yet.")
        else:
            for fav in favorites:
                with st.expander(fav["title"]):
                    st.markdown(fav["content"])

    with hist_col:
        st.subheader("📜 Recent History")
        recent = get_recent_recipes(limit=10)
        if not recent:
            st.caption("No recipes yet.")
        else:
            for r in recent:
                with st.expander(r["title"]):
                    st.markdown(r["content"])
                    if not r["is_favorite"]:
                        if st.button("⭐ Save as Favorite", key=f"fav_{r['id']}"):
                            mark_favorite(r["id"])
                            st.rerun()