import streamlit as st
import json
import re
from pathlib import Path
import os
from dotenv import load_dotenv

# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    st.error("❌ Please install the Google Generative AI library: pip install google-generativeai")
    st.stop()

# =========================================================
# STREAMLIT CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="AI Website Wireframe Generator (Optimized)",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# INITIALIZE GEMINI
# =========================================================
def init_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            pass
    if not api_key:
        st.error("❌ GEMINI_API_KEY not found! Please set it in your .env file or Streamlit secrets.")
        st.stop()
    genai.configure(api_key=api_key)

if 'gemini_initialized' not in st.session_state:
    init_gemini()
    st.session_state.gemini_initialized = True

# =========================================================
# JSON EXTRACTION (IMPROVED)
# =========================================================
def extract_json_from_response(response_text):
    """Extract JSON safely from Gemini output."""
    # Remove markdown code fences if present
    response_text = response_text.strip()
    if response_text.startswith("```"):
        response_text = re.sub(r"```json|```", "", response_text).strip()

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        st.error("❌ Invalid JSON from Gemini. Showing raw output below:")
        st.code(response_text)
        return None

# =========================================================
# GEMINI GENERATION FUNCTION (REALISTIC + EXTENDED)
# =========================================================
def generate_website_json(prompt):
    """Generate structured website JSON using Gemini 2.5 Pro with 6 tabs and realistic content."""
    safety_settings = [
        {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
        {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
        {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
        {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
    ]

    # === UPGRADED SYSTEM PROMPT ===
    system_prompt = """
You are an expert UI/UX designer generating realistic multi-page website wireframes.

Create a **complete JSON layout** representing a 6-tab modern responsive website.

### DESIGN RULES:
1. Include **exactly 6 pages**:
   - Login
   - Sign Up
   - Home
   - About
   - Services (or Products)
   - Contact (or Dashboard)
2. Each page must have **unique content**, layout, and structure.
3. Layouts must be clean and scrollable with spacing (min y=80px between sections).
4. Content should feel realistic — no placeholder text like “Lorem Ipsum”.
5. Use diverse elements: hero sections, text, images, inputs, buttons, cards, footers.
6. Home/About/Services pages should look like real websites.
7. Include a global header and footer applied to all pages.

### FORMAT:
Return valid JSON only:
{
  "websiteTitle": "The Website Name",
  "globalHeader": { "layout": [ ...header elements... ] },
  "globalFooter": { "layout": [ ...footer elements... ] },
  "pages": [
    {
      "pageId": "login",
      "pageTitle": "Login",
      "backgroundColor": "#ffffff",
      "layout": [...]
    },
    ...
  ]
}

All text should be natural and readable (e.g., “Welcome to Sunrise Interiors” or “Contact our support team”).
    """

    try:
        with st.spinner("🤖 Generating realistic 6-page website wireframe with Gemini..."):
            model = genai.GenerativeModel(
                "gemini-2.5-pro",
                system_instruction=system_prompt,
                safety_settings=safety_settings
            )
            response = model.generate_content(prompt)
            wireframe_data = extract_json_from_response(response.text)
            if not wireframe_data or "pages" not in wireframe_data:
                st.error("❌ Gemini failed to return valid website JSON.")
                return None
            return wireframe_data
    except Exception as e:
        st.error(f"⚠️ Gemini generation failed: {e}")
        return None

# =========================================================
# HTML RENDERING
# =========================================================
def generate_element_html(element):
    elem_type = element.get("type", "section")
    content = element.get("content", "")
    x, y = element.get("x", 5), element.get("y", 0)
    width, height = element.get("width", 90), element.get("height", 80)

    style = f"""
        position: absolute;
        left: {x}%;
        top: {y}px;
        width: {width}%;
        height: {height}px;
        border-radius: 6px;
        padding: 10px;
        color: #333;
        font-family: 'Segoe UI', sans-serif;
    """

    if elem_type == "button":
        style += "background-color:#007bff;color:white;font-weight:600;text-align:center;display:flex;align-items:center;justify-content:center;"
    elif elem_type == "input":
        style += "border:1px solid #aaa;background-color:white;display:flex;align-items:center;padding-left:15px;"
    elif elem_type == "card":
        style += "background:#f9f9ff;border:1px solid #ccc;box-shadow:0 1px 3px rgba(0,0,0,0.1);"
    elif elem_type == "image":
        style += "background:#e0e0e0;border:2px dashed #999;"
    elif elem_type == "text":
        style += "font-size:14px;text-align:left;"
    else:
        style += "background-color:white;border:1px solid #ddd;"

    return f"<div class='element' style='{style}'>{content}</div>"

def generate_multi_page_html(website_data):
    if not website_data:
        return ""

    title = website_data.get("websiteTitle", "AI Website")
    pages = website_data.get("pages", [])
    tabs = ""
    content_html = ""

    for i, page in enumerate(pages):
        active = "active" if i == 0 else ""
        tabs += f"<button class='tab {active}' onclick=\"showPage('{page['pageId']}')\">{page['pageTitle']}</button>"

        layout_html = "".join([generate_element_html(el) for el in page.get("layout", [])])
        display = "block" if i == 0 else "none"
        content_html += f"<div id='{page['pageId']}' class='page' style='display:{display};background:{page.get('backgroundColor','#fff')};'>{layout_html}</div>"

    html = f"""
    <html>
    <head>
    <style>
    body {{
        font-family: 'Segoe UI', sans-serif;
        margin: 0;
        background: #f4f6f8;
    }}
    .tabs {{ display: flex; background: #eee; border-bottom: 1px solid #ccc; }}
    .tab {{
        padding: 10px 20px;
        cursor: pointer;
        background: #f0f0f0;
        border: none;
        border-right: 1px solid #ccc;
    }}
    .tab.active {{ background: white; font-weight: 600; color:#007bff; }}
    .page {{ position: relative; padding: 40px; min-height: 700px; }}
    </style>
    </head>
    <body>
    <h2 style='text-align:center'>{title}</h2>
    <div class='tabs'>{tabs}</div>
    <div>{content_html}</div>
    <script>
    function showPage(id) {{
        document.querySelectorAll('.page').forEach(p => p.style.display='none');
        document.getElementById(id).style.display='block';
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        event.target.classList.add('active');
    }}
    </script>
    </body>
    </html>
    """
    return html

# =========================================================
# STREAMLIT UI
# =========================================================
def main():
    with st.sidebar:
        st.title("🌐 Realistic Website Wireframe Generator")
        st.info("Generates a realistic 6-page website (Login, Signup, Home, About, Services, Contact).")

    st.title("🚀 AI Website Wireframe Generator (Enhanced Realism & 6 Tabs)")
    st.markdown("Describe your website style or niche (e.g., *interior design, tech startup, education, portfolio*).")

    prompt = st.text_area(
        "📝 Describe your website:",
        placeholder="Example: Generate a modern responsive website for an AI startup with login, signup, home, about, services, and contact pages.",
        height=150,
    )

    if st.button("✨ Generate Wireframe"):
        if not prompt.strip():
            st.warning("Please enter a valid description.")
        else:
            data = generate_website_json(prompt)
            if data:
                st.session_state["wireframe_data"] = data
                st.session_state["html_output"] = generate_multi_page_html(data)

    if "html_output" in st.session_state:
        st.markdown("---")
        st.subheader("🖼️ Generated Wireframe Preview")
        st.components.v1.html(st.session_state["html_output"], height=900, scrolling=True)

        st.download_button(
            "⬇️ Download JSON",
            data=json.dumps(st.session_state["wireframe_data"], indent=2),
            file_name="website_wireframe.json",
            mime="application/json",
        )
        st.download_button(
            "⬇️ Download HTML",
            data=st.session_state["html_output"],
            file_name="website_wireframe.html",
            mime="text/html",
        )

if __name__ == "__main__":
    main()

