"""verify_levels.py —— 核验「层级锚点」体例

用法：python verify_levels.py <新稿.md> [<旧快照>]
产出：<新稿.md>.vlevels.txt
"""
import os
import re
import sys
import difflib
import traceback
from collections import Counter

PREFIX_TS = re.compile(r"^【\d{1,2}:\d{2}")
SPK = re.compile(r"^\*\*([^*]+)\*\*\s*[：:]\s*")
H2 = re.compile(r"^##\s+(.*?)【(\d{1,2}:\d{2}(?::\d{2})?)-(\d{1,2}:\d{2}(?::\d{2})?)】\s*$")
H3 = re.compile(r"^###\s+(.*?)【(\d{1,2}:\d{2}(?::\d{2})?)-(\d{1,2}:\d{2}(?::\d{2})?)】\s*$")
ANYHEAD = re.compile(r"^#{2,3}\s")
OLDSEG = re.compile(r"^\[(\d{1,2}:\d{2}(?::\d{2})?)-(\d{1,2}:\d{2}(?::\d{2})?)\]\s*(.*)$")
OLDSPK = re.compile(r"^\*\*[^*]+\*\*\s*[：:]\s*")


def secs(t):
    p = [int(x) for x in t.split(":")]
    return p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2]


def new_body(txt):
    out = []
    for l in txt.splitlines():
        s = l.strip()
        m = SPK.match(s)
        if m:
            out.append(s.replace("**", "").replace(" ", ""))
    return "".join(out)


def old_body(txt):
    out = []
    for l in txt.splitlines():
        s = l.strip()
        m = OLDSEG.match(s)
        if m:
            b = OLDSPK.sub("", m.group(3))
            b = re.sub(r"^【[\d:]+】\s*", "", b)
            out.append(b.replace("**", "").replace(" ", ""))
    return "".join(out)


def run():
    doc = sys.argv[1]
    bak = sys.argv[2] if len(sys.argv) > 2 else None
    txt = open(doc, encoding="utf-8").read()
    lines = txt.splitlines()
    res = ["文件: " + doc]

    segs = [l.strip() for l in lines if SPK.match(l.strip())]
    res.append("段落数=%d" % len(segs))
    res.append("说话人分布=%s" % dict(Counter(SPK.match(s).group(1) for s in segs)))
    res.append("段前时间戳残留=%d（应为 0）" % sum(1 for l in lines if PREFIX_TS.match(l.strip())))

    h2 = [l for l in lines if H2.match(l.strip())]
    h3 = [l for l in lines if H3.match(l.strip())]
    heads = [l for l in lines if ANYHEAD.match(l.strip())]
    res.append("##=%d（带区间 %d）  ###=%d（带区间 %d）  无区间标题=%s" % (
        sum(1 for l in lines if l.startswith("## ")), len(h2),
        sum(1 for l in lines if l.startswith("### ")), len(h3),
        [l[:40] for l in heads if "【" not in l]))
    res.append("章分隔 ---=%d" % sum(1 for l in lines if l.strip() == "---"))

    spans = [(m.group(2), m.group(3)) for m in (H2.match(l.strip()) for l in lines) if m]
    bad = []
    for i in range(1, len(spans)):
        if spans[i][0] != spans[i - 1][1]:
            bad.append("%s|%s->%s" % (spans[i - 1][0], spans[i - 1][1], spans[i][0]))
    res.append("## 层区间断点=%d %s" % (len(bad), "; ".join(bad[:6])))
    if spans:
        res.append("章区间范围=%s ~ %s" % (spans[0][0], spans[-1][1]))

    res.append("金句章=%s  存疑汇总表=%s  frontmatter=%s" % (
        "金句精选与关键洞察" in txt, "存疑标记汇总" in txt, txt.startswith("---")))
    res.append("【?】=%d" % txt.count("【?】"))

    if bak and os.path.exists(bak):
        a, b = old_body(open(bak, encoding="utf-8").read()), new_body(txt)
        res.append("旧净正文=%d 新净正文=%d 差=%+d" % (len(a), len(b), len(b) - len(a)))
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        op = [o for o in sm.get_opcodes() if o[0] != "equal"]
        res.append("差异块数=%d" % len(op))
        for tag, i1, i2, j1, j2 in op[:8]:
            res.append("  [%s] 旧=%r 新=%r" % (tag, a[i1:i2][:50], b[j1:j2][:50]))
    else:
        res.append("未提供快照，跳过正文比对")

    res.append("== 首 8 行结构预览 ==")
    res.extend("   " + l[:100] for l in lines[:8])
    res.append("== 正文起始 6 行 ==")
    cnt = 0
    for l in lines:
        if SPK.match(l.strip()):
            res.append("   " + l[:100])
            cnt += 1
            if cnt >= 6:
                break
    open(doc + ".vlevels.txt", "w", encoding="utf-8").write("\n".join(res))


try:
    run()
except Exception:
    open(sys.argv[1] + ".vlevels.txt", "w", encoding="utf-8").write(traceback.format_exc())
