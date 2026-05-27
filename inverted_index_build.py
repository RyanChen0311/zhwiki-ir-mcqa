"""
inverted_index_build.py — Build an inverted index from a tokenised Wikipedia dump
==================================================================================

Input format
------------
A JSON file produced by a Wikipedia tokenisation pipeline.  Each item is:

    {
        "id": 259003,
        "tokens": [
            [["詞彙", "n"], ["另一個詞", "nr"], ...],   ← sentence 1
            ...
        ]
    }

Output format
-------------
    {
        "趙高": [259003, 640980, ...],
        ...
    }

Each key is a noun token (length ≥ 2, POS in TARGET_POS).
Each value is a sorted list of article IDs in which that token appears.

Usage
-----
    python inverted_index_build.py --input  wiki_tokenize.json \
                                   --output inverted_index.json \
                                   --log-every 1000

Author: Ryan Chen
"""

import json
import argparse
import ijson


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Part-of-speech tags to index
TARGET_POS = {'n', 'ng', 'nr', 'nrfg', 'nrt', 'ns', 'nt', 'nz'}


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------

def build_index(input_path: str, log_every: int = 1000) -> dict:
    """
    Stream-parse *input_path* with ijson and build the inverted index.

    Using ijson avoids loading the entire multi-GB Wikipedia dump into
    memory — articles are processed one at a time.

    Parameters
    ----------
    input_path : str
        Path to the tokenised Wikipedia JSON file.
    log_every : int
        Print a progress message every this many articles.

    Returns
    -------
    dict
        token → sorted list of article IDs
    """
    index: dict[str, set] = {}   # use sets during build for O(1) membership
    article_count = 0

    print(f'[build] streaming {input_path} ...')

    with open(input_path, mode='r', encoding='utf-8') as f:
        for article in ijson.items(f, 'item'):
            article_id = article['id']

            for sentence in article['tokens']:
                for token, pos in sentence:
                    # Filter: length ≥ 2, target POS only
                    if len(token) < 2 or pos not in TARGET_POS:
                        continue

                    if token not in index:
                        index[token] = set()
                    index[token].add(article_id)

            article_count += 1
            if article_count % log_every == 0:
                print(f'  processed {article_count:,} articles '
                      f'| index size: {len(index):,} tokens')

    print(f'[build] done — {article_count:,} articles, '
          f'{len(index):,} unique tokens')

    # Convert sets to sorted lists for JSON serialisation
    return {token: sorted(ids) for token, ids in index.items()}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def save_json(obj: object, path: str) -> None:
    """Save *obj* to a UTF-8 JSON file."""
    print(f'[save] writing {path} ...')
    with open(path, mode='w', encoding='utf-8') as f:
        json.dump(obj, f, sort_keys=True, indent=4, ensure_ascii=False)
        f.write('\n')
    print(f'[save] done → {path}')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Build an inverted index from a tokenised Wikipedia dump'
    )
    parser.add_argument('--input',     default='wiki_tokenize.json',
                        help='Path to tokenised Wikipedia JSON')
    parser.add_argument('--output',    default='inverted_index.json',
                        help='Path for the output inverted index JSON')
    parser.add_argument('--log-every', type=int, default=1000,
                        help='Print progress every N articles (default: 1000)')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    index = build_index(args.input, log_every=args.log_every)
    save_json(index, args.output)