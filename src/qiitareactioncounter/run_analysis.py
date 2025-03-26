import json
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from qiitareactioncounter.analyze_reactions import analyze_reactions
from qiitareactioncounter.count_reactions import run_count_reactions
from qiitareactioncounter.schemas import ReactionStats


class Settings(BaseSettings):
    qiita_token: str = Field(..., description="Qiitaのアクセストークン")
    start_date: str = Field(
        default="1900-01-01", description="開始日（YYYY-MM-DD形式）"
    )
    end_date: str = Field(default="2099-12-31", description="終了日（YYYY-MM-DD形式）")
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
    """集計結果を分析する"""
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
        settings: 設定
    """
    # 出力ディレクトリの作成
    output_path = Path(settings.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 全ユーザーの集計と分析
    print("全ユーザーのリアクション数を集計します...")
    all_users_csv = output_path / "all_users_reactions.csv"
    run_count_reactions(
        start_date=settings.start_date,
        end_date=settings.end_date,
        qiita_token=settings.qiita_token,
        userid=None,
        sample_size=settings.sample_size,
        output_file=str(all_users_csv),
    )
    print(f"全ユーザーの集計結果を保存しました: {all_users_csv}")

    print("\n全ユーザーの集計結果を分析します...")
    all_users_analysis = output_path / "all_users_analysis_result.json"
    run_analyze_reactions(str(all_users_csv), str(all_users_analysis))

    # 特定ユーザーの集計と分析（useridが指定されている場合）
    if settings.userid:
        print(f"\n{settings.userid}のリアクション数を集計します...")
        user_csv = output_path / f"{settings.userid}_reactions.csv"
        run_count_reactions(
            start_date=settings.start_date,
            end_date=settings.end_date,
            qiita_token=settings.qiita_token,
            userid=settings.userid,
            sample_size=settings.sample_size,
            output_file=str(user_csv),
        )
        print(f"{settings.userid}の集計結果を保存しました: {user_csv}")

        print(f"\n{settings.userid}の集計結果を分析します...")
        user_analysis = output_path / f"{settings.userid}_analysis_result.json"
        run_analyze_reactions(str(user_csv), str(user_analysis))


def main():
    # 設定の読み込み
    settings = Settings()  # type: ignore

    # 分析の実行
    run_analysis(settings)


if __name__ == "__main__":
    main()
