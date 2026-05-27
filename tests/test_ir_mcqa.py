import json
from unittest.mock import patch
import ir_mcqa


def test_load_json(tmp_path):
    data = {"key": "value"}
    f = tmp_path / "test.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    assert ir_mcqa.load_json(str(f)) == data


def test_save_json(tmp_path):
    data = ["A", "B", "C"]
    f = tmp_path / "out.json"
    ir_mcqa.save_json(data, str(f))
    assert json.loads(f.read_text(encoding="utf-8")) == data


def test_answer_question_picks_best():
    question = {"Question": "...", "A": "鄭丰", "B": "荊軻", "C": "趙高"}
    index = {
        "秦始皇": [1, 2, 3, 10, 11],
        "鄭丰":   [5],
        "荊軻":   [7, 8],
        "趙高":   [1, 2, 3, 10],
    }
    with patch("ir_mcqa.extract_keywords", return_value=["秦始皇"]):
        result = ir_mcqa.answer_question(question, index)
    assert result == "C"


def test_answer_question_missing_keywords():
    question = {"Question": "...", "A": "甲", "B": "乙", "C": "丙"}
    with patch("ir_mcqa.extract_keywords", return_value=["不存在"]):
        result = ir_mcqa.answer_question(question, {})
    assert result in ("A", "B", "C")


def test_answer_question_tie():
    question = {"Question": "...", "A": "甲", "B": "乙", "C": "丙"}
    index = {"關鍵字": [1, 2, 3], "甲": [1, 2, 3], "乙": [1, 2, 3], "丙": [1, 2, 3]}
    with patch("ir_mcqa.extract_keywords", return_value=["關鍵字"]):
        result = ir_mcqa.answer_question(question, index)
    assert result in ("A", "B", "C")
