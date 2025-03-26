"""Qiitaのリアクション数を分析するモジュール

このモジュールは、Qiitaのリアクション数の集計結果を分析し、統計情報を生成する機能を提供します。
主な機能は以下の通りです：

- リアクション数の基本統計量の計算（平均値、中央値など）
- 上位10%の記事の分析
- n以上のリアクションがついた記事の割合の計算
"""

from typing import List

import numpy as np
import pandas as pd
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from qiitareactioncounter.schemas import ReactionStats


class Settings(BaseSettings):
    """リアクション数分析の設定を管理するクラス

    Attributes:
        filepath (str): 分析対象のCSVファイルのパス
        n_values (List[int]): n以上のリアクションがついた記事の割合を計算するn値のリスト
    """

    filepath: str = Field(..., description="分析対象のCSVファイルのパス")
    n_values: List[int] = Field(
        default=[1, 2, 3],
        description="n以上のリアクションがついた記事の割合を計算するn値のリスト",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        cli_parse_args=True,
        extra="ignore",
        cli_ignore_unknown_args=True,
    )


def analyze_reactions(file_path: str, n_values: List[int]) -> ReactionStats:
    """リアクション数の集計結果を分析し、統計情報を生成する

    Args:
        file_path (str): 集計結果のCSVファイルのパス
        n_values (List[int]): n以上のリアクションがついた記事の割合を計算するn値のリスト

    Returns:
        ReactionStats: 分析結果の統計情報

    Note:
        以下の統計情報を計算します：
        - 全記事数
        - リアクション数の中央値
        - リアクション数の平均値
        - 上位10%の閾値、平均値、中央値
        - 各n値について、n以上のリアクションがついた記事の割合
    """
    df = pd.read_csv(file_path)

    # リアクション数の分布を計算
    reactions = []
    for _, row in df.iterrows():
        reactions.extend([row["value"]] * row["reactions"])
    reactions = np.array(reactions)

    # 基本統計量
    total_articles = len(reactions)
    median = float(np.median(reactions))
    mean = float(np.mean(reactions))

    # 上位10%の閾値を計算
    top_10_threshold = float(np.percentile(reactions, 90))
    top_10_articles = reactions[reactions >= top_10_threshold]
    top_10_mean = float(np.mean(top_10_articles))
    top_10_median = float(np.median(top_10_articles))

    # n以上の記事の割合を計算
    n_more_or_ratio = {}
    for n in n_values:
        articles_with_n_or_more = np.sum(reactions > (n - 1))
        ratio = float(articles_with_n_or_more / total_articles * 100)
        n_more_or_ratio[n] = ratio

    return ReactionStats(
        total_articles=total_articles,
        median=median,
        mean=mean,
        top_10_threshold=top_10_threshold,
        top_10_mean=top_10_mean,
        top_10_median=top_10_median,
        top_10_count=len(top_10_articles),
        n_more_or_ratio=n_more_or_ratio,
    )


def main() -> None:
    """メイン関数

    コマンドライン引数から設定を読み込み、リアクション数の分析を実行します。
    環境変数や.envファイルから設定を読み込むこともできます。

    Note:
        分析結果は以下の情報を出力します：
        - 全記事数
        - リアクション数の中央値
        - リアクション数の平均値
        - 上位10%の閾値、平均値、中央値
        - 各n値について、n以上のリアクションがついた記事の割合
    """
    # 設定の読み込み
    settings = Settings()  # type: ignore

    # データを分析
    stats = analyze_reactions(settings.filepath, settings.n_values)

    print(f"=== {settings.filepath}の統計 ===")
    print(f"全記事数: {stats.total_articles}")
    print(f"中央値: {stats.median:.2f}")
    print(f"平均値: {stats.mean:.2f}")
    print(f"上位10%の閾値: {stats.top_10_threshold:.2f}")
    print(f"上位10%の平均: {stats.top_10_mean:.2f}")
    print(f"上位10%の中央値: {stats.top_10_median:.2f}")
    print(f"上位10%の記事数: {stats.top_10_count}")
    for n, ratio in stats.n_more_or_ratio.items():
        print(f"\n{n}以上リアクションがついた記事の割合: {ratio:.2f}%")


if __name__ == "__main__":
    main()
