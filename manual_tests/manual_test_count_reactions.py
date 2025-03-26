import os
import sys
from datetime import datetime
from pathlib import Path

import pytest
import requests

from qiitareactioncounter.count_reactions import (
    Settings,
    collect_articles,
    get_authenticated_user,
    get_user_oldest_article_date,
    run_count_reactions,
)
from qiitareactioncounter.schemas import ReactionCounts


def test_run_count_reactions():
    """run_count_reactionsのマニュアルテスト
    実際のAPIを呼び出して、記事の取得と集計が正しく行われることを確認します。
    """
    # テスト用の設定
    qiita_token = os.getenv("QIITA_TOKEN")
    if not qiita_token:
        pytest.skip("環境変数 QIITA_TOKEN が設定されていません")

    output_file = "test_manual_counts.csv"
    sys.argv = ["script.py", "--output_file", output_file, "--sample_size", "100"]

    settings = Settings()  # type: ignore

    # 実行
    output_path = run_count_reactions(settings)

    # 検証
    assert Path(output_path).exists(), "CSVファイルが生成されていること"
    assert Path(output_path).stat().st_size > 0, "CSVファイルが空でないこと"

    # 生成されたCSVファイルの内容を確認
    counts = ReactionCounts.from_csv(output_path)
    assert len(counts.likes) > 0, "いいねの集計結果が存在すること"
    assert len(counts.stocks) > 0, "ストックの集計結果が存在すること"
    assert len(counts.reactions) > 0, "リアクションの集計結果が存在すること"

    # テスト用のファイルを削除
    Path(output_path).unlink()


def test_get_authenticated_user():
    """get_authenticated_userのマニュアルテスト
    実際のAPIを呼び出して、認証ユーザーの情報が正しく取得できることを確認します。

    実行例:
        QIITA_USERID=shimajiroxyz uv run pytest manual_tests/manual_test_count_reactions.py -v -k test_get_authenticated_user
    """
    # テスト用の設定
    qiita_token = os.getenv("QIITA_TOKEN")
    if not qiita_token:
        pytest.skip("環境変数 QIITA_TOKEN が設定されていません")

    qiita_userid = os.getenv("QIITA_USERID")
    if not qiita_userid:
        pytest.skip("環境変数 QIITA_USERID が設定されていません")

    headers = {"Authorization": f"Bearer {qiita_token}"}

    # 認証ユーザー情報の取得
    userid = get_authenticated_user(headers)

    # 結果の表示
    print(f"\n取得したユーザーID: {userid}")
    print(f"環境変数のユーザーID: {qiita_userid}")

    # APIレスポンスの内容を確認
    r = requests.get("https://qiita.com/api/v2/authenticated_user", headers=headers)
    print(f"\nAPIレスポンス: {r.json()}")

    # 検証
    assert userid == qiita_userid, "取得したユーザーIDが環境変数と一致しません"


def test_collect_articles_sample_size():
    """collect_articles関数のサンプルサイズ適用をテストする

    このテストでは、collect_articles関数が指定されたサンプルサイズを正しく適用するかを
    以下のケースで検証します：

    1. サンプルサイズが少ない場合（5件）
    2. サンプルサイズが多い場合（100件）
    3. 特定ユーザーを指定した場合

    実行例:
        uv run pytest manual_tests/manual_test_count_reactions.py -v -k test_collect_articles_sample_size
    """
    # テスト用の設定
    qiita_token = os.getenv("QIITA_TOKEN")
    if not qiita_token:
        pytest.skip("環境変数 QIITA_TOKEN が設定されていません")

    headers = {"Authorization": f"Bearer {qiita_token}"}
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = "2020-01-01"  # 十分に過去の日付

    print("\n=== collect_articles関数のサンプルサイズテスト ===")

    # 1. 少ないサンプルサイズのテスト（5件）
    print("\n--- 少ないサンプルサイズのテスト（5件） ---")
    small_sample_size = 5

    small_articles = collect_articles(
        start_date=start_date,
        end_date=end_date,
        userid=None,  # 全ユーザー
        sample_size=small_sample_size,
        pages_to_fetch=[1],  # 十分なページ数
        headers=headers,
    )

    print(f"指定したサンプルサイズ: {small_sample_size}")
    print(f"実際に取得した記事数: {len(small_articles)}")

    # サンプル数の検証
    assert len(small_articles) == small_sample_size

    if len(small_articles) > 0:
        print("\n最初の記事のタイトル:", small_articles[0].title)

    # 2. 大きいサンプルサイズのテスト（100件）
    print("\n--- 大きいサンプルサイズのテスト（100件） ---")
    large_sample_size = 99

    large_articles = collect_articles(
        start_date=start_date,
        end_date=end_date,
        userid=None,  # 全ユーザー
        sample_size=large_sample_size,
        pages_to_fetch=[1],  # 十分なページ数
        headers=headers,
    )

    print(f"指定したサンプルサイズ: {large_sample_size}")
    print(f"実際に取得した記事数: {len(large_articles)}")

    # Qiita全体からの取得のためlarge_sample_sizeだけ取得できるはず
    assert len(large_articles) == large_sample_size

    # 3. 特定ユーザーに対するテスト
    print("\n--- 特定ユーザーに対するテスト ---")
    user_sample_size = 10
    test_userid = "Qiita"  # 公式アカウント

    user_articles = collect_articles(
        start_date=start_date,
        end_date=end_date,
        userid=test_userid,
        sample_size=user_sample_size,
        pages_to_fetch=[1],  # 十分なページ数
        headers=headers,
    )

    print(f"指定したユーザー: {test_userid}")
    print(f"指定したサンプルサイズ: {user_sample_size}")
    print(f"実際に取得した記事数: {len(user_articles)}")

    # サンプル数の検証
    assert len(user_articles) == user_sample_size


def test_get_user_oldest_article_date():
    """Qiitaの最も古い投稿の日付を取得するテスト
    ユーザーIDを指定した場合、最も古い投稿の日付が正しく取得できることを確認します。

    実行例:
        QIITA_USERID=shimajiroxyz uv run pytest manual_tests/manual_test_count_reactions.py -v -s -k test_get_user_oldest_article_date
    """
    # 環境変数からQiitaトークンを取得
    qiita_token = os.getenv("QIITA_TOKEN")
    if not qiita_token:
        pytest.skip("環境変数 QIITA_TOKEN が設定されていません")

    # ユーザーIDを環境変数から取得
    userid = os.getenv("QIITA_USERID", "Qiita")

    # テスト実行
    settings = Settings()  # type: ignore
    headers = {"Authorization": f"Bearer {settings.qiita_token}"}
    oldest_date = get_user_oldest_article_date(headers, userid)

    # 結果の表示
    print(f"\n取得した最も古い投稿の日付: {oldest_date}")

    # 検証
    assert oldest_date is not None, "日付が取得できていること"
    assert isinstance(oldest_date, str), "日付が文字列であること"
    assert len(oldest_date.split("-")) == 3, "日付がYYYY-MM-DD形式であること"
