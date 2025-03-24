import os
import tempfile

import pandas as pd

from qiitareactioncounter.analyze_reactions import analyze_reactions


def test_analyze_reactions_basic_stats():
    # テスト用のデータを作成
    data = {"value": [1, 2, 3, 4, 5], "reactions": [1, 1, 1, 1, 1]}
    df = pd.DataFrame(data)

    # 一時的なCSVファイルを作成
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        df.to_csv(f.name, index=False)
        # 分析を実行
        stats = analyze_reactions(f.name, n_values=[1, 2, 3])

    # 一時ファイルを削除
    os.unlink(f.name)

    # 基本統計量の検証
    assert stats.total_articles == 5
    assert stats.median == 3.0
    assert stats.mean == 3.0


def test_analyze_reactions_top_10():
    # テスト用のデータを作成
    data = {
        "value": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "reactions": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    }
    df = pd.DataFrame(data)

    # 一時的なCSVファイルを作成
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        df.to_csv(f.name, index=False)
        # 分析を実行
        stats = analyze_reactions(f.name, n_values=[1, 2, 3])

    # 一時ファイルを削除
    os.unlink(f.name)

    # 上位10%の検証
    assert stats.top_10_threshold == 9.1
    assert stats.top_10_count == 1
    assert stats.top_10_mean == 10.0
    assert stats.top_10_median == 10.0


def test_analyze_reactions_ratios():
    # テスト用のデータを作成
    data = {"value": [1, 2, 3, 4, 5], "reactions": [1, 1, 1, 1, 1]}
    df = pd.DataFrame(data)

    # 一時的なCSVファイルを作成
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        df.to_csv(f.name, index=False)
        # 分析を実行
        stats = analyze_reactions(f.name, n_values=[1, 2, 3])

    # 一時ファイルを削除
    os.unlink(f.name)

    # 割合の検証
    assert stats.n_more_or_ratio[1] == 100.0
    assert stats.n_more_or_ratio[2] == 80.0
    assert stats.n_more_or_ratio[3] == 60.0


def test_analyze_reactions_custom_n_values():
    # テスト用のデータを作成
    data = {"value": [1, 2, 3, 4, 5], "reactions": [1, 1, 1, 1, 1]}
    df = pd.DataFrame(data)

    # 一時的なCSVファイルを作成
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        df.to_csv(f.name, index=False)
        # 分析を実行
        stats = analyze_reactions(f.name, n_values=[2, 4, 5])

    # 一時ファイルを削除
    os.unlink(f.name)

    # 割合の検証
    assert stats.n_more_or_ratio[2] == 80.0
    assert stats.n_more_or_ratio[4] == 40.0
    assert stats.n_more_or_ratio[5] == 20.0
