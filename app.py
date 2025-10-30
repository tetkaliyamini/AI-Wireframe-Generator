# ===========================================================
# AI Wireframe Generator - Enhanced Single File Edition
# ===========================================================
import streamlit as st
import google.generativeai as genai
import plotly.graph_objects as go
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from io import BytesIO

# =====================================================
# CONFIGURATION & SETUP
# =====================================================
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

ELEMENT_COLORS = {
    "navbar": {"fill": "#3B82F6", "text": "#FFFFFF", "border": "#1E40AF"},
    "button": {"fill": "#10B981", "text": "#FFFFFF", "border": "#059669"},
    "input": {"fill": "#FFFFFF", "text": "#1F2937", "border": "#D1D5DB"},
    "card": {"fill": "#F3F4F6", "text": "#1F2937", "border": "#E5E7EB"},
    "label": {"fill": "#FFFFFF", "text": "#374151", "border": "#E5E7EB"},
    "image": {"fill": "#E5E7EB", "text": "#6B7280", "border": "#D1D5DB"},
    "footer": {"fill": "#1F2937", "text": "#FFFFFF", "border": "#111827"},
    "section": {"fill": "#F9FAFB", "text": "#1F2937", "border": "#E5E7EB"},
    "grid": {"fill": "#FFFFFF", "text": "#1F2937", "border": "#D1D5DB"},
    "divider": {"fill": "#D1D5DB", "text": "#6B7280", "border": "#9CA3AF"},
}

# =====================================================
# GEMINI CONFIGURATION
# =====================================================
def configure_gemini(api_key):
    """Configure Gemini API with error handling."""
    if not api_key:
        st.error("❌ Missing GOOGLE_API_KEY in your environment or .env file.")
        st.stop()
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-pro")

# =====================================================
# WIREFRAME GENERATION
# =====================================================
def generate_wireframe_and_outline(model, user_prompt):
    """Generate wireframe layout and interface outline from user prompt."""
    prompt = f"""
    You are a senior UX/UI designer with 10+ years of experience. Create a professional wireframe.
    
    REQUIREMENTS:
    1. Generate a clean hierarchical OUTLINE describing the interface structure
    2. Create a WIREFRAME_JSON with precise layout coordinates
    3. Use realistic proportions and spacing
    4. Include diverse element types: navbar, button, input, card, label, image, footer, section, grid, divider
    5. Ensure all elements fit within a 100x100 grid
    6. Add meaningful labels for each element
    
    JSON FORMAT (MUST be valid JSON):
    {{
      "elements": [
        {{
          "type": "navbar|button|input|card|label|image|footer|section|grid|divider",
          "label": "descriptive name",
          "x": 0-100,
          "y": 0-100,
          "width": 5-100,
          "height": 5-100
        }}
      ]
    }}
    
    LAYOUT GUIDELINES:
    - Navbar: top of page, full width (0, 0, 100, 8)
    - Main content: centered with padding
    - Cards: organized in grid patterns
    - Footer: bottom of page, full width
    - Maintain 5-10 unit margins between elements
    
    USER REQUEST:
    "{user_prompt}"
    
    OUTPUT FORMAT (EXACTLY as shown):
    OUTLINE:
    [Your detailed outline here]
    
    WIREFRAME_JSON:
    [Valid JSON only, no markdown]
    """
    
    response = model.generate_content(prompt)
    text = response.text

    try:
        # Parse outline and JSON
        outline = text.split("OUTLINE:")[1].split("WIREFRAME_JSON:")[0].strip()
        json_text = text.split("WIREFRAME_JSON:")[1].strip()
        
        # Remove markdown code blocks if present
        if json_text.startswith("```"):
            json_text = json_text.split("```")[1]
            if json_text.startswith("json"):
                json_text = json_text[4:]
            json_text = json_text.strip()
        
        json_data = json.loads(json_text)
        return outline, json_data.get("elements", [])
    except Exception as e:
        st.error(f"⚠️ Failed to parse Gemini response: {str(e)}")
        st.code(text, language="text")
        return None, None

# =====================================================
# WIREFRAME RENDERING
# =====================================================
def render_wireframe_plotly(elements, theme="light"):
    """Render wireframe with enhanced visual hierarchy and styling."""
    fig = go.Figure()
    
    for idx, el in enumerate(elements):
        x, y, w, h = el["x"], el["y"], el["width"], el["height"]
        
        # Flip Y-axis for proper display
        y_top = 100 - y
        y_bottom = 100 - (y + h)
        
        rect_x = [x, x + w, x + w, x, x]
        rect_y = [y_top, y_top, y_bottom, y_bottom, y_top]
        
        # Get colors for element type
        el_type = el.get("type", "card")
        colors = ELEMENT_COLORS.get(el_type, ELEMENT_COLORS["card"])
        
        shadow_offset = 0.3
        shadow_x = [x + shadow_offset, x + w + shadow_offset, x + w + shadow_offset, x + shadow_offset, x + shadow_offset]
        shadow_y = [y_top - shadow_offset, y_top - shadow_offset, y_bottom - shadow_offset, y_bottom - shadow_offset, y_top - shadow_offset]
        
        fig.add_trace(go.Scatter(
            x=shadow_x, y=shadow_y, mode='lines',
            line=dict(color='rgba(0,0,0,0)', width=0),
            fill='toself', fillcolor='rgba(0,0,0,0.08)',
            hoverinfo='none', showlegend=False
        ))
        
        # Main rectangle with enhanced border
        fig.add_trace(go.Scatter(
            x=rect_x, y=rect_y, mode='lines',
            line=dict(color=colors["border"], width=2),
            fill='toself', fillcolor=colors["fill"],
            hoverinfo='text',
            hovertext=f"<b>{el['label']}</b><br>Type: {el_type}<br>Size: {w:.1f}x{h:.1f}",
            showlegend=False
        ))
        
        # Element label with better typography
        label_text = el["label"]
        text_size = max(8, min(12, w / 3))  # Dynamic text size based on element width
        
        fig.add_trace(go.Scatter(
            x=[x + w / 2], y=[y_top - h / 2],
            text=[label_text], mode="text",
            textfont=dict(size=text_size, color=colors["text"], family="Arial, sans-serif"),
            hoverinfo='skip', showlegend=False
        ))
    
    fig.update_layout(
        width=900, height=900,
        xaxis=dict(visible=False, range=[-5, 105]),
        yaxis=dict(visible=False, range=[-5, 105]),
        plot_bgcolor="#FFFFFF" if theme == "light" else "#1F2937",
        paper_bgcolor="#F9FAFB" if theme == "light" else "#111827",
        margin=dict(l=30, r=30, t=30, b=30),
        showlegend=False,
        hovermode='closest'
    )
    
    # Export to PNG buffer
    buf = BytesIO()
    fig.write_image(buf, format="png", scale=3, width=900, height=900)
    buf.seek(0)
    return fig, buf

