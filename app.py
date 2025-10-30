# ===========================================================
# AI Wireframe Generator - Streamlit Safe Deployment Version
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
API_KEY = os.getenv("GOOGLE_APIKEY")

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
    if not api_key:
        st.error("❌ Missing GOOGLE_APIKEY in your environment or secrets.")
        st.stop()
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-pro")

# =====================================================
# WIREFRAME GENERATION
# =====================================================
def generate_wireframe_and_outline(model, user_prompt):
    prompt = f"""
    You are a senior UX/UI designer with 10+ years of experience. Create a professional wireframe.

    REQUIREMENTS:
    1. Generate a clean hierarchical OUTLINE describing the interface structure.
    2. Create a WIREFRAME_JSON with layout coordinates.
    3. Use realistic proportions and spacing (0–100 grid).
    4. Include: navbar, button, input, card, label, image, footer, section, grid, divider.
    5. Maintain margins and balanced layout.

    USER REQUEST:
    "{user_prompt}"

    OUTPUT FORMAT:
    OUTLINE:
    [detailed outline here]

    WIREFRAME_JSON:
    [valid JSON only]
    """

    response = model.generate_content(prompt)
    text = response.text

    try:
        outline = text.split("OUTLINE:")[1].split("WIREFRAME_JSON:")[0].strip()
        json_text = text.split("WIREFRAME_JSON:")[1].strip()

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
    fig = go.Figure()

    for el in elements:
        x, y, w, h = el["x"], el["y"], el["width"], el["height"]
        y_top = 100 - y
        y_bottom = 100 - (y + h)

        rect_x = [x, x + w, x + w, x, x]
        rect_y = [y_top, y_top, y_bottom, y_bottom, y_top]

        el_type = el.get("type", "card")
        colors = ELEMENT_COLORS.get(el_type, ELEMENT_COLORS["card"])

        fig.add_trace(go.Scatter(
            x=rect_x, y=rect_y, mode="lines",
            line=dict(color=colors["border"], width=2),
            fill="toself", fillcolor=colors["fill"],
            hoverinfo="text",
            hovertext=f"<b>{el['label']}</b><br>Type: {el_type}<br>Size: {w:.1f}×{h:.1f}",
            showlegend=False
        ))

        fig.add_trace(go.Scatter(
            x=[x + w/2], y=[y_top - h/2],
            text=[el["label"]], mode="text",
            textfont=dict(size=max(8, min(12, w/3)), color=colors["text"]),
            hoverinfo="skip"
        ))

    fig.update_layout(
        width=800, height=800,
        xaxis=dict(visible=False, range=[0, 100]),
        yaxis=dict(visible=False, range=[0, 100]),
        plot_bgcolor="#FFFFFF" if theme == "light" else "#1F2937",
        paper_bgcolor="#F9FAFB" if theme == "light" else "#111827",
        margin=dict(l=10, r=10, t=10, b=10)
    )

    # Generate in-memory PNG (safe for Streamlit Cloud)
    try:
        buf = BytesIO(fig.to_image(format="png", width=900, height=900, scale=3))
    except Exception:
        buf = None  # fallback in case Kaleido not supported
    return fig, buf

# =====================================================
# HTML PREVIEW EXPORT
# =====================================================
def generate_html_preview(elements, title="Wireframe"):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{ font-family: sans-serif; background: #f9fafb; padding: 20px; }}
            .wireframe {{ position: relative; width: 800px; height: 800px; border: 1px solid #ccc; }}
            .element {{
                position: absolute; border: 2px solid #aaa; border-radius: 4px;
                display: flex; align-items: center; justify-content: center;
                font-size: 12px; color: #333;
            }}
        </style>
    </head>
    <body>
        <h2>🎨 {title}</h2>
        <div class="wireframe">
    """
    for el in elements:
        colors = ELEMENT_COLORS.get(el.get("type", "card"), ELEMENT_COLORS["card"])
        html += f"""
        <div class="element" style="
            left:{el['x']}%;
            top:{el['y']}%;
            width:{el['width']}%;
            height:{el['height']}%;
            background:{colors['fill']};
            border-color:{colors['border']};
            color:{colors['text']};
        ">{el['label']}</div>
        """
    html += "</div></body></html>"
    return html.encode("utf-8")

# =====================================================
# STREAMLIT INTERFACE
# =====================================================
st.set_page_config(page_title="AI Wireframe Generator", layout="wide")

st.markdown("""
    <h1 style='color:#3B82F6;'>🎨 AI Wireframe Generator</h1>
    <p style='color:#6B7280;'>Generate professional UI wireframes from text using Gemini 2.5 Pro</p>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Settings")
    theme = st.radio("Theme", ["Light", "Dark"], index=0)
    theme_lower = theme.lower()

    st.divider()
    st.markdown("### 📝 Prompt Tips")
    st.markdown("""
    - Be specific (mention navbar, footer, etc.)
    - Example: *Dashboard with sidebar, cards, charts, and user profile section.*
    """)

user_prompt = st.text_area(
    "💡 Describe your UI idea:",
    placeholder="Example: A travel booking homepage with search, cards, filters, and testimonials.",
    height=120,
)

if st.button("🚀 Generate Wireframe", use_container_width=True):
    if not user_prompt.strip():
        st.warning("⚠️ Please enter a description.")
        st.stop()

    model = configure_gemini(API_KEY)
    with st.spinner("🧠 Generating wireframe..."):
        outline, elements = generate_wireframe_and_outline(model, user_prompt)

    if outline and elements:
        tab1, tab2, tab3, tab4 = st.tabs(["📐 Wireframe", "📋 Outline", "📊 JSON", "💾 Export"])

        with tab1:
            st.subheader("Wireframe Preview")
            fig, buf = render_wireframe_plotly(elements, theme_lower)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("Interface Outline")
            st.markdown(outline)

        with tab3:
            st.subheader("Layout JSON")
            st.json({"elements": elements})

        with tab4:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                "📄 Download JSON",
                json.dumps({"elements": elements}, indent=2).encode("utf-8"),
                file_name=f"wireframe_{timestamp}.json",
                mime="application/json",
                use_container_width=True
            )

            html_data = generate_html_preview(elements, "Wireframe Preview")
            st.download_button(
                "🌐 Download HTML Preview",
                html_data,
                file_name=f"wireframe_{timestamp}.html",
                mime="text/html",
                use_container_width=True
            )

            if buf:
                st.download_button(
                    "📸 Download PNG",
                    buf,
                    file_name=f"wireframe_{timestamp}.png",
                    mime="image/png",
                    use_container_width=True
                )
            else:
                st.info("⚠️ PNG export not available on this platform.")
    else:
        st.error("❌ Could not generate wireframe. Try again with a clearer prompt.")
