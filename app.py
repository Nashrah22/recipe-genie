
import os
import json
import re
import html
import gradio as gr
from google import genai
from google.genai import types


MODEL = "gemini-3.5-flash"

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not configured.")

client = genai.Client(api_key=API_KEY)


def clean_ingredients(text):
    items = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        line = re.sub(r"^[•\-\*\d\.\)\s]+", "", line).strip()

        if line:
            items.append(line)

    return items


def safe(value):
    return html.escape(str(value or ""))


def generate_recipe(ingredients, servings, preference):
    items = clean_ingredients(ingredients)

    if not items:
        return (
            "<div class='error-box'>Please enter at least one ingredient.</div>"
        )

    ingredient_text = ", ".join(items)

    preference = preference.strip() if preference else "No special preference"

    prompt = f"""
You are a professional home-cooking recipe writer.

Create ONE practical recipe using the ingredients the user already has.

Available ingredients:
{ingredient_text}

Desired servings:
{servings}

Preference:
{preference}

Important rules:
- Use the available ingredients intelligently.
- You may include a small number of normal pantry staples such as salt, pepper, oil, water, garlic, or basic spices when appropriate.
- Do not invent unusual ingredients unnecessarily.
- The recipe must actually be cookable.
- Give realistic quantities.
- Keep the instructions clear and practical.
- Do not mention artificial intelligence, AI, language models, Gemini, prompts, or generation.
- Do not use emojis.
- Return ONLY valid JSON.
- Do not wrap the JSON in markdown.

Use exactly this JSON structure:

{{
  "title": "Recipe name",
  "description": "Short appetizing description",
  "time": "30 minutes",
  "difficulty": "Easy",
  "servings": "{servings}",
  "ingredients": [
    {{
      "item": "ingredient",
      "amount": "amount"
    }}
  ],
  "steps": [
    "Step one",
    "Step two",
    "Step three"
  ],
  "tips": [
    "Useful cooking tip"
  ],
  "substitutions": [
    {{
      "original": "ingredient",
      "replacement": "alternative"
    }}
  ]
}}
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7
            )
        )

        raw = response.text.strip()

        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        recipe = json.loads(raw)

        return render_recipe(recipe)

    except Exception as e:
        return f"""
        <div class="error-box">
            <strong>Something went wrong.</strong><br><br>
            {safe(e)}
        </div>
        """


def render_recipe(recipe):

    title = safe(recipe.get("title", "Your Recipe"))
    description = safe(recipe.get("description", ""))

    time = safe(recipe.get("time", ""))
    difficulty = safe(recipe.get("difficulty", ""))
    servings = safe(recipe.get("servings", ""))

    ingredients = recipe.get("ingredients", [])
    steps = recipe.get("steps", [])
    tips = recipe.get("tips", [])
    substitutions = recipe.get("substitutions", [])

    ingredient_html = ""

    for ingredient in ingredients:
        item = safe(ingredient.get("item", ""))
        amount = safe(ingredient.get("amount", ""))

        ingredient_html += f"""
        <div class="ingredient-row">
            <span>{item}</span>
            <span>{amount}</span>
        </div>
        """

    steps_html = ""

    for index, step in enumerate(steps, start=1):
        steps_html += f"""
        <div class="step-row">
            <div class="step-index">{index:02d}</div>
            <div class="step-content">{safe(step)}</div>
        </div>
        """

    tips_html = ""

    for tip in tips:
        tips_html += f"""
        <li>{safe(tip)}</li>
        """

    substitutions_html = ""

    for substitution in substitutions:
        original = safe(substitution.get("original", ""))
        replacement = safe(substitution.get("replacement", ""))

        substitutions_html += f"""
        <div class="swap-row">
            <span>{original}</span>
            <span class="swap-arrow">→</span>
            <span>{replacement}</span>
        </div>
        """

    if not substitutions_html:
        substitutions_html = """
        <div class="no-swaps">
            No substitutions needed.
        </div>
        """

    return f"""
    <article class="recipe-page">

        <div class="recipe-top">
            <div class="recipe-number">PANTRYPAL / RECIPE</div>
        </div>

        <header class="recipe-header">

            <h1>{title}</h1>

            <p class="recipe-description">
                {description}
            </p>

            <div class="recipe-facts">

                <div>
                    <span>TIME</span>
                    <strong>{time}</strong>
                </div>

                <div>
                    <span>LEVEL</span>
                    <strong>{difficulty}</strong>
                </div>

                <div>
                    <span>SERVES</span>
                    <strong>{servings}</strong>
                </div>

            </div>

        </header>

        <div class="recipe-divider"></div>

        <section class="recipe-grid">

            <div class="ingredients-column">

                <div class="small-heading">
                    INGREDIENTS
                </div>

                <div class="ingredient-list">
                    {ingredient_html}
                </div>

            </div>

            <div class="method-column">

                <div class="small-heading">
                    METHOD
                </div>

                <div class="steps-list">
                    {steps_html}
                </div>

            </div>

        </section>

        <div class="recipe-divider"></div>

        <section class="notes-grid">

            <div class="notes-column">

                <div class="small-heading">
                    NOTES
                </div>

                <ul>
                    {tips_html}
                </ul>

            </div>

            <div class="notes-column">

                <div class="small-heading">
                    SWAPS
                </div>

                <div>
                    {substitutions_html}
                </div>

            </div>

        </section>

    </article>
    """


CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --black: #10100f;
    --black-2: #171715;
    --cream: #f3efe5;
    --cream-dim: #aaa69b;
    --line: #34332f;
    --accent: #d47755;
}

html,
body,
.gradio-container {
    margin: 0 !important;
    padding: 0 !important;
    background: var(--black) !important;
    font-family: 'Manrope', sans-serif !important;
}

.gradio-container {
    max-width: none !important;
}

.main-wrap {
    min-height: 100vh;
    background: var(--black);
    color: var(--cream);
    padding: 46px 7vw 70px;
    box-sizing: border-box;
}

.brand {
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    letter-spacing: 0.18em;
    color: var(--cream-dim);
    margin-bottom: 95px;
}

.hero {
    max-width: 1000px;
}

.eyebrow {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.16em;
    color: var(--accent);
    margin-bottom: 24px;
}

.hero h1 {
    margin: 0;
    max-width: 950px;
    font-size: clamp(48px, 7vw, 94px);
    line-height: 0.98;
    letter-spacing: -0.055em;
    font-weight: 700;
    color: var(--cream);
}

.hero-copy {
    max-width: 570px;
    margin-top: 30px;
    font-size: 17px;
    line-height: 1.7;
    color: var(--cream-dim);
}

.input-area {
    max-width: 900px;
    margin-top: 72px;
}

.field-label {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.16em;
    color: var(--cream-dim);
    margin-bottom: 12px;
}

textarea,
input,
.gradio-dropdown {
    background: var(--black-2) !important;
    color: var(--cream) !important;
    border: 1px solid var(--line) !important;
    border-radius: 0 !important;
    box-shadow: none !important;
}

textarea {
    min-height: 145px !important;
    font-family: 'Manrope', sans-serif !important;
    font-size: 17px !important;
    line-height: 1.6 !important;
    padding: 20px !important;
}

textarea::placeholder,
input::placeholder {
    color: #77746c !important;
}

.options {
    display: grid;
    grid-template-columns: 220px 1fr;
    gap: 20px;
    margin-top: 22px;
}

.make-btn {
    margin-top: 26px;
}

.make-btn button {
    width: 100% !important;
    min-height: 58px !important;
    border-radius: 0 !important;
    border: 1px solid var(--cream) !important;
    background: var(--cream) !important;
    color: var(--black) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.16em !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}

.make-btn button:hover {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    color: white !important;
}

.output-area {
    margin-top: 70px;
}

.recipe-page {
    background: var(--cream) !important;
    color: #252522 !important;
    padding: 65px 7vw 85px;
    margin: 0;
    font-family: 'Manrope', sans-serif;
}

.recipe-page,
.recipe-page * {
    color: #252522 !important;
}

.recipe-top {
    margin-bottom: 75px;
}

.recipe-number,
.small-heading,
.step-index,
.swap-arrow {
    color: #9b563f !important;
}

.recipe-number {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.16em;
}

.recipe-header {
    max-width: 950px;
}

.recipe-header h1 {
    font-size: clamp(48px, 7vw, 90px);
    line-height: 0.98;
    letter-spacing: -0.055em;
    font-weight: 700;
    margin: 0;
    color: #252522 !important;
}

.recipe-description {
    max-width: 680px;
    margin-top: 28px;
    font-size: 18px;
    line-height: 1.7;
    color: #5f5c55 !important;
}

.recipe-facts {
    display: flex;
    gap: 65px;
    margin-top: 48px;
}

.recipe-facts div {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.recipe-facts span {
    color: #77736a !important;
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.14em;
}

.recipe-facts strong {
    color: #252522 !important;
    font-size: 14px;
    font-weight: 600;
}

.recipe-divider {
    height: 1px;
    background: #d5d0c4;
    margin: 65px 0;
}

.recipe-grid {
    display: grid;
    grid-template-columns: 0.8fr 1.2fr;
    gap: 90px;
    max-width: 1150px;
}

.small-heading {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.15em;
    margin-bottom: 25px;
}

.ingredient-list {
    border-top: 1px solid #d5d0c4;
}

.ingredient-row {
    display: flex;
    justify-content: space-between;
    gap: 20px;
    padding: 15px 0;
    border-bottom: 1px solid #d5d0c4;
    font-size: 14px;
}

.ingredient-row span:first-child {
    color: #252522 !important;
}

.ingredient-row span:last-child {
    color: #5f5c55 !important;
    text-align: right;
}

.step-row {
    display: grid;
    grid-template-columns: 48px 1fr;
    gap: 20px;
    margin-bottom: 38px;
}

.step-index {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    padding-top: 4px;
}

.step-content {
    color: #252522 !important;
    font-size: 15px;
    line-height: 1.75;
    max-width: 650px;
}

.notes-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 90px;
    max-width: 1150px;
}

.notes-column ul {
    margin: 0;
    padding-left: 20px;
}

.notes-column li {
    color: #5f5c55 !important;
    line-height: 1.7;
    margin-bottom: 12px;
    font-size: 14px;
}

.swap-row {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 13px 0;
    border-bottom: 1px solid #d5d0c4;
    font-size: 14px;
}

.swap-row {
    color: #252522 !important;
}

.swap-arrow {
    font-family: 'DM Mono', monospace;
}

.no-swaps {
    color: #5f5c55 !important;
    font-size: 14px;
}

.error-box {
    background: #201b19;
    border: 1px solid #5d3d32;
    color: #f0d8ce;
    padding: 24px;
    line-height: 1.6;
}

footer {
    display: none !important;
}

@media (max-width: 750px) {

    .main-wrap {
        padding: 30px 24px 55px;
    }

    .brand {
        margin-bottom: 65px;
    }

    .options,
    .recipe-grid,
    .notes-grid {
        grid-template-columns: 1fr;
        gap: 45px;
    }

    .recipe-page {
        padding: 45px 24px 60px;
    }

    .recipe-facts {
        gap: 30px;
        flex-wrap: wrap;
    }

    .recipe-divider {
        margin: 45px 0;
    }
}
"""


