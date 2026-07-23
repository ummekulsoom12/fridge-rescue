# 🥘 Fridge Rescue

**Fridge Rescue** turns whatever random ingredients you have at home into a real, cookable recipe — instantly. Type what's in your fridge, or snap a photo of it, and AI figures out what to make, scaled to how many people you're feeding and tailored to your dietary needs, time limit, and spice preference.

**Who it's for:** students, young professionals, and anyone managing their own meals who's ever opened the fridge, stared at a random mix of leftovers and half-used ingredients, and had no idea what to cook. Instead of ordering takeout, wasting food, or eating something boring out of laziness, Fridge Rescue gives a fast, realistic answer to *"what can I actually make with this?"* — without assuming you have a fully stocked pantry like most recipe websites do.

## 🔗 Live App

**[https://fridge-rescue-ummekulsoom.streamlit.app/](https://fridge-rescue-ummekulsoom.streamlit.app/)**

## ✨ Features

- **🍳 Cook Now** — type whatever ingredients you have, comma-separated, and get a full recipe back
- **🎲 Surprise Me** — don't want to decide? Generates a recipe from a random pantry combination
- **📸 Snap & Cook** — upload a photo of your fridge or pantry, and AI identifies the ingredients visible in the photo automatically, which you can then edit before generating
- **✨ For You (personalized recommendations)** — once you've saved a few favorites, this analyzes them and suggests a brand-new recipe in a similar style/flavor profile you haven't tried yet
- **⭐ Favorites** — save any recipe you loved with one click, stored permanently in a real database
- **📖 Recipe history** — every recipe generated is automatically saved and browsable later
- **Custom preferences** — dietary restrictions (vegetarian, vegan, halal, no dairy, no nuts, low carb), spice level, available cooking time, and number of servings, all applied to every recipe generated
- **Familiar dish recognition** — the AI is specifically instructed to recognize and name real, familiar dishes (biryani, pulao, khow suey, karahi, curry, etc.) rather than giving vague, generic descriptions, whenever the ingredients reasonably fit
- **Persistent storage** — favorites and history are stored in a real Postgres database (Supabase), so they survive page refreshes and are never lost when the session ends
- **Clean tabbed interface** — Cook Now, Snap & Cook, For You, and My Recipes are organized into separate tabs so the experience never feels cluttered or mixed together

## 🤖 The AI Feature

Fridge Rescue uses **Google Gemini** (`gemini-3.1-flash-lite`) in two distinct ways:

### 1. Vision-based ingredient detection
When a user uploads a photo, the image is sent directly to Gemini along with this instruction:

> *"List only the edible food ingredients you can clearly see in this image, as a simple comma-separated list. Do not include any explanation, just the list."*

This lets the app understand a real photo of a fridge or pantry and turn it into usable ingredient data without the user typing anything.

### 2. Recipe generation with personalization
The core recipe-generation prompt instructs the model to act as a home cooking assistant with specific knowledge of South Asian and Southeast Asian cuisine:

> *"You are a friendly, practical home cooking assistant who is especially knowledgeable about South Asian and Southeast Asian home cooking (e.g. biryani, pulao, karahi, khow suey, haleem, nihari, hotpot, curry, fried rice, noodles) as well as familiar everyday dishes. A user has these ingredients available: {ingredients}. Dietary restrictions to respect: {diet}. Time available to cook: {time_limit}. Preferred spice level: {spice}. Number of people to cook for: {servings}. Suggest ONE realistic recipe they can make mostly using these ingredients... Whenever the ingredients reasonably allow it, prefer suggesting a recognizable, familiar dish by its real name rather than a generic description..."*

The **"For You"** feature reuses this same model but with an entirely different prompt — instead of ingredients, it feeds the AI a summary of the user's previously favorited recipes and asks it to generate something new in a similar style:

> *"Based on a user's favorite past recipes: {fav_titles}, and ingredients they've enjoyed before: {fav_ingredients}, suggest ONE new recipe idea in a similar style/cuisine/flavor profile that they haven't tried yet... Include a one-line note explaining why it fits their taste based on their favorites."*

This makes the personalization genuine — the model is reasoning about taste patterns, not just repeating a static list.

## 🛠️ Tools, Services, and Models Used

| Tool | Purpose |
|---|---|
| **Streamlit** | Python web framework used to build the entire UI |
| **Google Gemini API** (`gemini-3.1-flash-lite`) | Powers both text-based recipe generation and image-based ingredient detection |
| **Supabase** | Free hosted Postgres database used for persistent storage of recipe history and favorites |
| **Pillow (PIL)** | Handles the uploaded image before sending it to Gemini |
| **Streamlit Community Cloud** | Free hosting for the live deployed app |
| **PyCharm** | Code editor used to build the project |
| **GitHub** | Version control and public code hosting |

## 📸 Screenshots

*(Add your screenshots below — drag and drop directly into this file when editing on GitHub, or reference an `/screenshots` folder)*

**1. Cook Now — typing ingredients and generating a recipe**
![Cook Now tab](screenshots/cook-now.png)

**2. Snap & Cook — detecting ingredients from a fridge photo**
![Snap and Cook tab](screenshots/snap-and-cook.png)

**3. For You — a personalized recommendation based on favorites**
![For You tab](screenshots/for-you.png)

**4. My Recipes — favorites and history**
![My Recipes tab](screenshots/my-recipes.png)

## ⚙️ How to Run This Project Locally

1. **Clone the repository**
   ```bash
   git clone https://github.com/ummekulsoom12/fridge-rescue.git
   cd fridge-rescue
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your environment variables**

   You'll need three keys:
   - A free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)
   - A free Supabase project (URL + publishable key) from [supabase.com](https://supabase.com)

   Create the following table in your Supabase project's SQL editor:
   ```sql
   create table recipes (
     id bigint generated always as identity primary key,
     title text not null,
     content text not null,
     ingredients text,
     is_favorite boolean default false,
     created_at timestamp with time zone default now()
   );
   ```

   Then set these environment variables in your terminal:
   ```bash
   # Windows (PowerShell)
   $env:GEMINI_API_KEY="your_gemini_key"
   $env:SUPABASE_URL="your_supabase_url"
   $env:SUPABASE_KEY="your_supabase_publishable_key"

   # macOS/Linux
   export GEMINI_API_KEY="your_gemini_key"
   export SUPABASE_URL="your_supabase_url"
   export SUPABASE_KEY="your_supabase_publishable_key"
   ```

4. **Run the app**
   ```bash
   streamlit run app.py
   ```

   It will open automatically at `http://localhost:8501`

## 📝 Notes

- Since this app has no login/authentication system, favorites and recipe history are shared across everyone who uses the deployed app — it functions as a communal recipe board rather than individual private accounts. This was a deliberate scope decision to keep the project focused; adding real per-user accounts would be a natural next step.
- API keys and database credentials are never committed to this repository. They are provided via environment variables locally, and via Streamlit Cloud's secrets manager in production.
