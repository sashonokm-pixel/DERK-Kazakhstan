"""DERK: preliminary, auditable thematic screening. No final percentage without review.
Usage: python derk_preliminary_coding.py article_corpus.csv --ethnos Немцы --out derk_results
Requires Python standard library only. Read-only with respect to source and Supabase.
"""
import argparse
import csv
import re
from pathlib import Path

RULES = {
    'Немцы': {'origin': 'Германия', 'terms': [r'германи\w*', r'фрг\b', r'берлин\w*', r'бундестаг\w*']},
    'Русские': {'origin': 'Россия', 'terms': [r'росси\w*', r'российск\w*', r'москв\w*', r'санкт.петербург\w*']},
    'Корейцы': {'origin': 'Корейский полуостров', 'terms': [r'коре\w*', r'сеул\w*', r'пхеньян\w*']},
}
KZ = [r'казахстан\w*', r'республик\w+ казахстан\w*', r'астан\w*', r'алмат\w*', r'петропавловск\w*', r'караганд\w*', r'шымкент\w*', r'актоб\w*']
KAZAKH_MARKERS = [r'\bқазақ\w*', r'\bқазақстан\w*', r'\bжәне\b', r'\bүшін\b', r'\bтуралы\b', r'\bқұрметті\b', r'\bқатысты\b', r'\bбүгін\b', r'\bмемлекетт\w*']


def hits(text, patterns):
    return sorted(set(m.group(0) for p in patterns for m in re.finditer(p, text, re.I)))[:12]


def classify(row, rules):
    title = (row.get('title') or row.get('title_hint') or '').strip()
    body = (row.get('text') or '').strip()
    # Stronger title evidence; body evidence alone does not establish thematic relevance.
    kz_title, kz_body = hits(title, KZ), hits(body, KZ)
    origin_title, origin_body = hits(title, rules['terms']), hits(body, rules['terms'])
    kazakh_hits = hits(body, KAZAKH_MARKERS)
    # A single Kazakh word, proper name or website footer is not a Kazakh-language publication.
    return {
        **row,
        'internal_agenda_preliminary': 'candidate' if kz_title or kz_body else 'no_signal',
        'internal_evidence': '; '.join(kz_title or kz_body),
        'origin_agenda_preliminary': 'candidate' if origin_title or origin_body else 'no_signal',
        'origin_evidence': '; '.join(origin_title or origin_body),
        'state_language_preliminary': 'review_language' if len(kazakh_hits) >= 3 else 'no_clear_signal',
        'state_language_evidence': '; '.join(kazakh_hits),
        'internal_agenda_verified': '',
        'origin_agenda_verified': '',
        'state_language_verified': '',
        'verified_article': '',
        'review_note': '',
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('corpus')
    p.add_argument('--ethnos', default='Немцы')
    p.add_argument('--out', default='derk_results')
    args = p.parse_args()
    if args.ethnos not in RULES:
        p.error('Для этого этноса сначала требуется согласовать референтную страну/регион и словарь: ' + args.ethnos)
    with open(args.corpus, encoding='utf-8-sig', newline='') as f:
        records = list(csv.DictReader(f))
    seen = set()
    results = []
    for r in records:
        url = (r.get('url') or '').strip().rstrip('/')
        if not url or url in seen:
            continue
        seen.add(url)
        results.append(classify(r, RULES[args.ethnos]))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    destination = out / 'content_preliminary_review.csv'
    if results:
        with destination.open('w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(results[0]))
            w.writeheader()
            w.writerows(results)
    print(f'{len(results)} уникальных материалов; предварительные сигналы, НЕ подтверждённые проценты. {destination}')

if __name__ == '__main__':
    main()
