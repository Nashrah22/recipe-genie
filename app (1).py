import streamlit as st
import google.generativeai as genai
import os
import json
import html as html_lib

MODEL_NAME = "gemini-flash-lite-latest"

st.set_page_config(page_title="Recipe Genie", page_icon="🍳", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap');
:root { --bg: #0a0a0b; --ink: #f2efe6; --muted: #8c8c93; --card-border: #232327; --field-bg: #17171a; --cream: #f3eee2; --cream-ink: #17181a; --cream-muted: #6b6c72; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: var(--bg); color: var(--ink); }
#MainMenu, footer, header { visibility: hidden; }
.block-container { max-width: 780px; padding-top: 3rem; padding-bottom: 4rem; }
.kicker { text-align: center; font-size: 0.68rem; letter-spacing: 3px; text-transform: uppercase; color: var(--muted); font-weight: 600; margin-bottom: 0.8rem; }
.headline { font-family: 'Fraunces', serif; font-weight: 600; font-size: clamp(2.1rem, 5.6vw, 3.4rem); line-height: 1.06; text-align: center; color: var(--ink); max-width: 640px; margin: 0 auto 1.1rem auto; }
.subtitle { text-align: center; color: #a5a5ac; font-size: 0.94rem; line-height: 1.55; max-width: 460px; margin: 0 auto 2.6rem auto; }
.field-label { font-size: 0.66rem; letter-spacing: 2px; text-transform: uppercase; color: var(--muted); font-weight: 700; margin-bottom: 0.5rem; }
div[data-baseweb="textarea"] textarea, .stTextArea textarea { background-color: var(--field-bg) !important; color: var(--ink) !important; border: 1px solid var(--card-border) !important; border-radius: 10px !important; font-size: 0.92rem !important; }
div[data-baseweb="select"] > div { background-color: var(--field-bg) !important; border: 1px solid var(--card-border) !important; border-radius: 10px !important; color: var(--ink) !important; }
label { display: none !important; }
.stButton>button { background: var(--cream); color: var(--cream-ink); border: none; border-radius: 8px; padding: 0.68rem 1.6rem; font-size: 0.72rem; letter-spacing: 2px; text-transform: uppercase; font-weight: 700; transition: opacity 0.15s ease; }
.stButton>button:hover { opacity: 0.85; color: var(--cream-ink); }
.recipe-card { background: var(--cream); color: var(--cream-ink); border-radius: 20px; padding: 2.6rem 2.8rem; margin-top: 2.8rem; }
.recipe-kicker { font-size: 0.66rem; letter-spacing: 2.5px; text-transform: uppercase; color: #9a8c63; font-weight: 700; margin-bottom: 0.6rem; }
.recipe-title { font-family: 'Fraunces', serif; font-weight: 700; font-size: 2rem; line-height: 1.15; margin: 0 0 0.9rem 0; color: var(--cream-ink); }
.recipe-description { font-style: italic; color: var(--cream-muted); font-size: 1rem; line-height: 1.5; margin-bottom: 1.5rem; }
.recipe-meta { display: flex; flex-wrap: wrap; gap: 0.4rem 1.6rem; font-size: 0.72rem; letter-spacing: 1.5px; text-transform: uppercase; color: var(--cream-muted); font-weight: 600; border-top: 1px solid rgba(0,0,0,0.1); border-bottom: 1px solid rgba(0,0,0,0.1); padding: 0.9rem 0; margin-bottom: 1.8rem; }
.section-title { font-size: 0.7rem; letter-spacing: 2px; text-transform: uppercase; font-weight: 700; color: var(--cream-ink); margin: 1.8rem 0 0.9rem 0; padding-bottom: 0.4rem; border-bottom: 2px solid rgba(0,0,0,0.12); }
.ingredient-row { display: flex; justify-content: space-between; gap: 1rem; padding: 0.5rem 0; border-bottom: 1px dashed rgba(0,0,0,0.12); font-size: 0.94rem; color: var(--cream-ink); }
.ingredient-row:last-child { border-bottom: none; }
.step-row { display: flex; gap: 0.9rem; margin-bottom: 1.1rem; align-items: flex-start; }
.step-num { flex-shrink: 0; width: 26px; height: 26px; border-radius: 50%; background: var(--cream-ink); color: var(--cream); font-size: 0.76rem; font-weight: 700; display: flex; align-items: center; justify-content: center; }
.step-text { font-size: 0.95rem; line-height: 1.55; color: var(--cream-ink); padding-top: 2px; }
.tip-box { background: rgba(0,0,0,0.045); border-radius: 10px; padding: 1rem 1.2rem; font-size: 0.9rem; font-style: italic; color: var(--cream-muted); margin-top: 1.6rem; }
.notice { text-align: center; color: #7a7a82; font-size: 0.85rem; margin-top: 3rem; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

def get_api_key():
    key = os.environ.get("GEMINI_API_KEY", "")
    try:
        key = st.secrets.get("GEMINI_API_KEY", key)
    except Exception:
        pass
    return key

API_KEY = get_api_key()

st.markdown('<div class="kicker">What\'s in your kitchen?</div>', unsafe_allow_html=True)
st.markdown('<div class="headline">Make something good from what you have.</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Tell us what\'s already in your kitchen. We\'ll turn it into a practical recipe, with no unnecessary shopping list.</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1.6, 1])
with col1:
    st.markdown('<div class="field-label">Ingredients</div>', unsafe_allow_html=True)
    ingredients = st.text_area("ingredients", placeholder="2 eggs\ncheese\npotato", height=132, label_visibility="collapsed")
with col2:
    st.markdown('<div class="field-label">Servings</div>', unsafe_allow_html=True)
    servings = st.selectbox("servings", list(range(1, 13)), index=1, label_visibility="collapsed")
    st.markdown('<div class="field-label" style="margin-top:1.1rem;">Preference</div>', unsafe_allow_html=True)
    diet = st.selectbox("diet", ["No preference", "Vegetarian", "Vegan", "Keto", "Halal", "Gluten-free", "Dairy-free"], label_visibility="collapsed")

st.write("")
generate = st.button("Make the recipe")

def build_prompt(ingredients, servings, diet):
    return f"""You are a professional chef. Using primarily these ingredients: {ingredients}
(you may assume basic pantry staples like salt, oil, water are available, but do not
assume any other missing ingredient), create ONE practical, realistic recipe for
{servings} servings. Dietary preference: {diet}.

Return ONLY valid JSON, no markdown fences, no commentary, matching exactly this shape:

{{
  "title": "string, recipe name",
  "description": "string, one enticing sentence",
  "time_minutes": integer, total time in minutes,
  "difficulty": "Easy" or "Medium" or "Hard",
  "servings": {servings},
  "ingredients": ["quantity + ingredient", "..."],
  "instructions": ["step 1 text", "step 2 text", "..."],
  "tip": "string, one short chef's tip"
}}

Scale ingredient quantities correctly for {servings} servings. Keep instructions concise
and numbered implicitly by array order. Do not include any text outside the JSON object."""

def parse_recipe_json(raw_text):
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    return json.loads(text.strip())

def render_recipe(data):
    ingredients_html = "".join(f'<div class="ingredient-row"><span>{html_lib.escape(item)}</span></div>' for item in data.get("ingredients", []))
    steps_html = "".join(f'<div class="step-row"><div class="step-num">{i+1}</div><div class="step-text">{html_lib.escape(step)}</div></div>' for i, step in enumerate(data.get("instructions", [])))
    meta_parts = [f'{data.get("time_minutes", "?")} min', html_lib.escape(str(data.get("difficulty", ""))), f'{data.get("servings", "?")} servings']
    meta_html = "".join(f"<span>{p}</span>" for p in meta_parts)
    card = f"""
    <div class="recipe-card">
        <div class="recipe-kicker">Your Recipe</div>
        <div class="recipe-title">{html_lib.escape(data.get("title", "Recipe"))}</div>
        <div class="recipe-description">{html_lib.escape(data.get("description", ""))}</div>
        <div class="recipe-meta">{meta_html}</div>
        <div class="section-title">Ingredients</div>
        {ingredients_html}
        <div class="section-title">Instructions</div>
        {steps_html}
        <div class="tip-box">💡 {html_lib.escape(data.get("tip", ""))}</div>
    </div>
    """
    st.markdown(card, unsafe_allow_html=True)

if generate:
    if not API_KEY:
        st.markdown('<div class="notice">Recipe Genie isn\'t configured yet.<br>Add <code>GEMINI_API_KEY</code> to Streamlit secrets to enable it.</div>', unsafe_allow_html=True)
    elif not ingredients.strip():
        st.markdown('<div class="notice">Add a few ingredients above to get started.</div>', unsafe_allow_html=True)
    else:
        with st.spinner("Writing your recipe..."):
            try:
                genai.configure(api_key=API_KEY)
                model = genai.GenerativeModel(MODEL_NAME, generation_config=genai.GenerationConfig(response_mime_type="application/json"))
                prompt = build_prompt(ingredients, servings, diet)
                response = model.generate_content(prompt)
                data = parse_recipe_json(response.text)
                render_recipe(data)
            except json.JSONDecodeError:
                st.markdown('<div class="notice">The recipe came back in an unexpected format. Please try again.</div>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f'<div class="notice">Something went wrong: {html_lib.escape(str(e))}</div>', unsafe_allow_html=True)
