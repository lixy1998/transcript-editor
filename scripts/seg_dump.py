"""seg_dump.py —— 抽取带时间戳的段落骨架（供语义分组与说话人判定使用）

用法：
    python seg_dump.py <整理稿.md> <输出.txt> [前N字，默认34]

输出每行：序号|起-止|正文前N字
另附：统计行（段数、总时长、最长/最短段）
"""
import re
import sys

SEG = re.compile(r"^\[(\d{1,2}:\d{2}(?::\d{2})?)-(\d{1,2}:\d{2}(?::\d{2})?)\]\s*(.*)$")


def main():
    doc = sys.argv[1]
    out = sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 34
    text = open(doc, encoding="utf-8").read()
    res = []
    i = 0
    for ln in text.splitlines():
        m = SEG.match(ln.strip())
        if m:
            i += 1
            body = m.group(3).replace("**", "").replace("【", "(").replace("】", ")")
            res.append("%d|%s-%s|%s" % (i, m.group(1), m.group(2), body[:n]))
    res.append("---")
    res.append("total_segs=%d" % i)
    res.append("chars=%d" % len(text))
    open(out, "w", encoding="utf-8").write("\n".join(res))


main()
