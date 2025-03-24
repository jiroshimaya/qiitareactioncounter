#!/usr/bin/env python3

import pytest

from qiitareactioncounter.count_reactions import get_articles


@pytest.mark.manual
def test_get_articles(headers, query):
    """手動テスト: get_articles関数の動作確認"""
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
