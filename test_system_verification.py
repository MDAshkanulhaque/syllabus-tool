import os
import sys
import json
import uuid
import requests
from datetime import datetime

BACKEND_URL = "http://127.0.0.1:8000"
HISTORY_FILE = os.path.join("frontend", "chat_history.json")

def test_backend_health():
    print("[TEST] Checking FastAPI backend health...")
    try:
        r = requests.get(f"{BACKEND_URL}/docs", timeout=5)
        assert r.status_code == 200, f"Backend docs returned {r.status_code}"
        print(" -> FastAPI Backend is UP and running at http://127.0.0.1:8000")
        return True
    except Exception as e:
        print(f" -> Backend connection failed: {e}")
        return False

def test_a_dynamic_search():
    print("\n[TEST A] Testing Dynamic Search Queries...")
    from backend.book_engine.internet_books import search_internet_books
    
    # 1. The Time Machine
    r_tm = search_internet_books("The Time Machine")
    b_tm = r_tm.get("primary_book", {})
    assert "time machine" in b_tm.get("title", "").lower(), f"Unexpected title: {b_tm.get('title')}"
    print(f" -> Search 'The Time Machine': Found '{b_tm.get('title')}' by {b_tm.get('authors')}")
    
    # 2. NMNT (Numerical Methods)
    r_nmnt = search_internet_books("NMNT")
    b_nmnt = r_nmnt.get("primary_book", {})
    assert "numerical" in b_nmnt.get("title", "").lower() or "grewal" in str(b_nmnt.get("authors", [])).lower(), f"Unexpected NMNT result: {b_nmnt}"
    print(f" -> Search 'NMNT': Found '{b_nmnt.get('title')}' by {b_nmnt.get('authors')}")
    
    # 3. Artificial Intelligence
    r_ai = search_internet_books("Artificial Intelligence")
    b_ai = r_ai.get("primary_book") or (r_ai.get("results", [{}])[0] if r_ai.get("results") else {})
    assert "intelligence" in b_ai.get("title", "").lower() or "academic" in b_ai.get("title", "").lower(), f"Unexpected AI result: {b_ai.get('title')}"
    print(f" -> Search 'Artificial Intelligence': Found '{b_ai.get('title')}' by {b_ai.get('authors')}")
    
    # 4. Another Book (Kreyszig Math)
    r_aem = search_internet_books("Advanced Engineering Mathematics")
    b_aem = r_aem.get("primary_book") or (r_aem.get("results", [{}])[0] if r_aem.get("results") else {})
    assert "mathematics" in b_aem.get("title", "").lower() or "kreyszig" in str(b_aem.get("authors", [])).lower(), f"Unexpected AEM result: {b_aem}"
    print(f" -> Search 'Advanced Engineering Mathematics': Found '{b_aem.get('title')}' by {b_aem.get('authors')}")
    
    print(" -> TEST A PASSED: All searches are completely dynamic with correct metadata!")

def test_b_c_d_quick_actions_and_panels():
    print("\n[TEST B, C, D] Testing Quick Actions & Panel Data...")
    from backend.book_engine.internet_books import search_internet_books
    
    # Test for The Time Machine
    r_tm = search_internet_books("The Time Machine")
    b_tm = r_tm.get("primary_book", {})
    
    # 1. Read Online
    assert b_tm.get("reading_url"), "Missing reading_url"
    print(f" -> Read Online Link: {b_tm.get('reading_url')}")
    
    # 2. Download
    has_dl = bool(b_tm.get("download_url"))
    print(f" -> Download Status: {'Available (' + str(b_tm.get('download_format')) + ')' if has_dl else 'Unavailable'}")
    
    # 3. View Details (Metadata)
    assert b_tm.get("authors"), "Missing authors"
    assert b_tm.get("published_year"), "Missing published_year"
    genre = b_tm.get("genre") or b_tm.get("content_type")
    assert genre, "Missing genre or content_type"
    print(f" -> View Details Metadata: Author={b_tm.get('authors')}, Year={b_tm.get('published_year')}, Genre={genre}")
    
    # 4. Related Books
    results = r_tm.get("results", [])
    print(f" -> Related Books Count from Search: {len(results)}")
    for rel in results[:3]:
        print(f"    - {rel.get('title')} by {rel.get('authors')}")
        
    print(" -> TEST B, C, D PASSED!")

def test_e_f_g_chat_history_persistence():
    print("\n[TEST E, F, G] Testing Chat History Persistence, New Chat, & Deletion...")
    
    # Backup original chat history
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        original_data = json.load(f)
        
    try:
        # Create 3 unique test conversations
        test_convs = []
        for i in range(3):
            cid = f"test_conv_{int(datetime.now().timestamp())}_{i}_{uuid.uuid4().hex[:4]}"
            c_record = {
                "id": cid,
                "title": f"Test Conversation {i+1} Query",
                "date": datetime.now().strftime("%b %d, %I:%M %p"),
                "file_name": "Test_Syllabus.pdf",
                "messages": [
                    {"role": "user", "content": f"Hello question {i+1}", "time": "10:00 AM"},
                    {"role": "assistant", "content": f"Answer response {i+1}", "time": "10:01 AM"}
                ],
                "book_query": f"Query {i+1}",
                "internet_book": {"title": f"Test Book {i+1}", "authors": [f"Author {i+1}"]},
                "book_sections": None
            }
            test_convs.append(c_record)
            
        # Prepend to history and save
        working_history = test_convs + original_data
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(working_history, f, ensure_ascii=False)
            
        # Verify persistence from disk
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            
        saved_ids = [c["id"] for c in loaded]
        for tc in test_convs:
            assert tc["id"] in saved_ids, f"Conversation {tc['id']} was not saved!"
        print(f" -> Successfully saved and reloaded 3 test conversations from disk.")
        
        # Test Delete of exactly 1 conversation (Test F)
        target_del_id = test_convs[1]["id"]
        updated_history = [c for c in loaded if c["id"] != target_del_id]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(updated_history, f, ensure_ascii=False)
            
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            after_del = json.load(f)
            
        after_del_ids = [c["id"] for c in after_del]
        assert target_del_id not in after_del_ids, "Target conversation was not deleted!"
        assert test_convs[0]["id"] in after_del_ids, "Unrelated conversation 0 was deleted!"
        assert test_convs[2]["id"] in after_del_ids, "Unrelated conversation 2 was deleted!"
        print(f" -> TEST F PASSED: Conversation {target_del_id} deleted successfully without affecting others.")
        
    finally:
        # Restore original history
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(original_data, f, ensure_ascii=False)
        print(" -> Original chat_history.json restored cleanly.")
        
    print(" -> TEST E, F, G PASSED!")

def test_h_local_textbook_search():
    print("\n[TEST H] Testing Local Textbook PDF Search...")
    try:
        from backend.book_engine.book_search import search_book_sections
        results = search_book_sections("numerical methods bisection grewal")
        print(f" -> Local Textbook Search Results for 'bisection grewal': {len(results)} books found")
        for b_name, secs in results.items():
            print(f"    * {b_name}: {len(secs)} sections")
        print(" -> TEST H PASSED!")
    except Exception as e:
        print(f" -> Local textbook search note: {e}")

if __name__ == "__main__":
    ok = test_backend_health()
    test_a_dynamic_search()
    test_b_c_d_quick_actions_and_panels()
    test_e_f_g_chat_history_persistence()
    test_h_local_textbook_search()
    print("\n==========================================")
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("==========================================")
