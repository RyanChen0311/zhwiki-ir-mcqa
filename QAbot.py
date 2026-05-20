"""
QAbot.py — Traditional Chinese multiple-choice QA system
=========================================================

Algorithm
---------
1. Tokenise the question using jieba (noun-only, POS tag = 'n').
2. For each keyword, retrieve the set of Wikipedia article IDs from the
   inverted index.
3. For each answer option (A / B / C), count how many articles contain
   BOTH the keyword AND the answer option (set intersection size).
4. The option with the highest total intersection count is selected as
   the answer.

This is an unsupervised IR-based approach — no model training required.

Usage
-----
    python QAbot.py --questions questions_example.json \
                    --index    inverted_index.json \
                    --output   answer_list.json

Author: Ryan Chen
"""

import json
import argparse
import jieba
import jieba.posseg as pseg


# ---------------------------------------------------------------------------
# Stop-word / noise configuration
# ---------------------------------------------------------------------------

# Base noise words (too generic to be discriminative)
_NOISE_BASE = {
    '官方', '主權國家', '簡稱', '首任', '校長', '定位', '大學', '目標',
    '綜合大學', '改名', '現代', '學風', '省份', '省會', '人類', '生活',
    '距今', '中國', '亞洲', '並稱', '分屬', '國家', '城市', '憲法',
    '首都', '政府', '國王', '全世界', '語言', '地區', '總部', '從事',
    '行動', '生產', '成立於', '業務', '技術', '授權', '消費者', '部門',
    '品牌', '製造', '跨國公司', '通訊設備', '頂點', '鄰國', '人口',
    '國界', '原本', '全國', '中央', '地理位置', '在一起', '能力', '相關',
    '產品', '中部', '中心', '城鎮', '又稱', '景點',
    # Extended noise
    '東北', '西南', '服務', '基礎', '通信', '遷都', '國土', '海港',
    '西岸', '市為', '方面', '非洲', '美國', '致力於', '戰爭', '實現', '合作',
}

# Word normalisation: map specific tokens to a more useful lookup term
_WORD_MAP = {
    '西非國家': '西非',
}

# Part-of-speech tags to keep (noun only)
_TARGET_POS = {'n'}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def load_json(path: str) -> object:
    """Load a UTF-8 JSON file and return the parsed object."""
    with open(path, mode='r', encoding='utf-8') as f:
        return json.load(f)


def save_json(obj: object, path: str) -> None:
    """Save an object to a UTF-8 JSON file with readable indentation."""
    with open(path, mode='w', encoding='utf-8') as f:
        json.dump(obj, f, sort_keys=True, indent=4, ensure_ascii=False)
        f.write('\n')
    print(f'[saved] {path}')


def extract_keywords(text: str) -> list[str]:
    """
    Tokenise *text* with jieba POS tagging and return discriminative nouns.

    Filters:
    - Only keep tokens whose POS tag is in _TARGET_POS.
    - Drop single-character tokens (too ambiguous).
    - Drop tokens in _NOISE_BASE.
    - Apply _WORD_MAP normalisation.
    - Deduplicate while preserving order.
    """
    seen = set()
    keywords = []
    for word, flag in pseg.cut(text):
        if flag not in _TARGET_POS:
            continue
        if len(word) == 1:
            continue
        if word in _NOISE_BASE:
            continue
        word = _WORD_MAP.get(word, word)
        if word not in seen:
            seen.add(word)
            keywords.append(word)
    return keywords


# ---------------------------------------------------------------------------
# Core QA logic
# ---------------------------------------------------------------------------

def answer_question(question: dict, inverted_index: dict) -> str:
    """
    Select the best answer option for *question* using inverted-index scoring.

    Parameters
    ----------
    question : dict
        Keys: 'Question', 'A', 'B', 'C'
    inverted_index : dict
        Maps token → list of Wikipedia article IDs.

    Returns
    -------
    str
        The winning option key: 'A', 'B', or 'C'.
    """
    options = {key: question[key] for key in ('A', 'B', 'C')}

    # Build article-ID sets for each option
    option_sets = {
        key: set(inverted_index.get(term, []))
        for key, term in options.items()
    }

    # Log missing options
    for key, term in options.items():
        if not option_sets[key]:
            print(f'  [warn] option {key} ("{term}") not in inverted index')

    # Score each option by counting keyword co-occurrences
    scores = {key: 0 for key in options}
    keywords = extract_keywords(question['Question'])

    print(f'  keywords: {keywords}')

    for kw in keywords:
        kw_articles = set(inverted_index.get(kw, []))
        if not kw_articles:
            print(f'  [warn] keyword "{kw}" not in inverted index')
            continue
        for key, opt_articles in option_sets.items():
            scores[key] += len(kw_articles & opt_articles)

    print(f'  scores → A:{scores["A"]}  B:{scores["B"]}  C:{scores["C"]}')

    best = max(scores, key=lambda k: scores[k])
    return best


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(questions_path: str, index_path: str, output_path: str) -> None:
    """Load data, run QAbot on every question, and save answers."""

    # Load resources
    print('[init] loading jieba dictionary ...')
    jieba.set_dictionary('dict.txt.big')
    print('[init] loading user dictionary ...')
    jieba.load_userdict('userdict_ex.txt')
    print('[init] dictionaries loaded.')

    print(f'[load] questions  : {questions_path}')
    questions = load_json(questions_path)
    print(f'[load] index      : {index_path}')
    inverted_index = load_json(index_path)
    print(f'[info] {len(questions)} questions | {len(inverted_index)} index entries\n')

    answers = []
    for i, q in enumerate(questions, start=1):
        print(f'--- Q{i} ---')
        ans = answer_question(q, inverted_index)
        print(f'  answer: {ans}')
        answers.append(ans)

    print(f'\n[result] {answers}')
    save_json(answers, output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Traditional Chinese multiple-choice QA via inverted index'
    )
    parser.add_argument('--questions', default='questions_example.json',
                        help='Path to question JSON file')
    parser.add_argument('--index',     default='inverted_index.json',
                        help='Path to inverted index JSON file')
    parser.add_argument('--output',    default='answer_list.json',
                        help='Path for output answer JSON file')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    run(args.questions, args.index, args.output)