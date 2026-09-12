"""strip_chapter_rules.py —— 去掉章节之间的分隔线 `---`

保留：frontmatter 的 `---`、文末附注（存疑表）前的 `---`
删除：紧邻 `## ` 标题之前的分隔线（及其产生的多余空行）

用法：python strip_chapter_rules.py <稿.md> ...
"""
import os
import re
import sys

log = []
for p in sys.argv[1:]:
    lines = open(p, encoding="utf-8").read().split("\n")
    keep = []
    removed = 0
    for i, ln in enumerate(lines):
        if ln.strip() == "---":
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines) and lines[j].startswith("## "):
                removed += 1
                continue
        keep.append(ln)
    # 压缩连续空行（最多保留 1 行）
    out = []
    for ln in keep:
        if ln.strip() == "" and out and out[-1].strip() == "":
            continue
        out.append(ln)
    open(p, "w", encoding="utf-8").write("\n".join(out))
    left = sum(1 for l in out if l.strip() == "---")
    log.append("%s : 删除章间分隔线 %d 条，剩余 --- %d 条" % (os.path.basename(p), removed, left))

_logdir = os.path.dirname(os.path.abspath(sys.argv[1])) if len(sys.argv) > 1 else "."
open(os.path.join(_logdir, "_strip_log.txt"), "w", encoding="utf-8").write("\n".join(log))
