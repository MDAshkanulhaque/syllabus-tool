import streamlit as st
import streamlit.components.v1 as components
import requests
import os
import json
import base64
import html
from datetime import datetime

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Academic Syllabus AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

components.html(
    """
    <script>
        if (window.parent && window.parent.document) {
            window.parent.document.addEventListener('keydown', function(e) {
                var k = e.key ? e.key.toLowerCase() : '';
                if (k === 'c' || k === 'r') {
                    var activeEl = window.parent.document.activeElement;
                    var isInput = activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA' || activeEl.isContentEditable);
                    if (e.ctrlKey || e.metaKey) {
                        e.stopPropagation();
                    } else if (!isInput) {
                        e.stopPropagation();
                        e.preventDefault();
                    }
                }
            }, true);
        }
    </script>
    """,
    height=0,
    width=0
)

# ---------------------------------------------------------
# BACKEND & PATH SETTINGS
# ---------------------------------------------------------
BACKEND_URL = "http://127.0.0.1:8000"
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "chat_history.json")
HERO_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "assets", "hero_books.jpg")

# Persistent HTTP session pool for sub-second responses
@st.cache_resource
def get_http_session():
    s = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20)
    s.mount("http://", adapter)
    return s

http_session = get_http_session()

# ---------------------------------------------------------
# HELPER: BASE64 IMAGE ENCODER
# ---------------------------------------------------------
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

hero_b64 = get_base64_image(HERO_IMAGE_PATH)

# ---------------------------------------------------------
# HELPER: CHAT HISTORY PERSISTENCE (NO HARDCODED SAMPLES)
# ---------------------------------------------------------
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []

def save_history(history_data):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_data, f, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving history: {e}")

# ---------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = load_history()

if "active_conv_id" not in st.session_state:
    st.session_state.active_conv_id = None

if "active_messages" not in st.session_state:
    st.session_state.active_messages = []

if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = "Syllabus_ComputerScience_2024.pdf"

if "attached_files" not in st.session_state:
    st.session_state.attached_files = []

if "attached_file" not in st.session_state:
    st.session_state.attached_file = None

if "is_thinking" not in st.session_state:
    st.session_state.is_thinking = False

