"""Check tracking, heading hierarchy, sitemap exclusions and article parity."""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit, unquote

root = Path(sys.argv[1])
for file in root.rglob('*.html'):
    html = file.read_text()
    assert not re.search(r'adsbygoogle|googletagmanager\.com|google-analytics\.com', html), file
    assert len(re.findall(r'<h1[ >]', html)) <= 1, file
for locale, sitemap in (('', 'zh-cn/sitemap.xml'), ('en/', 'en/sitemap.xml'), ('ja/', 'ja/sitemap.xml')):
    urls = {e.text for e in ET.parse(root / sitemap).findall('.//{*}loc')}
    assert not any(any(part in urlsplit(u).path for part in ('/private/', '/search/')) for u in urls)
    core = json.loads((Path(__file__).resolve().parent.parent / 'data/core_tags.json').read_text())
    for url in urls:
        path = unquote(urlsplit(url).path)
        if '/tags/' in path:
            term = path.split('/tags/')[1].strip('/')
            if term:
                assert term in {tag.replace(' ', '-') for tag in core}, url
                html = (root / path.lstrip('/') / 'index.html').read_text()
                assert not re.search(r'name=[\"\']?robots[^>]*noindex', html), url
    articles = json.loads((root / locale / 'index.json').read_text())
    assert all(a['permalink'] in urls for a in articles)
    if not locale:
        archive = (root / 'archives/index.html').read_text()
        assert len(re.findall(r'class=\"?archive-entry(?:\"|>)', archive)) == len(articles)
        for article in articles:
            path = unquote(urlsplit(article['permalink']).path).lstrip('/')
            assert (root / path / 'index.html').is_file()
    print(f'{locale or "zh-cn"}: {len(articles)} articles, {len(urls)} sitemap URLs')
print('SEO checks passed: no tracking, at most one H1, clean sitemaps, matching article collections.')
