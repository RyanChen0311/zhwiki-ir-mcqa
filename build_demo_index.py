"""
build_demo_index.py — Build a small inverted index from Wikipedia API articles
===============================================================================

Fetches ~25 Chinese Wikipedia articles that are relevant to questions_example.json,
tokenises them with jieba, and writes inverted_index.json.

This is a quick-start alternative to processing the full Wikipedia dump
(which requires hours of tokenisation). Accuracy will be lower due to the
smaller corpus, but the end-to-end pipeline can be verified in ~2 minutes.

Usage
-----
    python build_demo_index.py [--output inverted_index.json]

Author: Ryan Chen
"""

import json
import os
import argparse
import time
import requests
import jieba
import jieba.posseg as pseg


# ---------------------------------------------------------------------------
# Articles to fetch — covers all answer options in questions_example.json
# ---------------------------------------------------------------------------

ARTICLES = [
    # Q1 — 趙高
    '趙高', '荊軻', '秦始皇', '秦二世',
    # Q2 — 柏拉圖
    '柏拉圖', '亞里斯多德', '伊比鳩魯', '蘇格拉底',
    # Q3 — 愛因斯坦
    '愛因斯坦', '波耳', '相對論', '光電效應',
    # Q4 — 孫中山
    '孫中山', '蔣中正', '袁世凱', '辛亥革命',
    # Q5 — 聖母峰
    '聖母峰', '干城章嘉峰', '喜馬拉雅山脈',
    # Q6 — 濁水溪
    '濁水溪', '淡水河', '大甲溪',
    # Q7 — 牛頓
    '牛頓', '伽利略', '克卜勒', '萬有引力定律',
]

# POS tags to index (same set as inverted_index_build.py)
TARGET_POS = {'n', 'ng', 'nr', 'nrfg', 'nrt', 'ns', 'nt', 'nz'}

WIKI_API = 'https://zh.wikipedia.org/w/api.php'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fetch_article(title: str, retries: int = 3) -> str:
    """Return the plain-text extract of a Chinese Wikipedia article."""
    params = {
        'action': 'query',
        'prop': 'extracts',
        'explaintext': True,
        'format': 'json',
        'titles': title,
        'redirects': True,
        'variant': 'zh-hant',   # return Traditional Chinese content
    }
    for attempt in range(retries):
        try:
            resp = requests.get(WIKI_API, params=params, timeout=15,
                                headers={'User-Agent': 'ir-mcqa-demo/1.0',
                                         'Accept-Language': 'zh-TW'})
            if resp.status_code == 429:
                wait = 10 * (attempt + 1)
                print(f'  [rate-limit] waiting {wait}s before retry ...')
                time.sleep(wait)
                continue
            resp.raise_for_status()
            pages = resp.json()['query']['pages']
            page = next(iter(pages.values()))
            return page.get('extract', '')
        except Exception as exc:
            print(f'  [warn] attempt {attempt + 1} failed for "{title}": {exc}')
            time.sleep(5)
    return ''


def tokenise(text: str, article_id: int, index: dict) -> None:
    """Tokenise *text* with jieba POS and add nouns to *index*."""
    seen = set()
    for word, flag in pseg.cut(text):
        if len(word) < 2 or flag not in TARGET_POS:
            continue
        if word in seen:
            continue
        seen.add(word)
        if word not in index:
            index[word] = set()
        index[word].add(article_id)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build(output_path: str) -> None:
    print('[init] loading jieba dictionary ...')
    jieba.set_dictionary('dict.txt.big')
    if os.path.exists('userdict_ex.txt'):
        print('[init] loading user dictionary ...')
        jieba.load_userdict('userdict_ex.txt')
    print('[init] done.\n')

    index: dict[str, set] = {}

    for article_id, title in enumerate(ARTICLES):
        print(f'[fetch] ({article_id + 1}/{len(ARTICLES)}) {title}')
        text = fetch_article(title)
        if not text:
            continue
        tokenise(text, article_id, index)
        time.sleep(2.0)  # stay well under Wikipedia's rate limit

    print(f'\n[build] {len(ARTICLES)} articles → {len(index):,} unique tokens')

    sorted_index = {token: sorted(ids) for token, ids in index.items()}

    print(f'[save] writing {output_path} ...')
    with open(output_path, mode='w', encoding='utf-8') as f:
        json.dump(sorted_index, f, sort_keys=True, indent=4, ensure_ascii=False)
        f.write('\n')
    print(f'[save] done → {output_path}')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Build a demo inverted index from Wikipedia API articles'
    )
    parser.add_argument('--output', default='inverted_index.json',
                        help='Path for the output inverted index JSON')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    build(args.output)
