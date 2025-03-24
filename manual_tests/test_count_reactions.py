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


@pytest.mark.manual
def test_get_articles():
    """get_articlesのマニュアルテスト
    実際のAPIを呼び出して、記事の取得が正しく行われることを確認します。
    """
    # テスト用の設定
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")  # 過去7日間
    query = create_query(start_date, end_date)
    headers = {
        "Authorization": "Bearer your_token"
    }  # テスト実行時に実際のトークンに置き換えてください

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


@pytest.mark.manual
def test_run_count_reactions():
    """run_count_reactionsのマニュアルテスト
    実際のAPIを呼び出して、記事の取得と集計が正しく行われることを確認します。
    """
    # テスト用の設定
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")  # 過去7日間
    output_file = "test_manual_counts.csv"

    settings = Settings(
        qiita_token="your_token",  # テスト実行時に実際のトークンに置き換えてください
        start_date=start_date,
        end_date=end_date,
        username=None,  # 全ユーザーの記事を取得
        sample_size=100,  # テスト用に少なめの件数
        output_file=output_file,
    )

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
