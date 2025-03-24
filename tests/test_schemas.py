import csv
import os
import tempfile
from pathlib import Path

import pytest

from qiitareactioncounter.schemas import ReactionCounts


@pytest.fixture
def sample_counts() -> ReactionCounts:
    """テスト用のサンプルデータを作成"""
    return ReactionCounts(
        likes={1: 10, 2: 5, 3: 2},
        stocks={1: 8, 2: 3},
        reactions={1: 12, 2: 6, 3: 4},
    )


@pytest.fixture
def temp_csv_file() -> Path:
    """一時的なCSVファイルを作成"""
    fd, path = tempfile.mkstemp(suffix=".csv", text=True)
    os.close(fd)
    return Path(path)


def test_to_csv(sample_counts: ReactionCounts, temp_csv_file: Path) -> None:
    """CSVファイルへの出力をテスト"""
    # CSVファイルに出力
    sample_counts.to_csv(str(temp_csv_file))

    # 出力されたファイルの内容を確認
    with open(temp_csv_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # ヘッダーの確認
    assert reader.fieldnames == ["value", "likes", "stocks", "reactions"]

    # データの確認
    expected_rows = [
        {"value": "1", "likes": "10", "stocks": "8", "reactions": "12"},
        {"value": "2", "likes": "5", "stocks": "3", "reactions": "6"},
        {"value": "3", "likes": "2", "stocks": "0", "reactions": "4"},
    ]
    assert rows == expected_rows


def test_from_csv(sample_counts: ReactionCounts, temp_csv_file: Path) -> None:
    """CSVファイルからの読み込みをテスト"""
    # まずサンプルデータをCSVファイルに出力
    sample_counts.to_csv(str(temp_csv_file))

    # CSVファイルから読み込む
    loaded_counts = ReactionCounts.from_csv(str(temp_csv_file))

    # 読み込んだデータが元のデータと一致することを確認
    assert loaded_counts.likes == sample_counts.likes
    assert loaded_counts.stocks == sample_counts.stocks
    assert loaded_counts.reactions == sample_counts.reactions


def test_csv_roundtrip(sample_counts: ReactionCounts, temp_csv_file: Path) -> None:
    """出力して読み込む一連の流れをテスト"""
    # 出力して読み込む
    sample_counts.to_csv(str(temp_csv_file))
    loaded_counts = ReactionCounts.from_csv(str(temp_csv_file))

    # 元のデータと完全に一致することを確認
    assert loaded_counts == sample_counts


def test_from_csv_empty_file(temp_csv_file: Path) -> None:
    """空のCSVファイルからの読み込みをテスト"""
    # 空のCSVファイルを作成
    with open(temp_csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["value", "likes", "stocks", "reactions"])

    # 空のファイルから読み込む
    counts = ReactionCounts.from_csv(str(temp_csv_file))

    # 空の辞書が返されることを確認
    assert counts.likes == {}
    assert counts.stocks == {}
    assert counts.reactions == {}
