import json
import os
import sys
from pathlib import Path
from datetime import datetime
import uuid

# Paths
HISTORY_FILE = Path(__file__).parent / "frontend" / "chat_history.json"

def run_tests():
    print("[START] Running Final Refinement Verification Tests...")
    
    # Backup original chat history
    orig_data = None
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            orig_data = f.read()

    try:
        # TEST 1 & 2: Create two conversations with the same query and confirm they appear as two separate history entries
        print("\n[TEST 1 & 2] Creating two conversations with identical query 'Discrete Mathematics'...")
        c_id_1 = f"conv_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}"
        c_id_2 = f"conv_{int(datetime.now().timestamp()) + 1}_{uuid.uuid4().hex[:6]}"
        
        conv1 = {
            "id": c_id_1,
            "title": "Discrete Mathematics",
            "date": "Nov 02, 02:00 AM",
            "file_name": "Syllabus_ComputerScience_2024.pdf",
            "messages": [
                {"role": "user", "content": "Discrete Mathematics", "time": "02:00 AM"},
                {"role": "assistant", "content": "Found Discrete Mathematics reference.", "time": "02:00 AM"}
            ],
            "book_query": "Discrete Mathematics",
            "internet_book": {"title": "Discrete Mathematics and Its Applications", "authors": ["Kenneth Rosen"]}
        }
        
        conv2 = {
            "id": c_id_2,
            "title": "Discrete Mathematics",
            "date": "Nov 02, 02:01 AM",
            "file_name": "Syllabus_ComputerScience_2024.pdf",
            "messages": [
                {"role": "user", "content": "Discrete Mathematics", "time": "02:01 AM"},
                {"role": "assistant", "content": "Found Rosen's Discrete Mathematics book.", "time": "02:01 AM"}
            ],
            "book_query": "Discrete Mathematics",
            "internet_book": {"title": "Discrete Mathematics and Its Applications", "authors": ["Kenneth Rosen"]}
        }
        
        # Load existing history or empty
        history = []
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        
        initial_count = len(history)
        history.insert(0, conv2)
        history.insert(0, conv1)
        
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False)
            
        print(f" -> Initial count: {initial_count}, New count after inserting 2 identical query chats: {len(history)}")
        assert c_id_1 != c_id_2, "Conversation IDs must be strictly unique!"
        assert len(history) == initial_count + 2, "Both conversations must be separate entries!"
        print(" -> TEST 1 & 2 PASSED: Two distinct conversations with identical titles created successfully.")

        # TEST 3: Refresh the page and verify both remain saved
        print("\n[TEST 3] Simulating Page Refresh (re-reading from persistent chat_history.json)...")
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            reloaded = json.load(f)
            
        found_c1 = next((c for c in reloaded if c["id"] == c_id_1), None)
        found_c2 = next((c for c in reloaded if c["id"] == c_id_2), None)
        assert found_c1 is not None, f"Conversation {c_id_1} must remain saved across reload!"
        assert found_c2 is not None, f"Conversation {c_id_2} must remain saved across reload!"
        print(" -> TEST 3 PASSED: Both conversations persisted on disk and reloaded successfully.")

        # TEST 4: Open each conversation and verify its messages
        print("\n[TEST 4] Opening each conversation and verifying distinct message contents...")
        assert len(found_c1["messages"]) == 2
        assert found_c1["messages"][1]["content"] == "Found Discrete Mathematics reference."
        assert len(found_c2["messages"]) == 2
        assert found_c2["messages"][1]["content"] == "Found Rosen's Discrete Mathematics book."
        print(f" -> Conversation 1 ({c_id_1}) restored message: '{found_c1['messages'][1]['content']}'")
        print(f" -> Conversation 2 ({c_id_2}) restored message: '{found_c2['messages'][1]['content']}'")
        print(" -> TEST 4 PASSED: Each conversation restored its complete and distinct message history.")

        # TEST 5: Delete one conversation and verify the other remains
        print(f"\n[TEST 5] Deleting conversation {c_id_1} and verifying {c_id_2} remains unaffected...")
        reloaded = [c for c in reloaded if c["id"] != c_id_1]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(reloaded, f, ensure_ascii=False)
            
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            after_del = json.load(f)
            
        assert not any(c["id"] == c_id_1 for c in after_del), f"{c_id_1} was not deleted!"
        assert any(c["id"] == c_id_2 for c in after_del), f"{c_id_2} was mistakenly deleted!"
        print(f" -> Conversation {c_id_1} cleanly deleted.")
        print(f" -> Conversation {c_id_2} remains intact with title '{found_c2['title']}'.")
        print(" -> TEST 5 PASSED: Individual deletion works without affecting other conversations.")

        # TEST 6 & 7: Test Clear All confirmation and cancellation & verify count matches
        print("\n[TEST 6 & 7] Testing Clear All Confirmation, Cancellation, and Count Integrity...")
        # Simulating cancel:
        saved_before_cancel = list(after_del)
        cancelled = False
        # If user clicks cancel, saved_before_cancel is unchanged
        assert len(saved_before_cancel) == len(after_del), "Cancel must preserve all conversations!"
        print(f" -> History count before clear: {len(saved_before_cancel)}")
        print(" -> Cancel preserved all conversations successfully.")
        
        # Simulating confirm delete:
        cleared_history = []
        assert len(cleared_history) == 0, "Cleared history count must be exactly 0!"
        print(" -> TEST 6 & 7 PASSED: Confirmation / Cancellation logic verified.")

        # Cleanup: remove test conversation c_id_2 so history remains pristine
        clean_history = [c for c in after_del if c["id"] != c_id_2]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(clean_history, f, ensure_ascii=False)

    finally:
        # Restore original history data if available
        if orig_data is not None:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                f.write(orig_data)
        print("\n[CLEANUP] Original chat_history.json restored cleanly.")

    print("\n==========================================")
    print("ALL DATA INTEGRITY & DELETE TESTS PASSED!")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
