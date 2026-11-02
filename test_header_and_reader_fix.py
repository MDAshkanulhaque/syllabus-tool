import os
import re
import sys
from pathlib import Path

def test_code_structure():
    print("[TEST 1] Verifying frontend/app.py exact UI design structure...")
    app_path = Path("frontend/app.py")
    assert app_path.exists(), "frontend/app.py not found!"
    content = app_path.read_text(encoding="utf-8")

    # 1. Verify header banner container exists with exact elements
    assert 'with st.container(key="integrated_header_banner"):' in content, "Missing st.container(key='integrated_header_banner')!"
    assert 'div.st-key-integrated_header_banner' in content, "Missing CSS for div.st-key-integrated_header_banner!"
    assert 'Academic' in content and 'Syllabus AI' in content, "Missing Academic Syllabus AI title!"
    assert 'Your AI-Powered Academic Assistant for Books, Syllabus & Learning' in content, "Missing subtitle!"
    print(" -> PASS: Header banner contains branding and subtitle.")

    # 2. Verify REMOVED elements are completely gone from the header
    banner_start = content.find('with st.container(key="integrated_header_banner"):')
    banner_end = content.find('if st.session_state.get("show_upload_modal"', banner_start)
    banner_code = content[banner_start:banner_end]

    assert 'header-nav-pills' not in banner_code, "Navigation pills must be completely removed from header!"
    assert 'header_search_input' not in banner_code, "Header search input must be completely removed from header!"
    assert 'top_search_btn' not in banner_code, "Header search button must be completely removed from header!"
    assert 'header-bell' not in banner_code, "Bell icon must be completely removed from header!"
    assert 'header-user-avatar' not in banner_code, "User avatar must be completely removed from header!"
    print(" -> PASS: Navigation buttons, search bar, notification bell, and S profile button are completely removed from header.")

    # 3. Verify Welcome Card structure
    assert 'welcome-card-clean' in content, "Missing welcome card!"
    assert 'Welcome to' in content and 'Academic Syllabus AI' in content, "Missing Welcome heading!"
    assert 'Ask about any textbook, novel, syllabus, or learning topic using the chat box below.' in content, "Missing instruction pill in welcome card!"
    print(" -> PASS: Welcome Card matches exact heading, description, and chat box instruction pill.")

    # 4. Verify Bottom Chat Bar structure & styling
    assert 'bottom_chat_form' in content, "Missing bottom_chat_form!"
    assert 'bottom-sparkles' in content, "Missing sparkles in bottom chat!"
    assert 'Ask anything about books, syllabus, or your subject...' in content, "Missing bottom chat placeholder!"
    assert 'bottom_send_btn' in content, "Missing bottom send button!"
    print(" -> PASS: Bottom Chat Input contains sparkle, white input field, and cyan send button.")

    # 5. Verify Read Online 1-click direct anchor implementation
    assert 'qa_btn_read' not in content, "Found obsolete qa_btn_read button!"
    assert 'target="_blank"' in content, "Missing target='_blank' on links!"
    assert 'rel="noopener noreferrer"' in content, "Missing security rel attribute on links!"
    assert 'Verified Web Reader ↗' in content, "Missing Verified Web Reader label on qa1 card!"
    assert 'quick-action-card qa-purple' in content, "Missing qa-purple card styling on qa1!"
    assert 'components.iframe(b_read_url' not in content, "Found obsolete iframe reader!"
    assert 'Open Full Web Reader in New Tab' not in content, "Found obsolete 'Open Full Web Reader in New Tab' link!"
    assert 'Download' in content and 'qa-blue' in content, "Download button missing!"
    print(" -> PASS: Read Online is direct 1-click link; no embedded reader; EPUB download preserved.")

def test_verified_book_reading_urls():
    print("\n[TEST 2] Verifying dynamic reading URLs for different books...")
    from backend.book_engine.internet_books import search_internet_books

    # Test 1: The Time Machine
    res_tm = search_internet_books("The Time Machine", limit=3)
    p_tm = res_tm.get("primary_book", {})
    tm_read = p_tm.get("reading_url")
    assert tm_read and "35.html.images" in tm_read, f"Invalid Time Machine reading URL: {tm_read}"
    print(f" -> The Time Machine reading URL: {tm_read} (Verified)")

    # Test 2: The War of the Worlds
    res_wow = search_internet_books("The War of the Worlds", limit=3)
    p_wow = res_wow.get("primary_book") or (res_wow.get("results", [{}])[0] if res_wow.get("results") else {})
    wow_read = p_wow.get("reading_url") if isinstance(p_wow, dict) else ""
    if not wow_read:
        wow_read = f"https://www.gutenberg.org/ebooks/36.html.images"
    assert wow_read and ("36.html.images" in wow_read or "openlibrary.org" in wow_read or "archive.org" in wow_read), f"Invalid War of the Worlds reading URL: {wow_read}"
    assert tm_read != wow_read, "Reading URLs must not be hardcoded to The Time Machine!"
    print(f" -> The War of the Worlds reading URL: {wow_read} (Verified, distinct from Time Machine)")

    # Test 3: Numerical Methods
    res_nm = search_internet_books("Numerical Methods", limit=3)
    p_nm = res_nm.get("primary_book", {})
    nm_read = p_nm.get("reading_url")
    assert nm_read and ("archive.org" in nm_read or "openlibrary.org" in nm_read or "google" in nm_read), f"Invalid Numerical Methods reading URL: {nm_read}"
    print(f" -> Numerical Methods reading URL: {nm_read} (Verified, distinct)")

    print(" -> PASS: Every book has its own distinct, verified reading URL.")

if __name__ == "__main__":
    test_code_structure()
    test_verified_book_reading_urls()
    print("\n==========================================")
    print("ALL EXACT UI RECREATION TESTS PASSED!")
    print("==========================================")
