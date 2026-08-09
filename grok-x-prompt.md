# Grokタスク用プロンプト: 週次Xクオンツ収集(幅広版)

> 使い方: grok.com/automations の「New Automation」作成画面へ「プロンプト」欄へ下記をコピペ。
> スケジュール: 毎週日曜 18:00 (JST)。
> コネクタ: @GitHub を必ず接続 (grok.com/connectors で接続済みであること)。
> 出力先: GitHub リポジトリ `yamahei21python/quant-weekly` の `grok-x-YYYY-MM-DD.md` にコミット。
> (コミット後、GitHub Actions が自動で digest を再生成します。)

---

## プロンプト(コピペ用)

以下を実施してください。週次クオンツ定点観測のための X (Twitter) 収集です。

### 検索方法(厳守)
- **X (Twitter) の検索機能 (X検索) を使用**して、今週(直近7日)の投稿を検索してください
- X検索で不十分な場合のみ web検索 を併用し、その場合は「web検索」と明記
- ウォッチ対象アカウントの投稿は、各アカウントのタイムラインを直接確認

### 目的
今週(直近7日)のクオンツ・トレーディング・金融工学関連の注目ツイート/スレッドを
幅広くリストアップする。深掘り分析は不要。収集と一覧化のみ。

### 収集対象
1. **フォロー/ウォッチ対象アカウント** の今週の投稿(下記「ウォッチ対象アカウント」を確認)
2. **キーワード検索**: 今週の投稿を対象に以下を検索
   - quant trading / algo trading / market microstructure / execution / TCA
   - HFT / market making / alpha research / factor investing
   - risk management / portfolio optimization / LLM agent trading
   - 日本語: クオンツ / アルゴ / 執行 / マイクロストラクチャー
3. **ウォッチリストの維持(重要)**: 下記リストは固定ではない
   - 初回実行時: 全ハンドルの**実在確認** → 誤りがあれば修正して報告
   - 毎週: **新規フォロー候補を1〜3件提案** → 下表「層C」に追記してよい
   - 3週間連続で実績のないアカウントは「層C」から削除候補として報告

### 収集ルール
- アカウント種別を明記: 機関(ファンド/ベンダー)・個人トレーダー・研究者/学者・メディア
- 各項目に **投稿URLを必ず付与** (post/X/status 形式)
- 内容は **1〜2文の要約** のみ。考察・拡張・意見は書かない
- 前回収集分と同一トピックの場合は「既出」と明記
- 情報が不確かな場合は「未確認」と明記
- 「儲けるネタ」の提案・具体的シグナル・相場観の深掘りは **対象外**(除外して良い)

### 出力先(厳守)

`@GitHub` コネクタを使って、下記の内容を **GitHub リポジトリ `yamahei21python/quant-weekly` のブランチ `main` のルート直下に、`grok-x-YYYY-MM-DD.md` (YYYY-MM-DD は今日の日付) としてコミット**してください。

- ファイルパス: `grok-x-YYYY-MM-DD.md` (リポジトリルート直下)
- コミットメッセージ: `feat: grok-x collect YYYY-MM-DD`
- コミット後、リポジトリのファイル一覧でファイルが存在することを確認して報告してください。

### 出力形式(厳守)

```
# X収集 (YYYY-MM-DD)
- 収集日: YYYY-MM-DD
- 対象期間: YYYY-MM-DD 〜 YYYY-MM-DD

## [投稿者名/handle](投稿URL)
- アカウント: @handle (種別)
- 要約: 1〜2文
- 状態: 新規 / 既出 / 未確認
```

- 件数: 重要度順に **最大20件** まで
- 収集できなかった場合は「0件(理由)」と明記

---

## ウォッチ対象アカウント(3層構造・随時更新)

> 凡例: ✅=ハンドル確認済み / 🔍=要検証(初回実行時にGrokが実在確認) / ~=X未確認(削除候補)
> 出典: Databento「Quants worth following」/ r/quant「X/Twitter Account Recommendations」(2024,Xpoz収集・全検証済) / r/algotrading フォロースレ(2020) / arXiv著者追跡

