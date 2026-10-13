import streamlit as st
from PIL import Image
from io import BytesIO
from constants import MAX_FILE_SIZE, ALLOWED_IMAGE_TYPES, MAX_IMAGE_DIMENSIONS, CHAT_SUGGESTIONS

def load_css():
    """Load custom CSS from external file with proper UTF-8 encoding and error handling."""
    try:
        with open("styles.css", "r", encoding="utf-8", errors="ignore") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

    except FileNotFoundError:
        load_fallback_css()
    except UnicodeDecodeError as e:
        load_fallback_css()
    except Exception as e:
        load_fallback_css()

def load_fallback_css():
    """Load fallback CSS when main CSS file fails"""
    fallback_css = """
    .main {
        font-family: 'Arial', sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .stButton > button {
        background: linear-gradient(135deg, #ff6b6b 0%, #ffa726 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    }
    .feature-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .success-message, .error-message {
        padding: 15px 20px;
        border-radius: 12px;
        margin: 15px 0;
        font-weight: 600;
    }
    .success-message {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
    }
    .error-message {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
    }
    h1, h2, h3, h4, h5, h6, p {
        color: white !important;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
    }
    /* Compact chat suggestions */
    .compact-suggestion-btn {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 11px;
        margin: 2px;
        cursor: pointer;
        transition: all 0.2s ease;
        display: inline-block;
        text-decoration: none;
    }
    .compact-suggestion-btn:hover {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.08) 100%);
        transform: translateY(-1px);
    }
    """
    st.markdown(f"<style>{fallback_css}</style>", unsafe_allow_html=True)
def bytes_to_pil(b: bytes) -> Image.Image:
    """Convert bytes to PIL Image with error handling."""
    try:
        if not b:
            return None
        return Image.open(BytesIO(b))
    except Exception as e:
        return None

def pil_to_bytes(img: Image.Image) -> bytes:
    """Convert PIL Image to bytes with error handling."""
    try:
        if not img:
            return None
        buf = BytesIO()
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    except Exception as e:
        return None

def safe_image_processing(uploaded_file, max_size=MAX_IMAGE_DIMENSIONS):
    """Safely process uploaded images with size limits and validation"""
    try:
        if not uploaded_file:
            return None
            
        if uploaded_file.size > MAX_FILE_SIZE:
            raise ValueError(f"File too large (max {MAX_FILE_SIZE // (1024*1024)}MB)")
       
        if uploaded_file.type not in ALLOWED_IMAGE_TYPES:
            raise ValueError(f"Invalid file type. Only {', '.join(ALLOWED_IMAGE_TYPES)} allowed")
        
        image = Image.open(uploaded_file)
   
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        return pil_to_bytes(image)
        
    except ValueError:
        raise
    except Exception as e:
        raise ValueError("Invalid image file")

