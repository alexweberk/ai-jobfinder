# AI Job Finder

Enter your resume and a URL for a job listing page, and get the best matching job for you from that job list.

The repo uses [FireCrawl](https://firecrawl.dev/) to scrape job listings, and [OpenAI](https://openai.com/) to generate job recommendations.
You will need to sign up and get API keys for both services.

## How to use

Find a company's job listing page, and get your resume ready.

1. Clone the repository
   ```bash
   git clone https://github.com/alexweberk/ai-jobfinder.git
   cd ai-jobfinder
   ```
2. Install the dependencies

   If using `uv`:

   ```bash
   uv sync
   ```

3. Setup your environment variables in `.env`

   ```bash
   cp .env.example .env
   ```

   Add the following:

   - `OPENAI_API_KEY`: Your OpenAI API key
   - `FIRECRAWL_API_KEY`: Your FireCrawl API key

4. Save your resume in `./resume.txt`
5. Run the CLI app

   If using `uv`:

   ```bash
   uv run python main.py --jobs-url https://www.anthropic.com/jobs -n 5 -m 100
   ```

   You can get the available options by running:

   ```bash
   uv run python main.py --help
   ```

   Some of the main options available:

   | Option                  | Short | Description                              |
   | ----------------------- | ----- | ---------------------------------------- |
   | `--jobs-url`            | `-u`  | URL of the jobs page to scrape           |
   | `--resume-path`         | `-r`  | Path to your resume file                 |
   | `--max-jobs`            | `-m`  | Maximum number of jobs to scrape         |
   | `--num-recommendations` | `-n`  | Number of job recommendations to return  |
   | `--output-dir`          | `-o`  | Directory to save the results            |
   | `--rate-limit`          | `-l`  | Rate limit for API requests per minute   |
   | `--window-size`         | `-w`  | Time window in seconds for rate limiting |

## 使い方 (日本語)

FireCrawl を使って求人ページをスクレイピングし、OpenAI を使って求人を推薦してもらいます。
コード実行には、[FireCrawl](https://firecrawl.dev/) と [OpenAI](https://openai.com/) の API キーが必要です。

まずは興味のある会社の求人ページを見つけて、レジュメを準備しましょう。

1. リポジトリをクローン

   ```bash
   git clone https://github.com/alexweberk/ai-jobfinder.git
   cd ai-jobfinder
   ```

2. 依存関係をインストール

   If using `uv`:

   ```bash
   uv sync
   ```

3. 環境変数をセットアップ

   `.env.example` をコピーして `.env` を作成し、適切な値をセットしてください。

4. レジュメを `./resume.txt` に保存
5. スクリプトを実行

   `uv` を使用している場合:

   ```bash
   uv run python main.py --jobs-url https://www.anthropic.com/jobs -n 5 -m 100
   ```

   利用可能なオプションを取得するには、以下のコマンドを実行します:

   ```bash
   uv run python main.py --help
   ```

   選択可能なオプションは以下の通りです:

   | オプション              | 短縮形 | 説明                                |
   | ----------------------- | ------ | ----------------------------------- |
   | `--jobs-url`            | `-u`   | 求人一覧の URL                      |
   | `--resume-path`         | `-r`   | レジュメのパス                      |
   | `--max-jobs`            | `-m`   | スクレイピングする求人の最大数      |
   | `--num-recommendations` | `-n`   | 返す求人の数                        |
   | `--output-dir`          | `-o`   | 結果を保存するディレクトリ          |
   | `--rate-limit`          | `-l`   | 1 分間に API リクエストのレート制限 |
   | `--window-size`         | `-w`   | レート制限の時間ウィンドウ          |
