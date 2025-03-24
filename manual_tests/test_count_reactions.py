import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from qiitareactioncounter.count_reactions import (
    Settings,
    create_query,
    get_articles,
    run_count_reactions,
)
from qiitareactioncounter.schemas import ReactionCounts

# 環境変数でマニュアルテスト実行を制御
run_manual_tests = os.getenv("RUN_MANUAL_TESTS") == "1"


@pytest.mark.skip
def test_get_articles():
    """get_articlesのマニュアルテスト
    実際のAPIを呼び出して、記事の取得が正しく行われることを確認します。
    """
    # テスト用の設定
    qiita_token = os.getenv("QIITA_TOKEN")
    if not qiita_token:
        pytest.skip("環境変数 QIITA_TOKEN が設定されていません")

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")  # 過去7日間
    query = create_query(start_date, end_date)
    headers = {"Authorization": f"Bearer {qiita_token}"}

    # 記事の取得
    print(f"クエリ: {query}")
    articles = get_articles(query=query, page=1, per_page=10, headers=headers)

    # 結果の表示
    print(f"\n取得した記事数: {len(articles)}")
    for article in articles:
        print("\n--- 記事情報 ---")
        print(f"タイトル: {article.title}")
        print(f"いいね数: {article.likes_count}")
        print(f"ストック数: {article.stocks_count}")
        print(f"URL: {article.url}")
        print(f"作成日時: {article.created_at}")
        print(f"更新日時: {article.updated_at}")

    # 基本的な検証
    assert len(articles) > 0, "記事が取得できていません"
    assert len(articles) <= 10, "取得件数が想定より多いです"


@pytest.mark.skip
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
