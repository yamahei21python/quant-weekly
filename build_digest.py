"""週次digest統合スクリプト。

reddit-{date}.md / arxiv-{date}.md / grok-x-{date}.md を統合して
{date}.md (週次digest・素材集約版) を生成する。

- 深掘り分析は行わない(素材集約のみ)。深掘りは別フェーズ(モデル任せ)。
- ファイル命名規則:
  - reddit:  reddit-{date}.md     (fetch_reddit.py が出力)
  - arxiv:   arxiv-{date}.md      (fetch_arxiv.py が出力)
  - X収集:   grok-x-{date}.md     (Grokタスク出力を手動配置)
  - digest:  {date}.md            (本スクリプトの出力・最終物)

使い方:
    python build_digest.py [YYYY-MM-DD]   # 引数省略時は今日
"""

import sys
from datetime import date, timedelta
from pathlib import Path

# (key, 表示ラベル, 生成元) の順。並び順が出力セクション順になる。
SOURCES: list[tuple[str, str, str]] = [
    ('arxiv', 'arXiv (q-fin.TR / PM / RM)', 'fetch_arxiv.py'),
    ('reddit', 'Reddit (r/quant, r/algotrading)', 'fetch_reddit.py'),
    ('grok-x', 'X (Grok収集)', 'Grokタスク手動配置'),
]


def _strip_first_h1(text: str) -> str:
    """先頭の '# ' 見出しを削除(タイトル重複回避)。見出しが無ければそのまま。"""
    lines = text.splitlines()
    if lines and lines[0].startswith('# '):
        return '\n'.join(lines[1:]).strip()
    return text.strip()


def load_source(cwd: Path, key: str, date_str: str) -> tuple[str, str, int] | None:
    path = cwd / f'{key}-{date_str}.md'
    if not path.exists():
        return None
    body = _strip_first_h1(path.read_text(encoding='utf-8'))
    # 件数: arXiv は '## [Title](url)'、Reddit/X は '- [Title](url)' で計上
    count = sum(1 for ln in body.splitlines()
                if ln.startswith('## [') or ln.startswith('- ['))
    return body, path.name, count


def build_digest(cwd: Path, date_str: str) -> Path:
    start = (date.fromisoformat(date_str) - timedelta(days=7)).isoformat()
    out = cwd / f'{date_str}.md'
    out_rel = out.relative_to(cwd)  # フッター表示用（cwd からの相対パス）
    sections: list[str] = []
    rows: list[str] = []

    for key, label, producer in SOURCES:
        loaded = load_source(cwd, key, date_str)
        if loaded is None:
            rows.append(f'| {label} | 未取得 | - | {producer} |')
            continue
        body, fname, count = loaded
        rows.append(f'| {label} | {count}件 | `{fname}` | {producer} |')
        sections.append(f'\n## {label}\n\n{body}\n')
    header = [
        '# 週次クオンツ定点観測',
        '',
        f'- 対象期間: {start} 〜 {date_str}',
        f'- 収集日: {date_str}',
        '- ソース: arXiv (q-fin.TR/PM/RM), Reddit (r/quant, r/algotrading), X (Grok収集)',
        '- 深掘り分析: 未実施(素材集約版)',
        '',
        '## 収集サマリ',
        '',
        '| ソース | 状態 | ファイル | 生成元 |',
        '|--------|------|----------|--------|',
    ] + rows + [
        '',
        '---',
        '',
        '## 収集素材',
    ] + sections + [
        '---',
        '',
        f'*生成: build_digest.py ({date_str}) / 保存先: `{out_rel}`*',
        '',
    ]

    out.write_text('\n'.join(header), encoding='utf-8')
    return out


def main() -> None:
    date_str = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    try:
        date.fromisoformat(date_str)
    except ValueError:
        print(f'ERROR: 日付形式が不正: {date_str}（YYYY-MM-DD で指定）', file=sys.stderr)
        sys.exit(1)

    cwd = Path.cwd()
    out = build_digest(cwd, date_str)
    missing = [f'{key}-{date_str}.md' for key, _, _ in SOURCES
               if not (cwd / f'{key}-{date_str}.md').exists()]
    print(f'Done. Digest saved to {out.name}')
    if missing:
        print(f'WARN: 未取得ソース: {", ".join(missing)}', file=sys.stderr)


if __name__ == '__main__':
    main()