# =====================================================
# HTML EXPORT
# =====================================================
def generate_html_preview(elements, title="Wireframe"):
    """Generate interactive HTML preview of wireframe."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f9fafb; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            h1 {{ color: #1f2937; margin-bottom: 30px; }}
            .wireframe {{ background: white; border: 2px solid #e5e7eb; border-radius: 8px; padding: 20px; position: relative; aspect-ratio: 1; }}
            .element {{ position: absolute; border: 2px solid #d1d5db; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 500; color: #6b7280; overflow: hidden; }}
            .element:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.1); z-index: 10; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎨 {title}</h1>
            <div class="wireframe">
    """
    
    for el in elements:
        colors = ELEMENT_COLORS.get(el.get("type", "card"), ELEMENT_COLORS["card"])
        html_content += f"""
                <div class="element" style="
                    left: {el['x']}%;
                    top: {el['y']}%;
                    width: {el['width']}%;
                    height: {el['height']}%;
                    background-color: {colors['fill']};
                    border-color: {colors['border']};
                    color: {colors['text']};
                " title="{el['label']} ({el['type']})">
                    {el['label']}
                </div>
        """
    
    html_content += """
            </div>
        </div>
    </body>
    </html>
    """
    return html_content.encode("utf-8")

# =====================================================
# STREAMLIT INTERFACE
# =====================================================
st.set_page_config(
    page_title="AI Wireframe Generator",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main-header { font-size: 2.5em; font-weight: 700; background: linear-gradient(135deg, #3B82F6 0%, #10B981 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 10px; }
    .subtitle { font-size: 1.1em; color: #6B7280; margin-bottom: 30px; }
    </style>
    <div class="main-header">🎨 AI Wireframe Generator</div>
    <div class="subtitle">Create professional wireframes from text descriptions using Gemini 2.5 Pro</div>
""", unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Settings")
    theme = st.radio("Theme", ["Light", "Dark"], index=0)
    theme_lower = theme.lower()
    
    st.divider()
    st.markdown("### 📝 Tips")
    st.markdown("""
    - Be specific about layout structure
    - Mention key components (navbar, cards, etc.)
    - Describe the purpose of the interface
    - Example: "E-commerce product page with hero image, product details, reviews section, and related items"
    """)

# Main input area
col1, col2 = st.columns([3, 1])
with col1:
    user_prompt = st.text_area(
        "💡 Describe your UI idea:",
        placeholder="Example: A food delivery app homepage with search bar, restaurant cards, filters, and bottom navigation.",
        height=120,
        key="prompt_input"
    )

with col2:
    st.write("")
    st.write("")
    generate_btn = st.button("🚀 Generate", use_container_width=True, type="primary")

# Generate wireframe
if generate_btn and user_prompt.strip():
    model = configure_gemini(API_KEY)
    
    with st.spinner("🧠 Generating wireframe..."):
        outline, elements = generate_wireframe_and_outline(model, user_prompt)
    
    if outline and elements:
        # Display results in tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📐 Wireframe", "📋 Outline", "📊 Layout Data", "💾 Export"])
        
        with tab1:
            st.subheader("Wireframe Preview")
            fig, buf = render_wireframe_plotly(elements, theme_lower)
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.subheader("Interface Outline")
            st.markdown(outline)
        
        with tab3:
            st.subheader("Layout Data (JSON)")
            st.json({"elements": elements})
        
        with tab4:
            st.subheader("Download Options")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.download_button(
                    label="📸 PNG Wireframe",
                    data=buf,
                    file_name=f"wireframe_{timestamp}.png",
                    mime="image/png",
                    use_container_width=True
                )
            
            with col2:
                json_data = json.dumps({"elements": elements}, indent=2).encode("utf-8")
                st.download_button(
                    label="📄 JSON Layout",
                    data=json_data,
                    file_name=f"wireframe_{timestamp}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col3:
                html_data = generate_html_preview(elements, "Wireframe")
                st.download_button(
                    label="🌐 HTML Preview",
                    data=html_data,
                    file_name=f"wireframe_{timestamp}.html",
                    mime="text/html",
                    use_container_width=True
                )
    else:
        st.error("❌ Could not generate wireframe. Please try refining your prompt.")

elif not user_prompt.strip() and generate_btn:
    st.warning("⚠️ Please enter a description of your UI idea.")
