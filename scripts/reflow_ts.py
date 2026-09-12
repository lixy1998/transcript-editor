"""reflow_ts.py —— 按映射表把逐段碎时间戳重构为语义段 + 主体标注 + 关键节点

用法：
    python reflow_ts.py <整理稿.md> <映射表.txt> [--check]

映射表格式（每行对应文档中的第 i 个时间戳段落，顺序必须一致）：
    组号,说话人[,节点]
    例：  1,张三,0
          2,李四,1     ← 第 3 列=1 表示在该段正文前插入【该段起点时间】作为关键节点

规则：
    · 同一组号的连续段落合并为一段，区间取「组首段起点 - 组末段终点」
    · 段首统一为  `[MM:SS-MM:SS] **说话人**：` + 组内正文顺序拼接
    · 拼接时若前段末尾无终止标点，自动补「。」
    · 组内若夹有非空非段落行（小标题/引用块/表格）则判为非法分组，报错

产出：
    <文档>.reflow_log.txt     运行结果（OK / 错误清单）
    <文档>.pre-reflow.bak     覆盖前的原文快照
"""
import re
import sys

SEG = re.compile(r"^\[(\d{1,2}:\d{2}(?::\d{2})?)-(\d{1,2}:\d{2}(?::\d{2})?)\]\s*(.*)$")
TERM = "。！？…”』）】"


def main():
    doc = sys.argv[1]
    mapf = sys.argv[2]
    check_only = "--check" in sys.argv
    logp = doc + ".reflow_log.txt"
    raw = open(doc, encoding="utf-8").read()
    lines = raw.split("\n")

    segs = []
    for i, ln in enumerate(lines):
        m = SEG.match(ln.strip())
        if m:
            segs.append((i, m.group(1), m.group(2), m.group(3)))

    maps = []
    for ln in open(mapf, encoding="utf-8").read().split("\n"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        parts = [p.strip() for p in ln.split(",")]
        if len(parts) < 2:
            open(logp, "w", encoding="utf-8").write("BAD MAP LINE: %s" % ln)
            return 1
        maps.append((int(parts[0]), parts[1], int(parts[2]) if len(parts) > 2 and parts[2] else 0))

    errs = []
    if len(maps) != len(segs):
        errs.append("映射行数=%d，文档时间戳段落数=%d，不一致" % (len(maps), len(segs)))

    groups = []
    cur = None
    for idx, (g, s, n) in enumerate(maps):
        if cur is None or g != cur[0]:
            cur = (g, [])
            groups.append(cur)
        cur[1].append(idx)

    seen = set()
    for g, _ in groups:
        if g in seen:
            errs.append("组号 %d 不连续" % g)
        seen.add(g)

    if not errs:
        seg_line = {s[0]: k for k, s in enumerate(segs)}
        for g, idxs in groups:
            a, b = segs[idxs[0]][0], segs[idxs[-1]][0]
            for li in range(a + 1, b):
                if li in seg_line:
                    continue
                if lines[li].strip():
                    errs.append("组 %d 跨越了非段落行 L%d：%s" % (g, li + 1, lines[li][:40]))

    if errs:
        open(logp, "w", encoding="utf-8").write("\n".join(errs))
        return 1

    if check_only:
        open(logp, "w", encoding="utf-8").write(
            "OK(check) segs=%d groups=%d" % (len(segs), len(groups)))
        return 0

    out, pos = [], 0
    for g, idxs in groups:
        a, b = segs[idxs[0]][0], segs[idxs[-1]][0]
        out.extend(lines[pos:a])
        body_parts = []
        for k in idxs:
            _, st, en, txt = segs[k]
            txt = txt.strip()
            if maps[k][2]:
                txt = "【%s】 " % st + txt
            if body_parts and body_parts[-1] and body_parts[-1][-1] not in TERM:
                body_parts[-1] += "。"
            body_parts.append(txt)
        head = "[%s-%s] **%s**：" % (segs[idxs[0]][1], segs[idxs[-1]][2], maps[idxs[0]][1])
        out.append(head + "".join(body_parts))
        pos = b + 1
    out.extend(lines[pos:])

    open(doc + ".pre-reflow.bak", "w", encoding="utf-8").write(raw)
    open(doc, "w", encoding="utf-8").write("\n".join(out))
    open(logp, "w", encoding="utf-8").write(
        "OK written segs=%d -> groups=%d paragraphs" % (len(segs), len(groups)))
    return 0


sys.exit(main())
