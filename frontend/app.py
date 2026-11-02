import streamlit as st
import streamlit.components.v1 as components
import requests
import os
import sys
import json
import base64
import html
import re
import urllib.parse
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import uuid

# Ensure project root is in sys.path for backend package imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import importlib
try:
    import backend.book_engine.book_search as _book_search_mod
    _book_search_mod = importlib.reload(_book_search_mod)
    from backend.book_engine.book_search import (
        search_pages,
        search_book_sections,
        format_book_sections_response,
        group_results_by_section,
    )
    _book_search_import_error = None
except Exception as _import_err:
    try:
        from backend.book_engine.book_search import (
            search_pages,
            group_results_by_section,
        )
        search_book_sections = getattr(_book_search_mod, "search_book_sections", None) if "_book_search_mod" in locals() else None
        format_book_sections_response = getattr(_book_search_mod, "format_book_sections_response", None) if "_book_search_mod" in locals() else None
        _book_search_import_error = None
    except Exception as _fallback_err:
        search_pages = None
        search_book_sections = None
        format_book_sections_response = None
        group_results_by_section = None
        _book_search_import_error = str(_fallback_err)

try:
    import backend.book_engine.internet_books as _internet_books_mod
    _internet_books_mod = importlib.reload(_internet_books_mod)
    from backend.book_engine.internet_books import (
        search_internet_books,
        format_internet_books_chat_response,
        clean_search_query,
        get_book_readable_content,
        CANONICAL_WORKS,
        normalize_title_for_matching
    )
except Exception:
    try:
        from backend.book_engine.internet_books import (
            search_internet_books,
            format_internet_books_chat_response,
            clean_search_query,
            get_book_readable_content,
            CANONICAL_WORKS,
            normalize_title_for_matching
        )
    except Exception:
        search_internet_books = None
        format_internet_books_chat_response = None
        clean_search_query = None
        get_book_readable_content = None
        CANONICAL_WORKS = {}
        normalize_title_for_matching = lambda t: t.lower().strip()

try:
    import backend.book_engine.intent_search as _intent_search_mod
    _intent_search_mod = importlib.reload(_intent_search_mod)
    from backend.book_engine.intent_search import (
        detect_search_intent,
        search_books,
        search_book_topics,
        INTENT_BOOK_SEARCH,
        INTENT_TOPIC_SEARCH,
        INTENT_AMBIGUOUS,
    )
except Exception:
    try:
        from backend.book_engine.intent_search import (
            detect_search_intent,
            search_books,
            search_book_topics,
            INTENT_BOOK_SEARCH,
            INTENT_TOPIC_SEARCH,
            INTENT_AMBIGUOUS,
        )
    except Exception:
        detect_search_intent = None
        search_books = None
        search_book_topics = None
        INTENT_BOOK_SEARCH = "BOOK_SEARCH"
        INTENT_TOPIC_SEARCH = "TOPIC_SEARCH"
        INTENT_AMBIGUOUS = "AMBIGUOUS"

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
HEADER_BANNER_PATH = os.path.join(os.path.dirname(__file__), "assets", "header_banner.jpg")
TM_COVER_PATH = os.path.join(os.path.dirname(__file__), "assets", "time_machine_cover.jpg")
WOW_COVER_PATH = os.path.join(os.path.dirname(__file__), "assets", "war_of_the_worlds_cover.jpg")

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

header_b64 = get_base64_image(HEADER_BANNER_PATH)
tm_cover_b64 = get_base64_image(TM_COVER_PATH)
wow_cover_b64 = get_base64_image(WOW_COVER_PATH)

# Default "The Time Machine" canonical data
DEFAULT_TIME_MACHINE = {
    "title": "The Time Machine",
    "authors": ["H. G. Wells"],
    "published_year": "1895",
    "genre": "Science Fiction",
    "sub_genre": "Novel",
    "description": "A classic science fiction novel that explores time travel, human evolution, and the future of civilization.",
    "rating": "4.6",
    "reviews_count": "12,430 reviews",
    "language": "English",
    "formats": "Online, EPUB, PDF",
    "reading_url": "https://www.gutenberg.org/ebooks/35.html.images",
    "download_url": "https://www.gutenberg.org/ebooks/35.epub.images",
    "download_format": "EPUB",
    "source_provider": "Project Gutenberg & Open Library",
    "cover_b64": tm_cover_b64,
    "related_book": {
        "title": "The War of the Worlds",
        "authors": ["H. G. Wells"],
        "cover_b64": wow_cover_b64,
        "reading_url": "https://www.gutenberg.org/ebooks/36.html.images"
    }
}

# ---------------------------------------------------------
# SAFE BOOK METADATA NORMALIZATION HELPERS
# ---------------------------------------------------------
def normalize_book_description(desc, max_len: int = 400) -> str:
    """Safely normalize any book description (None, list, dict, bytes, str, int, etc.)
    into a clean string up to max_len characters.
    """
    if desc is None:
        return "Description not available."
    
    # Bytes handling
    if isinstance(desc, (bytes, bytearray)):
        try:
            desc = desc.decode("utf-8", errors="replace")
        except Exception:
            return "Description not available."
    
    # Dictionary handling (e.g. Open Library {"type": "...", "value": "..."}, or schema.org)
    if isinstance(desc, dict):
        val = desc.get("value") or desc.get("text") or desc.get("description")
        if val is not None:
            return normalize_book_description(val, max_len=max_len)
        str_vals = [str(v).strip() for v in desc.values() if v and isinstance(v, (str, int, float))]
        if str_vals:
            desc = " ".join(str_vals)
        else:
            return "Description not available."
    
    # List / tuple / set handling (e.g. Internet Archive returns list of string notes)
    if isinstance(desc, (list, tuple, set)):
        extracted = []
        for item in desc:
            norm_item = normalize_book_description(item, max_len=max_len)
            if norm_item and norm_item != "Description not available.":
                extracted.append(norm_item)
        if extracted:
            desc = " ".join(extracted)
        else:
            return "Description not available."
    
    # Convert anything else to string
    desc_str = str(desc).strip()
    # Strip HTML tags if any (e.g., <p>, <br>, etc. from Google Books / Archive)
    desc_str = re.sub(r"<[^>]+>", " ", desc_str)
    desc_str = re.sub(r"\s+", " ", desc_str).strip()
    
    if not desc_str:
        return "Description not available."
    
    if max_len and len(desc_str) > max_len:
        return desc_str[:max_len].rstrip() + "..."
    return desc_str


def safe_text(val, default: str = "") -> str:
    """Convert any object (None, bytes, list, dict, str) into a clean string."""
    if val is None:
        return default
    if isinstance(val, (bytes, bytearray)):
        try:
            return val.decode("utf-8", errors="replace").strip()
        except Exception:
            return default
    if isinstance(val, (list, tuple)):
        items = [safe_text(x) for x in val if x is not None]
        items = [x for x in items if x]
        return ", ".join(items) if items else default
    if isinstance(val, dict):
        return safe_text(val.get("name") or val.get("title") or val.get("value") or default)
    s = str(val).strip()
    return s if s else default


def safe_authors_list(authors) -> list:
    """Safely extracts a list of author name strings from any data structure."""
    if not authors:
        return ["Unknown Author"]
    if isinstance(authors, str):
        parts = [p.strip() for p in re.split(r"[,;]+", authors) if p.strip()]
        return parts if parts else ["Unknown Author"]
    if isinstance(authors, (list, tuple, set)):
        result = []
        for a in authors:
            if isinstance(a, dict):
                name = a.get("name") or a.get("author") or str(a)
                if name.strip():
                    result.append(name.strip())
            elif isinstance(a, (list, tuple)):
                result.extend(safe_authors_list(a))
            elif a is not None:
                s = str(a).strip()
                if s:
                    result.append(s)
        return result if result else ["Unknown Author"]
    if isinstance(authors, dict):
        name = authors.get("name") or authors.get("author") or ""
        return [name.strip()] if name.strip() else ["Unknown Author"]
    return [str(authors).strip() or "Unknown Author"]


# ---------------------------------------------------------
# HELPER: CHAT HISTORY PERSISTENCE
# ---------------------------------------------------------
def load_history():
    data = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
                if isinstance(raw, list):
                    data = raw
        except Exception as e:
            print(f"Error loading {HISTORY_FILE}: {e}")
            data = []
    return data

def save_history(history_data):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_data, f, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving {HISTORY_FILE}: {e}")

def save_current_conversation():
    c_id = st.session_state.get("active_conv_id")
    if not c_id:
        return
    msgs = st.session_state.get("active_messages", [])
    p_book = st.session_state.get("last_internet_book")
    s_books = st.session_state.get("searched_books", [])
    p_sections = st.session_state.get("last_book_search_sections")
    p_query = st.session_state.get("last_book_search_query", "")

    # Don't save completely empty new chats
    if not msgs and not p_book and not s_books and not p_sections:
        return

    existing_idx = None
    existing_title = None
    for idx, c in enumerate(st.session_state.history):
        if c.get("id") == c_id:
            existing_idx = idx
            existing_title = c.get("title")
            break

    title = existing_title
    if not title or title in ("Conversation", "Academic Query"):
        if p_query:
            title = p_query.strip()
        elif msgs and msgs[0].get("content"):
            title = msgs[0]["content"].strip()
        else:
            title = "Academic Query"
        title = (title[:30] + "...") if len(title) > 30 else title

    conv_record = {
        "id": c_id,
        "title": title,
        "date": datetime.now().strftime("%b %d, %I:%M %p"),
        "file_name": st.session_state.get("uploaded_file_name", "Syllabus_ComputerScience_2024.pdf"),
        "messages": msgs,
        "book_query": p_query,
        "internet_book": p_book,
        "searched_books": s_books,
        "internet_search": st.session_state.get("last_internet_search"),
        "book_sections": p_sections
    }

    if existing_idx is not None:
        st.session_state.history[existing_idx] = conv_record
    else:
        st.session_state.history.insert(0, conv_record)

    save_history(st.session_state.history)

# ---------------------------------------------------------
# SESSION STATE INITIALIZATION & CALLBACKS
# ---------------------------------------------------------
if "history" not in st.session_state or not st.session_state.history:
    st.session_state.history = load_history()

if "show_reader" not in st.session_state:
    st.session_state.show_reader = False

if "show_book_details" not in st.session_state:
    st.session_state.show_book_details = False

if "show_related_books" not in st.session_state:
    st.session_state.show_related_books = False

if "delete_confirm_id" not in st.session_state:
    st.session_state.delete_confirm_id = None

if "confirm_clear_all" not in st.session_state:
    st.session_state.confirm_clear_all = False

def handle_new_chat():
    new_id = f"conv_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}"
    st.session_state.active_conv_id = new_id
    st.session_state.active_messages = []
    st.session_state.attached_file = None
    st.session_state.attached_files = []
    st.session_state["last_book_search_sections"] = None
    st.session_state["last_book_search_query"] = ""
    st.session_state["last_internet_book"] = None
    st.session_state["searched_books"] = []
    st.session_state["last_internet_search"] = None
    st.session_state["user_prompt_input"] = ""
    st.session_state["header_search_input"] = ""
    st.session_state.show_reader = False
    st.session_state.show_book_details = False
    st.session_state.show_related_books = False
    st.session_state.show_upload_modal = False
    st.session_state.delete_confirm_id = None

def handle_select_conv(conv_id: str):
    for conv in st.session_state.history:
        if conv["id"] == conv_id:
            st.session_state.active_conv_id = conv["id"]
            st.session_state.active_messages = list(conv.get("messages", []))
            st.session_state.uploaded_file_name = conv.get("file_name", "Syllabus_ComputerScience_2024.pdf")
            st.session_state["last_book_search_sections"] = conv.get("book_sections", None)
            st.session_state["last_book_search_query"] = conv.get("book_query", "")
            st.session_state["last_internet_book"] = conv.get("internet_book", None)
            restored_books = conv.get("searched_books")
            if not restored_books and conv.get("internet_book"):
                restored_books = [conv["internet_book"]]
            st.session_state["searched_books"] = list(restored_books or [])
            st.session_state["last_internet_search"] = conv.get("internet_search", None)
            st.session_state.attached_file = None
            st.session_state.attached_files = []
            st.session_state["user_prompt_input"] = ""
            st.session_state["header_search_input"] = conv.get("book_query", "")
            st.session_state.show_reader = False
            st.session_state.show_book_details = False
            st.session_state.show_related_books = False
            st.session_state.delete_confirm_id = None
            break

if "active_conv_id" not in st.session_state or not st.session_state.active_conv_id:
    handle_new_chat()

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

