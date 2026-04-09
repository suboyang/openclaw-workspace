#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

import duckdb

DB_PATH = Path('/home/openclaw/.openclaw/workspace/openclaw.duckdb')


def tokenize_query(query: str):
    query = query.strip()
    if not query:
        return []
    tokens = [query]
    for part in re.split(r'[\s,，、;；/]+', query):
        part = part.strip()
        if part and part not in tokens:
            tokens.append(part)
    return tokens


def search_articles(query: str, limit: int):
    con = duckdb.connect(str(DB_PATH), read_only=True)
    tokens = tokenize_query(query)
    if not tokens:
        return []

    field_weights = [
        ('article_title_zh', 100),
        ('summary_zh', 60),
        ('article_title', 40),
        ('summary', 20),
        ('description', 10),
        ('tags', 5),
    ]

    select_parts = [
        'article_title', 'article_title_zh', 'summary', 'summary_zh', 'source_url',
        'source_file', 'author', 'published_time', 'tags', 'audio_file', 'status'
    ]

    score_clauses = []
    where_clauses = []
    params = []
    where_params = []

    for token in tokens:
        q = f'%{token}%'
        token_match_clauses = []
        for field, weight in field_weights:
            score_clauses.append(f"CASE WHEN {field} ILIKE ? THEN {weight} ELSE 0 END")
            params.append(q)
            token_match_clauses.append(f"{field} ILIKE ?")
            where_params.append(q)
        where_clauses.append('(' + ' OR '.join(token_match_clauses) + ')')

    sql = f'''
        SELECT
            {', '.join(select_parts)},
            ({' + '.join(score_clauses)}) AS score
        FROM clippings_articles
        WHERE {' OR '.join(where_clauses)}
        ORDER BY score DESC, published_time DESC
        LIMIT ?
    '''

    rows = con.execute(sql, params + where_params + [limit]).fetchall()
    con.close()

    results = []
    for r in rows:
        results.append({
            'article_title': r[0],
            'article_title_zh': r[1],
            'summary': r[2],
            'summary_zh': r[3],
            'source_url': r[4],
            'source_file': r[5],
            'author': r[6],
            'published_time': str(r[7]) if r[7] else None,
            'tags': r[8],
            'audio_file': r[9],
            'status': r[10],
            'score': r[11],
        })
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('query', help='keyword to search in clippings_articles')
    ap.add_argument('--limit', type=int, default=5)
    args = ap.parse_args()

    results = search_articles(args.query, args.limit)
    print(json.dumps({
        'db': str(DB_PATH),
        'query': args.query,
        'tokens': tokenize_query(args.query),
        'count': len(results),
        'results': results,
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
