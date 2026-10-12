import json
import re
from collections import defaultdict

with open('backend/book_index/pages_index.json', 'r', encoding='utf-8') as f:
    records = json.load(f)

GENERIC_MATH_TERMS = {
    'series', 'method', 'methods', 'equation', 'equations', 'function', 'functions',
    'test', 'tests', 'problem', 'problems', 'system', 'systems', 'rule', 'rules',
    'form', 'forms', 'analysis', 'theory', 'approximation', 'approximations',
    'solution', 'solutions', 'value', 'values', 'space', 'spaces', 'integral',
    'integrals', 'transform', 'transforms', 'derivative', 'derivatives', 'error',
    'errors', 'variable', 'variables', 'theorem', 'theorems', 'formula', 'formulas',
    'computation', 'computations', 'introduction', 'basic', 'concepts', 'application',
    'applications'
}

def normalize_text(text):
    if not isinstance(text, str):
        return ''
    text = text.casefold()
    text = re.sub(r'[\u2010-\u2015]', '-', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def tokenize(text):
    return re.findall(r'[a-z0-9]+(?:[.-][a-z0-9]+)*', normalize_text(text))

def test_search(query):
    norm_q = normalize_text(query)
    q_words = tokenize(norm_q)
    q_word_set = set(q_words)
    distinctive_words = [w for w in q_words if w not in GENERIC_MATH_TERMS]
    if not distinctive_words:
        distinctive_words = q_words

    print(f"\n==========================================")
    print(f"=== Testing Query: '{query}' ===")
    print(f"==========================================")
    print('Query words:', q_words)
    print('Distinctive words:', distinctive_words)

    # Group records by (book, chapter, section)
    sections_by_book = defaultdict(lambda: defaultdict(list))
    for r in records:
        b = r.get('book_name')
        ch = r.get('chapter_heading') or 'Unavailable'
        sec = r.get('section_heading') or 'Unavailable'
        sections_by_book[b][(ch, sec)].append(r)

    categorized_results = defaultdict(lambda: {'direct': [], 'related': [], 'content': []})

    for b, secs in sections_by_book.items():
        for (ch, sec), pages in secs.items():
            if sec == 'Unavailable' and ch == 'Unavailable':
                continue
            pages_sorted = sorted(pages, key=lambda x: x['pdf_page'])
            sec_searchable = ' '.join(p.get('search_text', '') for p in pages_sorted)
            sec_clean = normalize_text(sec)
            sec_core = re.sub(r'^\d+(\.\d+)*\s*', '', sec_clean)
            ch_clean = normalize_text(ch)

            # Check if distinctive words exist anywhere in heading or body
            has_dist_in_sec_head = any(w in sec_clean for w in distinctive_words)
            has_dist_in_ch_head = any(w in ch_clean for w in distinctive_words)
            has_dist_in_body = any(w in sec_searchable for w in distinctive_words)

            if not (has_dist_in_sec_head or has_dist_in_ch_head or has_dist_in_body):
                continue

            # Exact matching checks
            exact_sec_heading = (sec_core == norm_q) or (sec_clean == norm_q)
            phrase_in_sec_head = norm_q in sec_clean
            all_words_in_sec_head = q_word_set.issubset(set(tokenize(sec_clean)))
            phrase_in_body = norm_q in sec_searchable
            phrase_count_body = len(re.findall(rf'\b{re.escape(norm_q)}\b', sec_searchable))
            all_words_in_body = q_word_set.issubset(set(tokenize(sec_searchable)))

            # Distinguish whether heading is a specialized/related variant
            # (e.g. Fourier Transform, Fourier Integral, Generalized Fourier Series, Fourier-Bessel)
            is_specialized_variant = False
            if norm_q == 'fourier series':
                if any(w in sec_clean for w in ['transform', 'integral', 'generalized', 'bessel', 'polynomial', 'period', 'sturm']):
                    is_specialized_variant = True

            match_type = None
            score = 0.0

            # 1. DIRECT MATCH
            if exact_sec_heading:
                match_type = 'direct'
                score = 10000.0 + phrase_count_body * 2
            elif phrase_in_sec_head and not is_specialized_variant:
                match_type = 'direct'
                score = 8000.0 + phrase_count_body * 2
            elif all_words_in_sec_head and len(q_words) > 1 and not is_specialized_variant:
                match_type = 'direct'
                score = 6000.0 + phrase_count_body * 2
            elif is_specialized_variant:
                # Labeled as Related Topic per Task 1
                match_type = 'related'
                score = 3000.0 + phrase_count_body * 5
            elif phrase_in_body and phrase_count_body >= 5 and (has_dist_in_sec_head or has_dist_in_ch_head):
                match_type = 'direct'
                score = 4000.0 + phrase_count_body * 10
            # 2. RELATED TOPIC
            elif has_dist_in_sec_head:
                match_type = 'related'
                score = 2500.0 + phrase_count_body * 5
            elif has_dist_in_ch_head:
                match_type = 'related'
                score = 2000.0 + phrase_count_body * 5
            # 3. OTHER CONTENT MATCH
            elif phrase_in_body and phrase_count_body >= 1:
                match_type = 'content'
                score = 500.0 + phrase_count_body * 10
            elif all_words_in_body and phrase_count_body >= 1:
                match_type = 'content'
                score = 200.0 + phrase_count_body

            if match_type:
                categorized_results[b][match_type].append({
                    'section': sec,
                    'chapter': ch,
                    'score': score,
                    'phrase_count': phrase_count_body,
                    'pdf_start': pages_sorted[0]['pdf_page'],
                    'pdf_end': pages_sorted[-1]['pdf_page']
                })

    for b, cat_dict in categorized_results.items():
        total_b = sum(len(lst) for lst in cat_dict.values())
        print(f"\nBook: {b} (Total: {total_b} matching sections)")
        for cat in ['direct', 'related', 'content']:
            cat_list = cat_dict[cat]
            cat_list.sort(key=lambda x: (-x['score'], x['pdf_start']))
            print(f"  [{cat.upper()}] ({len(cat_list)} sections):")
            for item in cat_list:
                print(f"     • {item['section']} (PDF pp. {item['pdf_start']}–{item['pdf_end']}, score: {item['score']}, count: {item['phrase_count']})")

if __name__ == '__main__':
    test_search('Fourier Series')
