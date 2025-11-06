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
    page_title="AI Website Wireframe Generator (Enhanced)",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# INITIALIZE GEMINI
# =========================================================
def init_gemini():
    """Initializes Gemini client using API key from .env or Streamlit secrets."""
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
# JSON EXTRACTION
# =========================================================
def extract_json_from_response(response_text):
    """Safely extract JSON object from Gemini output."""
    match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", response_text, re.DOTALL)
    if match:
        response_text = match.group(1)
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        st.error("❌ Invalid JSON from Gemini. Showing raw output below:")
        st.code(response_text)
        return None

# =========================================================
# GEMINI GENERATION FUNCTION
# =========================================================
def generate_website_json(prompt):
    """Generate structured website JSON using Gemini 2.5 Pro."""
    safety_settings = [
        {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
        {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
        {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
        {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
    ]

    # --- IMPROVED SYSTEM PROMPT ---
    system_prompt = """
You are an expert UI/UX wireframe designer for multi-page websites.
Generate a clean, well-aligned, scrollable layout structure in JSON.

Ensure:
- Pages do not overlap elements.
- Vertical spacing (y values) is consistent (minimum 80px between sections).
- x values stay between 5%–95% for side padding.
- Create up to 8 pages if the user requests a large website.
- Logical layout order: header → hero → sections → footer.

Return only valid JSON (no markdown) using this structure:
{
  "websiteTitle": "The Website Name",
  "globalHeader": { "layout": [] },
  "globalFooter": { "layout": [] },
  "pages": [
    {
      "pageId": "unique_page_id",
      "pageTitle": "Page Name",
      "backgroundColor": "#ffffff",
      "layout": [
        { "id": "el_1", "type": "section|card|text|button|image|input", 
          "x": 5, "y": 100, "width": 90, "height": 100, "content": "..." }
      ]
    }
  ]
}
    """

    try:
        with st.spinner("🤖 Generating website layout with Gemini..."):
            model = genai.GenerativeModel(
                "gemini-2.5-pro",
                system_instruction=system_prompt,
                safety_settings=safety_settings
            )
            response = model.generate_content(prompt)
            wireframe_data = extract_json_from_response(response.text)
            if not wireframe_data or "pages" not in wireframe_data:
                st.error("❌ Gemini failed to return valid structure.")
                return None
            return wireframe_data
    except Exception as e:
        st.error(f"⚠️ Gemini generation failed: {e}")
        return None

# =========================================================
# HTML RENDERING (ENHANCED)
# =========================================================
def generate_element_html(element):
    """Render a single layout element as visually enhanced HTML."""
    elem_type = element.get("type", "section")
    content = element.get("content", "Placeholder Content")
    x, y = element.get("x", 5), element.get("y", 0)
    width, height = element.get("width", 90), element.get("height", 80)
    
    # Base styles for a clean, wireframe look
    style = f"""
        position: absolute;
        left: {x}%;
        top: {y}px;
        width: {width}%;
        height: {height}px;
        box-sizing: border-box;
        border-radius: 4px;
        color: {element.get('textColor', '#333')};
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: {element.get('fontSize', 14)}px;
        overflow: hidden;
        font-weight: 500;
        text-align: center;
        padding: 10px;
    """

    inner_content = f"<p style='margin:0; max-height:100%; overflow:hidden; text-overflow:ellipsis;'>{content}</p>"
    
    # Custom styles based on element type
    if elem_type == "section":
        style += "background-color: #ffffff; border: 1px solid #e0e0e0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);"
        inner_content = f"<p style='margin:0; font-size:16px; font-weight:600; color:#555;'>SECTION: {content}</p>"
    elif elem_type == "card":
        style += "background-color: #f8f8ff; border: 1px solid #d0d0ff; box-shadow: 0 2px 5px rgba(0,0,0,0.08);"
        inner_content = f"<p style='margin:0; font-size:14px; color:#555;'>CARD: {content}</p>"
    elif elem_type == "button":
        style += "background-color: #007bff; color: white; border: none; font-size: 14px; font-weight: 700; border-radius: 6px;"
        inner_content = content
    elif elem_type == "input":
        style += "background-color: white; border: 1px dashed #777; font-size: 14px; color: #555; justify-content: flex-start; padding-left: 15px;"
        inner_content = f"Input: {content}"
    elif elem_type == "image":
        style += "background-color: #e0e0e0; border: 2px dashed #999; color: #555;"
        inner_content = f"<p style='margin:0; font-size:14px;'>[Image Placeholder: {content}]</p>"
    elif elem_type == "text":
        style += "background-color: #ffffff; border: none; box-shadow: none; color: #333; justify-content: flex-start; align-items: flex-start; padding: 0 10px;"
        inner_content = f"<p style='margin:0; text-align:left; font-size:14px;'>{content}</p>"
    elif elem_type in ["header", "footer"]: # Assuming global elements might pass through here
        style += "background-color: #333333; color: white; border: none; font-size: 18px;"
        
    return f"""
        <div class='element {elem_type}' style='{style}'>
            <span class='element-label'>{elem_type.upper()}</span>
            <div style='text-align:center;'>{inner_content}</div>
        </div>
    """

# =========================================================
# MULTI-PAGE HTML RENDERER (ENHANCED STYLES)
# =========================================================
def generate_multi_page_html(website_data):
    """Convert JSON structure into visual HTML wireframe with multiple pages."""
    if not website_data:
        return ""

    title = website_data.get("websiteTitle", "AI Wireframe Website")
    global_header = website_data.get("globalHeader", {}).get("layout", [])
    global_footer = website_data.get("globalFooter", {}).get("layout", [])
    pages = website_data.get("pages", [])

    # Tabs
    page_tabs = ""
    page_contents = ""

    for i, page in enumerate(pages):
        pid = page.get("pageId", f"page-{i}")
        ptitle = page.get("pageTitle", f"Page {i+1}")
        # Add 'active' class to the first button
        active_class = " active" if i == 0 else ""
        page_tabs += f"<button class='tab-button{active_class}' onclick=\"showPage('{pid}')\">{ptitle}</button>"

        bg = page.get("backgroundColor", "#ffffff")
        layout = page.get("layout", [])
        elements_html = ""
        current_max_y = 0

        # Combine global and page elements for rendering
        all_elements = global_header + layout + global_footer
        
        # Sort elements by y-coordinate to ensure correct Z-indexing for labels
        # (elements higher on the page should render first)
        all_elements.sort(key=lambda el: el.get("y", 0))

        for el in all_elements:
            elements_html += generate_element_html(el)
            current_max_y = max(current_max_y, el.get("y", 0) + el.get("height", 0))

        display = "block" if i == 0 else "none"
        page_contents += f"""
        <div id="{pid}" class="page-container" style="background:{bg};display:{display};min-height:{current_max_y + 120}px;">
            {elements_html}
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background-color: #f4f6f8;
                padding: 30px;
            }}
            .wireframe-wrapper {{
                max-width: 1200px;
                margin: auto;
                border: 1px solid #ddd;
                border-radius: 12px;
                background: white;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .tab-nav {{
                display: flex;
                flex-wrap: wrap;
                gap: 0; 
                background: #f0f0f0; 
                padding: 0 20px;
                border-bottom: 1px solid #ddd;
            }}
            .tab-button {{
                background: none;
                color: #555;
                border: none;
                padding: 10px 20px;
                border-radius: 8px 8px 0 0;
                cursor: pointer;
                font-weight: 600;
                margin-right: 5px; 
                transition: all 0.2s ease;
            }}
            .tab-button.active {{ 
                background: white; 
                color: #007bff; 
                border-top: 2px solid #007bff;
                border-left: 1px solid #ddd;
                border-right: 1px solid #ddd;
                border-bottom: 1px solid white;
                z-index: 10;
            }}
            .tab-button:hover:not(.active) {{ background: #e9e9e9; }}

            .page-container {{
                position: relative;
                width: 100%;
                padding: 20px 40px; 
                box-sizing: border-box;
                border-top: 1px solid white; 
            }}
            .element {{
                box-sizing: border-box;
                transition: all 0.15s ease;
                z-index: 1; /* Ensure elements sit above background */
            }}
            .element:hover {{ 
                transform: none; 
                box-shadow: 0 0 5px rgba(0,123,255,0.4); 
                z-index: 5;
            }}
            .element-label {{
                position: absolute;
                top: -15px; 
                left: 0;
                font-size: 9px; 
                color: #888;
                background: #f0f0f0;
                padding: 1px 5px;
                border-radius: 3px;
                font-weight: 700;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                z-index: 2; /* Ensure label is above other elements */
            }}
            
            /* Specific wireframe styles for text clarity */
            .text {{ background: none !important; border: none !important; box-shadow: none !important; color: #333; justify-content: flex-start; align-items: flex-start; padding: 0 10px !important; }}
            .text p {{ text-align: left !important; }}
            .image {{ display: flex !important; flex-direction: column; justify-content: center; align-items: center; }}


            .download-btn {{
                position: fixed; top: 12px; right: 20px;
                background: #2ecc71; color: white;
                border: none; padding: 8px 16px;
                border-radius: 6px; cursor: pointer;
                font-weight: bold;
            }}
            .download-btn:hover {{ background: #27ae60; }}
        </style>
    </head>
    <body>
        <button class="download-btn" onclick="downloadScreenshot()">Download PNG</button>
        <h2 style="text-align:center;">{title}</h2>
        <div class="wireframe-wrapper">
            <div class="tab-nav">{page_tabs}</div>
            <div id="wireframe-content">{page_contents}</div>
        </div>
        <script>
            // Initialize first page as active
            document.addEventListener('DOMContentLoaded', () => {{
                showPage(document.querySelector('.tab-button').getAttribute('onclick').match(/'(.*?)'/)[1]);
            }});
            
            function showPage(id) {{
                document.querySelectorAll('.page-container').forEach(p => p.style.display = 'none');
                document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
                const page = document.getElementById(id);
                if (page) page.style.display = 'block';
                const btn = Array.from(document.querySelectorAll('.tab-button'))
                    .find(b => b.getAttribute('onclick') === `showPage('${{id}}')`);
                if (btn) btn.classList.add('active');
            }}
            function downloadScreenshot() {{
                const el = document.querySelector('.wireframe-wrapper');
                html2canvas(el, {{ scale: 2 }}).then(canvas => {{
                    const link = document.createElement('a');
                    link.href = canvas.toDataURL('image/png');
                    link.download = 'wireframe_screenshot.png';
                    link.click();
                }});
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
        st.title("🌐 AI Website Wireframe Generator")
        st.markdown("---")
        st.write("1️⃣ Describe your website layout.\n2️⃣ Click **Generate Website**.\n3️⃣ Use tabs to switch pages.")
        st.markdown("---")
        st.info("✅ Supports up to 8 pages. Clean layout, non-cluttered design.")

    st.title("🚀 AI Website Wireframe Generator (Enhanced)")
    st.markdown("Design a complete **multi-page website wireframe** from a text prompt.")

    prompt = st.text_area(
        "📝 Describe your website (pages, style, and layout):",
        placeholder="e.g., 8-page corporate site: Home, About, Services, Portfolio, Team, Testimonials, Blog, Contact.",
        height=150,
        key="prompt_input"
    )

    if st.button("✨ Generate Wireframe"):
        if not prompt.strip():
            st.warning("Please enter a website description.")
        else:
            website_data = generate_website_json(prompt)
            if website_data:
                st.session_state.website_data = website_data
                st.session_state.html_content = generate_multi_page_html(website_data)

    if "html_content" in st.session_state:
        st.markdown("---")
        st.subheader("🖼️ Generated Wireframe Preview")
        # Set a default page on initial load if not already set (for tab initialization)
        if 'default_page_set' not in st.session_state:
            st.session_state.default_page_set = True 

        st.components.v1.html(st.session_state.html_content, height=900, scrolling=True)

        with st.expander("📁 Download Files"):
            st.download_button(
                label="Download JSON",
                data=json.dumps(st.session_state.website_data, indent=2),
                file_name="website_wireframe.json",
                mime="application/json"
            )
            st.download_button(
                label="Download HTML",
                data=st.session_state.html_content,
                file_name="website_wireframe.html",
                mime="text/html"
            )

if __name__ == "__main__":
    main()
