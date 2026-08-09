"""r/quant, r/algotrading の「フォロー推奨スレ」を Xpoz 経由で収集 → @handle 抽出 → Markdown保存。

目的: grok-x-prompt.md のウォッチリスト(層B/層C)充実のための候補抽出。
Xpoz は Reddit API 403 を回避できる(サードパーティデータプロバイダ)。

方針:
- 既知スレID(POST_IDS)は get_post_with_comments で直接取得(高速・確実)
- 未知スレは DISCOVERY_QUERIES で search_posts → タイトルでフィルタしてから取得

使い方:
    source .venv/bin/activate
    python fetch_follow_recommendations.py [YYYY-MM-DD]
"""

import asyncio
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Web検索で特定済みの「フォロー推奨スレ」ID
POST_IDS = ['hllcbg']  # r/algotrading: Any recommendations of blogs or Twitter account to follow... (2020)
SUBREDDITS = ['algotrading', 'quant']
DISCOVERY_QUERIES = ['twitter accounts', 'accounts to follow', 'quant twitter']
DISCOVERY_PER_SUB = 2
POST_FIELDS = ['id', 'title', 'score', 'comments_count', 'url', 'selftext', 'created_at_date']
COMMENT_FIELDS = ['body', 'score', 'author_username', 'created_at_date']
SEARCH_LIMIT = 10
# API 連続呼び出し間の待機時間（レート制限回避）
REQUEST_DELAY = 0.5
# タイトルがフォロー推奨スレらしきものだけ拾う
TITLE_KEYWORDS = ('follow', 'twitter', 'account', 'x ', 'x/', 'x account')
# X ハンドル: @ に英数字/アンダースコア 2〜15文字
HANDLE_RE = re.compile(r'@([A-Za-z0-9_]{2,15})')
EXCLUDE_HANDLES = {'everyone', 'mods', 'reddit', 'u', 'the', 'its', 'this', 'that', 'please'}

Post = dict[str, object]
Thread = dict[str, object]


def _post_dict(p: object) -> Post:
    """Xpoz 投稿オブジェクトを表示用 dict に整形（欠損値は None）。"""
    return {
        'id': getattr(p, 'id', None),
        'title': getattr(p, 'title', None),
        'score': getattr(p, 'score', None),
        'comments_count': getattr(p, 'comments_count', None),
        'url': getattr(p, 'url', None),
        'selftext': getattr(p, 'selftext', ''),
        'created_at_date': getattr(p, 'created_at_date', None),
    }


def extract_handles(text: str) -> list[str]:
    """テキストから X ハンドル候補を抽出(小文字化・除外語フィルタ)。"""
    return [m for m in (h.lower() for h in HANDLE_RE.findall(text or ''))
            if m not in EXCLUDE_HANDLES and not m.endswith('_')]


def looks_like_follow_thread(title: str) -> bool:
    t = (title or '').lower()
    return any(kw in t for kw in TITLE_KEYWORDS)


async def discover_threads(client: object, sub: str) -> list[Post]:
    """サブレディット内を発見用検索し、タイトルフィルタを通したスレを返す。"""
    posts: list[Post] = []
    for query in DISCOVERY_QUERIES:
        try:
            res = await client.reddit.search_posts(
                query,
                subreddit=sub,
                sort='relevance',
                limit=SEARCH_LIMIT,
                fields=POST_FIELDS,
            )
            for p in res.data or []:
                posts.append(_post_dict(p))
        except Exception as exc:
            print(f'ERROR search {sub}/{query!r}: {exc!r}', file=sys.stderr)
        await asyncio.sleep(REQUEST_DELAY)
    seen: set[str] = set()
    uniq: list[Post] = []
    for p in sorted(posts, key=lambda x: x['score'] or 0, reverse=True):
        if not looks_like_follow_thread(str(p['title'])):
            continue
        pid = str(p['id'])
        if pid and pid not in seen:
            seen.add(pid)
            uniq.append(p)
    return uniq[:DISCOVERY_PER_SUB]


