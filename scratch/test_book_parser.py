import sys
import os
import re

sys.stdout.reconfigure(encoding='utf-8')

sample_entries = [
    '1. Morris R. Mano, Michael D. Ciletti, “Digital Design: With an Introduction to the Verilog HDL, VHDL, and SystemVerilog”, 6th Edition, Pearson Education, 2018.',
    '2. David A. Patterson and John L. Hennessy, Computer Organization and Design: The Hardware/Software Interface, Fifth Edition, Morgan Kaufmann / Elsevier, 2014.',
    '3. John F. Wakerly, Digital Design Principles and Practices, Fifth Edition, Pearson Education, 2018.',
    '4. Charles H. Roth Jr, Larry L. Kinney, Fundamentals of Logic Design, Sixth Edition, CENGAGE Learning, 2013.',
    '1. Reema Thareja, Python Programming: Using Problem Solving Approach, Oxford University Press, 2019',
    '2. Allen B. Downey, “Think Python: How to Think Like a Computer Scientist”, Second Edition, Updated for Python 3, Shroff/O’Reilly Publishers, 2016.',
    '1. Grewal B.S., “Higher Engineering Mathematics”, 44th Edition, Khanna Publishers, 2021.',
    '1. Jean-Paul Tremblay and Paul G. Sorenson, “An Introduction to Data Structures with Applications”, 2nd Edition, McGraw Hill, 2013.'
]

KNOWN_PUBLISHERS = [
    'Pearson', 'McGraw-Hill', 'McGraw Hill', 'MC Graw Hill', 'Elsevier', 'Wiley', 'Oxford', 'Cambridge',
    'Prentice', 'Khanna', 'Cengage', 'CENGAGE', 'Springer', 'O’Reilly', 'O\'Reilly', 'Shroff',
    'Addison-Wesley', 'Morgan Kaufmann', 'New Age', 'Tata McGraw', 'Laxmi', 'Vikas', 'PHI'
]

def parse_book_entry(entry):
    clean_e = re.sub(r'^\s*(?:[TR]?\d+[\.\)\-]?\s*)+', '', entry).strip()
    
    # Year
    year_m = re.search(r'\b(19\d{2}|20\d{2})\b', clean_e)
    year_val = int(year_m.group(1)) if year_m else 'Not specified'
    clean_no_yr = re.sub(r'\b(19\d{2}|20\d{2})\b', '', clean_e)
    
    # Edition
    ed_m = re.search(r'\b((?:First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|\d+(?:st|nd|rd|th))\s+(?:Edition|Ed\.?))\b', clean_no_yr, re.I)
    ed_val = ed_m.group(1) if ed_m else 'Standard Edition'
    clean_no_ed = re.sub(r'\b((?:First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|\d+(?:st|nd|rd|th))\s+(?:Edition|Ed\.?))\b', '', clean_no_yr, flags=re.I)
    
    # Quoted Title
    quote_m = re.search(r'[\"“]([^\"”]+)[\"”]', clean_no_ed)
    if quote_m:
        title_val = quote_m.group(1).strip(' ,.-;')
        author_val = clean_no_ed[:quote_m.start()].strip(' ,.-;')
        pub_val = clean_no_ed[quote_m.end():].strip(' ,.-;')
    else:
        # Check publisher keyword position
        pub_pos = -1
        pub_keyword_found = ''
        for pub_kw in KNOWN_PUBLISHERS:
            m_pub = re.search(rf'\b{re.escape(pub_kw)}\b', clean_no_ed, re.I)
            if m_pub:
                pub_pos = m_pub.start()
                pub_keyword_found = pub_kw
                break
                
        if pub_pos != -1:
            pub_val = clean_no_ed[pub_pos:].strip(' ,.-;')
            before_pub = clean_no_ed[:pub_pos].strip(' ,.-;')
            
            # Split before_pub into Author and Title by comma or colon
            comma_parts = [p.strip() for p in before_pub.split(',') if p.strip()]
            if len(comma_parts) >= 2:
                w_count = len(comma_parts[0].split())
                if 1 <= w_count <= 5 and not re.search(r'\b(Introduction|Principles|Fundamentals|Digital|Data|Computer|Programming|System|Architecture|Design|Engineering|Mathematics)\b', comma_parts[0], re.I):
                    author_val = comma_parts[0]
                    title_val = ', '.join(comma_parts[1:])
                else:
                    author_val = 'Not specified'
                    title_val = before_pub
            else:
                author_val = 'Not specified'
                title_val = before_pub
        else:
            parts = [p.strip() for p in clean_no_ed.split(',') if p.strip()]
            author_val = parts[0] if len(parts) > 1 else 'Not specified'
            title_val = ', '.join(parts[1:]) if len(parts) > 1 else clean_no_ed
            pub_val = 'Not specified'
            
    author_val = author_val if author_val and len(author_val) >= 3 else 'Not specified'
    pub_val = pub_val if pub_val and len(pub_val) >= 3 else 'Not specified'
    title_val = title_val if title_val else entry
    
    return {'title': title_val, 'author': author_val, 'publisher': pub_val, 'edition': ed_val, 'year': year_val}

for e in sample_entries:
    res = parse_book_entry(e)
    print('RAW:', e)
    print('  Parsed -> Title:', res['title'])
    print('            Author:', res['author'])
    print('            Pub:', res['publisher'])
    print('            Ed:', res['edition'], '| Year:', res['year'])
    print('-'*50)
