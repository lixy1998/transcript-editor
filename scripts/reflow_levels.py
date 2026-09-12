"""reflow_levels.py —— 层级化时间戳重构

把「段前时间戳」体例改为「标题层级锚点」体例：
  · 删除段落前的时间戳，段落只留 `**说话人**：正文`
  · 给 `##`（章）、`###`（节）标题末尾补该层级所辖范围的时间区间
  · 相邻 `##` 章节之间插入 `---` 分隔

用法：python reflow_levels.py <稿.md> ...
产出：<稿.md>.levels_log.txt
"""
import os
import re
import sys

SEG = re.compile(r"^【(\d{1,2}:\d{2}(?::\d{2})?)-(\d{1,2}:\d{2}(?::\d{2})?)】\s*(.*)$")
HEAD = re.compile(r"^(#{2,3})\s+(.*)$")
TS_TAIL = re.compile(r"\s*【[\d:]+-[\d:]+】\s*$")


def run(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    items = []
    for ln in lines:
        s = ln.strip()
        m = SEG.match(s)
        if m:
            items.append(["seg", (m.group(1), m.group(2), m.group(3))])
            continue
        h = HEAD.match(s)
        if h:
            items.append(["head", (h.group(1), TS_TAIL.sub("", h.group(2)).strip())])
            continue
        items.append(["other", ln])

    heads = [(k, it[1][0], it[1][1]) for k, it in enumerate(items) if it[0] == "head"]
    newline = [None] * len(items)
    for k, it in enumerate(items):
        if it[0] == "seg":
            newline[k] = it[1][2]
        elif it[0] == "other":
            newline[k] = it[1]

    n_head = 0
    for n, (k, lvl, txt) in enumerate(heads):
        end = len(items)
        for k2, lvl2, _ in heads[n + 1:]:
            if len(lvl2) <= len(lvl):
                end = k2
                break
        segs = [it[1] for it in items[k + 1:end] if it[0] == "seg"]
        if segs:
            newline[k] = "%s %s 【%s-%s】" % (lvl, txt, segs[0][0], segs[-1][1])
            n_head += 1
        else:
            newline[k] = "%s %s" % (lvl, txt)

    out = []
    n_sep = 0
    for k, it in enumerate(items):
        if it[0] == "head" and it[1][0] == "##":
            while out and out[-1].strip() == "":
                out.pop()
            if out and out[-1].strip() != "---":
                out.append("")
                out.append("---")
                n_sep += 1
            out.append("")
        out.append(newline[k])

    open(path, "w", encoding="utf-8").write("\n".join(out))
    return "OK  %s\n    标题补区间=%d/%d，插入章分隔=%d，段落=%d" % (
        os.path.basename(path), n_head, len(heads), n_sep,
        sum(1 for it in items if it[0] == "seg"))


log = []
for p in sys.argv[1:]:
    try:
        log.append(run(p))
    except Exception as e:
        log.append("ERR %s : %r" % (p, e))
_logdir = os.path.dirname(os.path.abspath(sys.argv[1])) if len(sys.argv) > 1 else "."
open(os.path.join(_logdir, "_levels_log.txt"), "w", encoding="utf-8").write("\n".join(log))