async def fetch_thread(client: object, post_id: str, sub: str | None = None) -> Thread | None:
    """指定ポストとコメントを取得。失敗時は None。sub 未指定時はポスト情報から判定。"""
    try:
        res = await client.reddit.get_post_with_comments(
            post_id,
            post_fields=POST_FIELDS,
            comment_fields=COMMENT_FIELDS,
        )
        post = res.post
        if post is None:
            return None
        comments = res.comments or []
        handles = extract_handles(getattr(post, 'selftext', '') or '')
        for cm in comments:
            handles.extend(extract_handles(getattr(cm, 'body', '') or ''))
        return {
            'sub': sub or (getattr(post, 'subreddit_name', '?') or '?'),
            'id': post_id,
            'title': getattr(post, 'title', None),
            'url': getattr(post, 'url', None),
            'score': getattr(post, 'score', None),
            'comments_count': getattr(post, 'comments_count', None),
            'created_at_date': getattr(post, 'created_at_date', None),
            'handles': sorted(set(handles)),
            'num_comments_fetched': len(comments),
        }
    except Exception as exc:
        print(f'ERROR comments {post_id}: {exc!r}', file=sys.stderr)
        return None


async def collect() -> list[Thread]:
    from xpoz import AsyncXpozClient

    api_key = os.environ.get('XPOZ_API_KEY')
    if not api_key:
        print('ERROR: XPOZ_API_KEY not set in .env', file=sys.stderr)
        sys.exit(1)

    results: list[Thread] = []
    client = AsyncXpozClient(api_key=api_key)
    try:
        await client.connect()
        # 1) 既知スレID
        for pid in POST_IDS:
            r = await fetch_thread(client, pid)
            if r:
                results.append(r)
            await asyncio.sleep(REQUEST_DELAY)
        # 2) 発見用検索
        for sub in SUBREDDITS:
            threads = await discover_threads(client, sub)
            for t in threads:
                r = await fetch_thread(client, str(t['id']), sub=sub)
                if r:
                    results.append(r)
                await asyncio.sleep(REQUEST_DELAY)
    finally:
        await client.close()
    return results


def save_markdown(date_str: str, threads: list[Thread]) -> Path:
    md_path = Path.cwd() / f'reddit-follow-recs-{date_str}.md'
    counter: Counter[str] = Counter()
    sources: dict[str, set[str]] = defaultdict(set)
    for t in threads:
        for h in t['handles']:
            counter[h] += 1
            sources[h].add(str(t['title']))

    with md_path.open('w', encoding='utf-8') as f:
        f.write(f'# Redditフォロー推奨スレ収集 ({date_str})\n\n')
        f.write(f'- 収集日: {date_str}\n')
        f.write(f'- スレ数: {len(threads)} / ユニークハンドル: {len(counter)}\n\n')
        f.write('## 抽出ハンドル(言及数順)\n\n')
        f.write('| ハンドル | 言及数 | 出典スレ |\n')
        f.write('|----------|--------|----------|\n')
        for h, n in counter.most_common():
            src = ', '.join(sorted(sources[h]))[:80]
            f.write(f'| @{h} | {n} | {src} |\n')
        f.write('\n---\n\n## スレ一覧\n\n')
        for t in threads:
            f.write(f"### [{t['title']}]({t['url']})  \n")
            f.write(f"- r/{t['sub']} | Score: {t['score']} | Comments: {t['comments_count']} | "
                    f"取得コメント: {t['num_comments_fetched']}\n")
            hs = ', '.join(f'@{h}' for h in t['handles'])
            f.write(f"- ハンドル: {hs}\n\n")
    return md_path


def main() -> None:
    date_str = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    threads = asyncio.run(collect())
    md_path = save_markdown(date_str, threads)
    print(f'Done. Saved to {md_path.name}')


if __name__ == '__main__':
    main()
