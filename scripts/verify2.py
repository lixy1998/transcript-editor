"""verify2.py —— 正文一致性严格比对（去时间戳/姓名/空白后逐字比对）

用法：python verify2.py <新稿.md> <旧稿.bak>
输出：<新稿.md>.verify2.txt
"""
import re
import sys
import difflib
import traceback

SEG = re.compile(r"^\[(\d{1,2}:\d{2}(?::\d{2})?)-(\d{1,2}:\d{2}(?::\d{2})?)\]\s*(.*)$")
P_TS = re.compile(r"^\[[\d:]+-[\d:]+\]\s*")
P_SPK = re.compile(r"^\*\*[^*]+\*\*\s*[：:]\s*")
P_NODE = re.compile(r"^【[\d:]+】\s*")


def secs(t):
    p = [int(x) for x in t.split(":")]
    return p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2]


def norm(txt):
    out = []
    for l in txt.splitlines():
        s = l.strip()
        if not SEG.match(s):
            continue
        s = P_TS.sub("", s)
        s = P_SPK.sub("", s)
        s = P_NODE.sub("", s)
        s = s.replace("**", "").replace(" ", "").replace("\u3000", "")
        out.append(s)
    return "".join(out)


def run():
    new = open(sys.argv[1], encoding="utf-8").read()
    old = open(sys.argv[2], encoding="utf-8").read()
    a, b = norm(old), norm(new)
    res = []
    res.append("旧净正文=%d  新净正文=%d  差=%+d" % (len(a), len(b), len(b) - len(a)))
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    op = [o for o in sm.get_opcodes() if o[0] != "equal"]
    res.append("差异块数=%d" % len(op))
    for tag, i1, i2, j1, j2 in op[:14]:
        res.append("[%s] 旧[%d:%d]=%r  新[%d:%d]=%r" % (tag, i1, i2, a[i1:i2][:70], j1, j2, b[j1:j2][:70]))
    res.append("== 短段（<10 秒，未合并的碎片）==")
    for l in new.splitlines():
        m = SEG.match(l.strip())
        if m:
            d = secs(m.group(2)) - secs(m.group(1))
            if d < 10:
                res.append("   %s-%s (%ds) %s" % (m.group(1), m.group(2), d, m.group(3)[:60]))
    res.append("== 段数 ==")
    res.append("旧=%d 新=%d" % (len([1 for l in old.splitlines() if SEG.match(l.strip())]),
                                len([1 for l in new.splitlines() if SEG.match(l.strip())])))
    open(sys.argv[1] + ".verify2.txt", "w", encoding="utf-8").write("\n".join(res))


try:
    run()
except Exception:
    open(sys.argv[1] + ".verify2.txt", "w", encoding="utf-8").write(traceback.format_exc())
