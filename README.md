# 週次クオンツ定点観測

Zenn記事「Redditのヘッジファンド、クオンツトピックをGrokタスクで毎週自動収集する」（AlpacaTech 北山）を参考に、
**Grok節約方針**でReddit/arXivは自前スクリプト、XのみGrokタスクで収集するパイプライン。
Reddit/arXiv は **GitHub Actions** でサーバーレス自動実行、X は **grok.com Automations** が **GitHub へ直接コミット**。PC電源不要・外部サービス不要。

## パイプライン

| ソース | ツール | 出力 | コスト |
|--------|--------|------|--------|
| Reddit (r/quant, r/algotrading) | `fetch_reddit.py` (Xpoz SDK) | `reddit-YYYY-MM-DD.md` | 無料 |
| arXiv (q-fin.TR/PM/RM) | `fetch_arxiv.py` (arXiv API) | `arxiv-YYYY-MM-DD.md` | 無料 |
| X (Twitter) | Grok Automations (grok.com + GitHubコネクタ) | `grok-x-YYYY-MM-DD.md` | Grok消費 |
| 統合digest | `build_digest.py` | `YYYY-MM-DD.md` | 無料 |

## 自動化アーキテクチャ

```
毎週日曜 18:00 JST (09:00 UTC)
├─ GitHub Actions (cron weekly-collect.yml) … Reddit + arXiv 収集 → digest → auto commit&push
└─ grok.com Automations (スケジュール)      … X収集 → GitHub に grok-x-YYYY-MM-DD.md を直接コミット
    └─ GitHub Actions (grok-x-push.yml)     … コミット検知 → digest 再生成 → auto commit&push
```

### GitHub Actions

- `weekly-collect.yml` … cron `0 9 * * 0` (日曜 18:00 JST) で Reddit/arXiv/digest を実行
- `grok-x-push.yml` … `push` イベント (`paths: grok-x-*.md`) で digest を再生成
  - コミットされた `grok-x-YYYY-MM-DD.md` の日付を抽出し `python build_digest.py YYYY-MM-DD` を実行
  - `digest コミットには [skip ci] を含める`(念のための無限ループ防止。paths 指定により digest 変更では発火しない)
- `grok-x-ingest.yml` … 旧方式 (Make/repository_dispatch)。利用停止中だが残置
- 手動実行: Actions タブの「Run workflow」ボタン、または `gh workflow run weekly-collect.yml`

### grok.com Automations 設定 (X取り込み)

1. **GitHub コネクタ接続**: grok.com/connectors → New Connector → GitHub → OAuth 承認 (scope: repo)
2. **Automation 作成**: grok.com/automations → New Automation
   - プロンプト: `grok-x-prompt.md` の「プロンプト(コピペ用)」を貼り付け
   - コネクタ: `@GitHub` をメンション (プロンプト内に指示あり)
   - スケジュール: 毎週日曜 18:00 JST
3. 保存後、「Run now」でテスト実行 → GitHub に `grok-x-YYYY-MM-DD.md` がコミットされることを確認
   - コミット → `grok-x-push.yml` 発火 → digest 自動再生成

### シークレット

- `XPOZ_API_KEY` … GitHub → Settings → Secrets and variables → Actions に設定済み

## 使い方 (ローカル)

```bash
cd quant-weekly
source .venv/bin/activate   # python-dotenv, xpoz が必要 (fetch_reddit.py のみ)

# 1. Reddit収集
python fetch_reddit.py

# 2. arXiv収集 (stdlibのみ・venv不要)
python fetch_arxiv.py

# 3. X収集 (Grok Automations が GitHub に直接コミット)

# 4. 統合digest生成
python build_digest.py            # 引数省略時は今日
python build_digest.py 2026-08-09 # 日付指定
```

## 出力形式

- `reddit-YYYY-MM-DD.md`: 投稿リスト (score降順・キャリア系キーワード除外済)
- `arxiv-YYYY-MM-DD.md`: 論文リスト (要約300字・カテゴリ絞り込み済)
- `grok-x-YYYY-MM-DD.md`: X投稿リスト (Grok Automations が生成・GitHub にコミット)
- `YYYY-MM-DD.md`: 統合digest (素材集約版・深掘りなし)

> 深掘り分析は別フェーズ (モデル任せ)。素材収集と分析を分離している。

## X収集 (Grok Automations)

- プロンプト: `grok-x-prompt.md` を grok.com の Automations 作成画面へコピペ
- スケジュール: 毎週日曜 18:00 JST (GH Actions cron と同時刻)
- 出力先: GitHub リポジトリ `yamahei21python/quant-weekly` へ `grok-x-YYYY-MM-DD.md` を直接コミット
- ルール: 幅広収集・リストのみ・URL必須・深掘り禁止・「既出」「未確認」明記

## 注意

- 儲ける系シグナルは明示除外 (記事の肝)
- r/quant はキャリア話が多く密度低 → `fetch_reddit.py` がフィルタ
- Xpoz は r/quant のインデックスが古い (8/3 以降欠損あり) → 件数が少なくても正常
- xpoz は `mcp==1.29.0` に固定 (2.x で streamable_http_client のタプル構造が変わり接続不能)
- Grok の GitHub コネクタは大規模変更でコミットが稀に失敗することが報告されている。
  小さな1ファイルのコミットは動作実績あり。もしコミットされない場合はリポジトリのファイル一覧で確認し、
  手動で `gh api -X POST .../dispatches` するか、プロンプトで再実行を依頼する。

