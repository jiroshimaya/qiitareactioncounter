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


def test_run_analysis_with_userid(test_output_dir):
    """特定のユーザーIDを指定した場合のテスト
    全ユーザーの集計と分析、および指定したユーザーの集計と分析が実行されることを確認します。

    実行例:
        QIITA_USERID=Qiita uv run pytest manual_tests/manual_test_run_analysis.py -v -k test_run_analysis_with_userid
    """
    # 環境変数からQiitaトークンを取得
    qiita_token = os.getenv("QIITA_TOKEN")
    if not qiita_token:
        pytest.skip("環境変数 QIITA_TOKEN が設定されていません")

    # ユーザーIDを環境変数から取得
    userid = os.getenv("QIITA_USERID", "Qiita")

    # コマンドライン引数の設定
    sys.argv = [
        "script.py",
        "--start_date=2024-01-01",
        "--end_date=2024-01-31",
        f"--userid={userid}",
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
    user_csv = output_path / f"{userid}_reactions.csv"
    assert user_csv.exists()
    user_analysis = output_path / f"{userid}_analysis_result.json"
    assert user_analysis.exists()


def test_run_analysis(test_output_dir):
    """useridを指定しない場合のテスト
    全ユーザーの集計と分析、および認証ユーザーの集計と分析が実行されることを確認します。

    実行例:
        uv run pytest manual_tests/manual_test_run_analysis.py -v -k test_run_analysis
    """
    # テスト用の設定
    qiita_token = os.getenv("QIITA_TOKEN")
    if not qiita_token:
        pytest.skip("環境変数 QIITA_TOKEN が設定されていません")

    # コマンドライン引数の設定
    sys.argv = [
        "script.py",
        "--start_date=2024-01-01",
        "--end_date=2024-01-31",
        f"--output_dir={test_output_dir}",
        "--sample_size=100",
    ]

    # テスト実行
    settings = Settings()  # type: ignore
    run_analysis(settings)

    # 出力ファイルの確認
    output_path = Path(test_output_dir)

    # デバッグ用：出力ディレクトリの内容を表示
    print("\n=== 出力ディレクトリの内容 ===")
    for file in output_path.glob("*"):
        print(f"- {file}")
    print("===========================\n")

    # 全ユーザーの集計結果の確認
    assert (output_path / "all_users_reactions.csv").exists(), (
        "全ユーザーの集計結果が生成されていること"
    )
    assert (output_path / "all_users_analysis_result.json").exists(), (
        "全ユーザーの分析結果が生成されていること"
    )

    # 認証ユーザーの集計結果の確認
    user_files = list(output_path.glob("*_reactions.csv"))
    assert len(user_files) > 0, "認証ユーザーの集計結果が生成されていること"
    user_id = user_files[0].stem.replace("_reactions", "")
    assert (output_path / f"{user_id}_reactions.csv").exists(), (
        "認証ユーザーの集計結果が生成されていること"
    )
    assert (output_path / f"{user_id}_analysis_result.json").exists(), (
        "認証ユーザーの分析結果が生成されていること"
    )
