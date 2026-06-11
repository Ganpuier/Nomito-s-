"""抓取知乎热榜前十（来自 tophub.today），保存为 hotlist.json"""
import re, json, html, urllib.request, ssl

url = 'https://tophub.today/'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})
ctx = ssl.create_default_context()

try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        content = resp.read().decode('utf-8', errors='replace')
except Exception:
    # fallback: use requests if available
    import requests as reqs
    resp = reqs.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
    content = resp.text

items = []
# 匹配知乎热榜条目（tophub 的 HTML 结构）
p = r'<a href="(https://www\.zhihu\.com/question/\d+)"[^>]*itemid="\d+">(.*?)</a>'
seen = set()
for m in re.finditer(p, content, re.DOTALL):
    link = m.group(1)
    if link in seen:
        continue
    seen.add(link)
    raw = m.group(2)
    raw = re.sub(r'<.*?>', '', raw)       # 去 HTML 标签
    raw = html.unescape(raw)
    parts = [p.strip() for p in raw.split('\n') if p.strip()]
    # 格式：['1', '标题', '热度']
    title = parts[1] if len(parts) > 1 else parts[0] if parts else ''
    # 提取热度（可能在 third line 或跟在标题后）
    heat = ''
    for p in parts:
        h = re.search(r'(\d+[\d.]*)\s*万热度', p)
        if h:
            heat = h.group(1) + '万'
            break
    if title:
        items.append({'rank': len(items)+1, 'title': title, 'url': link, 'heat': heat})
    if len(items) >= 10:
        break

with open('hotlist.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=2)
print(f'ok {len(items)} 条 -> hotlist.json')
