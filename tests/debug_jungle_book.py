import requests

# Open Library
r_ol = requests.get('https://openlibrary.org/search.json', params={'title': 'The Jungle Book', 'limit': 5, 'fields': 'key,title,author_name,first_publish_year,cover_i,isbn,ia,ebook_access'}, timeout=6)
print('OL Status:', r_ol.status_code)
for d in r_ol.json().get('docs', [])[:3]:
    print('  OL:', d.get('title'), '|', d.get('author_name'), '| ia:', d.get('ia'))

# Internet Archive
r_ia = requests.get('https://archive.org/advancedsearch.php', params={'q': 'title:("The Jungle Book") AND mediatype:(texts)', 'output': 'json', 'rows': 5, 'fl[]': ['identifier', 'title', 'creator', 'year', 'format']}, timeout=6)
print('IA Status:', r_ia.status_code)
for d in r_ia.json().get('response', {}).get('docs', [])[:3]:
    print('  IA:', d.get('title'), '|', d.get('creator'), '| id:', d.get('identifier'))
