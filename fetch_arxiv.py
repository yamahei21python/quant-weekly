"""arXiv API 経由で直近7日間の q-fin 系論文を取得 → Markdown保存。

- 対象カテゴリ: q-fin.TR / q-fin.PM / q-fin.RM（primary category）
- 日付フィルタ: submittedDate 範囲（arXiv API 仕様）
- 出力: arxiv-YYYY-MM-DD.md（後段の LLM キュレーション用の素データ）
"""

import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

API_URL = 'https://export.arxiv.org/api/query'
NS_ATOM = 'http://www.w3.org/2005/Atom'
NS_ARXIV = 'http://arxiv.org/schemas/atom'
NS_OPEN = 'http://a9.com/-/spec/opensearch/1.1/'

CATEGORIES = ['q-fin.TR', 'q-fin.PM', 'q-fin.RM']
DAYS_BACK = 7
MAX_RESULTS = 200
BATCH = 100
API_INTERVAL = 3.0  # arXiv API 推奨のリクエスト間隔（秒）
ABSTRACT_MAX = 300  # 要約の最大文字数
EXCLUDE_KEYWORDS: list[str] = []  # タイトルに含まれる場合は除外（必要に応じて設定）
FILTER_BY_PRIMARY = True  # True: primary category が対象カテゴリの論文のみ表示

USER_AGENT = 'quant-weekly-arxiv-fetcher/1.0 (weekly quant digest)'


def _text(elem: ET.Element | None) -> str:
    if elem is None or elem.text is None:
        return ''
    return ' '.join(elem.text.split())


def build_query(cats: list[str], start: date, end: date) -> str:
    cat_str = ' OR '.join(f'cat:{c}' for c in cats)
    date_str = (
        f'submittedDate:[{start.strftime("%Y%m%d")}0000 '
        f'TO {end.strftime("%Y%m%d")}2359]'
    )
    return f'({cat_str}) AND {date_str}'


def fetch_entries(query: str) -> tuple[list[dict[str, object]], int]:
    """arXiv API をページングしながら取得。Atom XML を dict 化して返す。"""
    entries: list[dict[str, object]] = []
    start = 0
    total = 0
    while start < MAX_RESULTS:
        params = urllib.parse.urlencode({
            'search_query': query,
            'start': start,
            'max_results': BATCH,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending',
        })
        req = urllib.request.Request(f'{API_URL}?{params}', headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp:
            root = ET.fromstring(resp.read())

        total_elem = root.find(f'{{{NS_OPEN}}}totalResults')
        total = int(total_elem.text) if total_elem is not None else 0

        batch = []
        for entry in root.findall(f'{{{NS_ATOM}}}entry'):
            item = {
                'id': _text(entry.find(f'{{{NS_ATOM}}}id')),
                'title': _text(entry.find(f'{{{NS_ATOM}}}title')),
                'published': _text(entry.find(f'{{{NS_ATOM}}}published')),
                'summary': _text(entry.find(f'{{{NS_ATOM}}}summary')),
                'primary_category': (
                    entry.find(f'{{{NS_ARXIV}}}primary_category').get('term', '')
                    if entry.find(f'{{{NS_ARXIV}}}primary_category') is not None else ''
                ),
                'authors': [a.text or '' for a in entry.findall(f'{{{NS_ATOM}}}author/{{{NS_ATOM}}}name')],
            }
            batch.append(item)
        entries.extend(batch)

        if start + len(batch) >= total or len(batch) == 0:
            break
        start += len(batch)
        time.sleep(API_INTERVAL)
    return entries, total


def dedupe(entries: list[dict[str, object]]) -> list[dict[str, object]]:
    """同一 arXiv ID（バージョン違い含む）を除去。"""
    seen: set[str] = set()
    out: list[dict[str, object]] = []
    for e in entries:
        arxiv_id = str(e['id']).split('/abs/')[-1].split('v')[0]
        if arxiv_id in seen:
            continue
        seen.add(arxiv_id)
        e['arxiv_id'] = arxiv_id
        out.append(e)
    return out


def is_excluded(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in EXCLUDE_KEYWORDS)


def format_markdown(
    date_str: str,
    start: date,
    end: date,
    entries: list[dict[str, object]],
    total: int,
) -> str:
    lines = [
        f'# arXiv q-fin 収集（{start.isoformat()} 〜 {end.isoformat()}）',
        '',
        f'- 収集日: {date_str}',
        f'- カテゴリ: {", ".join(CATEGORIES)}',
        f'- 総ヒット: {total} / 表示: {len(entries)}',
        '',
    ]
    for e in entries:
        authors = e['authors'][:5] if isinstance(e['authors'], list) else []
        author_str = ', '.join(authors)
        if len(e['authors']) > 5:
            author_str += f' ほか {len(e["authors"]) - 5}名'
        summary = str(e['summary'])
        if len(summary) > ABSTRACT_MAX:
            summary = summary[:ABSTRACT_MAX] + '…'
        lines += [
            f'## [{e["title"]}](https://arxiv.org/abs/{e["arxiv_id"]})',
            '',
            f'- 公開: {str(e["published"])[:10]} | カテゴリ: {e["primary_category"]} | 著者: {author_str}',
            f'- 要約: {summary}',
            '',
        ]
    return '\n'.join(lines) + '\n'


def main() -> None:
    end = date.today()
    start = end - timedelta(days=DAYS_BACK)
    query = build_query(CATEGORIES, start, end)
    print(f'Fetching: {query}', flush=True)

    entries, total = fetch_entries(query)
    entries = [e for e in dedupe(entries) if not is_excluded(str(e['title']))]
    if FILTER_BY_PRIMARY:
        entries = [e for e in entries if str(e['primary_category']) in CATEGORIES]
    entries.sort(key=lambda e: str(e['published']), reverse=True)

    date_str = end.isoformat()
    md = format_markdown(date_str, start, end, entries, total)
    md_path = Path.cwd() / f'arxiv-{date_str}.md'
    md_path.write_text(md, encoding='utf-8')
    print(f'Done. {len(entries)} papers -> {md_path.name}')


if __name__ == '__main__':
    main()
