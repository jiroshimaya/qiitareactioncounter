import os
import sys
from pathlib import Path

import pytest

from qiitareactioncounter.run_analysis import Settings, run_analysis


@pytest.fixture
def test_output_dir(tmp_path):
    """テスト用の出力ディレクトリを作成"""
    output_dir = tmp_path / "test_results"
    output_dir.mkdir()
    return str(output_dir)


@pytest.mark.skip
def test_run_analysis(test_output_dir):
    """run_analysisの正常系テスト

    このテストでは以下の点を確認します：
    1. 全ユーザーの集計と分析が正常に実行されること
    2. 特定ユーザーの集計と分析が正常に実行されること
    3. 出力ディレクトリに必要なファイルが生成されること

    必要な環境変数：
    - QIITA_TOKEN: Qiitaのアクセストークン
    """
    # 環境変数からQiitaトークンを取得
    qiita_token = os.getenv("QIITA_TOKEN")
    if not qiita_token:
        pytest.skip("環境変数 QIITA_TOKEN が設定されていません")

    # ユーザー名を環境変数から取得
    username = os.getenv("USERNAME", "Qiita")

    # コマンドライン引数の設定
    sys.argv = [
        "script.py",
        "--start_date=2024-01-01",
        "--end_date=2024-01-31",
        f"--username={username}",
        f"--output_dir={test_output_dir}",
        "--sample_size=99",
    ]

    # テスト実行
    settings = Settings()  # type: ignore
    run_analysis(settings)

    # 出力ディレクトリの確認
    output_path = Path(test_output_dir)
    assert output_path.exists()

    # 全ユーザーの集計結果の確認
    all_users_csv = output_path / "all_users_reactions.csv"
    assert all_users_csv.exists()
    all_users_analysis = output_path / "all_users_analysis_result.json"
    assert all_users_analysis.exists()

    # 特定ユーザーの集計結果の確認
    user_csv = output_path / f"{username}_reactions.csv"
    assert user_csv.exists()
    user_analysis = output_path / f"{username}_analysis_result.json"
    assert user_analysis.exists()
