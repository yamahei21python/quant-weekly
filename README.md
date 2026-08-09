# 週次クオンツ定点観測

Zenn記事「Redditのヘッジファンド、クオンツトピックをGrokタスクで毎週自動収集する」（AlpacaTech 北山）を参考に、
**Grok節約方針**でReddit/arXivは自前スクリプト、XのみGrokタスクで収集するパイプライン。

## パイプライン

| ソース | ツール | 出力 | コスト |
|--------|--------|------|--------|
| Reddit (r/quant, r/algotrading) | `fetch_reddit.py` (Xpoz SDK) | `reddit-YYYY-MM-DD.md` | 無料 |
| arXiv (q-fin.TR/PM/RM) | `fetch_arxiv.py` (arXiv API) | `arxiv-YYYY-MM-DD.md` | 無料 |
| X (Twitter) | Grokタスク (grok.com) | `grok-x-YYYY-MM-DD.md` | Grok消費 |
| 統合digest | `build_digest.py` | `YYYY-MM-DD.md` | 無料 |

## 使い方

```bash
cd quant-weekly
source .venv/bin/activate   # python-dotenv, xpoz が必要 (fetch_reddit.py のみ)

# 1. Reddit収集
python fetch_reddit.py

# 2. arXiv収集 (stdlibのみ・venv不要)
python fetch_arxiv.py

# 3. X収集 (Grokタスク出力を grok-x-YYYY-MM-DD.md として配置)

# 4. 統合digest生成
python build_digest.py            # 引数省略時は今日
python build_digest.py 2026-08-09 # 日付指定
```

## 出力形式

- `reddit-YYYY-MM-DD.md`: 投稿リスト (score降順・キャリア系キーワード除外済)
- `arxiv-YYYY-MM-DD.md`: 論文リスト (要約300字・カテゴリ絞り込み済)
- `grok-x-YYYY-MM-DD.md`: X投稿リスト (Grokタスクが生成)
- `YYYY-MM-DD.md`: 統合digest (素材集約版・深掘りなし)

> 深掘り分析は別フェーズ (モデル任せ)。素材収集と分析を分離している。

## X収集 (Grokタスク)

- プロンプト: `grok-x-prompt.md` を grok.com の Tasks 作成画面へコピペ
- スケジュール: 毎週日曜想定
- ルール: 幅広収集・リストのみ・URL必須・深掘り禁止・「既出」「未確認」明記

## 注意

- 儲ける系シグナルは明示除外 (記事の肝)
- r/quant はキャリア話が多く密度低 → `fetch_reddit.py` がフィルタ
- Xpoz は r/quant のインデックスが古い (8/3 以降欠損あり) → 件数が少なくても正常
