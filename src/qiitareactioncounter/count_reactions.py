"""Qiitaの記事からリアクション数を集計するモジュール

このモジュールは、Qiitaの記事からリアクション数（いいね数、ストック数）を集計する機能を提供します。
主な機能は以下の通りです：

- Qiita APIを使用した記事の取得
- いいね数、ストック数、総リアクション数の集計
- 集計結果のCSVファイル出力
"""

#!/usr/bin/env python3
import random
import sys
from datetime import datetime

import requests
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from qiitareactioncounter.schemas import QiitaArticle, ReactionCounts

API_URL = "https://qiita.com/api/v2/items"


class Settings(BaseSettings):
    """Qiitaのリアクション数集計の設定を管理するクラス

    Attributes:
        qiita_token (str): Qiitaのアクセストークン
        start_date (str): 集計開始日（YYYY-MM-DD形式）
        end_date (str): 集計終了日（YYYY-MM-DD形式）
        userid (str | None): 集計対象のユーザーID（オプション）
        sample_size (int): 集計する記事のサンプル数
        output_file (str): 出力ファイル名
    """

    qiita_token: str = Field(..., description="Qiitaのアクセストークン")
    start_date: str = Field(
        default="1900-01-01", description="開始日（YYYY-MM-DD形式）"
    )
    end_date: str = Field(default="2099-12-31", description="終了日（YYYY-MM-DD形式）")
    userid: str | None = Field(default=None, description="ユーザーID（オプション）")
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
        cli_ignore_unknown_args=True,
        extra="ignore",
    )


def get_articles(
    query: str, page: int, per_page: int, headers: dict[str, str]
) -> list[QiitaArticle]:
    """Qiita APIから記事を取得する

    Args:
        query (str): 検索クエリ
        page (int): 取得するページ番号
        per_page (int): 1ページあたりの記事数
        headers (dict[str, str]): APIリクエストヘッダー

    Returns:
        list[QiitaArticle]: 取得した記事のリスト

    Note:
        APIのレスポンスステータスが200以外の場合は空のリストを返します。
    """
    params = {"page": page, "per_page": per_page, "query": query}
    r: requests.Response = requests.get(API_URL, params=params, headers=headers)
    if r.status_code != 200:
        print(f"Error fetching page {page}: {r.text}")
        return []
    return [QiitaArticle.model_validate(article) for article in r.json()]


def find_valid_last_page(query: str, headers: dict[str, str]) -> int:
    """二分探索で実際に記事が存在する最後のページを見つける

    Args:
        query (str): 検索クエリ
        headers (dict[str, str]): APIリクエストヘッダー

    Returns:
        int: 最後の有効なページ番号。記事が見つからない場合は0を返します。

    Note:
        Qiita APIの制限により、最大100ページまで検索します。
    """
    left = 1
    right = 100  # Qiita APIの制限（100ページ）
    last_valid_page = 1
    per_page = 100

    # まず1ページ目で記事が取得できるか確認
    articles = get_articles(query, 1, per_page, headers)
    if not articles:
        return 0

    while left <= right:
        mid = (left + right) // 2
        articles = get_articles(query, mid, per_page, headers)

        if articles:  # 記事が存在する場合
            last_valid_page = mid
            left = mid + 1
        else:  # 記事が存在しない場合
            right = mid - 1

    return last_valid_page


def create_query(start_date: str, end_date: str, userid: str | None = None) -> str:
    """Qiita APIの検索クエリを生成する

    Args:
        start_date (str): 開始日（YYYY-MM-DD形式）
        end_date (str): 終了日（YYYY-MM-DD形式）
        userid (str | None): ユーザーID（オプション）

    Returns:
        str: 生成された検索クエリ
    """
    query = f"created:>={start_date} created:<={end_date}"
    if userid:
        query = f"{query} user:{userid}"
    return query


def collect_articles(
    start_date: str,
    end_date: str,
    userid: str | None,
    sample_size: int,
    pages_to_fetch: list[int],
    headers: dict[str, str],
) -> list[QiitaArticle]:
    """指定されたページから記事を収集する

    Args:
        start_date (str): 開始日（YYYY-MM-DD形式）
        end_date (str): 終了日（YYYY-MM-DD形式）
        userid (str | None): ユーザーID（オプション）
        sample_size (int): 必要な記事数
        pages_to_fetch (list[int]): 取得するページ番号のリスト
        headers (dict[str, str]): APIリクエストヘッダー

    Returns:
        list[QiitaArticle]: 収集した記事のリスト

    Note:
        - 指定されたサンプルサイズに達した場合は、それ以降のページの取得を停止します
        - 収集した記事数がサンプルサイズを超える場合は、ランダムにサンプリングします
        - 記事が見つからない場合は、エラーメッセージを表示して終了します
    """
    collected_articles = []
    per_page = 100
    query = create_query(start_date, end_date, userid)

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
    """リアクションの集計を行う

    Args:
        articles (list[QiitaArticle]): 集計対象の記事リスト

    Returns:
        ReactionCounts: 集計結果

    Note:
        以下の3つの集計を行います：
        - いいね数の頻度分布
        - ストック数の頻度分布
        - 総リアクション数（いいね数 + ストック数）の頻度分布
    """
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