def render_profile_avatar(user, size=100):
    """Render user profile avatar (circular image or initials) with error handling."""
    try:
        if user and len(user) > 6 and user[6]:  
            img = bytes_to_pil(user[6])
            if img:
                st.image(img, width=size)
                return
        
        initial = "U"  
        if user and len(user) > 1 and user[1]:
            initial = user[1][0].upper()
        
        st.markdown(f"""
        <div style="width: {size}px; height: {size}px; border-radius: 50%; 
                   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   display: flex; align-items: center; justify-content: center; 
                   margin: 0 auto; color: white; font-size: {size//3}px; font-weight: bold;
                   box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);">
            {initial}
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        

        st.markdown(f"""
        <div style="width: {size}px; height: {size}px; border-radius: 50%; 
                   background: #6b7280; display: flex; align-items: center; 
                   justify-content: center; margin: 0 auto; color: white; 
                   font-size: {size//3}px; font-weight: bold;">
            U
        </div>
        """, unsafe_allow_html=True)

def render_feature_card(title, description, icon, start_color, end_color):
    """Render a feature card with gradient background and error handling."""
    try:
        title = str(title).replace('<', '&lt;').replace('>', '&gt;')
        description = str(description).replace('<', '&lt;').replace('>', '&gt;')
        icon = str(icon)
        
        st.markdown(f"""
        <div class="feature-card" style="
            background: linear-gradient(145deg, {start_color}20 0%, {end_color}20 100%);
            border-left: 4px solid {start_color};
        ">
            <h3 style="margin: 0 0 15px 0; color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.8);">
                {icon} {title}
            </h3>
            <p style="margin: 0; color: rgba(255,255,255,0.9); line-height: 1.6; text-shadow: 1px 1px 3px rgba(0,0,0,0.7);">
                {description}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:

        st.markdown(f"### {icon} {title}")
        st.markdown(description)

def render_success_message(message):
    """Render a success message with styling and error handling."""
    try:
        message = str(message).replace('<', '&lt;').replace('>', '&gt;')
        st.markdown(f"""
        <div class="success-message">
            ✅ {message}
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.success(f"✅ {message}")

def render_error_message(message):
    """Render an error message with styling and error handling."""
    try:
        message = str(message).replace('<', '&lt;').replace('>', '&gt;')
        st.markdown(f"""
        <div class="error-message">
            ⚠️ {message}
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"⚠️ {message}")

def render_chat_suggestions():
    """Render compact suggested chat prompts for new users."""
    try:
        st.markdown("""
        <div style="
            margin: 10px 0 15px 0;
            padding: 12px 15px;
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.03) 100%);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
        ">
            <div style="text-align: center; margin-bottom: 8px;">
                <span style="color: rgba(255,255,255,0.9); font-size: 16px; font-weight: 500; text-shadow: 1px 1px 3px rgba(0,0,0,0.7);">
                    💡 Quick start:
                </span>
            </div>
        """, unsafe_allow_html=True)
        
        suggestions = CHAT_SUGGESTIONS[:4] 

        cols1 = st.columns(2)
        for i in range(min(2, len(suggestions))):
            with cols1[i]:
                if st.button(
                    suggestions[i], 
                    key=f"suggestion_{i}",
                    help=f"Ask: {suggestions[i]}",
                    use_container_width=True
                ):
                    st.session_state['chat_input'] = suggestions[i]
                    st.rerun()
        
        if len(suggestions) > 2:
            cols2 = st.columns(2)
            for i in range(2, min(4, len(suggestions))):
                with cols2[i-2]:
                    if st.button(
                        suggestions[i], 
                        key=f"suggestion_{i}",
                        help=f"Ask: {suggestions[i]}",
                        use_container_width=True
                    ):
                        st.session_state['chat_input'] = suggestions[i]
                        st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        
    except Exception as e:

        st.markdown("**Try asking:** " + " | ".join(CHAT_SUGGESTIONS[:2]))

def render_chat_welcome():
    """Render compact welcome message for new chats with error handling."""
    try:
        st.markdown("""
        <div style="
            text-align: center; 
            padding: 15px 12px; 
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.04) 100%);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 12px;
            margin: 10px 0;
            color: white;
        ">
            <h3 style="color: white; margin-bottom: 8px; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); font-size: 50px;">
               ⚖️ Legal Assistant
            </h3>
            <p style="color: rgba(255,255,255,0.85); margin-bottom: 10px; font-size: 30px; text-shadow: 1px 1px 3px rgba(0,0,0,0.7);">
                Indian legal research & guidance
            </p>
            <div style="
                display: flex; 
                flex-wrap: wrap; 
                justify-content: center; 
                gap: 6px; 
                margin: 8px 0;
                max-width: 400px;
                margin-left: auto;
                margin-right: auto;
            ">
                <span style="
                    background: rgba(251, 191, 36, 0.15); 
                    padding: 4px 8px; 
                    border-radius: 12px; 
                    font-size: 20px;
                    color: #fbbf24;
                    border: 1px solid rgba(251, 191, 36, 0.25);
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.6);
                ">📚 IPC</span>
                <span style="
                    background: rgba(59, 130, 246, 0.15); 
                    padding: 4px 8px; 
                    border-radius: 12px; 
                    font-size: 20px;
                    color: #60a5fa;
                    border: 1px solid rgba(59, 130, 246, 0.25);
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.6);
                ">⚖️ Cases</span>
                <span style="
                    background: rgba(16, 185, 129, 0.15); 
                    padding: 4px 8px; 
                    border-radius: 12px; 
                    font-size: 20px;
                    color: #34d399;
                    border: 1px solid rgba(16, 185, 129, 0.25);
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.6);
                ">🔍 Research</span>
              
        </div>""", unsafe_allow_html=True)
        
        render_chat_suggestions()
        
    except Exception as e:

        st.markdown("### ⚖️ Legal Assistant")
        st.markdown("Indian legal research & guidance")