### 層A: 機関・ベンダー公式(固定・更新稀)

| アカウント | 種別 | 備考 |
|-----------|------|------|
| 🔍 @JaneStreet | 機関 | MM・執行 |
| 🔍 @Citadel | 機関 | マルチ戦略 |
| 🔍 @TwoSigma | 機関 | データ駆動・AI |
| 🔍 @ManGroup | 機関 | マルチ戦略・リスク |
| 🔍 @AQR | 機関 | 因子投資・リスク |
| 🔍 @Optiver | 機関 | MM・執行 |
| 🔍 @JumpTrading | 機関 | MM・暗号 |
| 🔍 @WorldQuant | 機関 | 群衆ソーシング |
| ✅ @manquanttech | 機関 | Man AHL公式テック(量子的テック・OSS) |
| 🔍 @quantconnect | ベンダー | リサーチプラットフォーム |
| 🔍 @databento | ベンダー | 市場データ |
| 🔍 @numerai | ベンダー | 群衆ヘッジファンド |

### 層B: 研究者・実務家(個人・要ウォッチ)

| アカウント | 種別 | 備考 |
|-----------|------|------|
| ✅ @chanep | 研究者/実務 | Ernie Chan / QTS・PredictNow / 著者 |
| ✅ @ArturSepp | 研究者/実務 | QIS・確率ボラモデル |
| ✅ @MebFaber | 研究者/実務 | Cambria / 配分・トレンド |
| ✅ @Thomster78 | 研究者/実務 | Thomas Schmelzer / Jebel Quant Research・Stanford |
| ✅ @kz_kiyoshi | 研究者 | Kiyoshi Kanazawa / 京大・平方根則・LMFモデル |
| ✅ @choffstein | 研究者/実務 | Corey Hoffstein / Newfound Research・Return Stacked / 因子投資 |
| ✅ @nope_its_lily | 実務 | Lily Francus / デリバティブ・オプションクオンツ(NOPEモデル) |
| ✅ @bennpeifert | 実務 | Benn Eifert / ボラ・オプション戦略の定量ファンド創設 |
| ✅ @jam_croissant | 実務 | Cem Karsan / Kai Volatility / デイラーフロー・ボラ |
| ✅ @macrocephalopod | 実務 | 匿名機関クオンツ / トレンドフォロー・執行・CTA |
| ✅ @quant_arb | 実務 | Stat Arb / algos.org / イベント駆動アルファ |
| ✅ @Ksidiii | 実務 | Kris Sidial / オプション・ボラ |
| ✅ @therobotjames | 実務 | James Hodges / ロボットウェルス・オプション教育 |
| ✅ @quant_xbt | 実務 | 暗号クオンツ / 先物コンベクシティ |
| 🔍 @buildalpha | 実務 | r/algotrading推奨(2020)・quantブロガー |
| 🔍 @MiquelNoguer | 研究者 | AIFI創設者 / arXiv q-fin 頻出(2026-08-09収集) |
| ~ @ShinjiKakinaka | 研究者 | **X実在未確認**・高知工科大 / マルチフラクタル配分 |

### 層C: コミュニティ発見(Grokが毎週提案・入れ替え)

| アカウント | 種別 | 備考 |
|-----------|------|------|
| (空) | - | 毎週の実行で1〜3件追記される想定 |
| (seed済み) | - | r/quant推奨スレ(2024)の7件は検証後すべて層Bへ昇格済み |

> 更新ルール: 層B/Cはこのファイルを直接更新してよい。層Aの変更は稀なので報告のみ。

---

## 出力ファイルの統合

`grok-x-YYYY-MM-DD.md` は `build_digest.py` が自動統合する。
コミットすると GitHub Actions (`grok-x-push.yml`) が digest を自動再生成する。
リポジトリ: https://github.com/yamahei21python/quant-weekly