def get_authenticated_user(headers: dict[str, str]) -> str:
    """認証されているユーザーのIDを取得する

    Args:
        headers (dict[str, str]): APIリクエストヘッダー

    Returns:
        str: 認証ユーザーのID

    Raises:
        Exception: 認証に失敗した場合
    """
    r: requests.Response = requests.get(
        "https://qiita.com/api/v2/authenticated_user", headers=headers
    )
    if r.status_code != 200:
        raise Exception(f"認証に失敗しました: {r.text}")
    return r.json()["id"]


def get_user_oldest_article_date(headers: dict[str, str], userid: str) -> str:
    """ユーザーの最も古い投稿の日付を取得する

    Args:
        headers (dict[str, str]): APIリクエストヘッダー
        userid (str): ユーザーID

    Returns:
        str: 最も古い投稿の日付（YYYY-MM-DD形式）

    Raises:
        Exception: ユーザーの記事を取得できない場合
    """
    # まず1ページ目を取得して総記事数を確認
    params = {"page": 1, "per_page": 100}
    r = requests.get(
        f"https://qiita.com/api/v2/users/{userid}/items", params=params, headers=headers
    )
    if r.status_code != 200:
        raise Exception(f"ユーザーの記事を取得できませんでした: {r.text}")

    # 総記事数から最後のページを計算
    total_count = int(r.headers.get("total-count", 0))
    if total_count == 0:
        raise Exception("ユーザーの記事が見つかりませんでした")

    last_page = (total_count - 1) // 100 + 1

    # 最後のページから記事を取得（作成日時でソート）
    params = {"page": last_page, "per_page": 100, "sort": "created_at"}
    r = requests.get(
        f"https://qiita.com/api/v2/users/{userid}/items", params=params, headers=headers
    )
    if r.status_code != 200:
        raise Exception(f"ユーザーの記事を取得できませんでした: {r.text}")

    articles = r.json()
    if not articles:
        raise Exception("ユーザーの記事が見つかりませんでした")

    # 最も古い投稿の日付を取得
    oldest_date = datetime.fromisoformat(
        articles[-1]["created_at"].replace("Z", "+00:00")
    )

    return oldest_date.strftime("%Y-%m-%d")


def run_count_reactions(settings: Settings | None = None, **kwargs) -> str:
    """リアクション数を集計し、CSVファイルに出力する

    Args:
        settings (Settings | None): 集計設定。Noneの場合はkwargsから設定を生成
        **kwargs: 設定の上書き用のキーワード引数

    Returns:
        str: 生成されたCSVファイルのパス

    Note:
        以下の処理を実行します：
        1. 設定の読み込みと検証
        2. 記事の取得（ランダムサンプリング）
        3. リアクション数の集計
        4. 結果のCSVファイル出力
    """
    # 設定の読み込み
    if settings is None:
        settings = Settings(**kwargs)
    elif kwargs:
        # 既存の設定をkwargsで上書き
        settings = Settings(**{**settings.model_dump(), **kwargs})
    if "userid" in kwargs:
        settings.userid = kwargs["userid"]

    if not settings.qiita_token:
        print("エラー: 環境変数 QIITA_TOKEN が設定されていません")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {settings.qiita_token}"}

    query = create_query(settings.start_date, settings.end_date, settings.userid)
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
        settings.userid,
        settings.sample_size,
        pages_to_fetch,
        headers,
    )
    counts = count_reactions(collected_articles)
    counts.to_csv(settings.output_file)

    print(f"{settings.output_file} を保存しました。")
    return settings.output_file


def main() -> None:
    """メイン関数

    コマンドライン引数から設定を読み込み、リアクション数の集計を実行します。
    環境変数や.envファイルから設定を読み込むこともできます。
    """
    settings = Settings()  # type: ignore
    run_count_reactions(settings)


if __name__ == "__main__":
    main()
