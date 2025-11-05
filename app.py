import streamlit as st
import json
import re
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    st.error("❌ Please install the Google Generative AI library: pip install google-generativeai")
    st.stop()

# --- CONFIGURATION ---

# Configure Streamlit page
st.set_page_config(
    page_title="AI Website Wireframe Generator",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- GEMINI INITIALIZATION ---

def init_gemini():
    """Initializes the Gemini client with an API key."""
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

# Initialize Gemini at the start
if 'gemini_initialized' not in st.session_state:
    init_gemini()
    st.session_state.gemini_initialized = True

# --- JSON/MODEL UTILITIES ---

def extract_json_from_response(response_text):
    """Extracts a JSON object from the model's response text."""
    # The response text might be enclosed in markdown backticks for json
    match = re.search(r"```json\n(\{.*?\})\n```", response_text, re.DOTALL)
    if match:
        response_text = match.group(1)

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        st.error("❌ Failed to decode JSON from the response. The model may have failed to adhere to the schema.")
        st.code(response_text) # Show the problematic text
        return None

def generate_website_json(prompt):
    """Generates a multi-page wireframe structure from a text prompt using the Gemini API."""
    
    # 1. Define safety settings
    safety_settings = [
        {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
        {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
        {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
        {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
    ]

    # 2. Define the system prompt (same as before)
    system_prompt = """
    You are an expert UI/UX wireframe designer for a full website. 
    Based on the user's description, generate a structured JSON object representing the entire multi-page website layout.
    
    Return ONLY a single, valid JSON object (no markdown, no code blocks, just pure JSON) with the following structure:
    {
        "websiteTitle": "The Website Name",
        "globalHeader": { "layout": [] },
        "globalFooter": { "layout": [] },
        "pages": [
            {
                "pageId": "unique_page_id",
                "pageTitle": "Human Readable Page Title",
                "backgroundColor": "#ffffff",
                "layout": [
                    // Element definitions...
                    { "id": "unique_element_id", "type": "header|section|card|button|input|text|grid|image", "x": 0, "y": 0, "width": 100, "height": 80, "content": "Text content here" }
                ]
            }
        ]
    }

    Constraints:
    - Elements use x:0-100 (percentage-based positioning for x) and y:0-2000 (pixels for y).
    - Ensure logical y-positioning to prevent overlap and create a scrollable page.
    - Create AT LEAST 2 pages unless the user explicitly asks for only one.
    - In the 'globalHeader' layout, include elements with type 'text' or 'button' that serve as navigation links for all pages in the 'pages' array.
    """
    
    try:
        with st.spinner("🤖 Generating complete website wireframe with Gemini..."):
            # 3. CORRECTED: Pass system_instruction and safety_settings during model initialization
            model = genai.GenerativeModel(
                'gemini-2.5-pro',
                system_instruction=system_prompt, 
                safety_settings=safety_settings
            )
            
            # 4. Now, call generate_content with only the prompt
            response = model.generate_content(prompt) # Pass the original user prompt here
            
            wireframe_data = extract_json_from_response(response.text)

            if not wireframe_data or 'pages' not in wireframe_data:
                st.error("❌ Failed to parse the required multi-page structure. The JSON output may be malformed.")
                return None

            return wireframe_data
    except Exception as e:
        # Catch and report any other potential errors
        st.error(f"❌ An error occurred while generating the wireframe: {e}")
        return None
# --- HTML RENDERING ---

def generate_element_html(element):
    """Generates the HTML string for a single wireframe element."""
    elem_type = element.get("type", "section")
    content = element.get('content', '')
    
    # Calculate text alignment based on element type
    justify_content = 'center'
    align_items = 'center'
    if elem_type == 'text':
        justify_content = 'flex-start'
        align_items = 'flex-start'
        content = f"<p style='margin: 0; padding: 5px; text-align: left;'>{content}</p>"
        
    # Styles for the element's container
    style = f"""
        position: absolute;
        left: {element.get('x', 0)}%;
        top: {element.get('y', 0)}px;
        width: {element.get('width', 100)}%;
        height: {element.get('height', 50)}px;
        background-color: {element.get('backgroundColor', '#f0f0f0')};
        border: {element.get('borderWidth', 1)}px solid {element.get('borderColor', '#cccccc')};
        border-radius: {element.get('borderRadius', 0)}px;
        color: {element.get('textColor', '#333333')};
        font-size: {element.get('fontSize', 14)}px;
        font-weight: {element.get('fontWeight', 'normal')};
        display: flex;
        align-items: {align_items};
        justify-content: {justify_content};
        overflow: hidden;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    """
    
    # Special handling for button/input for better visual representation
    if elem_type == 'button':
        content = f"<button style='background-color: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 4px; font-weight: bold; cursor: pointer;'>{content}</button>"
        align_items = 'center'
        justify_content = 'center'
        style = re.sub(r'background-color:.*?;', 'background-color: #007bff;', style)
        style = re.sub(r'color:.*?;', 'color: white;', style)
        
    elif elem_type == 'input':
        content = f"<input type='text' placeholder='{content}' style='width: 90%; padding: 5px; border: 1px solid #ccc; border-radius: 4px;'>"
        align_items = 'center'
        justify_content = 'center'
        style = re.sub(r'background-color:.*?;', 'background-color: white;', style)
        
    elif elem_type == 'image':
        content = f"[Image Placeholder: {content}]"

    return f"""
        <div class="element {elem_type}" style="{style}">
            <span class="element-label">{elem_type.upper()}</span>
            <div>{content}</div>
        </div>
    """

def generate_multi_page_html(website_data):
    """Converts the multi-page website JSON into a single HTML file with tabs."""
    if not website_data:
        return ""

    website_title = website_data.get("websiteTitle", "AI Wireframe Website")
    global_header = website_data.get("globalHeader", {}).get("layout", [])
    global_footer = website_data.get("globalFooter", {}).get("layout", [])
    pages = website_data.get("pages", [])

    page_tabs = ""
    page_contents = ""
    max_height = 800 # Min height for the container
    
    # 1. Generate Navigation Tabs (HTML)
    for i, page in enumerate(pages):
        page_id = page.get("pageId", f"page-{i}")
        page_title = page.get("pageTitle", f"Page {i+1}")
        page_tabs += f"""
            <button class="tab-button" onclick="showPage('{page_id}')">{page_title}</button>
        """

    # 2. Generate Page Content
    for i, page in enumerate(pages):
        page_id = page.get("pageId", f"page-{i}")
        bg_color = page.get("backgroundColor", "#ffffff")
        page_layout = page.get("layout", [])
        
        page_elements = ""
        # Combine global and page-specific elements
        all_elements = global_header + page_layout + global_footer
        
        # Track the lowest Y-position to set the container height
        current_max_y = 0
        
        for element in all_elements:
            page_elements += generate_element_html(element)
            # Update max height based on element bottom (y + height)
            current_max_y = max(current_max_y, element.get('y', 0) + element.get('height', 0))
            
        max_height = max(max_height, current_max_y + 50) # Add padding
        
        display_style = "display: none;"
        if i == 0:
            display_style = "display: block;"
            
        page_contents += f"""
            <div id="{page_id}" class="page-container" style="background-color: {bg_color}; {display_style} min-height: {max_height}px;">
                {page_elements}
            </div>
        """
    
    # 3. Assemble Full HTML
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{website_title}</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background-color: #f0f2f6;
                padding: 20px;
            }}
            .wireframe-wrapper {{
                max-width: 1200px;
                margin: 0 auto 20px auto;
                border: 1px solid #ddd;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .page-container {{
                position: relative;
                width: 100%;
                /* Height set dynamically via script to fit content */
            }}
            .element {{
                box-sizing: border-box;
                transition: all 0.1s ease-in-out;
                text-align: center;
            }}
            .element:hover {{
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
                z-index: 10;
            }}
            .element-label {{
                position: absolute;
                top: 0px;
                left: 3px;
                font-size: 8px;
                color: #7f8c8d;
                background-color: rgba(255, 255, 255, 0.7);
                padding: 1px 3px;
                border-radius: 2px;
                z-index: 5;
            }}
            
            /* Tab Styles */
            .tab-nav {{
                display: flex;
                background-color: #333;
                padding: 10px;
                border-bottom: 3px solid #007bff;
            }}
            .tab-button {{
                background-color: #444;
                color: white;
                border: none;
                padding: 10px 20px;
                cursor: pointer;
                margin-right: 5px;
                border-radius: 4px 4px 0 0;
                font-weight: bold;
                transition: background-color 0.3s;
            }}
            .tab-button:hover {{
                background-color: #555;
            }}
            .tab-button.active {{
                background-color: #007bff;
            }}
            
            /* Controls for download */
            .controls {{
                position: fixed;
                top: 10px;
                right: 20px;
                z-index: 1000;
            }}
            .download-btn {{
                padding: 8px 16px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
            }}
            .download-btn:hover {{
                background-color: #27ae60;
            }}
        </style>
    </head>
    <body>
        <div class="controls">
            <button class="download-btn" onclick="downloadScreenshot()">Download as PNG</button>
        </div>
        
        <h2 style="text-align: center; margin-bottom: 20px;">{website_title}</h2>
        
        <div class="wireframe-wrapper">
            <div class="tab-nav" id="tab-nav-container">
                {page_tabs}
            </div>
            
            <div id="wireframe-content">
                {page_contents}
            </div>
        </div>

        <script>
            // Ensure first page is active and all pages are sized correctly
            document.addEventListener('DOMContentLoaded', (event) => {{
                const firstPage = document.querySelector('.page-container');
                if (firstPage) {{
                    showPage(firstPage.id);
                }}
                adjustContainerHeight();
            }});
            
            function adjustContainerHeight() {{
                const activePage = document.querySelector('.page-container[style*="display: block"]');
                if (activePage) {{
                    // Find the lowest y + height of all elements on the active page
                    let maxBottom = 800; // Minimum height
                    activePage.querySelectorAll('.element').forEach(el => {{
                        const top = parseInt(el.style.top);
                        const height = parseInt(el.style.height);
                        maxBottom = Math.max(maxBottom, top + height);
                    }});
                    // Set the height of the active page container
                    activePage.style.minHeight = `${{maxBottom + 50}}px`; // Add padding
                }}
            }}
            
            function showPage(pageId) {{
                // Hide all pages
                document.querySelectorAll('.page-container').forEach(page => {{
                    page.style.display = 'none';
                    page.style.minHeight = '800px'; // Reset height temporarily
                }});

                // Deactivate all buttons
                document.querySelectorAll('.tab-button').forEach(button => {{
                    button.classList.remove('active');
                }});
                
                // Show the selected page
                const selectedPage = document.getElementById(pageId);
                if (selectedPage) {{
                    selectedPage.style.display = 'block';
                    // Activate the corresponding button
                    document.querySelector(`button[onclick="showPage('${{pageId}}')"]`).classList.add('active');
                    // Recalculate and set the height
                    adjustContainerHeight();
                }}
            }}
            
            function downloadScreenshot() {{
                const element = document.querySelector('.wireframe-wrapper');
                html2canvas(element, {{ scale: 2 }}).then(canvas => {{
                    const link = document.createElement('a');
                    link.href = canvas.toDataURL('image/png');
                    link.download = 'website_wireframe.png';
                    link.click();
                }});
            }}
        </script>
    </body>
    </html>
    """
    return html_content

# --- STREAMLIT MAIN APP ---

def main():
    # Sidebar
    with st.sidebar:
        st.title("🌐 AI Website Wireframe Generator")
        st.markdown("---")
        st.markdown("### How to use:")
        st.markdown("""
        1. Describe the **entire website** (e.g., "A 3-page e-commerce site with Home, Products, and Checkout pages...").
        2. Click '**Generate Website**'.
        3. Use the **tabs** in the generated view to switch between pages.
        """)
        st.markdown("---")
        st.info("Powered by Google Gemini and Streamlit.")

    # Main content
    st.title("🚀 AI-Powered Multi-Page Wireframe Generator")
    st.markdown("Design a **complete website architecture** from a single prompt.")

    prompt = st.text_area(
        "📝 **Describe your website (e.g., 3-page blog, portfolio with two case studies, etc.):**",
        placeholder="e.g., A 3-page website for a SaaS startup with a modern, clean design. Pages: Homepage, Features, Pricing. Include a consistent navigation header and footer.",
        height=150,
        key="prompt_input"
    )

    if st.button("✨ Generate Website", type="primary"):
        if prompt:
            # Clear previous page selection state
            if 'selected_page' in st.session_state:
                del st.session_state.selected_page
                
            website_data = generate_website_json(prompt)
            if website_data:
                st.session_state.website_data = website_data
                st.session_state.html_content = generate_multi_page_html(website_data)
        else:
            st.warning("Please enter a description for the website.")

    if "html_content" in st.session_state and st.session_state.html_content:
        st.markdown("---")
        st.subheader("🖼️ Generated Website Wireframe (Interactive)")
        
        # Render the full HTML with tabs
        st.components.v1.html(st.session_state.html_content, height=800, scrolling=True)

        with st.expander("📄 View/Download Assets"):
            col1, col2 = st.columns([1, 1])
            
            # Use Streamlit tabs to show JSON for each page
            page_titles = [p.get('pageTitle', f"Page {i+1}") for i, p in enumerate(st.session_state.website_data.get('pages', []))]
            
            # Use the Streamlit st.tabs component for easy JSON viewing
            tab_containers = st.tabs(["Full JSON Data"] + page_titles)
            
            # Tab 1: Full JSON
            with tab_containers[0]:
                st.subheader("Full Website JSON Structure")
                st.json(st.session_state.website_data)
                st.download_button(
                    label="Download Full JSON",
                    data=json.dumps(st.session_state.website_data, indent=2),
                    file_name="website_wireframe.json",
                    mime="application/json",
                )

            # Subsequent tabs: Individual Page JSON
            for i, page_title in enumerate(page_titles):
                with tab_containers[i+1]:
                    page_data = st.session_state.website_data['pages'][i]
                    st.subheader(f"{page_title} - Page Details")
                    # We combine global and page-specific data for a complete JSON view
                    display_data = {
                        "globalHeader": st.session_state.website_data.get("globalHeader"),
                        "globalFooter": st.session_state.website_data.get("globalFooter"),
                        "pageData": page_data
                    }
                    st.json(display_data)
            
            st.subheader("HTML File")
            st.download_button(
                label="Download HTML",
                data=st.session_state.html_content,
                file_name="website_wireframe.html",
                mime="text/html",
            )

if __name__ == "__main__":
    main()