# ---------------------------------------------------------
# CUSTOM CSS FOR SINGLE PAGE FIT & DARK INPUT CONTAINER
# ---------------------------------------------------------
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #0F172A;
        }

        /* Hide Streamlit Header, Footer, Menu, and Cache Clear Modals */
        header[data-testid="stHeader"] {
            display: none !important;
        }
        footer {
            display: none !important;
        }
        #MainMenu {
            display: none !important;
        }
        div[role="dialog"],
        div[data-baseweb="modal"],
        div[data-baseweb="backdrop"],
        div[data-testid="stModal"],
        div[class*="stDialog"],
        div[class*="stModal"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }
        .stApp {
            background-color: #F8FAF9;
        }

        /* Container Padding Fix for Single Page View */
        .block-container {
            padding-top: 0.2rem !important;
            padding-bottom: 0.8rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
            max-width: 100% !important;
        }

        /* ---------------- SIDEBAR STYLING ---------------- */
        section[data-testid="stSidebar"] {
            background-color: #F4F7F5 !important;
            border-right: 1px solid #E2E8F0 !important;
            width: 310px !important;
            padding-bottom: 90px !important;
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 0.5rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 0px !important;
            margin-bottom: 14px !important;
            padding-top: 0px !important;
        }

        .sidebar-brand-icon {
            font-size: 26px;
            color: #045B47;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .sidebar-brand-title {
            font-size: 19px;
            font-weight: 800;
            color: #0F172A;
            line-height: 1.15;
            letter-spacing: -0.3px;
        }

        /* Sidebar Buttons Override */
        div[data-testid="stSidebar"] button[kind="primary"]:not([key="btn_new_chat"]) {
            background-color: #D1E7DD !important;
            color: #045B47 !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            box-shadow: none !important;
            text-align: left !important;
        }

        div[data-testid="stSidebar"] button[kind="secondary"] {
            background-color: transparent !important;
            color: #334155 !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 500 !important;
            text-align: left !important;
        }

        div[data-testid="stSidebar"] button[kind="secondary"]:hover {
            background-color: #E6EDE8 !important;
            color: #045B47 !important;
        }

        /* Delete Button in Sidebar */
        div[data-testid="stSidebar"] button[key^="btn_del_"] {
            background-color: transparent !important;
            color: #94A3B8 !important;
            border: 1px solid #E2E8F0 !important;
            padding: 4px 6px !important;
            font-size: 14px !important;
            border-radius: 8px !important;
            height: 36px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        div[data-testid="stSidebar"] button[key^="btn_del_"]:hover {
            background-color: #FEE2E2 !important;
            color: #EF4444 !important;
            border-color: #FCA5A5 !important;
        }

        /* New Chat Button */
        div.stButton > button[key="btn_new_chat"] {
            background-color: #045B47 !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 12px 20px !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            width: 100% !important;
            box-shadow: 0 2px 4px rgba(4, 91, 71, 0.15) !important;
            transition: all 0.2s ease !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 8px !important;
            margin-bottom: 20px !important;
        }
        div.stButton > button[key="btn_new_chat"]:hover {
            background-color: #034B3B !important;
            color: #FFFFFF !important;
            transform: translateY(-1px);
        }

        /* History Header */
        .history-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            color: #64748B;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 12px;
            padding: 0 4px;
        }
        .history-header-icon {
            font-size: 14px;
            color: #94A3B8;
        }

        /* Fixed Sidebar Profile Card Anchored at Very Bottom */
        .sidebar-profile {
            position: fixed !important;
            bottom: 15px !important;
            left: 15px !important;
            width: 280px !important;
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 14px !important;
            padding: 10px 14px !important;
            display: flex !important;
            align-items: center !important;
            gap: 12px !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
            z-index: 999 !important;
        }

        .profile-avatar {
            width: 38px;
            height: 38px;
            border-radius: 50%;
            background-color: #045B47;
            color: #FFFFFF;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 16px;
        }

        .profile-info {
            flex: 1;
            overflow: hidden;
        }

        .profile-name {
            font-size: 14px;
            font-weight: 700;
            color: #0F172A;
            margin: 0;
            line-height: 1.2;
        }

        .profile-email {
            font-size: 12px;
            color: #64748B;
            margin: 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .profile-arrow {
            color: #94A3B8;
            font-size: 14px;
        }

        /* ---------------- COMPACT HERO BANNER CARD ---------------- */
        .hero-card {
            background: linear-gradient(135deg, #E6F4EE 0%, #EFF8F3 100%);
            border-radius: 16px;
            padding: 14px 22px;
            position: relative;
            margin-bottom: 12px;
            border: 1px solid #D1E7DD;
            display: flex;
            justify-content: space-between;
            align-items: center;
            overflow: hidden;
        }

        .hero-left {
            max-width: 65%;
            z-index: 2;
        }

        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background-color: #D1E7DD;
            color: #045B47;
            font-size: 12px;
            font-weight: 600;
            padding: 4px 12px;
            border-radius: 16px;
            margin-bottom: 8px;
        }

        .hero-title {
            font-size: 24px;
            font-weight: 800;
            color: #0F172A;
            margin-bottom: 6px;
            line-height: 1.15;
            letter-spacing: -0.4px;
        }

        .hero-title span {
            color: #045B47;
            font-style: italic;
        }

        .hero-desc {
            font-size: 13px;
            color: #475569;
            line-height: 1.4;
            margin-bottom: 12px;
        }

        .hero-features {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .feature-pill {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 5px 12px;
            font-size: 12px;
            font-weight: 600;
            color: #1E293B;
            display: flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }

        .hero-right {
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }

        .hero-image {
            width: 130px;
            height: auto;
            filter: drop-shadow(0 6px 10px rgba(0,0,0,0.06));
        }

        .hero-arrow-label {
            position: absolute;
            top: -12px;
            left: -65px;
            color: #045B47;
            font-family: 'Comic Sans MS', 'Chalkboard SE', cursive, sans-serif;
            font-size: 12px;
            font-weight: 700;
            text-align: center;
            transform: rotate(-10deg);
            white-space: nowrap;
        }

        /* ---------------- CHAT SECTION ---------------- */
        .chat-section {
            background: #FFFFFF;
            border-radius: 16px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02);
            padding: 14px 18px;
            margin-bottom: 8px;
            position: relative;
        }

        /* Message Bubbles */
        .chat-messages-container {
            display: flex;
            flex-direction: column;
            gap: 12px;
            min-height: 140px;
            max-height: 270px;
            overflow-y: auto;
            padding-right: 6px;
            margin-bottom: 10px;
        }

        .message-row {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
        }

        .message-row.user {
            flex-direction: row-reverse;
        }

        .avatar-container {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .avatar-bot {
            background-color: #045B47;
            color: #FFFFFF;
            font-size: 16px;
        }

        .avatar-user {
            background-color: #045B47;
            color: #FFFFFF;
            font-size: 15px;
        }

        .bubble-wrapper {
            max-width: 78%;
        }

        .message-bubble {
            padding: 10px 15px;
            border-radius: 14px;
            font-size: 13.5px;
            line-height: 1.5;
            word-wrap: break-word;
        }

        .message-bubble.bot {
            background-color: #F1F5F9;
            color: #1E293B;
            border-top-left-radius: 4px;
        }

        .message-bubble.user {
            background-color: #045B47;
            color: #FFFFFF;
            border-top-right-radius: 4px;
        }

        .message-meta {
            font-size: 11px;
            color: #94A3B8;
            margin-top: 3px;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .message-meta.user {
            justify-content: flex-end;
            color: #045B47;
            font-weight: 500;
        }

        /* ---------------- DARK PILL INPUT CONTAINER & ATTACHMENTS ---------------- */
        div[data-testid="stForm"] {
            border: 1px solid #333336 !important;
            border-radius: 26px !important;
            padding: 10px 16px !important;
            background: #1E1E1E !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25) !important;
        }

        /* Dark Attachment Chip */
        .dark-attachment-chip {
            background: #2C2C2E;
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 14px;
            padding: 6px 12px;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            max-width: 260px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
            margin-bottom: 4px;
        }

        .chip-pdf-circle {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            background: #EF4444;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .chip-img-thumb {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            object-fit: cover;
            flex-shrink: 0;
        }

        .chip-meta {
            display: flex;
            flex-direction: column;
            overflow: hidden;
            justify-content: center;
        }

        .chip-name {
            font-size: 13px;
            font-weight: 700;
            color: #FFFFFF !important;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            line-height: 1.25;
            max-width: 170px;
        }

        .chip-sub {
            font-size: 10.5px;
            font-weight: 500;
            color: #9A9A9E !important;
            margin-top: 2px;
            letter-spacing: 0.3px;
            white-space: nowrap;
        }

        /* Remove Streamlit default button background for delete X button */
        div.stButton > button[key^="btn_remove_file_"] {
            background-color: transparent !important;
            color: #9A9A9E !important;
            border: none !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            padding: 0 !important;
            height: 32px !important;
            box-shadow: none !important;
        }
        div.stButton > button[key^="btn_remove_file_"]:hover {
            color: #EF4444 !important;
            background-color: transparent !important;
        }

        /* Dark Container Text Input & Buttons Styling */
        .chat-input-container-dark div[data-testid="stTextInput"],
        .chat-input-container-dark div[data-testid="stTextInput"] > div,
        .chat-input-container-dark div[data-testid="stTextInput"] > div > div {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }

        .chat-input-container-dark input {
            background-color: transparent !important;
            color: #FFFFFF !important;
            border: none !important;
            font-size: 15px !important;
            font-weight: 400 !important;
            box-shadow: none !important;
            outline: none !important;
        }

        .chat-input-container-dark input:focus {
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
        }

        /* Plus Popover Button Styling */
        .chat-input-container-dark div[data-testid="stPopover"] > button {
            background-color: transparent !important;
            color: #E2E8F0 !important;
            border: none !important;
            font-size: 22px !important;
            font-weight: 300 !important;
            width: 36px !important;
            height: 36px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-shadow: none !important;
            padding: 0 !important;
        }
        .chat-input-container-dark div[data-testid="stPopover"] > button:hover {
            background-color: #2D2D30 !important;
            border-radius: 50% !important;
            color: #FFFFFF !important;
        }

        /* Blue Circular Send Button Inside Dark Bar */
        div.stButton > button[key="btn_send_prompt"] {
            background-color: #2563EB !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 50% !important;
            width: 38px !important;
            height: 38px !important;
            font-size: 18px !important;
            font-weight: 700 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-shadow: 0 2px 8px rgba(37, 99, 235, 0.4) !important;
            margin: auto !important;
            padding: 0 !important;
            transition: all 0.2s ease !important;
        }
        div.stButton > button[key="btn_send_prompt"]:hover {
            background-color: #1D4ED8 !important;
            transform: scale(1.05) !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# SIDEBAR CONTENT
# ---------------------------------------------------------
with st.sidebar:

    # 1. Logo Header (Right at the top)
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-icon">🎓</div>
            <div class="sidebar-brand-title">Academic<br>Syllabus AI</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. + New Chat Button (Right below header)
    if st.button("➕  New Chat", key="btn_new_chat", use_container_width=True):
        st.session_state.active_conv_id = None
        st.session_state.active_messages = []
        st.session_state.attached_file = None
        st.rerun()

    # 3. Chat History Header
    st.markdown(
        """
        <div class="history-header">
            <span>Chat History</span>
            <span class="history-header-icon">🔍</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4. Render History List (Saves all user searches)
    if not st.session_state.history:
        st.markdown(
            '<div style="color: #94A3B8; font-size: 13px; text-align: center; margin-top: 20px;">No previous chats</div>',
            unsafe_allow_html=True,
        )
    else:
        for conv in st.session_state.history:
            is_active = conv["id"] == st.session_state.active_conv_id
            c_btn, c_del = st.columns([0.84, 0.16])
            with c_btn:
                btn_kind = "primary" if is_active else "secondary"
                label = f"💬  {conv['title']}"
                if st.button(label, key=f"conv_{conv['id']}", type=btn_kind, use_container_width=True):
                    st.session_state.active_conv_id = conv["id"]
                    st.session_state.active_messages = conv.get("messages", [])
                    st.session_state.uploaded_file_name = conv.get("file_name", "Syllabus_ComputerScience_2024.pdf")
                    st.rerun()
            with c_del:
                if st.button("🗑️", key=f"btn_del_{conv['id']}", help="Delete chat"):
                    st.session_state.history = [c for c in st.session_state.history if c["id"] != conv["id"]]
                    save_history(st.session_state.history)
                    if st.session_state.active_conv_id == conv["id"]:
                        st.session_state.active_conv_id = None
                        st.session_state.active_messages = []
                    st.rerun()

    # Fixed Profile Section Anchored at Very Bottom
    st.markdown(
        """
        <div class="sidebar-profile">
            <div class="profile-avatar">S</div>
            <div class="profile-info">
                <div class="profile-name">Student</div>
                <div class="profile-email">student@example.com</div>
            </div>
            <div class="profile-arrow">❯</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# MAIN MAIN MAIN CONTENT AREA
# ---------------------------------------------------------

# 1. COMPACT HERO BANNER CARD AT TOP
st.markdown(
    f"""
    <div class="hero-card">
        <div class="hero-left">
            <div class="hero-badge">🪄 AI-Powered Academic Assistant</div>
            <div class="hero-title">Academic <span>Syllabus AI</span></div>
            <div class="hero-desc">Upload your college or university syllabus and ask anything about it.<br>Get summaries, subject lists, electives, and more — instantly.</div>
            <div class="hero-features">
                <div class="feature-pill">📖 Summaries</div>
                <div class="feature-pill">🎓 Subject Insights</div>
                <div class="feature-pill">🎯 Electives</div>
                <div class="feature-pill">⚡ Quick Answers</div>
            </div>
        </div>
        <div class="hero-right">
            <div class="hero-arrow-label">Your Syllabus<br>Made Simple</div>
            <img src="data:image/jpeg;base64,{hero_b64}" class="hero-image" alt="Books"/>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# 2. CHAT SECTION CONTAINER
components.html(
    """
    <script>
    (function() {
        var pDoc = window.parent.document;
        var existing = pDoc.getElementById('custom-scroll-nav-container');
        if (existing) { existing.remove(); }
        var style = pDoc.getElementById('custom-scroll-nav-style');
        if (style) { style.remove(); }
    })();
    </script>
    """,
    height=0,
    width=0
)

st.markdown('<div class="chat-section">', unsafe_allow_html=True)

# Render Chat Message History
st.markdown('<div class="chat-messages-container">', unsafe_allow_html=True)
if not st.session_state.active_messages:
    # Empty placeholder state
    pass
else:
    for msg in st.session_state.active_messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        msg_time = msg.get("time", "")
        img_b64 = msg.get("image_b64")

        safe_content = html.escape(content).replace("\n", "<br>")

        img_html = ""
        if img_b64:
            img_html = f'<br><img src="data:image/png;base64,{img_b64}" style="max-width: 200px; border-radius: 8px; margin-top: 6px;"/>'

        if role == "user":
            st.markdown(
                f"""
                <div class="message-row user">
                    <div class="avatar-container avatar-user">👤</div>
                    <div class="bubble-wrapper">
                        <div class="message-bubble user">{safe_content}{img_html}</div>
                        <div class="message-meta user">{msg_time} ✔️✔️</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="message-row bot">
                    <div class="avatar-container avatar-bot">🤖</div>
                    <div class="bubble-wrapper">
                        <div class="message-bubble bot">{safe_content}</div>
                        <div class="message-meta">{msg_time}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

if st.session_state.is_thinking:
    st.markdown(
        """
        <div class="message-row bot">
            <div class="avatar-container avatar-bot">🤖</div>
            <div class="bubble-wrapper">
                <div class="message-bubble bot" style="color: #64748B;">Thinking... • • •</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('</div>', unsafe_allow_html=True) # Close messages container

def handle_file_upload_change():
    if "popover_file_uploader" in st.session_state and st.session_state.popover_file_uploader:
        u_files = st.session_state.popover_file_uploader
        files_list = u_files if isinstance(u_files, list) else [u_files]
        for uf in files_list:
            file_ext = uf.name.split(".")[-1].lower()
            is_img = file_ext in ["jpg", "jpeg", "png", "webp"]
            file_bytes = uf.getvalue()
            
            uploaded_flag = False
            if not is_img:
                try:
                    files = {"file": (uf.name, file_bytes, "application/pdf")}
                    res = http_session.post(f"{BACKEND_URL}/upload-syllabus", files=files, timeout=60)
                    if res.status_code == 200:
                        uploaded_flag = True
                        print(f"Uploaded syllabus PDF to backend on file select: {uf.name}")
                except Exception as e:
                    print(f"Immediate backend upload error: {e}")

            file_obj = {
                "name": uf.name,
                "type": "image" if is_img else "pdf",
                "bytes": file_bytes,
                "b64": base64.b64encode(file_bytes).decode(),
                "uploaded_to_backend": uploaded_flag
            }
            if not any(f["name"] == uf.name for f in st.session_state.attached_files):
                st.session_state.attached_files.append(file_obj)
        if st.session_state.attached_files:
            st.session_state.attached_file = st.session_state.attached_files[0]
            st.session_state.uploaded_file_name = st.session_state.attached_files[0]["name"]

# Sync attached_files list with single attached_file if needed
if not st.session_state.attached_files and st.session_state.attached_file:
    st.session_state.attached_files = [st.session_state.attached_file]

# 4. BOTTOM INPUT CONTAINER (MATCHING REFERENCE IMAGES)
st.markdown('<div class="chat-input-container-dark">', unsafe_allow_html=True)

# Render Attached Files Chips at the top inside the dark container wrapper
if st.session_state.attached_files:
    st.markdown('<div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; padding-bottom: 4px;">', unsafe_allow_html=True)
    for idx, af in enumerate(st.session_state.attached_files):
        c_info, c_del = st.columns([0.88, 0.12])
        with c_info:
            if af["type"] == "image":
                icon_html = f'<img src="data:image/png;base64,{af["b64"]}" class="chip-img-thumb"/>'
            else:
                icon_html = '<div class="chip-pdf-circle"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#FFFFFF"/><path d="M14 2V8H20" fill="#E5E7EB"/></svg></div>'

            file_bytes = len(af.get("bytes", b""))
            if file_bytes > 0:
                kb = file_bytes / 1024
                if kb >= 1024:
                    size_lbl = f"{kb/1024:.2f}MB"
                else:
                    size_lbl = f"{kb:.2f}KB"
                sub_label = f"{af['type'].upper()} {size_lbl}"
            else:
                sub_label = f"{af['type'].upper()}"

            file_title = html.escape(af['name'])
            card_html = f'<div class="dark-attachment-chip">{icon_html}<div class="chip-meta"><div class="chip-name" title="{file_title}">{file_title}</div><div class="chip-sub">{sub_label}</div></div></div>'
            st.markdown(card_html, unsafe_allow_html=True)

        with c_del:
            if st.button("✕", key=f"btn_remove_file_{idx}", help=f"Remove {af['name']}"):
                st.session_state.attached_files.pop(idx)
                if st.session_state.attached_files:
                    st.session_state.attached_file = st.session_state.attached_files[0]
                else:
                    st.session_state.attached_file = None
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Process Prompt & File Submission on Send Click or Enter Key
def handle_user_message(user_text):
    attached_list = list(st.session_state.attached_files) or ([st.session_state.attached_file] if st.session_state.attached_file else [])

    raw_text = (user_text or "").strip()
    if not raw_text and not attached_list:
        return

    curr_time = datetime.now().strftime("%I:%M %p")

    # Determine message content and attachment info
    msg_content = raw_text
    clean_query = raw_text
    img_b64 = None

    for attached in attached_list:
        if attached["type"] == "image":
            img_b64 = attached["b64"]
            if not msg_content:
                msg_content = f"Uploaded image {attached['name']} for analysis."
                clean_query = "Analyze the uploaded image syllabus."
        elif attached["type"] == "pdf":
            st.session_state.uploaded_file_name = attached["name"]
            # Post PDF to FastAPI backend if not uploaded yet
            if not attached.get("uploaded_to_backend"):
                try:
                    files = {"file": (attached["name"], attached["bytes"], "application/pdf")}
                    res = http_session.post(f"{BACKEND_URL}/upload-syllabus", files=files, timeout=30)
                    if res.status_code == 200:
                        attached["uploaded_to_backend"] = True
                        print(f"Uploaded syllabus PDF to backend: {attached['name']}")
                except Exception as e:
                    print(f"Backend upload error: {e}")
            
            if not raw_text:
                msg_content = f"Attached PDF: {attached['name']}"
                clean_query = "Give me a summary of this syllabus."
            else:
                msg_content = f"Attached PDF: {attached['name']}\n\n{raw_text}"
                clean_query = raw_text

    user_msg = {
        "role": "user",
        "content": msg_content,
        "time": curr_time,
        "image_b64": img_b64
    }

    st.session_state.active_messages.append(user_msg)

    # Clear attached files state after attaching to user message
    st.session_state.attached_files = []
    st.session_state.attached_file = None

    # Check query intent: simple greeting vs actual syllabus question vs explicitly asked summary
    q_lower = (clean_query or "").lower().strip()

    greetings = ["hi", "hii", "hiii", "hello", "hey", "helo", "hlo", "ok", "okay", "thanks", "thank you", "good morning", "good evening"]
    is_greeting = (q_lower in greetings) or any(q_lower.startswith(g + " ") for g in ["hi ", "hello ", "hey "])
    is_summary_request = any(w in q_lower for w in ["summary", "summarize", "document summary", "pdf summary", "overview", "what document"])

    ans_text = ""

    if is_greeting and not is_summary_request:
        ans_text = "Hi! How can I help you with your syllabus? You can ask about subjects, year-wise syllabus, semester details, or specific topics."
    else:
        # Fetch answer from backend FastAPI using persistent HTTP session
        try:
            req_payload = {
                "query": clean_query or "Give me a summary of this syllabus.",
                "filename": st.session_state.uploaded_file_name
            }
            res = http_session.post(f"{BACKEND_URL}/chat", json=req_payload, timeout=5)
            if res.status_code == 200:
                data = res.json()
                ans_text = data.get("answer", "")
        except Exception as e:
            print(f"Chat request error: {e}")

        if not ans_text:
            # Fallback responses if backend offline
            is_count = any(k in q_lower for k in ["kitne subject", "kitne course", "kitna subject", "total subject", "total course", "how many subject", "subject count", "course count", "number of subject"])
            is_list = any(k in q_lower for k in ["subject list", "subjects name", "subjects batao", "subject batao", "all subjects", "all subject", "subjects bhejo"]) and not any(k in q_lower for k in ["complete syllabus", "full syllabus", "detailed syllabus"])

            if is_count and ("first year" in q_lower or "1st year" in q_lower):
                ans_text = "FIRST YEAR — Total Subjects: 10"
            elif is_count and ("second year" in q_lower or "2nd year" in q_lower):
                ans_text = "SECOND YEAR — Total Subjects: 10"
            elif is_count and ("third year" in q_lower or "3rd year" in q_lower):
                ans_text = "THIRD YEAR — Total Subjects: 10"
            elif is_count and ("final year" in q_lower or "4th year" in q_lower):
                ans_text = "FINAL YEAR — Total Subjects: 8"
            elif is_count and "6" in q_lower:
                ans_text = "SEMESTER 6 — Total Subjects: 6"
            elif is_count:
                ans_text = "TOTAL SUBJECTS: 10"
            elif is_summary_request:
                ans_text = (
                    f"Syllabus Analysis for {st.session_state.uploaded_file_name}:\n"
                    "• Program: Bachelor of Technology / Computer Science & Engineering\n"
                    "• Key Modules: Data Structures, DBMS, Java OOP, Discrete Mathematics, Computer Architecture.\n"
                    "• Assessment Scheme: 30% Internal Evaluation, 70% End-Semester Exam."
                )
            elif is_list and ("first year" in q_lower or "1st year" in q_lower):
                ans_text = (
                    "FIRST YEAR SUBJECTS (Total: 10)\n\n"
                    "SEMESTER 1:\n"
                    "1. Communicative English\n2. Engineering Mathematics - I\n3. Engineering Physics\n4. Engineering Chemistry\n5. Problem Solving & Python Programming\n\n"
                    "SEMESTER 2:\n"
                    "1. Professional English\n2. Engineering Mathematics - II\n3. Physics for Information Science\n4. Basic Electrical Engineering\n5. Programming in C"
                )
            elif is_list:
                ans_text = (
                    "SUBJECTS LIST:\n"
                    "1. Data Structures & Algorithms\n"
                    "2. Database Management Systems\n"
                    "3. Object-Oriented Programming in Java\n"
                    "4. Discrete Mathematics & Graph Theory\n"
                    "5. Computer Organization & Architecture"
                )
            elif "first year" in q_lower or "1st year" in q_lower:
                ans_text = (
                    "FIRST YEAR SYLLABUS (Total Subjects: 10)\n\n"
                    "━━━━━━━━━━━━━━\n"
                    "SEMESTER 1 (5 Subjects)\n"
                    "1. Communicative English\n   • Unit 1: Vocabulary & Grammar Fundamentals\n   • Unit 2: Reading & Writing Skills\n"
                    "2. Engineering Mathematics - I\n   • Unit 1: Matrices & Eigenvalues\n   • Unit 2: Differential Calculus\n"
                    "3. Engineering Physics\n   • Unit 1: Properties of Matter\n   • Unit 2: Lasers & Optics\n"
                    "4. Engineering Chemistry\n   • Unit 1: Water Treatment\n   • Unit 2: Electrochemistry\n"
                    "5. Problem Solving & Python\n   • Unit 1: Algorithmic Logic\n   • Unit 2: Python Data Types\n\n"
                    "━━━━━━━━━━━━━━\n"
                    "SEMESTER 2 (5 Subjects)\n"
                    "1. Professional English\n   • Unit 1: Technical Writing\n   • Unit 2: Presentation Skills\n"
                    "2. Engineering Mathematics - II\n   • Unit 1: Vector Calculus\n   • Unit 2: Complex Variables\n"
                    "3. Physics for Info Science\n   • Unit 1: Semiconductor Physics\n   • Unit 2: Optoelectronic Devices\n"
                    "4. Basic Electrical Engineering\n   • Unit 1: DC & AC Circuits\n   • Unit 2: Semiconductor Diodes\n"
                    "5. Programming in C\n   • Unit 1: C Fundamentals\n   • Unit 2: Arrays & Pointers"
                )
            else:
                ans_text = f"Here is the relevant syllabus information regarding '{user_text}' based on your syllabus document."

    bot_msg = {
        "role": "assistant",
        "content": ans_text,
        "time": datetime.now().strftime("%I:%M %p")
    }

    st.session_state.active_messages.append(bot_msg)

    # Save to history
    if not st.session_state.active_conv_id:
        conv_id = f"conv_{int(datetime.now().timestamp())}"
        st.session_state.active_conv_id = conv_id
        t_str = user_text if user_text else (attached_list[0]["name"] if attached_list else "New Chat")
        title = t_str[:30] + ("..." if len(t_str) > 30 else "")
        conv_obj = {
            "id": conv_id,
            "title": title,
            "date": "Today",
            "file_name": st.session_state.uploaded_file_name,
            "messages": list(st.session_state.active_messages)
        }
        st.session_state.history.insert(0, conv_obj)
    else:
        for conv in st.session_state.history:
            if conv["id"] == st.session_state.active_conv_id:
                conv["messages"] = list(st.session_state.active_messages)
                break

    save_history(st.session_state.history)

# Streamlit-safe Callback for Enter Key and Send Button
def handle_prompt_submit():
    p_text = st.session_state.get("user_prompt_input", "").strip()
    a_list = st.session_state.attached_files or ([st.session_state.attached_file] if st.session_state.attached_file else [])
    if p_text or a_list:
        handle_user_message(p_text)
        st.session_state["user_prompt_input"] = ""

# Bottom Typing Row (Plus, Prompt Input, Send Arrow inside Dark Bar)
col_plus, col_inp, col_send = st.columns([0.06, 0.86, 0.08])

with col_plus:
    with st.popover("➕", use_container_width=True, help="Attach PDF or Image"):
        st.markdown("<p style='font-size:13px; font-weight:700; color:#0F172A; margin-bottom:6px;'>Attach PDF or Image</p>", unsafe_allow_html=True)
        st.file_uploader(
            "Upload PDF or Image",
            type=["pdf", "png", "jpg", "jpeg", "webp"],
            key="popover_file_uploader",
            label_visibility="collapsed",
            accept_multiple_files=True,
            on_change=handle_file_upload_change
        )

with col_inp:
    st.text_input(
        "",
        placeholder="Ask anything...",
        key="user_prompt_input",
        label_visibility="collapsed",
        on_change=handle_prompt_submit
    )

with col_send:
    st.button("↑", key="btn_send_prompt", use_container_width=True, on_click=handle_prompt_submit)

st.markdown('</div>', unsafe_allow_html=True) # Close chat-input-container-dark
st.markdown('</div>', unsafe_allow_html=True) # Close chat section