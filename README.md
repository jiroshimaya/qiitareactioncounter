# Qiita Reaction Counter

Qiitaの記事に対するリアクション数を集計・分析するツールです。

## 機能

- Qiitaの記事に対するリアクション数の取得
- リアクション数の集計と分析
- CSV形式での結果出力
- 指定した期間における指定したユーザとQiita全体のリアクション数の取得、比較、分析

## 必要条件

- Python 3.11以上

## 推奨条件

- uv（Pythonパッケージマネージャー）

## インストール

1. リポジトリをクローン
```bash
git clone https://github.com/yourusername/qiitareactioncounter.git
cd qiitareactioncounter
```

## 使用方法

1. プロジェクトのルートディレクトリにある`.env_sample`ファイルをコピーして`.env`ファイルを作成し、Qiitaのアクセストークンを設定します：
   ```bash
   cp .env_sample .env
   ```
   `.env`ファイルを開き、`QIITA_TOKEN`にあなたのQiitaアクセストークンを設定してください。
   アクセストークンはQiitaの[設定ページ](https://qiita.com/settings/applications)から取得できます。

2. プロジェクトのルートディレクトリで以下のコマンドを実行します：
   ```bash
   uv run src/qiitareactioncounter/run_analysis.py
   ```

3. プログラムは指定した期間における指定したユーザとQiita全体のリアクション数を取得し、比較、分析を行います。結果は`results`ディレクトリにCSVおよびJSON形式で出力されます。

### 出力例

```
% uv run src/qiitareactioncounter/run_analysis.py --start_date 2024-10-01 --end_date 2025-03-20 --sample_size 100 --output_dir results --userid Qiita          
全ユーザーのリアクション数を集計します...
Query: created:>=2024-10-01 created:<=2025-03-20
ランダムに選んだページ番号: [98, 49]
ページ 98 から 100 件取得
results/all_users_reactions.csv を保存しました。
全ユーザーの集計結果を保存しました: results/all_users_reactions.csv

全ユーザーの集計結果を分析します...

=== results/all_users_reactions.csvの統計 ===
全記事数: 100
中央値: 1.00
平均値: 9.98
上位10%の閾値: 6.00
上位10%の平均: 83.09
上位10%の中央値: 13.00
上位10%の記事数: 11

1以上リアクションがついた記事の割合: 51.00%

2以上リアクションがついた記事の割合: 34.00%

3以上リアクションがついた記事の割合: 22.00%

Qiitaのリアクション数を集計します...
Query: created:>=2024-10-01 created:<=2025-03-20 user:Qiita
ランダムに選んだページ番号: [1]
ページ 1 から 7 件取得
results/Qiita_reactions.csv を保存しました。
Qiitaの集計結果を保存しました: results/Qiita_reactions.csv

Qiitaの集計結果を分析します...

=== results/Qiita_reactions.csvの統計 ===
全記事数: 7
中央値: 19.00
平均値: 36.86
上位10%の閾値: 81.00
上位10%の平均: 150.00
上位10%の中央値: 150.00
上位10%の記事数: 1

1以上リアクションがついた記事の割合: 100.00%

2以上リアクションがついた記事の割合: 100.00%

3以上リアクションがついた記事の割合: 100.00%
```

以下のファイルも合わせて出力されます。

- `results/all_users_reactions.csv`: 全ユーザーのリアクション数の集計結果
- `results/all_users_analysis_result.json`: 全ユーザーのリアクション数の分析結果
- `results/{userid}_reactions.csv`: 指定したユーザーのリアクション数の集計結果
- `results/{userid}_analysis_result.json`: 指定したユーザーのリアクション数の分析結果

出力されたJSONファイルには、以下のような統計情報が含まれます：
- 全記事数
- 中央値
- 平均値
- 上位10%の閾値、平均、中央値
- 各リアクション数以上の記事の割合


## 開発

### テストの実行

```bash
uv run pytest
```


### コード品質チェック

```bash
uvx ruff check .
uvx ruff format
```

## ライセンス

このプロジェクトはApache 2.0ライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。
