# AI SEO Optimizer — Phase 1 収集モジュール

競合ブログ記事および自社ブログ記事を継続的に収集し、変更検知してSQLiteに保存するクローラーです。

## 対応サイト

| サイト | 取得戦略 | Playwright |
|--------|----------|-----------|
| grooveinc.jp（自社） | pagination | 不要 |
| bxo.co.jp | sitemap | 不要 |
| itsumo365.co.jp | sitemap | 不要 |
| wac-works-ec.jp | sitemap | **必要** |
| pureflat.co.jp | sitemap | 不要 |
| cyber-records.co.jp | sitemap | 不要 |
| force-r.co.jp | pagination | 不要 |
| sobani.co.jp | sitemap | 不要 |
| picaro.co.jp | sitemap | 不要 |
| ubunbase.ubun.jp | sitemap | 不要 |
| finner.co.jp | sitemap | 不要 |
| meetsc.co.jp | single_page | 不要 |
| dentsudigital.co.jp | sitemap | 不要 |
| hakuhodody-one.co.jp | sitemap | 不要 |
| oneder.hakuhodody-one.co.jp | sitemap | 不要 |

## セットアップ

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.template .env
```

## 実行

```bash
# 全サイト（競合 + 自社）
python scripts/run_crawler.py --target both

# 競合サイトのみ
python scripts/run_crawler.py --target competitor

# 自社サイトのみ
python scripts/run_crawler.py --target own
```

## テスト

```bash
pytest tests/ -v
```

## ディレクトリ構成

```
ai-seo-optimizer/
├── crawler/
│   ├── fetchers/
│   │   ├── sitemap_fetcher.py      # サイトマップから記事URL取得
│   │   ├── pagination_fetcher.py   # ページネーションを辿って記事URL取得
│   │   └── single_page_fetcher.py  # 全記事が1ページにある場合の取得
│   ├── html_fetcher.py             # HTML取得（Playwright fallback対応）
│   ├── content_extractor.py        # 本文・タイトル・見出し・日付の抽出
│   ├── hash_detector.py            # 変更検知（SHA-256ハッシュ）
│   └── orchestrator.py             # 全体フロー調整
├── database/
│   ├── connection.py               # SQLite接続管理
│   ├── repository.py               # CRUD操作
│   └── schema.sql                  # テーブル定義
├── config/
│   ├── competitors.yaml            # 競合サイト設定
│   └── own_sites.yaml              # 自社サイト設定
├── scripts/
│   └── run_crawler.py              # CLIエントリーポイント
└── tests/                          # pytestテスト群
```
