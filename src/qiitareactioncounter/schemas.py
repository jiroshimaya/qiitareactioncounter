from datetime import datetime
from typing import Dict

from pydantic import BaseModel, HttpUrl
from pydantic_settings import SettingsConfigDict


class QiitaArticle(BaseModel):
    id: str
    likes_count: int
    stocks_count: int
    title: str
    url: HttpUrl
    created_at: datetime
    updated_at: datetime


class ReactionCounts(BaseModel):
    """リアクションの集計結果を表す型
    各フィールドは以下の形式の辞書:
    {
        リアクション数: そのリアクション数を持つ記事の数
    }
    """

    likes: Dict[int, int]  # いいね数 -> そのいいね数を持つ記事の数
    stocks: Dict[int, int]  # ストック数 -> そのストック数を持つ記事の数
    reactions: Dict[int, int]  # 総リアクション数 -> その総リアクション数を持つ記事の数

    def to_csv(self, output_file: str) -> None:
        """集計結果をCSVファイルに保存する

        Args:
            output_file: 出力先のCSVファイルパス
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
            input_file: 入力元のCSVファイルパス

        Returns:
            ReactionCounts: 読み込んだ集計結果
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
    total_articles: int
    median: float
    mean: float
    top_10_threshold: float
    top_10_mean: float
    top_10_median: float
    top_10_count: int
    n_more_or_ratio: dict[int, float]

    model_config = SettingsConfigDict(arbitrary_types_allowed=True)