with gr.Blocks(
    title="PantryPal",
    css=CSS
) as demo:

    with gr.Column(elem_classes="main-wrap"):

        gr.HTML(
            """
            <div class="brand">
                PANTRYPAL / HOME COOKING
            </div>
            """
        )

        gr.HTML(
            """
            <div class="hero">

                <div class="eyebrow">
                    WHAT'S IN YOUR KITCHEN?
                </div>

                <h1>
                    Make something<br>
                    good from what you have.
                </h1>

                <p class="hero-copy">
                    Tell us what is already in your kitchen.
                    We will turn it into a practical recipe,
                    with no unnecessary shopping list.
                </p>

            </div>
            """
        )

        with gr.Column(elem_classes="input-area"):

            gr.HTML(
                """
                <div class="field-label">
                    INGREDIENTS
                </div>
                """
            )

            ingredients = gr.Textbox(
                placeholder="eggs, potatoes, tomatoes, onion, cheese",
                lines=5,
                show_label=False
            )

            with gr.Row(elem_classes="options"):

                with gr.Column():
                    gr.HTML(
                        """
                        <div class="field-label">
                            SERVINGS
                        </div>
                        """
                    )

                    servings = gr.Dropdown(
                        choices=["1", "2", "3", "4", "5", "6+"],
                        value="2",
                        show_label=False
                    )

                with gr.Column():
                    gr.HTML(
                        """
                        <div class="field-label">
                            PREFERENCE
                        </div>
                        """
                    )

                    preference = gr.Textbox(
                        placeholder="eg spicy, vegetarian, quick, high protein",
                        show_label=False
                    )

            make_button = gr.Button(
                "MAKE THE RECIPE",
                elem_classes="make-btn"
            )

        with gr.Column(elem_classes="output-area"):

            result = gr.HTML(
                value=""
            )

        make_button.click(
            fn=generate_recipe,
            inputs=[
                ingredients,
                servings,
                preference
            ],
            outputs=result
        )


if __name__ == "__main__":
    demo.launch(
        share=True,
        debug=True
    )
