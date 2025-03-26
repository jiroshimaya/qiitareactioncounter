"""Qiitaのリアクション数集計・分析で使用するデータモデル

このモジュールは、Qiitaの記事データとリアクション数の集計・分析結果を表すデータモデルを提供します。
主な機能は以下の通りです：

- Qiita記事のデータモデル
- リアクション数の集計結果のデータモデル
- リアクション数の分析結果のデータモデル
- CSVファイルとの相互変換機能
"""

from datetime import datetime
from typing import Dict

from pydantic import BaseModel, HttpUrl
from pydantic_settings import SettingsConfigDict


class QiitaArticle(BaseModel):
    """Qiitaの記事を表すデータモデル

    Attributes:
        id (str): 記事のID
        likes_count (int): いいね数
        stocks_count (int): ストック数
        title (str): 記事のタイトル
        url (HttpUrl): 記事のURL
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時
    """

    id: str
    likes_count: int
    stocks_count: int
    title: str
    url: HttpUrl
    created_at: datetime
    updated_at: datetime


class ReactionCounts(BaseModel):
    """リアクションの集計結果を表すデータモデル

    各フィールドは以下の形式の辞書:
    {
        リアクション数: そのリアクション数を持つ記事の数
    }

    Attributes:
        likes (Dict[int, int]): いいね数の頻度分布
        stocks (Dict[int, int]): ストック数の頻度分布
        reactions (Dict[int, int]): 総リアクション数の頻度分布
    """

    likes: Dict[int, int]  # いいね数 -> そのいいね数を持つ記事の数
    stocks: Dict[int, int]  # ストック数 -> そのストック数を持つ記事の数
    reactions: Dict[int, int]  # 総リアクション数 -> その総リアクション数を持つ記事の数

    def to_csv(self, output_file: str) -> None:
        """集計結果をCSVファイルに保存する

        Args:
            output_file (str): 出力先のCSVファイルパス

        Note:
            CSVファイルは以下の列を含みます：
            - value: リアクション数
            - likes: そのいいね数を持つ記事の数
            - stocks: そのストック数を持つ記事の数
            - reactions: その総リアクション数を持つ記事の数
        """
        import csv

        # 全てのカウント値を取得してソート
        all_values = sorted(
            set(
                list(self.likes.keys())
                + list(self.stocks.keys())
                + list(self.reactions.keys())
            )
        )

        # 頻度の集計
        with open(output_file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["value", "likes", "stocks", "reactions"])

            for value in all_values:
                writer.writerow(
                    [
                        value,
                        self.likes.get(value, 0),
                        self.stocks.get(value, 0),
                        self.reactions.get(value, 0),
                    ]
                )

    @classmethod
    def from_csv(cls, input_file: str) -> "ReactionCounts":
        """CSVファイルから集計結果を読み込む

        Args:
            input_file (str): 入力元のCSVファイルパス

        Returns:
            ReactionCounts: 読み込んだ集計結果

        Note:
            - 0の値を持つキーは除外されます
            - CSVファイルは以下の列を含む必要があります：
              - value: リアクション数
              - likes: そのいいね数を持つ記事の数
              - stocks: そのストック数を持つ記事の数
              - reactions: その総リアクション数を持つ記事の数
        """
        import csv

        likes: Dict[int, int] = {}
        stocks: Dict[int, int] = {}
        reactions: Dict[int, int] = {}

        with open(input_file, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                value = int(row["value"])
                likes_value = int(row["likes"])
                stocks_value = int(row["stocks"])
                reactions_value = int(row["reactions"])

                # 0の値を持つキーは除外
                if likes_value > 0:
                    likes[value] = likes_value
                if stocks_value > 0:
                    stocks[value] = stocks_value
                if reactions_value > 0:
                    reactions[value] = reactions_value

        return cls(likes=likes, stocks=stocks, reactions=reactions)


class ReactionStats(BaseModel):
    """リアクション数の分析結果を表すデータモデル

    Attributes:
        total_articles (int): 分析対象の記事総数
        median (float): リアクション数の中央値
        mean (float): リアクション数の平均値
        top_10_threshold (float): 上位10%の閾値
        top_10_mean (float): 上位10%の平均値
        top_10_median (float): 上位10%の中央値
        top_10_count (int): 上位10%の記事数
        n_more_or_ratio (dict[int, float]): n以上のリアクションがついた記事の割合
    """

    total_articles: int
    median: float
    mean: float
    top_10_threshold: float
    top_10_mean: float
    top_10_median: float
    top_10_count: int
    n_more_or_ratio: dict[int, float]

    model_config = SettingsConfigDict(arbitrary_types_allowed=True)
