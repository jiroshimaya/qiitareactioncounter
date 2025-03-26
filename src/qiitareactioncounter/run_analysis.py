"""Qiitaのリアクション数を集計・分析するモジュール

このモジュールは、Qiitaの記事に対するリアクション数を集計し、分析を行う機能を提供します。
主な機能は以下の通りです：

- 全ユーザーのリアクション数集計
- 特定ユーザーのリアクション数集計
- リアクション数の統計分析（平均値、中央値、上位10%の分析など）
- 分析結果のJSONファイル出力
"""

import json
from datetime import datetime
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from qiitareactioncounter.analyze_reactions import analyze_reactions
from qiitareactioncounter.count_reactions import (
    get_authenticated_user,
    get_user_oldest_article_date,
    run_count_reactions,
)
from qiitareactioncounter.schemas import ReactionStats


class Settings(BaseSettings):
    """Qiitaのリアクション数集計・分析の設定を管理するクラス

    Attributes:
        qiita_token (str): Qiitaのアクセストークン
        start_date (str | None): 集計開始日（YYYY-MM-DD形式）。指定しない場合はユーザーの最も古い投稿の日付
        end_date (str | None): 集計終了日（YYYY-MM-DD形式）。指定しない場合は現在の日付
        userid (str | None): 集計対象のユーザーID（オプション）
        sample_size (int): 集計する記事のサンプル数
        output_dir (str): 出力ディレクトリのパス
    """

    qiita_token: str = Field(..., description="Qiitaのアクセストークン")
    start_date: str | None = Field(
        default=None,
        description="開始日（YYYY-MM-DD形式）。指定しない場合はユーザーの最も古い投稿の日付",
    )
    end_date: str | None = Field(
        default=None, description="終了日（YYYY-MM-DD形式）。指定しない場合は現在の日付"
    )
    userid: str | None = Field(default=None, description="ユーザーID（オプション）")
    sample_size: int = Field(
        default=1000, description="サンプル件数（デフォルト1000件）"
    )
    output_dir: str = Field(
        default="results", description="出力ディレクトリ（デフォルトresults）"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        cli_parse_args=True,
        extra="ignore",
        cli_ignore_unknown_args=True,
    )


def run_analyze_reactions(csv_path: str, output_path: str) -> ReactionStats:
    """リアクション数の集計結果を分析し、統計情報を出力する

    Args:
        csv_path (str): 集計結果のCSVファイルのパス
        output_path (str): 分析結果を保存するJSONファイルのパス

    Returns:
        ReactionStats: 分析結果の統計情報

    Note:
        分析結果は以下の情報を含みます：
        - 全記事数
        - リアクション数の中央値
        - リアクション数の平均値
        - 上位10%の閾値、平均値、中央値
        - 各リアクション数以上の記事の割合
    """
    stats = analyze_reactions(csv_path, [1, 2, 3])

    # 分析結果をJSONファイルに保存
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stats.model_dump(), f, ensure_ascii=False, indent=2)

    # コンソールにも出力
    print(f"\n=== {csv_path}の統計 ===")
    print(f"全記事数: {stats.total_articles}")
    print(f"中央値: {stats.median:.2f}")
    print(f"平均値: {stats.mean:.2f}")
    print(f"上位10%の閾値: {stats.top_10_threshold:.2f}")
    print(f"上位10%の平均: {stats.top_10_mean:.2f}")
    print(f"上位10%の中央値: {stats.top_10_median:.2f}")
    print(f"上位10%の記事数: {stats.top_10_count}")
    for n, ratio in stats.n_more_or_ratio.items():
        print(f"\n{n}以上リアクションがついた記事の割合: {ratio:.2f}%")

    return stats


def run_analysis(settings: Settings) -> None:
    """リアクション数の集計と分析を実行する

    Args:
        settings (Settings): 集計・分析の設定

    Note:
        この関数は以下の処理を実行します：
        1. 全ユーザーのリアクション数集計と分析
        2. 特定ユーザー（指定された場合）または認証ユーザーのリアクション数集計と分析
        3. 結果をCSVファイルとJSONファイルに保存
    """
    # 出力ディレクトリの作成
    output_path = Path(settings.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 特定ユーザーの集計と分析（useridが指定されている場合、またはトークンがある場合は認証ユーザー）
    userid = settings.userid
    if userid is None and settings.qiita_token:
        # トークンがあり、useridが指定されていない場合は認証ユーザーの情報を取得
        headers = {"Authorization": f"Bearer {settings.qiita_token}"}
        userid = get_authenticated_user(headers)
        print(f"\n認証ユーザーのIDを取得しました: {userid}")

    # 日付範囲が指定されていない場合、ユーザーの投稿履歴から取得
    start_date = settings.start_date
    if userid and start_date is None:
        headers = {"Authorization": f"Bearer {settings.qiita_token}"}
        start_date = get_user_oldest_article_date(headers, userid)
        print(f"\n開始日をユーザーの最も古い投稿の日付に設定しました: {start_date}")

    end_date = settings.end_date
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    # 全ユーザーの集計と分析
    print("全ユーザーのリアクション数を集計します...")
    all_users_csv = output_path / "all_users_reactions.csv"
    run_count_reactions(
        start_date=start_date,
        end_date=end_date,
        qiita_token=settings.qiita_token,
        userid=None,
        sample_size=settings.sample_size,
        output_file=str(all_users_csv),
    )
    print(f"全ユーザーの集計結果を保存しました: {all_users_csv}")

    print("\n全ユーザーの集計結果を分析します...")
    all_users_analysis = output_path / "all_users_analysis_result.json"
    run_analyze_reactions(str(all_users_csv), str(all_users_analysis))

    if userid:
        print(f"\n{userid}のリアクション数を集計します...")
        user_csv = output_path / f"{userid}_reactions.csv"
        run_count_reactions(
            start_date=start_date or "1900-01-01",
            end_date=end_date or "2099-12-31",
            qiita_token=settings.qiita_token,
            userid=userid,
            sample_size=settings.sample_size,
            output_file=str(user_csv),
        )
        print(f"{userid}の集計結果を保存しました: {user_csv}")

        print(f"\n{userid}の集計結果を分析します...")
        user_analysis = output_path / f"{userid}_analysis_result.json"
        run_analyze_reactions(str(user_csv), str(user_analysis))


def main() -> None:
    """メイン関数

    コマンドライン引数から設定を読み込み、リアクション数の集計と分析を実行します。
    環境変数や.envファイルから設定を読み込むこともできます。
    """
    # 設定の読み込み
    settings = Settings()  # type: ignore

    # 分析の実行
    run_analysis(settings)


if __name__ == "__main__":
    main()
