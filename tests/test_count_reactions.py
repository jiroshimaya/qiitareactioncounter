import sys
from unittest.mock import patch

import pytest

from qiitareactioncounter.count_reactions import (
    Settings,
    collect_articles,
    count_reactions,
    create_query,
)
from qiitareactioncounter.schemas import QiitaArticle


@pytest.fixture(autouse=True)
def setup_sys_argv():
    """テスト実行時にsys.argvを設定する"""
    original_argv = sys.argv
    sys.argv = ["script.py"]
    yield
    sys.argv = original_argv


@pytest.fixture
def settings():
    return Settings(
        qiita_token="test_token",
        start_date="2024-01-01",
        end_date="2024-01-31",
        username="test_user",
        sample_size=100,
        output_file="test_counts.csv",
    )


def test_create_query():
    query = create_query("2024-01-01", "2024-01-31", "test_user")
    expected = "created:>=2024-01-01 created:<=2024-01-31 user:test_user"
    assert query == expected


def test_create_query_without_username():
    query = create_query("2024-01-01", "2024-01-31")
    expected = "created:>=2024-01-01 created:<=2024-01-31"
    assert query == expected


@patch("qiitareactioncounter.count_reactions.get_articles")
def test_collect_articles(mock_get_articles, settings):
    # モックの設定
    mock_get_articles.side_effect = [
        [
            QiitaArticle.model_validate(
                {
                    "id": "1",
                    "likes_count": 10,
                    "stocks_count": 5,
                    "title": "Test Article 1",
                    "url": "https://qiita.com/articles/1",
                    "created_at": "2024-01-01T00:00:00+09:00",
                    "updated_at": "2024-01-01T00:00:00+09:00",
                }
            )
        ],  # ページ1の記事
        [
            QiitaArticle.model_validate(
                {
                    "id": "2",
                    "likes_count": 20,
                    "stocks_count": 10,
                    "title": "Test Article 2",
                    "url": "https://qiita.com/articles/2",
                    "created_at": "2024-01-02T00:00:00+09:00",
                    "updated_at": "2024-01-02T00:00:00+09:00",
                }
            )
        ],  # ページ2の記事
    ]

    # テスト実行
    articles = collect_articles(
        start_date=settings.start_date,
        end_date=settings.end_date,
        username=settings.username,
        sample_size=settings.sample_size,
        pages_to_fetch=[1, 2],
        headers={"Authorization": "Bearer test_token"},
    )

    # 検証
    assert len(articles) == 2
    assert [a.id for a in articles] == ["1", "2"]
    assert [a.likes_count for a in articles] == [10, 20]
    assert [a.stocks_count for a in articles] == [5, 10]
    assert mock_get_articles.call_count == 2


def test_count_reactions():
    articles = [
        QiitaArticle.model_validate(
            {
                "id": "1",
                "likes_count": 10,
                "stocks_count": 5,
                "title": "Test Article 1",
                "url": "https://qiita.com/articles/1",
                "created_at": "2024-01-01T00:00:00+09:00",
                "updated_at": "2024-01-01T00:00:00+09:00",
            }
        ),
        QiitaArticle.model_validate(
            {
                "id": "2",
                "likes_count": 20,
                "stocks_count": 10,
                "title": "Test Article 2",
                "url": "https://qiita.com/articles/2",
                "created_at": "2024-01-02T00:00:00+09:00",
                "updated_at": "2024-01-02T00:00:00+09:00",
            }
        ),
        QiitaArticle.model_validate(
            {
                "id": "3",
                "likes_count": 10,
                "stocks_count": 5,
                "title": "Test Article 3",
                "url": "https://qiita.com/articles/3",
                "created_at": "2024-01-03T00:00:00+09:00",
                "updated_at": "2024-01-03T00:00:00+09:00",
            }
        ),
    ]

    counts = count_reactions(articles)

    assert counts.likes == {10: 2, 20: 1}
    assert counts.stocks == {5: 2, 10: 1}
    assert counts.reactions == {15: 2, 30: 1}
