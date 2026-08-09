# 週次クオンツ定点観測

Zenn記事「Redditのヘッジファンド、クオンツトピックをGrokタスクで毎週自動収集する」（AlpacaTech 北山）を参考に、
**Grok節約方針**でReddit/arXivは自前スクリプト、XのみGrokタスクで収集するパイプライン。
Reddit/arXiv は **GitHub Actions** でサーバーレス自動実行、X は **grok.com Automations** + **Zapier** で自動取り込み。PC電源不要。

## パイプライン

| ソース | ツール | 出力 | コスト |
|--------|--------|------|--------|
| Reddit (r/quant, r/algotrading) | `fetch_reddit.py` (Xpoz SDK) | `reddit-YYYY-MM-DD.md` | 無料 |
| arXiv (q-fin.TR/PM/RM) | `fetch_arxiv.py` (arXiv API) | `arxiv-YYYY-MM-DD.md` | 無料 |
| X (Twitter) | Grok Automations (grok.com) | `grok-x-YYYY-MM-DD.md` | Grok消費 |
| 統合digest | `build_digest.py` | `YYYY-MM-DD.md` | 無料 |

## 自動化アーキテクチャ

```
毎週日曜 18:00 JST (09:00 UTC)
├─ GitHub Actions (cron)          … Reddit + arXiv 収集 → digest → auto commit&push
├─ grok.com Automations (同日)    … X収集 → 結果を email で Zapier 仮想アドレスへ送信
└─ Zapier (Email by Zapier)       … メール受信 → GitHub repository_dispatch 発火
    └─ GitHub Actions (grok-x-ingest) … grok-x-YYYY-MM-DD.md 保存 → digest 再生成 → push
```

### GitHub Actions

- `weekly-collect.yml` … cron `0 9 * * 0` (日曜 18:00 JST) で Reddit/arXiv/digest を実行
- `grok-x-ingest.yml` … `repository_dispatch` イベント `grok-x-email` で起動
  - `client_payload.date` … 収集日 (省略時は今日)
  - `client_payload.content_b64` … grok-x 本文の **base64エンコード** (エスケープ問題回避)
- 手動実行: Actions タブの「Run workflow」ボタン、または `gh workflow run weekly-collect.yml`
- 手動 dispatch テスト: `gh api -X POST repos/yamahei21python/quant-weekly/dispatches -f event_type=grok-x-email -f "client_payload[date]=2026-08-09" -f "client_payload[content_b64]=$(base64 <<< '本文')"`

### Zapier 設定 (X取り込み)

1. Zapier で **Email by Zapier** を選び仮想メールアドレスを発行 (無料プラン: 100 task/月)
2. Grok 側: Automations の配信先メールをそのアドレスに設定
3. Zap: Trigger = Email (件名 `grok-x`) / Action = GitHub → **Create a Repository Dispatch Event**
   - Repo: `yamahei21python/quant-weekly` / Event type: `grok-x-email`
   - Payload: `date` (メール件名の日付 or today) + `content_b64` (メール本文の base64)
4. GitHub PAT を作成し Zapier に接続 (scope: `repo`) — Actions の `GITHUB_TOKEN` は外部から dispatch 不可のため必須

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

# 3. X収集 (Grok Automations 出力を grok-x-YYYY-MM-DD.md として配置)

# 4. 統合digest生成
python build_digest.py            # 引数省略時は今日
python build_digest.py 2026-08-09 # 日付指定
```

## 出力形式

- `reddit-YYYY-MM-DD.md`: 投稿リスト (score降順・キャリア系キーワード除外済)
- `arxiv-YYYY-MM-DD.md`: 論文リスト (要約300字・カテゴリ絞り込み済)
- `grok-x-YYYY-MM-DD.md`: X投稿リスト (Grok Automations が生成)
- `YYYY-MM-DD.md`: 統合digest (素材集約版・深掘りなし)

> 深掘り分析は別フェーズ (モデル任せ)。素材収集と分析を分離している。

## X収集 (Grok Automations)

- プロンプト: `grok-x-prompt.md` を grok.com の Automations 作成画面へコピペ
- スケジュール: 毎週日曜 18:00 JST (GH Actions cron と同時刻)
- 配信先: Zapier 仮想メールアドレス (→ 自動で repository_dispatch → digest に反映)
- ルール: 幅広収集・リストのみ・URL必須・深掘り禁止・「既出」「未確認」明記

## 注意

- 儲ける系シグナルは明示除外 (記事の肝)
- r/quant はキャリア話が多く密度低 → `fetch_reddit.py` がフィルタ
- Xpoz は r/quant のインデックスが古い (8/3 以降欠損あり) → 件数が少なくても正常
- xpoz は `mcp==1.29.0` に固定 (2.x で streamable_http_client のタプル構造が変わり接続不能)

