
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
    page_title="AI Website Wireframe Generator (Editable)",
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
# GEMINI GENERATION FUNCTION (Content Density & Alignment Focus)
# =========================================================
def generate_website_json(prompt):
    """Generate structured website JSON using Gemini 2.5 Pro."""
    safety_settings = [
        {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
        {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
        {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
        {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
    ]

    # --- System Prompt: Max Content Density and Alignment Reinforcement ---
    system_prompt = """
You are an expert UI/UX wireframe designer for content-rich, multi-page websites.
Generate a clean, well-aligned, scrollable layout structure in JSON.

**CRITICAL TIMEOUT NOTE:** Limit the total output to **5 pages maximum**.

**MAX CONTENT DENSITY & ALIGNMENT RULES (CRITICAL):**
1. **FULL CONTENT:** Every 'text', 'section', and 'card' element **MUST** contain a detailed, full paragraph of unique, descriptive content related to the page's purpose. Do not use short phrases or placeholders.
2. **VERTICAL SPACE:** Ensure that pages are long. Set high 'y' coordinates (e.g., up to 2000px) and large 'height' values for sections to guarantee the wireframe extends vertically and requires scrolling, making it feel "full of content."
3. **ALIGNMENT:** For the main content elements ('text', 'section', 'card', 'image'), prefer width values of 90-95% and keep the x value low (around 2-5%) to ensure elements are nearly full-width and center-aligned, which improves layout in the mobile view simulation.

**PAGE ORDER AND CONTENT RULES (MANDATORY):**
1. **FIRST TWO PAGES MUST BE:** "Login" and "Sign Up" (or "Register"). These two pages must be the **first two objects** in the "pages" array.
2. **LOGIN/SIGN UP:** Must have appropriate form inputs and detailed, descriptive button text (e.g., "Securely Log In to Your Account").

**PAGE COUNT RULE:** Generate a **maximum of 5 distinct pages** in total.

Design elements (x, y, width, height) to adapt reasonably well to a mobile stacking view.

Return only valid JSON (no markdown) using this structure:
{
  "websiteTitle": "The Website Name",
  "globalHeader": { "layout": [] },
  "globalFooter": { "layout": [] },
  "pages": [
    // Login and Sign Up pages first
    {
      "pageId": "login_page_id", "pageTitle": "Login", "backgroundColor": "#ffffff", "layout": [...]
    },
    {
      "pageId": "signup_page_id", "pageTitle": "Sign Up", "backgroundColor": "#ffffff", "layout": [...]
    },
    // ... remaining content-rich user-requested pages follow ...
  ]
}
    """

    try:
        with st.spinner("🤖 Generating content-rich wireframe layout... (Optimizing for alignment)"):
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
        st.error(f"⚠️ Gemini generation failed: {e}. The request for maximum content may be hitting the API timeout limit. If this persists, please try a slightly simpler prompt.")
        return None

# =========================================================
# HTML RENDERING (CSS adjusted for better alignment)
# =========================================================

def generate_element_html(element):
    """Render a single layout element as visually enhanced HTML."""
    elem_type = element.get("type", "section")
    content = element.get("content", "Placeholder Content").replace("'", "&#39;")
    x, y = element.get("x", 5), element.get("y", 0)
    width, height = element.get("width", 90), element.get("height", 80)
    
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

    inner_content = f"<div class='editable-content' style='margin:0; max-height:100%; overflow:hidden; text-overflow:ellipsis;'>{content}</div>"
    
    if elem_type == "section":
        style += "background-color: #ffffff; border: 1px solid #e0e0e0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);"
        inner_content = f"<div class='editable-content' style='margin:0; font-size:16px; font-weight:600; color:#555;'>SECTION: {content}</div>"
    elif elem_type == "card":
        style += "background-color: #f8f8ff; border: 1px solid #d0d0ff; box-shadow: 0 2px 5px rgba(0,0,0,0.08);"
        inner_content = f"<div class='editable-content' style='margin:0; font-size:14px; color:#555;'>CARD: {content}</div>"
    elif elem_type == "button":
        style += "background-color: #007bff; color: white; border: none; font-size: 14px; font-weight: 700; border-radius: 6px;"
        inner_content = f"<div class='editable-content'>{content}</div>"
    elif elem_type == "input":
        style += "background-color: white; border: 1px dashed #777; font-size: 14px; color: #555; justify-content: flex-start; padding-left: 15px;"
        inner_content = f"<div class='editable-content'>Input: {content}</div>"
    elif elem_type == "image":
        style += "background-color: #e0e0e0; border: 2px dashed #999; color: #555;"
        inner_content = f"<div class='editable-content' style='margin:0; font-size:14px;'>[Image Placeholder: {content}]</div>"
    elif elem_type == "text":
        style += "background-color: #ffffff; border: none; box-shadow: none; color: #333; justify-content: flex-start; align-items: flex-start; padding: 0 10px;"
        inner_content = f"<div class='editable-content' style='margin:0; text-align:left; font-size:14px;'>{content}</div>"
    elif elem_type in ["header", "footer"]:
        style += "background-color: #333333; color: white; border: none; font-size: 18px;"
        inner_content = f"<div class='editable-content'>{content}</div>"
        
    return f"""
        <div class='element {elem_type}' style='{style}'>
            <span class='element-label'>{elem_type.upper()}</span>
            {inner_content}
        </div>
    """

def generate_multi_page_html(website_data):
    """Convert JSON structure into visual HTML wireframe with multiple pages and views, including edit logic."""
    if not website_data:
        return ""

    title = website_data.get("websiteTitle", "AI Wireframe Website")
    global_header = website_data.get("globalHeader", {}).get("layout", [])
    global_footer = website_data.get("globalFooter", {}).get("layout", [])
    pages = website_data.get("pages", [])

    page_tabs = ""
    page_contents = ""

    for i, page in enumerate(pages):
        pid = page.get("pageId", f"page-{i}")
        ptitle = page.get("pageTitle", f"Page {i+1}")
        active_class = " active" if i == 0 else ""
        page_tabs += f"<button class='tab-button{active_class}' onclick=\"showPage('{pid}')\">{ptitle}</button>"

        bg = page.get("backgroundColor", "#ffffff")
        layout = page.get("layout", [])
        elements_html = ""
        current_max_y = 0

        all_elements = global_header + layout + global_footer
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
            .wireframe-container {{
                display: flex;
                justify-content: center;
                gap: 50px;
            }}
            .wireframe-wrapper {{
                width: 100%;
                max-width: 1200px;
                border: 1px solid #ddd;
                border-radius: 12px;
                background: white;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                overflow: hidden;
                position: relative;
            }}
            /* --- Mobile Wrapper Styles --- */
            .wireframe-mobile-wrapper {{
                width: 375px; 
                height: 700px;
                border: 10px solid #333;
                border-radius: 30px;
                background: white;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                overflow: hidden;
                position: relative;
            }}
            .mobile-screen {{
                width: 100%;
                height: 100%;
                overflow-y: scroll;
                -webkit-overflow-scrolling: touch;
            }}
            /* --- Mobile Styling Overrides (Responsive Simulation) --- */
            .mobile-screen .page-container {{
                padding: 10px; 
                width: 100%;
                min-height: auto; 
            }}
            /* FIX: Ensure elements stack cleanly and are wide enough for content */
            .mobile-screen .element {{
                position: relative !important; /* Forces block flow */
                left: 0 !important;
                top: auto !important;
                width: 90% !important; /* Increased width for better content flow */
                margin: 10px auto; /* Centers elements */
                height: 60px; 
            }}
            .mobile-screen .element-label {{ top: -15px; left: 5%; }}
            .mobile-screen .section,
            .mobile-screen .image,
            .mobile-screen .card {{ height: 120px !important; }}
            .mobile-screen .text {{ height: auto !important; min-height: 40px; padding: 5px !important; }}
            .mobile-screen .button,
            .mobile-screen .input {{ height: 40px !important; }}

            /* --- Tab Navigation Styles --- */
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
                z-index: 1;
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
                z-index: 2;
            }}
            
            /* --- Edit Mode Styles --- */
            .edit-mode .element {{
                border: 1px dashed #ff6b6b !important;
                cursor: pointer;
                box-shadow: 0 0 5px rgba(255,107,107,0.5);
                transition: all 0.2s;
            }}
            .edit-mode .element:hover {{
                background-color: #fff0f0;
            }}
            .editable-content {{
                pointer-events: auto !important; 
            }}
            .edit-mode .editable-content {{
                pointer-events: auto; 
            }}
            .editable-content[contenteditable="true"] {{
                outline: 2px solid #007bff; 
                cursor: text;
                padding: 5px;
                border-radius: 4px;
                background: #e6f7ff;
            }}

            /* Download button position needs adjustment for Streamlit frame */
            .download-btn {{
                position: fixed; top: 12px; right: 20px;
                background: #2ecc71; color: white;
                border: none; padding: 8px 16px;
                border-radius: 6px; cursor: pointer;
                font-weight: bold;
                z-index: 1000;
            }}
            .download-btn:hover {{ background: #27ae60; }}
        </style>
    </head>
    <body>
        <button class="download-btn" onclick="downloadScreenshot()">Download PNG</button>
        <h2 style="text-align:center;">{title}</h2>

        <div id="wireframe-container" class="wireframe-container">
            <div id="desktop-view" class="wireframe-wrapper">
                <div class="tab-nav" id="desktop-tabs-container">{page_tabs}</div>
                <div id="desktop-content" class="desktop-content">{page_contents}</div>
            </div>

            <div id="mobile-view" class="wireframe-mobile-wrapper" style="display:none;">
                <div class="mobile-screen">
                    <div class="tab-nav" id="mobile-tabs-container">{page_tabs}</div>
                    <div id="mobile-content" class="mobile-content">{page_contents}</div>
                </div>
            </div>
        </div>

        <script>
            let currentView = 'desktop'; 
            
            function showPage(id) {{
                document.querySelectorAll('#desktop-content .page-container').forEach(p => p.style.display = 'none');
                const desktopPage = document.querySelector('#desktop-content #' + id);
                if (desktopPage) desktopPage.style.display = 'block';

                document.querySelectorAll('#mobile-content .page-container').forEach(p => p.style.display = 'none');
                const mobilePage = document.querySelector('#mobile-content #' + id);
                if (mobilePage) mobilePage.style.display = 'block';

                document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
                
                Array.from(document.querySelectorAll('.tab-nav .tab-button'))
                    .filter(b => b.getAttribute('onclick') === `showPage('${{id}}')`)
                    .forEach(btn => btn.classList.add('active'));
            }}

            function switchView(mode) {{
                currentView = mode;
                const desktop = document.getElementById('desktop-view');
                const mobile = document.getElementById('mobile-view');
                const container = document.getElementById('wireframe-container');
                
                container.classList.remove('edit-mode');
                
                if (mode === 'mobile') {{
                    desktop.style.display = 'none';
                    mobile.style.display = 'block';
                }} else if (mode === 'desktop' || mode === 'edit') {{
                    desktop.style.display = 'block'; 
                    mobile.style.display = 'none';
                    if (mode === 'edit') {{
                        container.classList.add('edit-mode');
                    }}
                }}

                const activeId = document.querySelector('.tab-button.active')?.getAttribute('onclick')?.match(/'(.*?)'/)?.[1];
                if (activeId) showPage(activeId);
            }}

            // --- CONTENT EDITING LOGIC (Double Click) ---
            document.addEventListener('dblclick', function(e) {{
                const contentDiv = e.target.closest('.editable-content');
                
                if (currentView === 'edit' && contentDiv) {{
                    
                    if (contentDiv.contentEditable === 'true') return;
                    
                    contentDiv.contentEditable = 'true';
                    contentDiv.focus();
                    
                    function disableEdit() {{
                        contentDiv.contentEditable = 'false';
                        contentDiv.removeEventListener('blur', disableEdit);
                    }}
                    
                    contentDiv.addEventListener('blur', disableEdit);
                }}
            }});


            // Initialize on load
            document.addEventListener('DOMContentLoaded', () => {{
                const firstId = document.querySelector('.tab-button')?.getAttribute('onclick')?.match(/'(.*?)'/)?.[1];
                if (firstId) showPage(firstId);
            }});
            
            function downloadScreenshot() {{
                const el = document.getElementById(currentView === 'desktop' || currentView === 'edit' ? 'desktop-view' : 'mobile-view');
                const dlBtn = document.querySelector('.download-btn');
                if (dlBtn) dlBtn.style.display = 'none';

                html2canvas(el, {{ scale: 2, removeContainer: true }}).then(canvas => {{
                    if (dlBtn) dlBtn.style.display = 'block';

                    const link = document.createElement('a');
                    link.href = canvas.toDataURL('image/png');
                    link.download = `wireframe_screenshot_${{currentView}}.png`;
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
    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🌐 AI Website Wireframe Generator")
        st.markdown("---")
        st.write("1️⃣ Describe your website layout (aim for up to 3 content pages).\n2️⃣ Click **Generate Wireframe**.\n3️⃣ Use the **View Selector** below the prompt to switch views.")
        st.markdown("---")
        st.info("🔥 **Max Content & Alignment Mode:** The generator is optimized to produce **detailed, full paragraphs** and use sensible width/alignment for better viewing on all screen sizes.")

    st.title("🚀 AI Website Wireframe Generator (Optimized Alignment)")
    st.markdown("Design a **content-heavy, scrolling multi-page wireframe** from a text prompt.")

    prompt = st.text_area(
        "📝 Describe your website (pages, style, and detailed content required):",
        placeholder="💡 e.g., Generate a simple e-commerce site with Home, Products, and Checkout pages. The Home page should have a large hero section, three detailed feature sections, and a long footer. (Login and Sign Up will be placed first).",
        height=150,
        key="prompt_input"
    )

    if st.button("✨ Generate Optimized Wireframe"):
        if not prompt.strip():
            st.warning("Please enter a website description.")
        else:
            website_data = generate_website_json(prompt)
            if website_data:
                st.session_state.website_data = website_data
                st.session_state.html_content = generate_multi_page_html(website_data)
                st.session_state.default_page_set = True
                st.session_state.current_view = 'desktop' 

    if "html_content" in st.session_state:
        st.markdown("---")
        st.subheader("🖼️ Generated Wireframe Preview")
        
        # --- VIEW SELECTOR ---
        view_mode = st.radio(
            "Select View Mode:",
            ('Desktop View', 'Mobile View', 'Edit Mode'),
            key='view_selector',
            horizontal=True,
            on_change=lambda: st.session_state.__setitem__('current_view', st.session_state.view_selector.lower().split()[0])
        )
        
        # CRITICAL FIX: Provide clear instructions for scrolling and alignment
        st.warning("✅ **View Visibility Fix:** The wireframe elements are now optimized for both views. **Please remember to scroll down inside the wireframe window** (using the inner scroll bar) to see the full content of the long page.")

        js_mode = st.session_state.get('current_view', 'desktop')
        updated_html = st.session_state.html_content
        
        js_injection = f"""
            <script>
                switchView('{js_mode}'); 
            </script>
        """
        
        # Ensuring ample height for the scrolling window
        st.components.v1.html(updated_html + js_injection, height=950, scrolling=True)

        # --- DOWNLOAD / INSPECT ---
        with st.expander("📁 Download Files & Inspect JSON"):
            st.warning("⚠️ **Edit Mode Caution:** Visual edits in the browser do not save back to the JSON structure below. This JSON only contains the data generated by Gemini.")
            st.json(st.session_state.website_data)

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
