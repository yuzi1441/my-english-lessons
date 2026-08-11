#!/usr/bin/env python3
"""Generate the week index page (lessons/week/index.html)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DAYS = [
    ("day-01", "Monday: My First Standup", "周一：我的第一次站会"),
    ("day-02", "Tuesday: The Branch and the Bug", "周二：分支与 Bug"),
    ("day-03", "Wednesday: The Pull Request", "周三：提交 PR"),
    ("day-04", "Thursday: The AI Brain", "周四：AI 大脑"),
    ("day-05", "Friday: Deploy Day", "周五：上线日"),
    ("day-06", "Saturday: English and Coffee", "周六：英语与咖啡"),
    ("day-07", "Sunday: Plan the Next Week", "周日：规划下周"),
]

rows = []
for slug, title, zh in DAYS:
    rows.append(
        f'<li><a href="{slug}/index.html"><h2>{title}</h2><p>{zh} · 约 15 分钟</p></a></li>'
    )

html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>英语学习周计划 · Week 1</title>
<style>
body{{font-family:-apple-system,sans-serif;max-width:720px;margin:0 auto;padding:32px 20px;line-height:1.6;background:#fafafa;color:#222}}
h1{{font-size:28px;margin-bottom:4px}}
.sub{{color:#666;margin-bottom:24px}}
ul{{list-style:none;padding:0}}
li{{background:#fff;border:1px solid #e3e3e3;border-radius:10px;margin-bottom:12px;overflow:hidden}}
a{{display:block;padding:16px 20px;text-decoration:none;color:#222}}
a:hover{{background:#f0f7ff}}
h2{{margin:0 0 4px;font-size:18px}}
p{{margin:0;color:#666;font-size:14px}}
</style>
</head>
<body>
<h1>英语学习周计划 · Week 1</h1>
<p class="sub">连续剧情：新工程师 Alex 的一周 · 每天一课 · 入门难度 · 全部含中文讲解</p>
<ul>
{''.join(rows)}
</ul>
</body>
</html>
"""

out = ROOT / "lessons" / "week" / "index.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html, encoding="utf-8")
print(f"written: {out}")
