"""verify_reflow.py —— 核验体例升级结果

用法：python verify_reflow.py <整理稿.md> [<pre-reflow.bak>]
输出：<整理稿.md>.verify.txt
"""
import re
import sys
import os
import traceback
from collections import Counter

SEG = re.compile(r"^\[(\d{1,2}:\d{2}(?::\d{2})?)-(\d{1,2}:\d{2}(?::\d{2})?)\]\s*(.*)$")
SPK = re.compile(r"^\[(\d{1,2}:\d{2}(?::\d{2})?)-(\d{1,2}:\d{2}(?::\d{2})?)\]\s*\*\*(.+?)\*\*\s*[：:]")


def secs(t):
    p = [int(x) for x in t.split(":")]
    return p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2]


def deltas(txt):
    """返回时间戳跨度的秒数列表（用于中位/均值）"""
    r = []
    for l in txt.splitlines():
        m = SEG.match(l.strip())
        if m:
            r.append(secs(m.group(2)) - secs(m.group(1)))
    return r


def body_of(txt):
    parts = []
    for l in txt.splitlines():
        m = SEG.match(l.strip())
        if m:
            parts.append(SPK.sub("", l.strip()))
    return "".join(parts).replace(" ", "").replace("**", "")


def run():
    doc = sys.argv[1]
    bak = sys.argv[2] if len(sys.argv) > 2 else None
    txt = open(doc, encoding="utf-8").read()
    lines = txt.splitlines()

    segs = []
    for i, ln in enumerate(lines):
        m = SEG.match(ln.strip())
        if m:
            s = SPK.match(ln.strip())
            segs.append((i, m.group(1), m.group(2), s.group(3) if s else "?"))

    out = []
    out.append("文件: " + doc)
    out.append("== 规模 ==")
    out.append("新段数=%d" % len(segs))
    d = deltas(txt)
    if d:
        ds = sorted(d)
        out.append("段时长 秒: min=%d 中位=%d 均值=%.1f max=%d" % (d[0] if False else ds[0], ds[len(ds) // 2], sum(ds) / len(ds), ds[-1]))
    out.append("字符=%d 行数=%d" % (len(txt), len(lines)))

    out.append("== 时间轴连续性 ==")
    gaps, overlaps = [], []
    for k in range(1, len(segs)):
        pe, ps = segs[k - 1][2], segs[k][1]
        if pe == ps:
            continue
        dd = secs(ps) - secs(pe)
        (gaps if dd > 0 else overlaps).append("%s|%s->%s(%+ds)" % (segs[k - 1][1], pe, ps, dd))
    out.append("断点数=%d 重叠数=%d" % (len(gaps), len(overlaps)))
    out.append("gaps(前8): " + "; ".join(gaps[:8]))
    out.append("overlaps(前8): " + "; ".join(overlaps[:8]))

    out.append("== 说话人 ==")
    out.append(str(dict(Counter(s[3] for s in segs))))
    out.append("无标注段: " + str([s[1] for s in segs if s[3] == "?"]))

    out.append("== 结构 ==")
    out.append("##=%d  ###=%d" % (sum(1 for l in lines if l.startswith("## ")),
                                  sum(1 for l in lines if l.startswith("### "))))
    out.append("金句章=%s  存疑汇总表=%s  表格行=%d" % (
        "金句精选与关键洞察" in txt, "存疑标记汇总" in txt,
        sum(1 for l in lines if l.strip().startswith("|"))))
    for l in lines:
        if l.startswith("## "):
            out.append("   " + l[:90])

    out.append("== 关键节点 ==")
    out.append("节点数=%d" % len(re.findall(r"【\d{1,2}:\d{2}(?::\d{2})?】", txt)))

    out.append("== 遗留标记 ==")
    out.append("【?】=%d  【?主体】=%d" % (txt.count("【?】"), txt.count("【?主体】")))
    for i, ln in enumerate(lines):
        if "【?】" in ln or "【?主体】" in ln:
            out.append("   L%d %s" % (i + 1, ln[:90]))

    if bak and os.path.exists(bak):
        old = open(bak, encoding="utf-8").read()
        out.append("== 与覆盖前快照比对 ==")
        out.append("旧段数=%d 旧字符=%d" % (
            sum(1 for l in old.splitlines() if SEG.match(l.strip())), len(old)))
        a, b = body_of(old), body_of(txt)
        out.append("旧正文净字符=%d 新正文净字符=%d 差=%+d" % (len(a), len(b), len(b) - len(a)))
    else:
        out.append("== 未找到快照文件（%s）==" % str(bak))

    out.append("== 首 6 段 ==")
    cnt = 0
    for l in lines:
        if SEG.match(l.strip()):
            out.append("   " + l[:120])
            cnt += 1
            if cnt >= 6:
                break

    open(doc + ".verify.txt", "w", encoding="utf-8").write("\n".join(out))


try:
    run()
except Exception:
    open(sys.argv[1] + ".verify.txt", "w", encoding="utf-8").write(traceback.format_exc())
