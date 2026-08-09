"""Xpoz SDK 経由で r/quant, r/algotrading の週間トップ投稿を取得 → Markdown保存。

判明済みの Xpoz API 仕様（2026-08-09 調査）:
- query は必須（最小1文字）。空文字は MCP error -32602。
- fields 指定なしだと score/url/comments_count 等が欠落するため明示必須。
- time='week' はサーバー側で無視される → start_date/end_date で明示。
- sort はランキング式（純粋な score 降順ではない）→ クライアント側で score 降順に並べ直す。

- 出力: reddit-{date}.md（最終 digest {date}.md との名前衝突回避のためプレフィックス付き）
"""

import asyncio
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SUBREDDITS = ['quant', 'algotrading']
# query は必須（最小1文字）。'the' はタイトル/本文マッチでほぼ全投稿にヒットする汎用語。
QUERY = 'the'
FIELDS = ['title', 'score', 'comments_count', 'url', 'permalink', 'author_username', 'created_at_date']
FILTER_KEYWORDS = ['career', 'salary', 'interview', 'job', 'hiring', 'resume']
POST_LIMIT = 25
DAYS_BACK = 7

# 整形後の投稿1件分（title/score/num_comments/author/url）。
Post = dict[str, object]


def is_filtered(title: str) -> bool:
    title = title.lower()
    return any(kw in title for kw in FILTER_KEYWORDS)


def _first_attr(obj: object, *names: str) -> object:
    """属性名群から最初の truthy 値を返す（欠損・別名フォールバック用）。"""
    for name in names:
        value = getattr(obj, name, None)
        if value:
            return value
    return None


def _post_url(p: object) -> str:
    url = _first_attr(p, 'url', 'permalink')
    if url and str(url).startswith('/'):
        return f'https://www.reddit.com{url}'
    return str(url or '')


def _fmt(value: object) -> str:
    """欠損値(None)を '?' に置換して表示用文字列化。"""
    return '?' if value is None else str(value)


async def fetch_all(end_date: date | None = None) -> dict[str, list[Post]]:
    """各サブレディットのトップ投稿を取得。end_date 省略時は今日。"""
    from xpoz import AsyncXpozClient

    api_key = os.environ.get('XPOZ_API_KEY')
    if not api_key:
        print('ERROR: XPOZ_API_KEY not set in .env', file=sys.stderr)
        sys.exit(1)

    end = end_date or date.today()
    start = end - timedelta(days=DAYS_BACK)

    results: dict[str, list[Post]] = {}
    client = AsyncXpozClient(api_key=api_key)
    try:
        await client.connect()
        for sub in SUBREDDITS:
            try:
                res = await client.reddit.search_posts(
                    QUERY,
                    subreddit=sub,
                    sort='top',
                    start_date=start.isoformat(),
                    end_date=end.isoformat(),
                    limit=POST_LIMIT,
                    fields=FIELDS,
                )
                posts: list[Post] = []
                for p in res.data or []:
                    title = str(_first_attr(p, 'title') or '')
                    if is_filtered(title):
                        continue
                    posts.append({
                        'title': title,
                        'score': _first_attr(p, 'score'),
                        'num_comments': _first_attr(p, 'comments_count', 'num_comments'),
                        'author': _first_attr(p, 'author_username', 'author'),
                        'url': _post_url(p),
                    })
                posts.sort(key=lambda x: x['score'] or 0, reverse=True)
                results[sub] = posts
            except Exception as exc:
                print(f'ERROR fetching r/{sub}: {exc!r}', file=sys.stderr)
                results[sub] = []
    finally:
        await client.close()
    return results


def save_markdown(date_str: str, results: dict[str, list[Post]]) -> Path:
    # arxiv-{date}.md と同名規則に揃え、最終digest({date}.md)との衝突を回避
    md_path = Path.cwd() / f'reddit-{date_str}.md'
    with md_path.open('w', encoding='utf-8') as f:
        f.write(f'# {date_str}\n\n')
        for subreddit, posts in results.items():
            f.write(f'## r/{subreddit}\n\n')
            if not posts:
                f.write('No posts fetched.\n\n')
                continue
            for post in posts:
                title = post['title']
                url = post['url']
                line = f'- [{title}]({url})  \n' if url else f'- {title}  \n'
                f.write(line)
                f.write(
                    f'  - Score: {_fmt(post["score"])}, '
                    f'Comments: {_fmt(post["num_comments"])}, '
                    f'Author: u/{_fmt(post["author"])}\n\n'
                )
    return md_path


def main() -> None:
    today = date.today()
    results = asyncio.run(fetch_all(today))
    md_path = save_markdown(today.isoformat(), results)
    print(f'Done. Markdown saved to {md_path.name}')


if __name__ == '__main__':
    main()
