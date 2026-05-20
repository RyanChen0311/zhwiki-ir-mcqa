# QAbot

> An unsupervised Traditional Chinese multiple-choice QA system built on a **Wikipedia-scale inverted index** and **jieba POS-tagged tokenisation** — no model training required.

---

## Overview

Given a multiple-choice question in Traditional Chinese, QAbot selects the correct answer by measuring how strongly each option co-occurs with the question's keywords across Wikipedia.

The approach is entirely **information-retrieval based**: no neural network, no training data, no GPU needed.

---

## How It Works

```
Question: "中國戰國時期秦國政治人物，歷仕秦始皇、秦二世..."
Options:  A. 鄭丰   B. 荊軻   C. 趙高
```

### Step 1 — Build the inverted index (offline, one-time)

```
Wikipedia dump (1.2M articles)
        ↓  jieba tokenisation + POS filtering (nouns only)
Inverted index: token → [article_id, article_id, ...]

e.g.  "趙高": [259003, 640980, 702905, ...]
      "秦始皇": [14201, 259003, 381774, ...]
```

### Step 2 — Answer a question (online)

```
1. Tokenise question → keywords: ["秦國", "政治人物", "秦始皇", "秦二世", ...]
2. For each keyword k and each option X:
       score[X] += |articles(k) ∩ articles(X)|
3. Return argmax(score)
```

The intuition: if "趙高" and "秦始皇" appear together in many Wikipedia articles, they are likely related — making C the correct answer.

---

## Architecture

```
inverted_index_build.py          QAbot.py
┌──────────────────────┐         ┌──────────────────────────┐
│ Wikipedia JSON dump  │         │ questions_example.json   │
│  (tokenised, ~5 GB)  │         │  inverted_index.json     │
└──────────┬───────────┘         └────────────┬─────────────┘
           │ ijson stream                      │
           ▼                                   ▼
  build_index()                     extract_keywords()
  ● filter nouns (len ≥ 2)          ● jieba POS tagging
  ● deduplicate per article         ● noun filter + noise removal
           │                                   │
           ▼                                   ▼
  inverted_index.json           answer_question()
                                ● set intersection scoring
                                ● argmax selection
                                           │
                                           ▼
                                  answer_list.json
```

---

## Project Structure

```
QAbot/
├── QAbot.py                  # QA pipeline: tokenise → score → answer
├── inverted_index_build.py   # Offline index builder (streams Wikipedia dump)
├── requirements.txt
└── README.md

External data files (not included — see Setup):
├── dict.txt.big              # jieba Traditional Chinese dictionary
├── userdict_ex.txt           # 300,000 custom vocabulary entries
├── wiki_tokenize_*.json      # Tokenised Wikipedia dump
├── inverted_index.json       # Pre-built index output
└── questions_example.json    # Question input file
```

---

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Download jieba Traditional Chinese dictionary
# Place dict.txt.big in the project root
# https://github.com/fxsjy/jieba

# (Optional) Add custom vocabulary
# Place userdict_ex.txt in the project root
```

---

## Usage

### 1. Build the inverted index (one-time, ~hours on full Wikipedia)

```bash
python inverted_index_build.py \
    --input   wiki_tokenize_2021_08_05_1215639.json \
    --output  inverted_index.json \
    --log-every 1000
```

Sample output:
```
[build] streaming wiki_tokenize_2021_08_05_1215639.json ...
  processed 1,000 articles | index size: 48,231 tokens
  processed 2,000 articles | index size: 89,104 tokens
  ...
[build] done — 1,215,639 articles, 1,243,087 unique tokens
[save] done → inverted_index.json
```

### 2. Run QAbot on a question set

```bash
python QAbot.py \
    --questions questions_example.json \
    --index     inverted_index.json \
    --output    answer_list.json
```

Sample output:
```
--- Q1 ---
  keywords: ['秦國', '政治人物', '秦始皇', '秦二世', '沙丘']
  scores → A:3  B:11  C:47
  answer: C
```

---

## Question Format

```json
[
  {
    "Question": "中國戰國時期秦國及秦朝政治人物，歷仕秦始皇、秦二世和秦王子嬰三代君主...",
    "A": "鄭丰",
    "B": "荊軻",
    "C": "趙高"
  }
]
```

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Noun-only keywords (`n`) | Nouns carry the most topical signal; verbs/adjectives add noise |
| Set intersection count | Simple, fast, and surprisingly effective for factual QA |
| `ijson` streaming | Wikipedia dump is 5+ GB — cannot fit in RAM as a single JSON load |
| Centralised noise list | Single `_NOISE_BASE` set replaces 5 duplicated `ignore_list` variables |
| `argparse` CLI | Paths are configurable without editing source code |

---

## Dataset

- **Wikipedia corpus**: Chinese Wikipedia dump (August 2021), tokenised with jieba — 1,215,639 articles
- **Questions**: Traditional Chinese multiple-choice questions (history, geography, science)
- **Custom dictionary**: 300,000 entries from KEM noun dictionary (`userdict_ex.txt`)

---

## License

MIT — see [LICENSE](LICENSE).