#!/usr/bin/env python3
import random
import sys

import requests
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from qiitareactioncounter.schemas import QiitaArticle, ReactionCounts

API_URL = "https://qiita.com/api/v2/items"


class Settings(BaseSettings):
    qiita_token: str = Field(..., description="Qiitaのアクセストークン")
    start_date: str = Field(
        default="1900-01-01", description="開始日（YYYY-MM-DD形式）"
    )
    end_date: str = Field(default="2099-12-31", description="終了日（YYYY-MM-DD形式）")
    username: str | None = Field(default=None, description="ユーザー名（オプション）")
    sample_size: int = Field(
        default=1000, description="サンプル件数（デフォルト1000件）"
    )
    output_file: str = Field(
        default="counts.csv", description="出力ファイル名（デフォルトcounts.csv）"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        cli_parse_args=True,
        extra="ignore",
    )


def get_articles(
    query: str, page: int, per_page: int, headers: dict[str, str]
) -> list[QiitaArticle]:
    params = {"page": page, "per_page": per_page, "query": query}
    r: requests.Response = requests.get(API_URL, params=params, headers=headers)
    if r.status_code != 200:
        print(f"Error fetching page {page}: {r.text}")
        return []
    return [QiitaArticle.model_validate(article) for article in r.json()]


def find_valid_last_page(query, headers):
    """二分探索で実際に記事が存在する最後のページを見つける"""
    left = 1
    right = 100  # Qiita APIの制限（100ページ）
    last_valid_page = 1

    # まず1ページ目で記事が取得できるか確認
    articles = get_articles(query, 1, 100, headers)
    if not articles:
        return 0

    while left <= right:
        mid = (left + right) // 2
        articles = get_articles(query, mid, 100, headers)

        if articles:  # 記事が存在する場合
            last_valid_page = mid
            left = mid + 1
        else:  # 記事が存在しない場合
            right = mid - 1

    return last_valid_page


def create_query(start_date: str, end_date: str, username: str | None = None) -> str:
    """クエリ文字列を生成する"""
    query = f"created:>={start_date} created:<={end_date}"
    if username:
        query = f"{query} user:{username}"
    return query


def collect_articles(
    start_date: str,
    end_date: str,
    username: str | None,
    sample_size: int,
    pages_to_fetch: list[int],
    headers: dict,
) -> list[QiitaArticle]:
    """指定されたページから記事を収集する"""
    collected_articles = []
    per_page = 100
    query = create_query(start_date, end_date, username)

    for page in pages_to_fetch:
        articles = get_articles(query, page, per_page, headers)
        print(f"ページ {page} から {len(articles)} 件取得")
        collected_articles.extend(articles)
        if len(collected_articles) >= sample_size:
            break

    if len(collected_articles) == 0:
        print("記事が見つかりませんでした。期間やクエリを確認してください。")
        sys.exit(1)

    if len(collected_articles) > sample_size:
        collected_articles = random.sample(collected_articles, sample_size)

    return collected_articles


def count_reactions(articles: list[QiitaArticle]) -> ReactionCounts:
    """リアクションの集計を行う"""
    counts = {"likes": {}, "stocks": {}, "reactions": {}}

    for article in articles:
        like_count = article.likes_count
        stock_count = article.stocks_count
        reaction_count = like_count + stock_count

        # 各カウントの頻度を集計
        counts["likes"][like_count] = counts["likes"].get(like_count, 0) + 1
        counts["stocks"][stock_count] = counts["stocks"].get(stock_count, 0) + 1
        counts["reactions"][reaction_count] = (
            counts["reactions"].get(reaction_count, 0) + 1
        )

    return ReactionCounts(**counts)


def run_count_reactions(settings: Settings | None = None, **kwargs) -> str:
    # 設定の読み込み
    if settings is None:
        settings = Settings(**kwargs)
    elif kwargs:
        # 既存の設定をkwargsで上書き
        settings = Settings(**{**settings.model_dump(), **kwargs})

    """リアクション数を集計し、生成されたCSVファイルのパスを返す"""
    if not settings.qiita_token:
        print("エラー: 環境変数 QIITA_TOKEN が設定されていません")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {settings.qiita_token}"}

    query = create_query(settings.start_date, settings.end_date, settings.username)
    print("Query:", query)

    # 実際に記事が存在する最後のページを見つける
    last_valid_page = find_valid_last_page(query, headers)
    if last_valid_page == 0:
        print("指定された期間内に記事が見つかりませんでした。")
        sys.exit(1)

    per_page = 100
    total_possible = last_valid_page * per_page

    if settings.sample_size >= total_possible:
        pages_to_fetch = list(range(1, last_valid_page + 1))
    else:
        num_pages_needed = (settings.sample_size // per_page) + 1
        if num_pages_needed > last_valid_page:
            pages_to_fetch = list(range(1, last_valid_page + 1))
        else:
            pages_to_fetch = random.sample(
                range(1, last_valid_page + 1), num_pages_needed
            )

    print("ランダムに選んだページ番号:", pages_to_fetch)

    collected_articles = collect_articles(
        settings.start_date,
        settings.end_date,
        settings.username,
        settings.sample_size,
        pages_to_fetch,
        headers,
    )
    counts = count_reactions(collected_articles)
    counts.to_csv(settings.output_file)

    print(f"{settings.output_file} を保存しました。")
    return settings.output_file


def main():
    settings = Settings()  # type: ignore
    run_count_reactions(settings)


if __name__ == "__main__":
    main()