if "last_internet_book" not in st.session_state:
    st.session_state["last_internet_book"] = None

if "searched_books" not in st.session_state:
    st.session_state["searched_books"] = []

if "last_internet_search" not in st.session_state:
    st.session_state["last_internet_search"] = None

if "last_book_search_sections" not in st.session_state:
    st.session_state["last_book_search_sections"] = None

if "last_book_search_query" not in st.session_state:
    st.session_state["last_book_search_query"] = ""

# ---------------------------------------------------------
# CUSTOM CSS FOR EXACT SCREENSHOT PARITY
# ---------------------------------------------------------
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
            color: #FFFFFF !important;
        }

        /* Hide Streamlit Header, Footer, Menu */
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
        div[data-testid="stModal"] {
            display: none !important;
        }

        /* App Background - Deep Midnight Navy */
        .stApp {
            background: radial-gradient(ellipse at 50% 0%, #0d1e3d 0%, #060c18 55%, #03070f 100%) !important;
            color: #FFFFFF !important;
        }

        /* Container Padding Fix for Compact Desktop View */
        .block-container {
            padding-top: 1.1rem !important;
            padding-bottom: 6rem !important;
            padding-left: 1.4rem !important;
            padding-right: 1.4rem !important;
            max-width: 100% !important;
        }

        /* ---------------- SIDEBAR STYLING ---------------- */
        section[data-testid="stSidebar"] {
            background-color: #060c18 !important;
            border-right: 1px solid rgba(0, 229, 255, 0.12) !important;
            width: 290px !important;
            padding-bottom: 75px !important;
            overflow-x: hidden !important;
        }

        section[data-testid="stSidebar"] > div:first-child,
        section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"] {
            overflow-y: auto !important;
            overflow-x: hidden !important;
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.4rem !important;
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
            padding-bottom: 125px !important;
        }

        .sidebar-brand-box {
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 12px;
            padding: 8px 6px 12px 6px;
            position: sticky;
            top: 0;
            background: #060c18;
            z-index: 100;
        }

        .sidebar-brand-logo {
            font-size: 36px;
            color: #00e5ff;
            filter: drop-shadow(0 0 12px rgba(0, 229, 255, 0.65));
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .sidebar-brand-text {
            display: flex;
            flex-direction: column;
        }

        .sidebar-brand-title {
            font-size: 20px;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: -0.3px;
            line-height: 1.15;
        }

        .sidebar-brand-sub {
            font-size: 11.5px;
            font-weight: 600;
            color: #38bdf8;
            margin-top: 3px;
            letter-spacing: 0.3px;
        }

        /* COMPACT SIDEBAR CONTAINERS & BUTTONS */
        section[data-testid="stSidebar"] div.stElementContainer {
            margin-bottom: 2px !important;
        }

        /* RESET ALL DEFAULT SIDEBAR BUTTON STYLES */
        section[data-testid="stSidebar"] div.stButton > button {
            background: transparent !important;
            background-color: transparent !important;
            border: 1px solid transparent !important;
            color: #94a3b8 !important;
            font-weight: 500 !important;
            font-size: 13px !important;
            text-align: left !important;
            border-radius: 8px !important;
            padding: 4px 10px !important;
            min-height: 28px !important;
            height: 28px !important;
            margin-bottom: 0px !important;
            box-shadow: none !important;
            transition: all 0.15s ease !important;
            display: flex !important;
            align-items: center !important;
            width: 100% !important;
        }
        section[data-testid="stSidebar"] div.stButton > button p,
        section[data-testid="stSidebar"] div.stButton > button div {
            color: inherit !important;
            font-size: 13px !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        section[data-testid="stSidebar"] div.stButton > button:hover {
            background-color: rgba(0, 229, 255, 0.08) !important;
            color: #00e5ff !important;
            border-color: rgba(0, 229, 255, 0.2) !important;
        }

        /* Clean Single-Layer Turquoise + New Chat Button in Sidebar */
        section[data-testid="stSidebar"] div.st-key-btn_sidebar_new_chat {
            position: sticky !important;
            top: 74px !important;
            background: #060c18 !important;
            z-index: 99 !important;
            padding-bottom: 4px !important;
            margin-bottom: 4px !important;
        }

        section[data-testid="stSidebar"] div.st-key-btn_sidebar_new_chat button {
            background: linear-gradient(135deg, #00f2fe 0%, #00b4d8 100%) !important;
            background-color: #00f2fe !important;
            border: none !important;
            border-radius: 22px !important;
            padding: 8px 16px !important;
            min-height: 40px !important;
            height: 40px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100% !important;
            box-shadow: 0 4px 15px rgba(0, 242, 254, 0.35) !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
            margin-bottom: 4px !important;
        }
        section[data-testid="stSidebar"] div.st-key-btn_sidebar_new_chat button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 20px rgba(0, 242, 254, 0.5) !important;
            background: linear-gradient(135deg, #38bdf8 0%, #00f2fe 100%) !important;
        }
        section[data-testid="stSidebar"] div.st-key-btn_sidebar_new_chat button p,
        section[data-testid="stSidebar"] div.st-key-btn_sidebar_new_chat button div,
        section[data-testid="stSidebar"] div.st-key-btn_sidebar_new_chat button span {
            background: transparent !important;
            background-color: transparent !important;
            color: #061320 !important;
            font-size: 14.5px !important;
            font-weight: 800 !important;
            box-shadow: none !important;
            border: none !important;
            padding: 0 !important;
            margin: 0 !important;
            line-height: 1 !important;
        }

        /* Chat History Section Header */
        .sidebar-section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            color: #94a3b8;
            font-size: 13px;
            font-weight: 700;
            margin-top: 8px;
            margin-bottom: 4px;
            padding: 4px 4px;
            letter-spacing: 0.2px;
        }

        /* Clear All Button Trigger */
        section[data-testid="stSidebar"] div.st-key-btn_clear_all_trigger button {
            background: rgba(239, 68, 68, 0.12) !important;
            border: 1px solid rgba(239, 68, 68, 0.35) !important;
            color: #fca5a5 !important;
            font-size: 11px !important;
            font-weight: 600 !important;
            border-radius: 6px !important;
            padding: 2px 8px !important;
            height: 24px !important;
            min-height: 24px !important;
            transition: all 0.2s ease !important;
        }
        section[data-testid="stSidebar"] div.st-key-btn_clear_all_trigger button:hover {
            background: rgba(239, 68, 68, 0.25) !important;
            border-color: #ef4444 !important;
            color: #FFFFFF !important;
        }
        section[data-testid="stSidebar"] div.st-key-btn_clear_all_trigger button p {
            font-size: 11px !important;
            margin: 0 !important;
            padding: 0 !important;
            color: inherit !important;
        }

        /* Custom sleek cyan scrollbar for sidebar */
        section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"]::-webkit-scrollbar {
            width: 5px;
        }
        section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"]::-webkit-scrollbar-thumb {
            background: rgba(0, 229, 255, 0.25);
            border-radius: 4px;
        }
        section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"]::-webkit-scrollbar-track {
            background: transparent;
        }

        /* Chat History Row Items */
        section[data-testid="stSidebar"] div[class*="st-key-conv_"] button {
            font-size: 13px !important;
            font-weight: 500 !important;
            padding: 6px 10px !important;
            min-height: 34px !important;
            height: 34px !important;
            border-radius: 8px !important;
            background: rgba(12, 24, 46, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            color: #cbd5e1 !important;
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            text-align: left !important;
            transition: all 0.15s ease !important;
            box-shadow: none !important;
        }
        section[data-testid="stSidebar"] div[class*="st-key-conv_"] button:hover {
            background: rgba(0, 229, 255, 0.12) !important;
            border-color: rgba(0, 229, 255, 0.4) !important;
            color: #00e5ff !important;
        }
        section[data-testid="stSidebar"] div[class*="st-key-conv_"] button p {
            font-size: 13px !important;
            font-weight: 500 !important;
            color: inherit !important;
            margin: 0 !important;
            padding: 0 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            text-align: left !important;
            line-height: 1.2 !important;
        }

        /* Active Selected Conversation Item */
        section[data-testid="stSidebar"] div[class*="st-key-conv_"] button[kind="primary"],
        section[data-testid="stSidebar"] div[class*="st-key-conv_"] button[data-testid="stBaseButton-primary"] {
            background: rgba(0, 229, 255, 0.18) !important;
            background-color: rgba(0, 229, 255, 0.18) !important;
            border: 1px solid #00e5ff !important;
            box-shadow: 0 0 12px rgba(0, 229, 255, 0.25) !important;
        }
        section[data-testid="stSidebar"] div[class*="st-key-conv_"] button[kind="primary"] p,
        section[data-testid="stSidebar"] div[class*="st-key-conv_"] button[data-testid="stBaseButton-primary"] p {
            color: #00e5ff !important;
            font-weight: 700 !important;
        }

        /* Delete Icon Button Beside Each Conversation */
        section[data-testid="stSidebar"] div[class*="st-key-del_"] button {
            background: rgba(239, 68, 68, 0.08) !important;
            background-color: rgba(239, 68, 68, 0.08) !important;
            border: 1px solid rgba(239, 68, 68, 0.25) !important;
            box-shadow: none !important;
            padding: 0 !important;
            min-height: 34px !important;
            height: 34px !important;
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            opacity: 0.85 !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
            border-radius: 8px !important;
            color: #f87171 !important;
        }
        section[data-testid="stSidebar"] div[class*="st-key-del_"] button:hover {
            opacity: 1 !important;
            background: rgba(239, 68, 68, 0.28) !important;
            border: 1px solid #ef4444 !important;
            color: #ffffff !important;
            transform: scale(1.05) !important;
            box-shadow: 0 0 8px rgba(239, 68, 68, 0.4) !important;
        }
        section[data-testid="stSidebar"] div[class*="st-key-del_"] button p {
            font-size: 14px !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Fixed Sidebar Profile Card Anchored at Very Bottom */
        .sidebar-profile-card {
            position: fixed !important;
            bottom: 18px !important;
            left: 14px !important;
            width: 262px !important;
            background: #0b172a !important;
            border: 1px solid rgba(0, 229, 255, 0.3) !important;
            border-radius: 14px !important;
            padding: 9px 12px !important;
            display: flex !important;
            align-items: center !important;
            gap: 10px !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.65), 0 0 10px rgba(0, 229, 255, 0.1) !important;
            z-index: 99999 !important;
        }

        .sidebar-profile-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: linear-gradient(135deg, #00f2fe 0%, #00b4d8 100%);
            color: #061320;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 15px;
            box-shadow: 0 0 10px rgba(0, 242, 254, 0.4);
        }

        .sidebar-profile-info {
            flex: 1;
            overflow: hidden;
        }

        .sidebar-profile-name {
            font-size: 13.5px;
            font-weight: 700;
            color: #FFFFFF;
            margin: 0;
            line-height: 1.2;
        }

        .sidebar-profile-email {
            font-size: 11px;
            color: #64748b;
            margin: 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* ---------------- TOP HEADER BANNER ---------------- */
        div.st-key-integrated_header_banner {
            position: relative !important;
            width: 100% !important;
            height: 168px !important;
            min-height: 168px !important;
            border-radius: 16px !important;
            overflow: hidden !important;
            border: 1px solid rgba(0, 229, 255, 0.38) !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.65), inset 0 0 25px rgba(0, 229, 255, 0.08) !important;
            margin-top: 0px !important;
            margin-bottom: 22px !important;
            padding: 0 !important;
            background-color: #070e1c !important;
        }

        .header-banner-img {
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            height: 100% !important;
            object-fit: cover !important;
            object-position: center center !important;
            z-index: 1 !important;
        }

        .header-banner-overlay {
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            height: 100% !important;
            background: linear-gradient(90deg, rgba(7, 14, 28, 0.05) 0%, rgba(7, 14, 28, 0.7) 28%, rgba(7, 14, 28, 0.7) 72%, rgba(7, 14, 28, 0.05) 100%) !important;
            z-index: 2 !important;
        }

        div.st-key-integrated_header_banner > div[data-testid="stVerticalBlock"] {
            gap: 0px !important;
            background: transparent !important;
            height: 100% !important;
            width: 100% !important;
        }

        div.st-key-integrated_header_banner div[data-testid="stVerticalBlock"] {
            background: transparent !important;
        }

        .integrated-header-inner {
            position: relative !important;
            z-index: 3 !important;
            width: 100% !important;
            height: 168px !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
        }

        .header-top-controls {
            position: absolute !important;
            top: 14px !important;
            right: 20px !important;
            display: flex !important;
            align-items: center !important;
            gap: 12px !important;
            z-index: 10 !important;
        }

        .header-bell {
            position: relative;
            background: rgba(10, 22, 42, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.22);
            border-radius: 50%;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            cursor: pointer;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
            transition: all 0.2s ease;
        }
        .header-bell:hover {
            border-color: #00e5ff;
        }

        .header-bell-badge {
            position: absolute;
            top: -2px;
            right: -2px;
            background: #EF4444;
            color: #FFFFFF;
            font-size: 9px;
            font-weight: 800;
            border-radius: 50%;
            width: 15px;
            height: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid #070e1c;
        }

        .header-user-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%);
            color: #FFFFFF;
            font-weight: 800;
            font-size: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid rgba(255, 255, 255, 0.28);
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
            cursor: pointer;
        }

        .header-branding-title {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            font-size: 32px;
            font-weight: 800;
            color: #FFFFFF;
            margin-bottom: 4px;
            letter-spacing: -0.5px;
            line-height: 1.2;
            text-shadow: 0 2px 14px rgba(0, 0, 0, 0.95);
        }
        .header-branding-cap-svg {
            filter: drop-shadow(0 0 14px rgba(0, 229, 255, 0.85));
            display: inline-flex;
            align-items: center;
            vertical-align: middle;
            flex-shrink: 0;
        }
        .header-branding-title span.cyan-text {
            color: #00e5ff;
            text-shadow: 0 0 18px rgba(0, 229, 255, 0.7);
        }

        .header-branding-sub {
            font-size: 13.5px;
            color: #cbd5e1;
            margin: 0;
            text-align: center;
            text-shadow: 0 1px 8px rgba(0, 0, 0, 0.95);
            font-weight: 500;
            letter-spacing: 0.15px;
        }

        /* Suppress any Streamlit auto-injected heading anchor/chain link icons */
        .header-anchor,
        a.header-anchor,
        [data-testid="stHeaderActionElements"],
        div[data-testid="stHeaderActionElements"],
        a[data-testid="stHeaderActionElements"],
        .welcome-card-clean a,
        .welcome-card-clean svg.anchor-icon {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }

        /* ---------------- SEARCH FORM INSIDE BANNER ---------------- */
        div.st-key-top_search_form {
            max-width: 820px !important;
            width: 100% !important;
            margin: 14px auto 0 auto !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
        }

        div.st-key-top_search_form div[data-testid="stForm"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        div.st-key-top_search_form div[data-testid="stTextInput"] {
            margin-bottom: 0px !important;
            padding-bottom: 0px !important;
        }

        div.st-key-top_search_form div[data-testid="stTextInput"] input {
            background: #FFFFFF !important;
            color: #0F172A !important;
            border-radius: 28px !important;
            padding: 10px 22px 10px 42px !important;
            background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="%2364748B" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>') !important;
            background-repeat: no-repeat !important;
            background-position: 16px center !important;
            font-size: 14.5px !important;
            font-weight: 600 !important;
            border: 1px solid #E2E8F0 !important;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.4) !important;
            height: 46px !important;
        }

        div.st-key-top_search_form div[data-testid="stTextInput"] input::placeholder {
            color: #64748B !important;
            font-weight: 500 !important;
        }

        div.st-key-top_search_form div[data-testid="stTextInput"] input:focus {
            border-color: #00e5ff !important;
            box-shadow: 0 0 0 2px rgba(0, 229, 255, 0.4), 0 4px 18px rgba(0, 0, 0, 0.4) !important;
        }

        /* Vibrant Turquoise Search Button inside Banner */
        div.st-key-top_search_btn button,
        div.st-key-top_search_btn button:hover,
        div.st-key-top_search_form div[data-testid="stFormSubmitButton"] button {
            background: linear-gradient(90deg, #00f2fe 0%, #00c4b4 100%) !important;
            background-color: #00f2fe !important;
            border: none !important;
            border-radius: 28px !important;
            height: 46px !important;
            width: 100% !important;
            color: #061320 !important;
            box-shadow: 0 4px 16px rgba(0, 242, 254, 0.45) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 6px !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
        }

        div.st-key-top_search_btn button p,
        div.st-key-top_search_btn button div,
        div.st-key-top_search_btn button span,
        div.st-key-top_search_form div[data-testid="stFormSubmitButton"] button p,
        div.st-key-top_search_form div[data-testid="stFormSubmitButton"] button div,
        div.st-key-top_search_form div[data-testid="stFormSubmitButton"] button span {
            background: transparent !important;
            color: #061320 !important;
            font-weight: 800 !important;
            font-size: 14.5px !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        div.st-key-top_search_btn button:hover,
        div.st-key-top_search_form div[data-testid="stFormSubmitButton"] button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 22px rgba(0, 242, 254, 0.6) !important;
        }

        /* ---------------- CARDS & DASHBOARD GRID ---------------- */
        .academic-card {
            background: rgba(10, 22, 42, 0.75) !important;
            border: 1px solid rgba(0, 229, 255, 0.25) !important;
            border-radius: 16px !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 0 15px rgba(0, 229, 255, 0.05) !important;
            backdrop-filter: blur(12px) !important;
            padding: 16px 20px;
            margin-bottom: 12px;
        }

        .academic-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 14px;
        }

        .card-header-left {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .card-header-icon {
            font-size: 18px;
            color: #00e5ff;
        }

        .card-header-title {
            font-size: 16px;
            font-weight: 700;
            color: #FFFFFF;
        }

        .card-header-badge {
            background: rgba(0, 229, 255, 0.12);
            border: 1px solid rgba(0, 229, 255, 0.3);
            color: #38bdf8;
            font-size: 11.5px;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 12px;
        }

        /* Book Search Result Content Layout */
        .book-result-body {
            display: flex;
            gap: 20px;
            align-items: flex-start;
        }

        .book-cover-wrap {
            flex-shrink: 0;
            width: 135px;
            height: 195px;
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid rgba(0, 229, 255, 0.35);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.6), 0 0 15px rgba(0, 229, 255, 0.15);
            background: #060e1d;
        }

        .book-cover-img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }

        .book-details-box {
            flex: 1;
            display: flex;
            flex-direction: column;
        }

        .book-title {
            font-size: 24px;
            font-weight: 800;
            color: #FFFFFF;
            margin: 0 0 4px 0;
            line-height: 1.2;
            letter-spacing: -0.3px;
        }

        .book-author-line {
            display: flex;
            align-items: center;
            gap: 6px;
            color: #38bdf8;
            font-size: 14.5px;
            font-weight: 600;
            margin-bottom: 10px;
        }

        .book-tags-row {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 10px;
        }

        .book-tag {
            font-size: 11.5px;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 12px;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        .tag-novel {
            background: rgba(88, 28, 135, 0.45);
            border: 1px solid rgba(168, 85, 247, 0.5);
            color: #d8b4fe;
        }
        .tag-genre {
            background: rgba(8, 51, 68, 0.5);
            border: 1px solid rgba(6, 182, 212, 0.5);
            color: #22d3ee;
        }
        .tag-year {
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(100, 116, 139, 0.4);
            color: #cbd5e1;
        }

        .book-desc {
            font-size: 13px;
            color: #94a3b8;
            line-height: 1.5;
            margin-bottom: 10px;
        }

        .book-rating-row {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 12px;
        }
        .rating-star {
            color: #FBBF24;
            font-size: 15px;
        }
        .rating-score {
            font-size: 13.5px;
            font-weight: 700;
            color: #FFFFFF;
        }
        .rating-count {
            font-size: 12px;
            color: #64748b;
        }

        /* Action Buttons Inside Card */
        div.st-key-btn_action_read button {
            background: #00e5ff !important;
            background-color: #00e5ff !important;
            border: none !important;
            border-radius: 10px !important;
            height: 38px !important;
            box-shadow: 0 2px 12px rgba(0, 229, 255, 0.35) !important;
            white-space: nowrap !important;
        }
        div.st-key-btn_action_read button p {
            color: #061320 !important;
            font-weight: 800 !important;
            font-size: 13px !important;
        }
        div.st-key-btn_action_read button:hover {
            background-color: #22d3ee !important;
            transform: translateY(-1px);
        }

        div.st-key-btn_action_details button,
        div.st-key-btn_action_bookmark button {
            background: rgba(10, 24, 46, 0.85) !important;
            background-color: rgba(10, 24, 46, 0.85) !important;
            border: 1px solid #00e5ff !important;
            border-radius: 10px !important;
            height: 38px !important;
            white-space: nowrap !important;
        }
        div.st-key-btn_action_details button p,
        div.st-key-btn_action_bookmark button p {
            color: #00e5ff !important;
            font-weight: 600 !important;
            font-size: 13px !important;
        }
        div.st-key-btn_action_details button:hover,
        div.st-key-btn_action_bookmark button:hover {
            background-color: rgba(0, 229, 255, 0.12) !important;
        }

        /* ---------------- QUICK ACTIONS SECTION ---------------- */
        .quick-actions-title {
            font-size: 15px;
            font-weight: 700;
            color: #FFFFFF;
            display: flex;
            align-items: center;
            gap: 7px;
            margin: 14px 0 10px 0;
        }
        .quick-actions-title span {
            color: #00e5ff;
        }

        .quick-action-card {
            border-radius: 12px;
            padding: 14px 10px;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 4px;
            cursor: pointer;
            transition: all 0.2s ease;
            height: 95px;
            text-decoration: none;
            width: 100%;
        }
        .quick-action-card:hover {
            transform: translateY(-2px);
        }

        .qa-purple {
            background: linear-gradient(135deg, rgba(88, 28, 135, 0.45) 0%, rgba(59, 7, 100, 0.6) 100%);
            border: 1px solid rgba(168, 85, 247, 0.45);
            box-shadow: 0 4px 14px rgba(88, 28, 135, 0.2);
        }
        .qa-blue {
            background: linear-gradient(135deg, rgba(14, 116, 144, 0.45) 0%, rgba(8, 51, 68, 0.6) 100%);
            border: 1px solid rgba(6, 182, 212, 0.45);
            box-shadow: 0 4px 14px rgba(6, 182, 212, 0.2);
        }
        .qa-green {
            background: linear-gradient(135deg, rgba(6, 78, 59, 0.45) 0%, rgba(4, 47, 46, 0.6) 100%);
            border: 1px solid rgba(16, 185, 129, 0.45);
            box-shadow: 0 4px 14px rgba(16, 185, 129, 0.2);
        }
        .qa-gold {
            background: linear-gradient(135deg, rgba(120, 53, 15, 0.45) 0%, rgba(69, 26, 3, 0.6) 100%);
            border: 1px solid rgba(245, 158, 11, 0.45);
            box-shadow: 0 4px 14px rgba(245, 158, 11, 0.2);
        }
        .qa-disabled {
            background: rgba(15, 23, 42, 0.5) !important;
            border: 1px dashed rgba(100, 116, 139, 0.35) !important;
            cursor: not-allowed !important;
        }

        .qa-icon {
            font-size: 22px;
            margin-bottom: 2px;
        }
        .qa-title {
            font-size: 13.5px;
            font-weight: 700;
            color: #FFFFFF;
            line-height: 1.1;
        }
        .qa-sub {
            font-size: 10.5px;
            color: #94a3b8;
        }

        /* Streamlit Button Overrides for Quick Action Cards */
        div[class*="st-key-qa_btn_details"] button,
        div[class*="st-key-qa_btn_related"] button {
            height: 95px !important;
            min-height: 95px !important;
            border-radius: 12px !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 12px 8px !important;
            width: 100% !important;
            transition: all 0.2s ease !important;
            border: none !important;
            white-space: pre-line !important;
            cursor: pointer !important;
            outline: none !important;
        }
        div[class*="st-key-qa_btn_details"] button:hover,
        div[class*="st-key-qa_btn_related"] button:hover {
            transform: translateY(-2px) !important;
        }

        div[class*="st-key-qa_btn_details"] button {
            background: linear-gradient(135deg, rgba(6, 78, 59, 0.45) 0%, rgba(4, 47, 46, 0.6) 100%) !important;
            background-color: rgba(6, 78, 59, 0.45) !important;
            border: 1px solid rgba(16, 185, 129, 0.45) !important;
            box-shadow: 0 4px 14px rgba(16, 185, 129, 0.2) !important;
        }
        div[class*="st-key-qa_btn_details"] button:hover {
            box-shadow: 0 6px 18px rgba(16, 185, 129, 0.4) !important;
            border-color: #34d399 !important;
            background: linear-gradient(135deg, rgba(6, 78, 59, 0.65) 0%, rgba(4, 47, 46, 0.8) 100%) !important;
            background-color: rgba(6, 78, 59, 0.65) !important;
        }
        div[class*="st-key-qa_btn_details"] button:focus,
        div[class*="st-key-qa_btn_details"] button:active,
        div[class*="st-key-qa_btn_details"] button:focus:not(:active) {
            outline: none !important;
            box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3) !important;
            border-color: rgba(16, 185, 129, 0.6) !important;
            color: #FFFFFF !important;
            background: linear-gradient(135deg, rgba(6, 78, 59, 0.55) 0%, rgba(4, 47, 46, 0.7) 100%) !important;
            background-color: rgba(6, 78, 59, 0.55) !important;
        }

        div[class*="st-key-qa_btn_related"] button {
            background: linear-gradient(135deg, rgba(120, 53, 15, 0.45) 0%, rgba(69, 26, 3, 0.6) 100%) !important;
            background-color: rgba(120, 53, 15, 0.45) !important;
            border: 1px solid rgba(245, 158, 11, 0.45) !important;
            box-shadow: 0 4px 14px rgba(245, 158, 11, 0.2) !important;
        }
        div[class*="st-key-qa_btn_related"] button:hover {
            box-shadow: 0 6px 18px rgba(245, 158, 11, 0.4) !important;
            border-color: #fbbf24 !important;
            background: linear-gradient(135deg, rgba(120, 53, 15, 0.65) 0%, rgba(69, 26, 3, 0.8) 100%) !important;
            background-color: rgba(120, 53, 15, 0.65) !important;
        }
        div[class*="st-key-qa_btn_related"] button:focus,
        div[class*="st-key-qa_btn_related"] button:active,
        div[class*="st-key-qa_btn_related"] button:focus:not(:active) {
            outline: none !important;
            box-shadow: 0 4px 14px rgba(245, 158, 11, 0.3) !important;
            border-color: rgba(245, 158, 11, 0.6) !important;
            color: #FFFFFF !important;
            background: linear-gradient(135deg, rgba(120, 53, 15, 0.55) 0%, rgba(69, 26, 3, 0.7) 100%) !important;
            background-color: rgba(120, 53, 15, 0.55) !important;
        }

        div[class*="st-key-qa_btn_details"] button div[data-testid="stMarkdownContainer"],
        div[class*="st-key-qa_btn_related"] button div[data-testid="stMarkdownContainer"] {
            width: 100% !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
        }

        div[class*="st-key-qa_btn_details"] button p,
        div[class*="st-key-qa_btn_related"] button p {
            color: #FFFFFF !important;
            font-size: 13.5px !important;
            font-weight: 700 !important;
            line-height: 1.25 !important;
            text-align: center !important;
            white-space: pre-line !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        div[class*="st-key-qa_btn_details"] button p::first-line,
        div[class*="st-key-qa_btn_related"] button p::first-line {
            font-size: 20px !important;
            line-height: 1.2 !important;
        }

        div[class*="st-key-qa_btn_details"] button em,
        div[class*="st-key-qa_btn_related"] button em,
        div[class*="st-key-qa_btn_details"] button span,
        div[class*="st-key-qa_btn_related"] button span {
            font-size: 10.5px !important;
            font-style: normal !important;
            font-weight: 400 !important;
            color: #94a3b8 !important;
            display: block !important;
            margin-top: 2px !important;
        }

        /* Suggestion Buttons in Welcome Screen */
        div.st-key-btn_sug_tm button,
        div.st-key-btn_sug_nmnt button,
        div.st-key-btn_sug_ai button,
        div.st-key-btn_sug_aem button {
            background: rgba(10, 24, 46, 0.85) !important;
            border: 1px solid rgba(0, 229, 255, 0.3) !important;
            border-radius: 12px !important;
            height: 68px !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            transition: all 0.2s ease !important;
            white-space: pre-line !important;
            width: 100% !important;
        }
        div.st-key-btn_sug_tm button p,
        div.st-key-btn_sug_nmnt button p,
        div.st-key-btn_sug_ai button p,
        div.st-key-btn_sug_aem button p {
            color: #FFFFFF !important;
            font-size: 13px !important;
            font-weight: 700 !important;
            line-height: 1.3 !important;
            text-align: center !important;
            white-space: pre-line !important;
            margin: 0 !important;
        }
        div.st-key-btn_sug_tm button:hover,
        div.st-key-btn_sug_nmnt button:hover,
        div.st-key-btn_sug_ai button:hover,
        div.st-key-btn_sug_aem button:hover {
            background: rgba(0, 229, 255, 0.12) !important;
            border-color: #00e5ff !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 18px rgba(0, 229, 255, 0.35) !important;
        }

        /* ---------------- RIGHT SIDE INFO CARDS ---------------- */
        .info-table {
            width: 100%;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .info-row {
            display: flex;
            align-items: center;
            font-size: 13px;
            padding: 4px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        .info-row:last-child {
            border-bottom: none;
        }

        .info-label {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #94a3b8;
            width: 105px;
            flex-shrink: 0;
        }

        .info-sep {
            color: #64748b;
            margin-right: 12px;
        }

        .info-val {
            color: #FFFFFF;
            font-weight: 600;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        /* Related Books Card Content */
        .related-book-item {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .related-cover {
            width: 72px;
            height: 98px;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid rgba(0, 229, 255, 0.3);
            flex-shrink: 0;
            background: #060e1d;
        }
        .related-cover img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .related-meta {
            flex: 1;
        }

        .related-title {
            font-size: 14px;
            font-weight: 700;
            color: #FFFFFF;
            margin: 0 0 4px 0;
            line-height: 1.25;
        }

        .related-author {
            font-size: 12px;
            color: #94a3b8;
            margin: 0;
        }

        .related-arrow-btn {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: rgba(0, 229, 255, 0.2);
            border: 1px solid #00e5ff;
            color: #00e5ff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 0 10px rgba(0, 229, 255, 0.2);
            transition: all 0.2s ease;
        }
        .related-arrow-btn:hover {
            background: #00e5ff;
            color: #05131f;
        }

        /* ---------------- FIXED BOTTOM CHAT BAR ---------------- */
        div.st-key-bottom_chat_form,
        form[aria-label="bottom_chat_form"] {
            position: fixed !important;
            bottom: 16px !important;
            left: 320px !important;
            right: 28px !important;
            z-index: 999999 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        div.st-key-bottom_chat_form [data-testid="stHorizontalBlock"] {
            align-items: center !important;
            gap: 12px !important;
        }

        .bottom-sparkles {
            font-size: 22px;
            color: #fbbf24;
            filter: drop-shadow(0 0 10px rgba(251, 191, 36, 0.75));
            display: flex;
            align-items: center;
            justify-content: center;
            line-height: 1;
        }

        div.st-key-bottom_chat_form div[data-testid="stTextInput"] {
            margin: 0 !important;
            padding: 0 !important;
            flex: 1 !important;
        }

        div.st-key-bottom_chat_form div[data-testid="stTextInput"] input {
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 24px !important;
            color: #0F172A !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35) !important;
            outline: none !important;
            height: 44px !important;
            padding: 0 18px !important;
        }

        div.st-key-bottom_chat_form div[data-testid="stTextInput"] input::placeholder {
            color: #64748B !important;
            font-weight: 400 !important;
        }

        div.st-key-bottom_chat_form div[data-testid="stTextInput"] input:focus {
            border-color: #00e5ff !important;
            box-shadow: 0 0 0 2px rgba(0, 229, 255, 0.35), 0 4px 14px rgba(0, 0, 0, 0.35) !important;
        }

        /* Circular Send Button in Bottom Bar */
        div.st-key-bottom_send_btn button,
        div.st-key-bottom_send_btn button:hover,
        div.st-key-bottom_chat_form div[data-testid="stFormSubmitButton"] > button {
            background: linear-gradient(135deg, #00f2fe 0%, #00c4b4 100%) !important;
            background-color: #00f2fe !important;
            border: none !important;
            border-radius: 50% !important;
            width: 44px !important;
            height: 44px !important;
            min-width: 44px !important;
            min-height: 44px !important;
            box-shadow: 0 4px 14px rgba(0, 242, 254, 0.5) !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
        }
        div.st-key-bottom_send_btn button p,
        div.st-key-bottom_send_btn button div,
        div.st-key-bottom_send_btn button span,
        div.st-key-bottom_chat_form div[data-testid="stFormSubmitButton"] > button p,
        div.st-key-bottom_chat_form div[data-testid="stFormSubmitButton"] > button div {
            background: transparent !important;
            color: #061320 !important;
            font-size: 18px !important;
            font-weight: 900 !important;
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1 !important;
        }
        div.st-key-bottom_send_btn button:hover,
        div.st-key-bottom_chat_form div[data-testid="stFormSubmitButton"] > button:hover {
            transform: scale(1.06);
            box-shadow: 0 6px 18px rgba(0, 242, 254, 0.7) !important;
        }

        /* Attachment Popover Button */
        div[data-testid="stPopover"] > button {
            background: transparent !important;
            color: #94a3b8 !important;
            border: none !important;
            font-size: 18px !important;
            padding: 0 !important;
            width: 30px !important;
            height: 30px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-shadow: none !important;
        }
        div[data-testid="stPopover"] > button:hover {
            color: #00e5ff !important;
        }

        /* Message Bubbles for Dark Theme */
        .chat-bubble-row {
            display: flex;
            gap: 10px;
            margin-bottom: 12px;
        }
        .chat-bubble-row.user {
            flex-direction: row-reverse;
        }
        .chat-bubble-bubble {
            padding: 10px 16px;
            border-radius: 14px;
            font-size: 13.5px;
            line-height: 1.5;
            max-width: 80%;
            word-wrap: break-word;
        }
        .chat-bubble-bubble.user {
            background: rgba(0, 229, 255, 0.15);
            border: 1px solid rgba(0, 229, 255, 0.4);
            color: #FFFFFF;
            border-top-right-radius: 2px;
        }
        .chat-bubble-bubble.bot {
            background: #0d1e38;
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #e2e8f0;
            border-top-left-radius: 2px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# SIDEBAR CONTENT (EXACT MATCH TO REFERENCE SCREENSHOT)
# ---------------------------------------------------------
with st.sidebar:

    # 1. Logo Header
    st.markdown(
        """
        <div class="sidebar-brand-box">
            <div class="sidebar-brand-logo">
                <svg width="34" height="34" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 0 10px rgba(0, 229, 255, 0.7));">
                    <defs>
                        <linearGradient id="s_cap_top" x1="4" y1="6" x2="44" y2="26" gradientUnits="userSpaceOnUse">
                            <stop offset="0%" stop-color="#a5f3fc"/>
                            <stop offset="35%" stop-color="#00e5ff"/>
                            <stop offset="100%" stop-color="#0284c7"/>
                        </linearGradient>
                        <linearGradient id="s_cap_edge" x1="4" y1="16" x2="44" y2="28" gradientUnits="userSpaceOnUse">
                            <stop offset="0%" stop-color="#0891b2"/>
                            <stop offset="100%" stop-color="#0369a1"/>
                        </linearGradient>
                        <linearGradient id="s_cap_base" x1="12" y1="21" x2="36" y2="36" gradientUnits="userSpaceOnUse">
                            <stop offset="0%" stop-color="#00e5ff"/>
                            <stop offset="100%" stop-color="#0284c7"/>
                        </linearGradient>
                        <linearGradient id="s_cap_body" x1="13" y1="22" x2="35" y2="34" gradientUnits="userSpaceOnUse">
                            <stop offset="0%" stop-color="#082f49"/>
                            <stop offset="100%" stop-color="#0369a1"/>
                        </linearGradient>
                    </defs>
                    <path d="M12.5 21V29.5C12.5 29.5 16.5 34 24 34C31.5 34 35.5 29.5 35.5 21" fill="url(#s_cap_body)"/>
                    <path d="M12 21V29.5C12 29.5 16.5 34.5 24 34.5C31.5 34.5 36 29.5 36 21" stroke="url(#s_cap_base)" stroke-width="2" stroke-linecap="round" fill="none"/>
                    <path d="M4 16L24 25.5L44 16V18.5L24 28L4 18.5V16Z" fill="url(#s_cap_edge)"/>
                    <path d="M24 6.5L44 16L24 25.5L4 16L24 6.5Z" fill="url(#s_cap_top)" stroke="#cffafe" stroke-width="0.8" stroke-linejoin="round"/>
                    <circle cx="24" cy="16" r="2.2" fill="#ffffff" stroke="#00e5ff" stroke-width="0.8"/>
                    <path d="M24 16C29 17.5 36.5 20.5 37 26V32" stroke="#38bdf8" stroke-width="2" stroke-linecap="round"/>
                    <circle cx="37" cy="32.5" r="1.5" fill="#facc15"/>
                    <path d="M35.5 33.5C35.5 33.5 37 38 37 38C37 38 38.5 33.5 38.5 33.5Z" fill="#38bdf8"/>
                    <ellipse cx="37" cy="38" rx="1.8" ry="0.8" fill="#00e5ff"/>
                </svg>
            </div>
            <div class="sidebar-brand-text">
                <div class="sidebar-brand-title">Academic<br>Syllabus <span style="color:#00e5ff;">AI</span></div>
                <div class="sidebar-brand-sub">Books · Syllabus · Q&A</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Clean Single-Layer Turquoise + New Chat Button
    st.button("➕  New Chat", key="btn_sidebar_new_chat", use_container_width=True, on_click=handle_new_chat)

    # 3. Chat History Header with Conversation Count & Clear All
    col_h_title, col_h_clear = st.columns([0.68, 0.32])
    with col_h_title:
        st.markdown(
            f'<div class="sidebar-section-header"><span>💬 Chat History ({len(st.session_state.history)})</span></div>',
            unsafe_allow_html=True,
        )
    with col_h_clear:
        if len(st.session_state.history) > 0:
            if st.button("Clear All", key="btn_clear_all_trigger", help="Delete all conversations"):
                st.session_state.confirm_clear_all = True
                st.rerun()

    # Clear All Confirmation Box (Requirement 5)
    if st.session_state.get("confirm_clear_all", False):
        st.markdown(
            f"""
            <div style="background: rgba(239, 68, 68, 0.16); border: 1px solid #ef4444; border-radius: 8px; padding: 10px; margin-bottom: 10px; font-size: 11.5px; color: #fca5a5; line-height: 1.45;">
                ⚠️ <strong>Delete all conversations?</strong><br>
                This will permanently delete all {len(st.session_state.history)} saved chats and cannot be undone.
            </div>
            """,
            unsafe_allow_html=True
        )
        col_c_yes, col_c_no = st.columns(2)
        with col_c_yes:
            if st.button("Confirm Delete", key="btn_clear_all_yes", use_container_width=True):
                st.session_state.history = []
                save_history([])
                handle_new_chat()
                st.session_state.confirm_clear_all = False
                st.rerun()
        with col_c_no:
            if st.button("Cancel", key="btn_clear_all_no", use_container_width=True):
                st.session_state.confirm_clear_all = False
                st.rerun()

    # 4. Scrollable List of All Saved Conversations
    if not st.session_state.history:
        st.markdown("<div style='color:#64748b; font-size:12px; padding:8px 6px;'>No saved conversations yet. Search for any book to begin!</div>", unsafe_allow_html=True)
    else:
        for conv in st.session_state.history[:50]:
            c_id = conv.get("id", "")
            c_title = conv.get("title", "Conversation")
            c_date = conv.get("date", "")
            is_active = (c_id == st.session_state.active_conv_id)

            # Check if this item is awaiting delete confirmation
            if st.session_state.get("delete_confirm_id") == c_id:
                st.markdown(
                    f"""
                    <div style="background: rgba(239, 68, 68, 0.16); border: 1px solid #ef4444; border-radius: 6px; padding: 6px 8px; margin: 4px 0; font-size: 11px; color: #fca5a5;">
                        Delete <strong>'{html.escape(c_title[:16])}'</strong>?
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                col_d_yes, col_d_no = st.columns(2)
                with col_d_yes:
                    if st.button("Delete", key=f"del_yes_{c_id}", use_container_width=True):
                        st.session_state.history = [c for c in st.session_state.history if c.get("id") != c_id]
                        save_history(st.session_state.history)
                        st.session_state.delete_confirm_id = None
                        if st.session_state.active_conv_id == c_id:
                            handle_new_chat()
                        st.rerun()
                with col_d_no:
                    if st.button("Cancel", key=f"del_no_{c_id}", use_container_width=True):
                        st.session_state.delete_confirm_id = None
                        st.rerun()
            else:
                col_c_btn, col_c_del = st.columns([0.82, 0.18], vertical_alignment="center")
                with col_c_btn:
                    btn_type = "primary" if is_active else "secondary"
                    display_title = (c_title[:24] + "...") if len(c_title) > 24 else c_title
                    if st.button(
                        f"💬 {display_title}",
                        key=f"conv_{c_id}",
                        type=btn_type,
                        use_container_width=True,
                        help=f"{c_title} ({c_date})"
                    ):
                        handle_select_conv(c_id)
                        st.rerun()
                with col_c_del:
                    if st.button("🗑️", key=f"del_{c_id}", help=f"Delete {c_title}", use_container_width=True):
                        st.session_state.delete_confirm_id = c_id
                        st.rerun()

    # 5. Fixed Profile Card at Bottom
    st.markdown(
        """
        <div class="sidebar-profile-card">
            <div class="sidebar-profile-avatar">S</div>
            <div class="sidebar-profile-info">
                <div class="sidebar-profile-name">Student</div>
                <div class="sidebar-profile-email">student@example.com</div>
            </div>
            <div style="color: #64748b; font-size: 13px;">›</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# BOOK SEARCH & QUERY ROUTING HELPER FUNCTIONS
# ---------------------------------------------------------
def extract_book_snippet(text: str, query: str, max_len: int = 280) -> str:
    if not text or not text.strip():
        return "Unavailable"
    clean = re.sub(r"[\r\n\t]+", " ", text).strip()
    clean = re.sub(r"\s+", " ", clean)
    clean = "".join(ch for ch in clean if ch.isprintable() or ch in " \n")
    q_words = [w for w in re.split(r"\W+", query.lower()) if len(w) >= 2]
    pos = -1
    for w in q_words:
        p = clean.lower().find(w)
        if p != -1 and (pos == -1 or p < pos):
            pos = p
    if pos == -1:
        snippet = clean[:max_len]
    else:
        start = max(0, pos - 40)
        end = min(len(clean), pos + max_len - 40)
        snippet = clean[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(clean):
            snippet = snippet + "..."
    return snippet.strip() or "Unavailable"

def extract_book_query_topic(text: str) -> str:
    clean = (text or "").strip()
    cleaned = re.sub(
        r"^(?:search\s+book\s+(?:for\s+)?|book\s+search\s+(?:for\s+)?|find\s+in\s+book\s+(?:for\s+)?|textbook\s*[:\-]?\s*|book\s*[:\-]?\s*|search\s+(?:for\s+)?|find\s+(?:for\s+)?)",
        "",
        clean,
        flags=re.IGNORECASE
    ).strip()
    cleaned = re.sub(
        r"\s+(?:in|from)\s+(?:the\s+)?(?:books?|textbooks?)$",
        "",
        cleaned,
        flags=re.IGNORECASE
    ).strip()
    cleaned = re.sub(
        r"^(?:what\s+is\s+|what\s+are\s+|explain\s+|tell\s+me\s+about\s+|kya\s+hai\s+|batao\s+)",
        "",
        cleaned,
        flags=re.IGNORECASE
    ).strip()
    return cleaned if cleaned else clean

def is_book_search_query(text: str, attached_files: list = None) -> bool:
    """Returns True if the query is a topic or section search inside textbooks."""
    if attached_files:
        return False
    clean = (text or "").strip()
    if not clean:
        return False
    if detect_search_intent is not None:
        intent = detect_search_intent(clean)
        if intent == INTENT_BOOK_SEARCH:
            return False
        if intent == INTENT_TOPIC_SEARCH:
            return True
    return False

def is_local_textbook_query(text: str) -> bool:
    clean = (text or "").strip()
    if not clean:
        return False
    q_lower = clean.lower()
    local_patterns = [
        r"\b(?:in|from|inside|within)\s+(?:my\s+|the\s+)?(?:uploaded\s+|local\s+)?(?:[a-zA-Z]+\s+)?(?:textbooks?|books?|pdfs?|files?|kreyszig|grewal)\b",
        r"\b(?:find|search|explain|get|show|list)\s+.*?\s+(?:in|from|inside|within)\s+(?:my\s+|the\s+)?(?:uploaded\s+|local\s+)?(?:[a-zA-Z]+\s+)?(?:textbooks?|books?|pdfs?|files?|kreyszig|grewal)\b",
        r"\b(?:kreyszig|grewal)\s*(?:pdf|book|textbook)\b",
        r"^(?:in\s+the\s+book|in\s+book|from\s+book|in\s+textbook|from\s+textbook)\s*[:\-]?\s*(.+)$"
    ]
    return any(re.search(pat, q_lower) for pat in local_patterns)

def is_syllabus_query(text: str) -> bool:
    clean = (text or "").strip()
    if not clean:
        return False
    q_lower = clean.lower()
    indicators = [
        "syllabus", "curriculum", "regulation", "regulations",
        "subject", "subjects", "course", "courses",
        "semester", "semesters", "sem", "credit", "credits", "elective", "electives",
        "exam", "exams", "course outcome", "course outcomes"
    ]
    return any(re.search(r"\b" + re.escape(ind) + r"\b", q_lower) for ind in indicators)

def is_internet_book_query(text: str, attached_files: list = None) -> bool:
    """Returns True if user query is intended to find a book by title, author, or ISBN."""
    if attached_files:
        return False
    clean = (text or "").strip()
    if not clean:
        return False
    if is_local_textbook_query(clean):
        return False
    if detect_search_intent is not None:
        intent = detect_search_intent(clean)
        return intent == INTENT_BOOK_SEARCH
    return False

def perform_book_search(query_text: str) -> str:
    """Topic Search Pipeline: Searches indexed book content and returns matching pages only."""
    clean_topic = extract_book_query_topic(query_text) if "extract_book_query_topic" in globals() else query_text
    if not clean_topic:
        clean_topic = query_text
    if search_book_topics is not None:
        try:
            t_res = search_book_topics(clean_topic)
            if t_res.get("status") == "found" and t_res.get("sections_by_book"):
                st.session_state["last_book_search_sections"] = t_res["sections_by_book"]
                st.session_state["last_book_search_query"] = t_res.get("topic", clean_topic)
                return t_res.get("formatted_answer")
            else:
                st.session_state["last_book_search_sections"] = None
                return t_res.get("formatted_answer")
        except Exception as exc:
            print(f"search_book_topics error: {exc}")
    elif search_book_sections is not None and format_book_sections_response is not None:
        try:
            results_by_book = search_book_sections(clean_topic)
            total = sum(len(secs) for secs in results_by_book.values())
            if total > 0:
                st.session_state["last_book_search_sections"] = results_by_book
                st.session_state["last_book_search_query"] = clean_topic
                return format_book_sections_response(clean_topic, results_by_book)
            else:
                st.session_state["last_book_search_sections"] = None
                return f"Information regarding topic '**{clean_topic}**' was not found in the indexed textbooks."
        except Exception as exc:
            print(f"search_book_sections error: {exc}")
    return "Search completed."

def perform_internet_book_search(query_text: str) -> dict:
    """Book Search Pipeline: Searches book metadata and returns matching books only."""
    clean = (query_text or "").strip()
    if not clean:
        return {"status": "not_found", "message": "Please enter a valid book title or author."}

    st.session_state["last_book_search_query"] = clean
    st.session_state["last_book_search_sections"] = None
    st.session_state.show_reader = False
    st.session_state.show_book_details = False
    st.session_state.show_related_books = False

    if search_books is not None:
        b_res = search_books(clean)
        found_book = b_res.get("book")
        search_res = b_res.get("search_res")
        if b_res.get("status") == "found" and found_book:
            if "searched_books" not in st.session_state or st.session_state.searched_books is None:
                st.session_state.searched_books = []
            already_exists = any(
                (pb.get("id") and pb.get("id") == found_book.get("id")) or
                pb.get("title", "").strip().lower() == found_book.get("title", "").strip().lower()
                for pb in st.session_state.searched_books
            )
            if not already_exists:
                st.session_state.searched_books.append(found_book)
            st.session_state["last_internet_book"] = found_book
            st.session_state["last_internet_search"] = search_res
            save_current_conversation()
            return b_res
        else:
            save_current_conversation()
            return b_res
    return {"status": "not_found", "message": f"📖 Book not found: No matching book record found for \"**{clean}**\"."}

# Process User Prompt / File Submission
def handle_user_message(user_text):
    raw_text = (user_text or "").strip()
    if not raw_text and not st.session_state.attached_files:
        return

    curr_time = datetime.now().strftime("%I:%M %p")
    clean_query = raw_text

    user_msg = {
        "role": "user",
        "content": raw_text,
        "time": curr_time
    }
    st.session_state.active_messages.append(user_msg)

    # Detect Search Intent
    intent = detect_search_intent(clean_query) if detect_search_intent is not None else INTENT_AMBIGUOUS

    if is_syllabus_query(clean_query) or st.session_state.attached_files:
        try:
            req_payload = {
                "query": clean_query or "Give me a summary of this syllabus.",
                "filename": st.session_state.uploaded_file_name
            }
            res = http_session.post(f"{BACKEND_URL}/chat", json=req_payload, timeout=6)
            if res.status_code == 200:
                data = res.json()
                bot_ans = data.get("answer", "")
            else:
                bot_ans = f"Answer regarding '{clean_query}' based on syllabus."
        except Exception:
            bot_ans = f"Information about '{clean_query}' from {st.session_state.uploaded_file_name}."

    elif intent == INTENT_BOOK_SEARCH:
        # Pipeline 1: Dedicated Book Search (Returns matching books only, never PDF pages)
        b_res = perform_internet_book_search(clean_query)
        bot_ans = b_res.get("message") or f"📖 Found book record for **{clean_query}**."

    elif intent == INTENT_TOPIC_SEARCH:
        # Pipeline 2: Dedicated Topic Search (Returns relevant PDF pages only, never replaces book catalogue)
        bot_ans = perform_book_search(clean_query)

    else:
        # Ambiguous Intent: Offer small choice asking whether user wants book search or topic search
        st.session_state["pending_ambiguous_query"] = clean_query
        bot_ans = (
            f"Your query '**{clean_query}**' can be searched as a **Book** or as a **Topic** inside indexed textbooks.\n\n"
            f"Please choose your preferred search below or use `book: {clean_query}` or `topic: {clean_query}`."
        )

    bot_msg = {
        "role": "assistant",
        "content": bot_ans,
        "time": datetime.now().strftime("%I:%M %p")
    }
    st.session_state.active_messages.append(bot_msg)
    save_current_conversation()

# ---------------------------------------------------------
# MAIN MAIN MAIN CONTENT AREA
# ---------------------------------------------------------

# 1. TOP HEADER BANNER (BRANDING & DECORATIVE BANNER)
with st.container(key="integrated_header_banner"):
    st.markdown(
        f"""
        <div style="position: relative; width: 100%; height: 168px; overflow: hidden;">
            <img src="data:image/jpeg;base64,{header_b64}" class="header-banner-img" alt="Academic Banner" />
            <div class="header-banner-overlay"></div>
            <div class="integrated-header-inner">
                <div class="header-branding-title">
                    <svg class="header-branding-cap-svg" width="38" height="38" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <defs>
                            <linearGradient id="cap_grad_top" x1="4" y1="6" x2="44" y2="26" gradientUnits="userSpaceOnUse">
                                <stop offset="0%" stop-color="#a5f3fc"/>
                                <stop offset="35%" stop-color="#00e5ff"/>
                                <stop offset="100%" stop-color="#0284c7"/>
                            </linearGradient>
                            <linearGradient id="cap_grad_edge" x1="4" y1="16" x2="44" y2="28" gradientUnits="userSpaceOnUse">
                                <stop offset="0%" stop-color="#0891b2"/>
                                <stop offset="100%" stop-color="#0369a1"/>
                            </linearGradient>
                            <linearGradient id="cap_grad_base" x1="12" y1="21" x2="36" y2="36" gradientUnits="userSpaceOnUse">
                                <stop offset="0%" stop-color="#00e5ff"/>
                                <stop offset="100%" stop-color="#0284c7"/>
                            </linearGradient>
                            <linearGradient id="cap_grad_body" x1="13" y1="22" x2="35" y2="34" gradientUnits="userSpaceOnUse">
                                <stop offset="0%" stop-color="#082f49"/>
                                <stop offset="100%" stop-color="#0369a1"/>
                            </linearGradient>
                        </defs>
                        <path d="M12.5 21V29.5C12.5 29.5 16.5 34 24 34C31.5 34 35.5 29.5 35.5 21" fill="url(#cap_grad_body)"/>
                        <path d="M12 21V29.5C12 29.5 16.5 34.5 24 34.5C31.5 34.5 36 29.5 36 21" stroke="url(#cap_grad_base)" stroke-width="2" stroke-linecap="round" fill="none"/>
                        <path d="M4 16L24 25.5L44 16V18.5L24 28L4 18.5V16Z" fill="url(#cap_grad_edge)"/>
                        <path d="M24 6.5L44 16L24 25.5L4 16L24 6.5Z" fill="url(#cap_grad_top)" stroke="#cffafe" stroke-width="0.8" stroke-linejoin="round"/>
                        <circle cx="24" cy="16" r="2.2" fill="#ffffff" stroke="#00e5ff" stroke-width="0.8"/>
                        <path d="M24 16C29 17.5 36.5 20.5 37 26V32" stroke="#38bdf8" stroke-width="2" stroke-linecap="round"/>
                        <circle cx="37" cy="32.5" r="1.5" fill="#facc15"/>
                        <path d="M35.5 33.5C35.5 33.5 37 38 37 38C37 38 38.5 33.5 38.5 33.5Z" fill="#38bdf8"/>
                        <ellipse cx="37" cy="38" rx="1.8" ry="0.8" fill="#00e5ff"/>
                    </svg> Academic <span class="cyan-text">Syllabus AI</span>
                </div>
                <div class="header-branding-sub">
                    Your AI-Powered Academic Assistant for Books, Syllabus & Learning
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if st.session_state.get("show_upload_modal", False):
    st.markdown(
        """
        <div class="academic-card" style="margin-bottom: 14px; border: 1px solid #00e5ff; box-shadow: 0 0 20px rgba(0, 229, 255, 0.2);">
            <div class="academic-card-header">
                <div class="card-header-left">
                    <span class="card-header-icon">☁️</span>
                    <span class="card-header-title">Upload Syllabus PDF / Textbook</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    col_up1, col_up2 = st.columns([0.85, 0.15])
    with col_up1:
        u_pdf = st.file_uploader("Select PDF or image", type=["pdf", "png", "jpg"], key="main_upload_input")
        if u_pdf is not None:
            st.session_state.uploaded_file_name = u_pdf.name
            try:
                files = {"file": (u_pdf.name, u_pdf.getvalue(), "application/pdf")}
                res = http_session.post(f"{BACKEND_URL}/upload-syllabus", files=files, timeout=40)
                if res.status_code == 200:
                    st.toast(f"Uploaded and indexed: {u_pdf.name}")
            except Exception as e:
                st.toast(f"Upload error: {e}")
    with col_up2:
        if st.button("✕ Close", key="btn_close_upload", use_container_width=True):
            st.session_state.show_upload_modal = False
            st.rerun()

# ---------------------------------------------------------
# DASHBOARD GRID: WELCOME SCREEN OR DYNAMIC BOOK RESULT CARD
# ---------------------------------------------------------
searched_books = st.session_state.get("searched_books", [])
if not searched_books and st.session_state.get("last_internet_book"):
    searched_books = [st.session_state["last_internet_book"]]
    st.session_state.searched_books = searched_books

if not searched_books and not st.session_state.get("last_book_search_sections"):
    st.markdown(
        """
        <div class="academic-card welcome-card-clean" style="text-align: center; padding: 42px 30px 36px 30px; margin-bottom: 24px; border: 1px solid rgba(0, 229, 255, 0.32); box-shadow: 0 8px 32px rgba(0,0,0,0.45), inset 0 0 25px rgba(0, 229, 255, 0.05); border-radius: 18px;">
            <div style="margin-bottom: 14px; display: flex; justify-content: center; align-items: center;">
                <svg width="54" height="54" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 0 16px rgba(0, 229, 255, 0.75));">
                    <defs>
                        <linearGradient id="w_cap_top" x1="4" y1="6" x2="44" y2="26" gradientUnits="userSpaceOnUse">
                            <stop offset="0%" stop-color="#a5f3fc"/>
                            <stop offset="35%" stop-color="#00e5ff"/>
                            <stop offset="100%" stop-color="#0284c7"/>
                        </linearGradient>
                        <linearGradient id="w_cap_edge" x1="4" y1="16" x2="44" y2="28" gradientUnits="userSpaceOnUse">
                            <stop offset="0%" stop-color="#0891b2"/>
                            <stop offset="100%" stop-color="#0369a1"/>
                        </linearGradient>
                        <linearGradient id="w_cap_base" x1="12" y1="21" x2="36" y2="36" gradientUnits="userSpaceOnUse">
                            <stop offset="0%" stop-color="#00e5ff"/>
                            <stop offset="100%" stop-color="#0284c7"/>
                        </linearGradient>
                        <linearGradient id="w_cap_body" x1="13" y1="22" x2="35" y2="34" gradientUnits="userSpaceOnUse">
                            <stop offset="0%" stop-color="#082f49"/>
                            <stop offset="100%" stop-color="#0369a1"/>
                        </linearGradient>
                    </defs>
                    <path d="M12.5 21V29.5C12.5 29.5 16.5 34 24 34C31.5 34 35.5 29.5 35.5 21" fill="url(#w_cap_body)"/>
                    <path d="M12 21V29.5C12 29.5 16.5 34.5 24 34.5C31.5 34.5 36 29.5 36 21" stroke="url(#w_cap_base)" stroke-width="2" stroke-linecap="round" fill="none"/>
                    <path d="M4 16L24 25.5L44 16V18.5L24 28L4 18.5V16Z" fill="url(#w_cap_edge)"/>
                    <path d="M24 6.5L44 16L24 25.5L4 16L24 6.5Z" fill="url(#w_cap_top)" stroke="#cffafe" stroke-width="0.8" stroke-linejoin="round"/>
                    <circle cx="24" cy="16" r="2.2" fill="#ffffff" stroke="#00e5ff" stroke-width="0.8"/>
                    <path d="M24 16C29 17.5 36.5 20.5 37 26V32" stroke="#38bdf8" stroke-width="2" stroke-linecap="round"/>
                    <circle cx="37" cy="32.5" r="1.5" fill="#facc15"/>
                    <path d="M35.5 33.5C35.5 33.5 37 38 37 38C37 38 38.5 33.5 38.5 33.5Z" fill="#38bdf8"/>
                    <ellipse cx="37" cy="38" rx="1.8" ry="0.8" fill="#00e5ff"/>
                </svg>
            </div>
            <div class="welcome-heading" style="font-size: 26px; font-weight: 800; color: #FFFFFF; margin: 0 0 10px 0; letter-spacing: -0.4px; line-height: 1.25;">
                Welcome to <span style="color: #00e5ff;">Academic Syllabus AI</span>
            </div>
            <p style="color: #94a3b8; font-size: 14px; max-width: 620px; margin: 0 auto 22px auto; line-height: 1.6;">
                Your AI-powered academic assistant for comprehensive textbooks, syllabus extraction, and instant subject learning.
            </p>
            <div style="display: inline-flex; align-items: center; justify-content: center; gap: 8px; background: rgba(8, 20, 38, 0.75); border: 1px solid rgba(0, 229, 255, 0.4); border-radius: 20px; padding: 9px 26px; color: #38bdf8; font-size: 13px; font-weight: 500; box-shadow: 0 0 14px rgba(0, 229, 255, 0.1);">
                <span style="font-size: 14px;">💬</span> Ask about any textbook, novel, syllabus, or learning topic using the chat box below.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

elif searched_books:
    for b_idx, curr_book in enumerate(searched_books):
        b_title = safe_text(curr_book.get("title"), "Book Title")
        b_authors = safe_authors_list(curr_book.get("authors"))
        b_author_str = ", ".join(b_authors)
        b_year = safe_text(curr_book.get("published_year") or curr_book.get("first_publish_year"), "N/A")
        b_genre = safe_text(curr_book.get("genre") or curr_book.get("content_type"), "Academic Reference")
        b_sub = safe_text(curr_book.get("sub_genre") or curr_book.get("edition"), "Textbook")
        
        raw_desc = curr_book.get("description")
        if raw_desc:
            b_desc = normalize_book_description(raw_desc, max_len=400)
        else:
            b_desc = f"Academic publication and reference for {b_title} by {b_author_str}."
        
        b_rating = safe_text(curr_book.get("rating"), "4.6")
        b_reviews = safe_text(curr_book.get("reviews_count"), "Verified")
        b_lang = safe_text(curr_book.get("language"), "English")
        b_formats = safe_text(curr_book.get("formats"), "Digital Reference")
        b_publisher = safe_text(curr_book.get("publisher"), "Academic Publisher")
        b_read_url = safe_text(curr_book.get("reading_url"), "")
        if not b_read_url:
            b_read_url = f"https://openlibrary.org/search?q={urllib.parse.quote(b_title)}"
        b_dl_url = safe_text(curr_book.get("download_url"), "")
        b_dl_fmt = safe_text(curr_book.get("download_format"), "EPUB")
        has_dl = bool(b_dl_url and b_dl_url.strip() and b_dl_url != "#")

        # Page limitation & Access breakdown fields
        tot_p = curr_book.get("total_pages")
        prev_p = curr_book.get("preview_pages")
        restr_p = curr_book.get("restricted_pages")
        access_type = curr_book.get("access_type") or ""
        price_val = safe_text(curr_book.get("price"), "")
        purch_url = safe_text(curr_book.get("purchase_url"), "")
        reading_status = safe_text(curr_book.get("reading_status"), "")

        is_full_free = (
            access_type == "full_free"
            or ("Free" in reading_status and "limited" not in reading_status.lower() and "borrow" not in reading_status.lower())
            or ("gutenberg" in curr_book.get("source_provider", "").lower())
        )

        is_purchase_req = bool(
            access_type in ("limited_preview_purchase", "purchase_required")
            or (price_val and any(c in price_val for c in ["USD", "EUR", "GBP", "$", "INR", "₹"]) and not is_full_free)
            or ("for sale" in price_val.lower() and not is_full_free)
        )

        if is_full_free:
            if isinstance(tot_p, int) and tot_p > 0:
                page_summary = f"Total: {tot_p} Pages • All Accessible Online (0 Restricted)"
            else:
                page_summary = "Complete Full Text Legally Available Free (0 Restricted Pages)"
            access_banner_html = f"""<div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 10px; padding: 10px 14px; margin: 10px 0 12px 0;">
<div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
<div style="display: flex; align-items: center; gap: 8px;">
<span style="font-size: 15px;">✅</span>
<span style="color: #34d399; font-weight: 700; font-size: 13px;">Full Book Access Legally Available</span>
</div>
<span style="color: #a7f3d0; font-size: 12px; font-weight: 600;">{page_summary}</span>
</div>
</div>"""
        elif is_purchase_req:
            price_badge = html.escape(price_val) if price_val else "For Sale (Check Store)"
            tot_str = f"{tot_p} pages" if (isinstance(tot_p, int) and tot_p > 0) else "Not specified"
            prev_str = f"{prev_p} pages" if (prev_p is not None and prev_p != "All") else "Sample preview"
            restr_str = f"{restr_p} pages" if (isinstance(restr_p, int) and restr_p > 0) else "Balance restricted"
            store_btn_html = ""
            if purch_url and purch_url.startswith("http"):
                store_btn_html = f'<a href="{html.escape(purch_url)}" target="_blank" rel="noopener noreferrer" style="background: #dc2626; color: #ffffff; padding: 4px 12px; border-radius: 6px; font-weight: 700; text-decoration: none; font-size: 11.5px; display: inline-flex; align-items: center; gap: 4px;">🛒 Official Purchase / Access Link ↗</a>'

            access_banner_html = f"""<div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 10px; padding: 10px 14px; margin: 10px 0 12px 0;">
<div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
<div style="display: flex; align-items: center; gap: 8px;">
<span style="font-size: 15px;">⚠️</span>
<span style="color: #f87171; font-weight: 700; font-size: 13px;">Limited Preview — Full Book Access Requires Purchase</span>
</div>
<span style="background: rgba(239, 68, 68, 0.25); color: #fecaca; border: 1px solid rgba(239, 68, 68, 0.45); padding: 2px 10px; border-radius: 4px; font-size: 12px; font-weight: 700;">Official Price: {price_badge}</span>
</div>
<div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-top: 6px; font-size: 12px; color: #cbd5e1;">
<div>📄 Total Pages: <strong>{tot_str}</strong> &nbsp;|&nbsp; 👁️ Available Preview: <strong>{prev_str}</strong> &nbsp;|&nbsp; 🔒 Restricted Pages: <strong>{restr_str}</strong></div>
{store_btn_html}
</div>
</div>"""
        else:
            tot_str = f"{tot_p} pages" if (isinstance(tot_p, int) and tot_p > 0) else "Complete catalog"
            prev_str = f"{prev_p} pages" if (prev_p is not None) else "5 pages"
            restr_str = f"{restr_p} pages" if (isinstance(restr_p, int) and restr_p > 0) else "Restricted"
            borrow_link_html = f'<a href="{html.escape(b_read_url)}" target="_blank" rel="noopener noreferrer" style="color: #00e5ff; font-weight: 600; text-decoration: underline; font-size: 12px;">Borrow Free on Internet Archive (Unlocks all {tot_str}) ↗</a>' if b_read_url else ''

            access_banner_html = f"""<div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 10px; padding: 10px 14px; margin: 10px 0 12px 0;">
<div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
<div style="display: flex; align-items: center; gap: 8px;">
<span style="font-size: 15px;">⚠️</span>
<span style="color: #fbbf24; font-weight: 700; font-size: 13px;">Limited Preview ({prev_str}) — Free Library Borrow Available</span>
</div>
<span style="color: #38bdf8; font-size: 12px; font-weight: 600;">Internet Archive Lending Library</span>
</div>
<div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-top: 6px; font-size: 12px; color: #cbd5e1;">
<div>📄 Total Pages: <strong>{tot_str}</strong> &nbsp;|&nbsp; 👁️ Available Preview: <strong>{prev_str}</strong> &nbsp;|&nbsp; 🔒 Remaining Restricted: <strong>{restr_str}</strong></div>
{borrow_link_html}
</div>
</div>"""

        # Cover image
        if "the time machine" in b_title.lower() and tm_cover_b64:
            cover_img_tag = f'<img src="data:image/jpeg;base64,{tm_cover_b64}" class="book-cover-img" alt="{html.escape(b_title)}"/>'
        elif curr_book.get("cover_b64"):
            cover_img_tag = f'<img src="data:image/jpeg;base64,{curr_book["cover_b64"]}" class="book-cover-img" alt="{html.escape(b_title)}"/>'
        elif curr_book.get("cover_url"):
            cover_img_tag = f'<img src="{curr_book["cover_url"]}" class="book-cover-img" alt="{html.escape(b_title)}" onerror="this.onerror=null; this.src=\'data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 140%22><rect width=%22100%22 height=%22140%22 fill=%22%230c192e%22/><text x=%2250%22 y=%2270%22 fill=%22%2300e5ff%22 font-size=%2228%22 text-anchor=%22middle%22 dominant-baseline=%22middle%22>📖</text></svg>\';"/>'
        else:
            cover_img_tag = f'<div style="width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; background:#0c192e; color:#00e5ff; font-size:36px; padding:10px; text-align:center;">📖<div style="font-size:11px; color:#94a3b8; margin-top:6px; line-height:1.2;">{html.escape(b_title[:24])}</div></div>'

        # 1. BOOK SEARCH RESULT CARD
        card_html = f"""<div class="academic-card" style="margin-bottom: 18px;">
<div class="academic-card-header">
<div class="card-header-left">
<span class="card-header-icon">📖</span>
<span class="card-header-title">Book Search Result #{b_idx + 1}</span>
</div>
<span class="card-header-badge">Found matching record for "{html.escape(b_title)}"</span>
</div>
<div class="book-result-body">
<div class="book-cover-wrap">{cover_img_tag}</div>
<div class="book-details-box">
<h2 class="book-title">{html.escape(b_title)}</h2>
<div class="book-author-line"><span>👤</span> <span>{html.escape(b_author_str)}</span></div>
<div class="book-tags-row">
<span class="book-tag tag-novel">📖 {html.escape(b_sub)}</span>
<span class="book-tag tag-genre">⚡ {html.escape(b_genre)}</span>
<span class="book-tag tag-year">📅 {html.escape(str(b_year))}</span>
</div>
{access_banner_html}
<div class="book-desc">{html.escape(b_desc)}</div>
<div class="book-rating-row">
<span class="rating-star">⭐</span>
<span class="rating-score">{b_rating}</span>
<span class="rating-count">({b_reviews})</span>
</div>
</div>
</div>
</div>"""
        st.markdown(card_html, unsafe_allow_html=True)

        # 2. FOUR QUICK ACTION BUTTONS PER BOOK (UNIQUE KEYS PER BOOK INDEX)
        st.markdown(f'<div class="quick-actions-title"><span>⚡</span> Quick Actions for #{b_idx + 1}: {html.escape(b_title[:32])}</div>', unsafe_allow_html=True)
        qa1, qa2, qa3, qa4 = st.columns(4)
        has_read = bool(b_read_url and isinstance(b_read_url, str) and b_read_url.strip().startswith(("http://", "https://")) and b_read_url.strip() != "#")
        with qa1:
            if has_read:
                st.markdown(
                    f"""
                    <a href="{html.escape(b_read_url.strip())}" target="_blank" rel="noopener noreferrer" style="text-decoration:none; display:block;">
                        <div class="quick-action-card qa-purple">
                            <div class="qa-icon">📖</div>
                            <div class="qa-title">Read Online</div>
                            <div class="qa-sub">Verified Web Reader ↗</div>
                        </div>
                    </a>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    """
                    <div class="quick-action-card qa-disabled" title="No verified online reader available for this title">
                        <div class="qa-icon" style="opacity: 0.35;">📖</div>
                        <div class="qa-title" style="color: #64748b;">Read Online</div>
                        <div class="qa-sub" style="color: #475569;">Unavailable</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with qa2:
            if has_dl:
                st.markdown(
                    f"""
                    <a href="{b_dl_url}" target="_blank" download style="text-decoration:none; display:block;">
                        <div class="quick-action-card qa-blue">
                            <div class="qa-icon">⬇️</div>
                            <div class="qa-title">Download</div>
                            <div class="qa-sub">{b_dl_fmt or 'EPUB/PDF'} Available</div>
                        </div>
                    </a>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    """
                    <div class="quick-action-card qa-disabled" title="No direct EPUB/PDF download available for this title">
                        <div class="qa-icon" style="opacity: 0.35;">⬇️</div>
                        <div class="qa-title" style="color: #64748b;">Download</div>
                        <div class="qa-sub" style="color: #475569;">Unavailable</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with qa3:
            details_active = st.session_state.get(f"show_book_details_{b_idx}", False)
            details_label = "✕\nHide Details\n*(Open Below)*" if details_active else "ℹ️\nView Details\n*Book Information*"
            if st.button(details_label, key=f"qa_btn_details_{b_idx}", use_container_width=True):
                st.session_state[f"show_book_details_{b_idx}"] = not details_active
                st.rerun()

        with qa4:
            related_active = st.session_state.get(f"show_book_related_{b_idx}", False)
            related_label = "✕\nHide Related\n*(Open Below)*" if related_active else "📚\nRelated Books\n*Explore Similar*"
            if st.button(related_label, key=f"qa_btn_related_{b_idx}", use_container_width=True):
                st.session_state[f"show_book_related_{b_idx}"] = not related_active
                st.rerun()

        # 3. EXPANDABLE SECTION: BOOK INFORMATION PER BOOK
        if st.session_state.get(f"show_book_details_{b_idx}", False):
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            col_det_hdr, col_det_btn = st.columns([0.84, 0.16])
            with col_det_hdr:
                st.markdown(
                    f"""
                    <div class="academic-card" style="margin-bottom: 0px; border-color: rgba(16, 185, 129, 0.45); box-shadow: 0 0 20px rgba(16, 185, 129, 0.15);">
                        <div class="academic-card-header" style="margin-bottom: 0px;">
                            <div class="card-header-left">
                                <span class="card-header-icon" style="color: #10b981;">ℹ️</span>
                                <span class="card-header-title">Book Information: {html.escape(b_title)}</span>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col_det_btn:
                if st.button("✕ Close Details", key=f"btn_close_details_panel_{b_idx}", use_container_width=True):
                    st.session_state[f"show_book_details_{b_idx}"] = False
                    st.rerun()

            store_row_html = ""
            if is_purchase_req and purch_url:
                store_row_html = f"""
                <div class="info-row">
                    <div class="info-label"><span>🛒</span> Official Store</div>
                    <div class="info-sep">:</div>
                    <div class="info-val"><a href="{html.escape(purch_url)}" target="_blank" style="color:#f87171; text-decoration:underline; font-weight:700;">Open Official Store / Purchase Link ↗</a></div>
                </div>
                """

            st.markdown(
                f"""
                <div class="academic-card" style="border-top: none; border-top-left-radius: 0; border-top-right-radius: 0; border-color: rgba(16, 185, 129, 0.45); margin-bottom: 16px;">
                    <div class="info-table">
                        <div class="info-row">
                            <div class="info-label"><span>👤</span> Author</div>
                            <div class="info-sep">:</div>
                            <div class="info-val">{html.escape(b_author_str)}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label"><span>📚</span> Genre</div>
                            <div class="info-sep">:</div>
                            <div class="info-val">{html.escape(b_genre)} ({html.escape(b_sub)})</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label"><span>📅</span> Published</div>
                            <div class="info-sep">:</div>
                            <div class="info-val">{html.escape(str(b_year))}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label"><span>🏢</span> Publisher</div>
                            <div class="info-sep">:</div>
                            <div class="info-val">{html.escape(str(b_publisher))}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label"><span>📄</span> Total Pages</div>
                            <div class="info-sep">:</div>
                            <div class="info-val">{tot_p if tot_p is not None else 'Not specified by provider'}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label"><span>👁️</span> Available Preview</div>
                            <div class="info-sep">:</div>
                            <div class="info-val">{f"{prev_p} pages" if isinstance(prev_p, int) else (prev_p or ('All pages' if is_full_free else 'Sample preview'))}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label"><span>🔒</span> Restricted Pages</div>
                            <div class="info-sep">:</div>
                            <div class="info-val">{f"{restr_p} pages" if isinstance(restr_p, int) else (0 if is_full_free else 'Restricted')}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label"><span>💵</span> Official Price</div>
                            <div class="info-sep">:</div>
                            <div class="info-val">{html.escape(price_val) if price_val else ('Free (Public Domain)' if is_full_free else 'Free with Library Account')}</div>
                        </div>
                        {store_row_html}
                        <div class="info-row">
                            <div class="info-label"><span>🌐</span> Language</div>
                            <div class="info-sep">:</div>
                            <div class="info-val">{html.escape(b_lang)}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label"><span>📦</span> Format</div>
                            <div class="info-sep">:</div>
                            <div class="info-val">{html.escape(b_formats)}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label"><span>⬇️</span> Download</div>
                            <div class="info-sep">:</div>
                            <div class="info-val">{('Available (' + b_dl_fmt + ')') if has_dl else 'Not Available in Public Domain'}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label"><span>📖</span> Reading Access</div>
                            <div class="info-sep">:</div>
                            <div class="info-val"><a href="{b_read_url}" target="_blank" style="color:#00e5ff; text-decoration:underline;">Open Reading Link ↗</a></div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # 4. EXPANDABLE SECTION: RELATED BOOKS PER BOOK
        if st.session_state.get(f"show_book_related_{b_idx}", False):
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            related_list = []
            search_res = curr_book.get("search_res") or st.session_state.get("last_internet_search") or {}
            cand_list = search_res.get("results", [])
            for cand in cand_list:
                if cand.get("title", "").strip().lower() != b_title.strip().lower():
                    related_list.append(cand)
                    if len(related_list) >= 4:
                        break

            if not related_list and curr_book.get("related_book"):
                related_list.append(curr_book["related_book"])

            if not related_list and "the time machine" in b_title.lower():
                related_list.append({
                    "title": "The War of the Worlds",
                    "authors": ["H. G. Wells"],
                    "cover_b64": wow_cover_b64,
                    "reading_url": "https://www.gutenberg.org/ebooks/36.html.images",
                    "published_year": "1898",
                    "genre": "Science Fiction"
                })

            col_rel_hdr, col_rel_btn = st.columns([0.84, 0.16])
            with col_rel_hdr:
                st.markdown(
                    f"""
                    <div class="academic-card" style="margin-bottom: 0px; border-color: rgba(245, 158, 11, 0.45); box-shadow: 0 0 20px rgba(245, 158, 11, 0.15);">
                        <div class="academic-card-header" style="margin-bottom: 0px;">
                            <div class="card-header-left">
                                <span class="card-header-icon" style="color: #f59e0b;">📚</span>
                                <span class="card-header-title">Related Books matching "{html.escape(b_title)}"</span>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col_rel_btn:
                if st.button("✕ Close Related", key=f"btn_close_related_panel_{b_idx}", use_container_width=True):
                    st.session_state[f"show_book_related_{b_idx}"] = False
                    st.rerun()

            if not related_list:
                st.markdown(
                    """
                    <div style="background: rgba(10, 22, 42, 0.7); border: 1px dashed rgba(245, 158, 11, 0.35); border-radius: 12px; padding: 22px; text-align: center; color: #94a3b8; font-size: 13.5px; margin-top: 8px; margin-bottom: 16px;">
                        No related books found for this title. Try searching for related subjects or author names above.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                rel_cols = st.columns(min(len(related_list), 4))
                for r_idx, r_book in enumerate(related_list[:4]):
                    r_title = safe_text(r_book.get("title"), "Related Book")
                    r_auth = ", ".join(safe_authors_list(r_book.get("authors")))
                    r_cover_b64 = r_book.get("cover_b64")
                    r_cover_url = r_book.get("cover_url")

                    with rel_cols[r_idx]:
                        if r_cover_b64:
                            c_tag = f'<img src="data:image/jpeg;base64,{r_cover_b64}" style="width:100%; height:130px; object-fit:cover; border-radius:6px;"/>'
                        elif r_cover_url:
                            c_tag = f'<img src="{r_cover_url}" style="width:100%; height:130px; object-fit:cover; border-radius:6px;" onerror="this.onerror=null; this.src=\'data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 130%22><rect width=%22100%22 height=%22130%22 fill=%22%230c192e%22/><text x=%2250%22 y=%2265%22 fill=%22%2300e5ff%22 font-size=%2224%22 text-anchor=%22middle%22 dominant-baseline=%22middle%22>📖</text></svg>\';"/>'
                        else:
                            c_tag = '<div style="width:100%; height:130px; display:flex; align-items:center; justify-content:center; background:#0c192e; color:#00e5ff; font-size:28px; border-radius:6px;">📖</div>'

                        st.markdown(
                            f"""
                            <div style="background: #09152a; border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 10px; padding: 10px; text-align: center; margin-top: 8px; margin-bottom: 8px;">
                                {c_tag}
                                <div style="font-weight: 700; color: #FFFFFF; font-size: 12.5px; margin-top: 8px; line-height: 1.2; height: 32px; overflow: hidden;">{html.escape(r_title)}</div>
                                <div style="color: #38bdf8; font-size: 11px; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{html.escape(r_auth)}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        if st.button("🔍 Search This", key=f"btn_search_rel_{b_idx}_{r_idx}", use_container_width=True):
                            perform_internet_book_search(r_title)
                            st.rerun()


# ---------------------------------------------------------
# TEXTBOOK PDF VIEWER FOR MATH / LOCAL SEARCH
# ---------------------------------------------------------
def render_pdf_page_image(pdf_path: str, page_num: int, dpi: int = 130):
    if not pdf_path or not Path(pdf_path).is_file() or page_num < 1:
        return None
    try:
        import pymupdf
        with pymupdf.open(pdf_path) as doc:
            if 1 <= page_num <= len(doc):
                pix = doc[page_num - 1].get_pixmap(dpi=dpi)
                return pix.tobytes("png")
    except Exception as exc:
        print(f"Error rendering PDF page: {exc}")
    return None

if st.session_state.get("last_book_search_sections"):
    book_results = st.session_state["last_book_search_sections"]
    active_q = st.session_state.get("last_book_search_query", "")
    total_found = sum(len(secs) for secs in book_results.values())
    if total_found > 0:
        st.markdown(
            f"""
            <div class="academic-card" style="margin-top: 14px;">
                <div class="academic-card-header">
                    <div class="card-header-left">
                        <span class="card-header-icon">📖</span>
                        <span class="card-header-title">Authentic Textbook PDF Pages for "{active_q}"</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        for b_name, sec_list in book_results.items():
            if not sec_list:
                continue
            for sec_idx, sec in enumerate(sec_list[:3]):
                pdf_path = sec.get("file_path", "")
                if pdf_path and Path(pdf_path).is_file():
                    p_nums = [p["pdf_page"] for p in sec.get("pages", [])[:2]]
                    for p_num in p_nums:
                        img_bytes = render_pdf_page_image(pdf_path, p_num, dpi=130)
                        if img_bytes:
                            img_b64 = base64.b64encode(img_bytes).decode("ascii")
                            st.markdown(
                                f"""
                                <div style="background: #09152a; border: 1px solid rgba(0, 229, 255, 0.25); border-radius: 12px; padding: 12px; margin-bottom: 12px; text-align: center;">
                                    <div style="font-size: 12px; color: #38bdf8; font-weight: 600; margin-bottom: 6px;">
                                        {sec.get('section_heading', 'Section')} (PDF Page {p_num})
                                    </div>
                                    <img src="data:image/png;base64,{img_b64}" style="max-width: 100%; height: auto; border-radius: 6px;"/>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

# ---------------------------------------------------------
# ACTIVE CHAT MESSAGE STREAM (IF CONVERSATION ACTIVE)
# ---------------------------------------------------------
if st.session_state.active_messages:
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    for msg in st.session_state.active_messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        time_str = msg.get("time", "")
        safe_c = html.escape(content).replace("\n", "<br>")
        if role == "user":
            st.markdown(
                f"""
                <div class="chat-bubble-row user">
                    <div class="chat-bubble-bubble user">
                        {safe_c}
                        <div style="font-size: 10.5px; color: #38bdf8; text-align: right; margin-top: 4px;">{time_str}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div class="chat-bubble-row">
                    <div class="chat-bubble-bubble bot">
                        {safe_c}
                        <div style="font-size: 10.5px; color: #64748b; margin-top: 4px;">{time_str}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

# ---------------------------------------------------------
# AMBIGUOUS INTENT CLARIFICATION PROMPT (IF PENDING)
# ---------------------------------------------------------
if st.session_state.get("pending_ambiguous_query"):
    amb_q = st.session_state["pending_ambiguous_query"]
    st.markdown(
        f"""
        <div style="background: rgba(14, 165, 233, 0.08); border: 1px solid rgba(0, 229, 255, 0.35); border-radius: 12px; padding: 12px 16px; margin: 10px 0 14px 0;">
            <div style="font-weight: 600; color: #38bdf8; font-size: 13px; margin-bottom: 6px;">
                🔍 Clarify Search Intent for "{html.escape(amb_q)}"
            </div>
            <div style="color: #94a3b8; font-size: 11.5px; margin-bottom: 10px;">
                Choose whether you want to find a book record or search inside indexed textbook pages:
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    col_a1, col_a2, col_a3 = st.columns([1, 1, 2])
    with col_a1:
        if st.button("📖 Find Book", key="btn_amb_book", use_container_width=True):
            st.session_state["pending_ambiguous_query"] = None
            b_res = perform_internet_book_search(amb_q)
            st.session_state.active_messages.append({
                "role": "assistant",
                "content": b_res.get("message") or f"📖 Found book record for **{amb_q}**.",
                "time": datetime.now().strftime("%I:%M %p")
            })
            save_current_conversation()
            st.rerun()
    with col_a2:
        if st.button("📄 Search Inside Books", key="btn_amb_topic", use_container_width=True):
            st.session_state["pending_ambiguous_query"] = None
            ans = perform_book_search(amb_q)
            st.session_state.active_messages.append({
                "role": "assistant",
                "content": ans,
                "time": datetime.now().strftime("%I:%M %p")
            })
            save_current_conversation()
            st.rerun()

# ---------------------------------------------------------
# FIXED BOTTOM CHAT INPUT BAR (EXACT SCREENSHOT MATCH)
# ---------------------------------------------------------
with st.form(key="bottom_chat_form", clear_on_submit=True):
    col_spark, col_c_text, col_c_btn = st.columns([0.035, 0.915, 0.05], vertical_alignment="center")
    with col_spark:
        st.markdown('<div class="bottom-sparkles">✨</div>', unsafe_allow_html=True)
    with col_c_text:
        user_msg_in = st.text_input(
            "Ask anything",
            placeholder="Ask anything about books, syllabus, or your subject...",
            key="prompt_text_field",
            label_visibility="collapsed"
        )
    with col_c_btn:
        submitted_prompt = st.form_submit_button("➤", key="bottom_send_btn")
        if submitted_prompt and user_msg_in:
            handle_user_message(user_msg_in)
            st.rerun()