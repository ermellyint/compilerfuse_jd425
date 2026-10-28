"""compilerfuse_jd425 —— 在编译器与算子融合专家·成本与吞吐的帕累托边界里找出重复内容并给出归并建议。

对内容做归一化与分片比对，找出编译器与算子融合专家·成本与吞吐的帕累托边界上的重复项并按相似度归并

定位：
  按归一化后的分片相似度判断，而不是按字符串完全相等

岗位对应：
  目标岗位　无问芯穹 · 实习编译器与算子融合专家
  技能主线　编译器、CUDA、Triton
  领域标签　AI芯片算力

设计约束：
  1. **只报告能定位到具体位置的结论**，不做语义猜测。
  2. **规则表公开**，每条命中都能对应到岗位要求的一条明示规则。
  3. **输入为空或格式不对时明确报错**，不静默返回空结果。

仅依赖 Python 标准库。

用法:
    python compilerfuse_jd425.py --help
    python compilerfuse_jd425.py --file input.txt
    python compilerfuse_jd425.py --text "示例内容"
    python compilerfuse_jd425.py --file input.txt --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys

# 岗位规则表：每条规则独立可核查，命中即报，不做推断。
# 规则由岗位 JD 的技能线与领域标签派生——每条都能对回岗位要求。
# 目标岗位：无问芯穹 · 实习编译器与算子融合专家
RULES: list[dict] = [
    {
        "name": "编译器与算子融合专家·成本与吞吐的帕累托边界·缺失",
        "why": "岗位要求「编译器」在输入里找不到对应内容",
        "severity": "high",
        "keywords": ['missing', 'absent', '缺少', '没有', '未提供', '编译器'],
    },
    {
        "name": "编译器与算子融合专家·成本与吞吐的帕累托边界·冲突",
        "why": "两处关于「CUDA」的描述互相矛盾",
        "severity": "high",
        "keywords": ['conflict', 'contradict', '矛盾', '不一致', '相反', 'CUDA'],
    },
    {
        "name": "编译器与算子融合专家·成本与吞吐的帕累托边界·越界",
        "why": "「Triton」的取值超出岗位场景的常规范围",
        "severity": "medium",
        "keywords": ['out of range', 'outlier', '越界', '超限', '超过', 'Triton'],
    },
    {
        "name": "编译器与算子融合专家·成本与吞吐的帕累托边界·退化",
        "why": "「AI芯片算力」相关的信息量不足以支撑判断",
        "severity": "medium",
        "keywords": ['degrade', 'insufficient', '不足', '太少', '无法', 'AI芯片算力'],
    },
    {
        "name": "编译器与算子融合专家·成本与吞吐的帕累托边界·泄漏",
        "why": "「编译器与算子融合专家」相关的内容被意外暴露",
        "severity": "high",
        "keywords": ['leak', 'expose', '泄漏', '暴露', '明文', '编译器与算子融合专家'],
    },
    {
        "name": "编译器与算子融合专家·成本与吞吐的帕累托边界·重复#2",
        "why": "同一处「编译器」信息被反复传递",
        "severity": "low",
        "keywords": ['duplicate', 'repeat', '重复', 'again', '编译器'],
    },
    {
        "name": "编译器与算子融合专家·成本与吞吐的帕累托边界·陈旧#2",
        "why": "「CUDA」的时效性已过期",
        "severity": "medium",
        "keywords": ['stale', 'expired', '过期', '陈旧', '旧版', 'CUDA'],
    },
    {
        "name": "编译器与算子融合专家·成本与吞吐的帕累托边界·不可核#2",
        "why": "关于「Triton」的说法无法追溯到具体证据",
        "severity": "high",
        "keywords": ['unverifiable', 'no evidence', '无法追溯', '没有来源', 'Triton'],
    },
]


def compilerfuse_jd425_normalize(text: str) -> str:
    """归一化：去空白、转小写、去标点。"""
    t = re.sub(r"\s+", "", text.lower())
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]", "", t)


def compilerfuse_jd425_shingles(text: str, k: int = 3) -> set[str]:
    """字符 k-gram 集合。"""
    n = compilerfuse_jd425_normalize(text)
    if len(n) <= k:
        return {n} if n else set()
    return {n[i:i + k] for i in range(len(n) - k + 1)}


def compilerfuse_jd425_jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def compilerfuse_jd425_group(items: list[str], threshold: float = 0.6) -> list[list[int]]:
    """按相似度做贪心聚类，返回每组的下标列表。"""
    sigs = [compilerfuse_jd425_shingles(x) for x in items]
    groups: list[list[int]] = []
    assigned = [False] * len(items)
    for i in range(len(items)):
        if assigned[i]:
            continue
        compilerfuse_jd425_group = [i]
        assigned[i] = True
        for j in range(i + 1, len(items)):
            if assigned[j]:
                continue
            if compilerfuse_jd425_jaccard(sigs[i], sigs[j]) >= threshold:
                compilerfuse_jd425_group.append(j)
                assigned[j] = True
        groups.append(compilerfuse_jd425_group)
    return groups


def compilerfuse_jd425_analyze(text: str) -> dict:
    """主分析：单文本内的重复段落与近似重复。"""
    blocks = [b for b in re.split(r"\n\s*\n", text) if b.strip()]
    groups = compilerfuse_jd425_group(blocks)
    dup_groups = [g for g in groups if len(g) > 1]
    exact = []
    seen: dict[str, list[int]] = {}
    for i, b in enumerate(blocks):
        key = compilerfuse_jd425_normalize(b)
        if key in seen:
            exact.append({"first": seen[key][0], "dup": i})
        else:
            seen.setdefault(key, []).append(i)
    return {
        "block_count": len(blocks),
        "groups": len(groups),
        "duplicate_groups": dup_groups,
        "exact_duplicates": exact,
        "redundancy": round(sum(len(g) - 1 for g in dup_groups) / len(blocks), 4) if blocks else 0.0,
        "clean": not dup_groups and not exact,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def render(result: dict) -> str:
    """把结果渲染成人读的文本。每个工具的版式不同。"""
    out: list[str] = []
    if not result.get("ok", True):
        out.append(f"无法分析：{{result.get('error', '未知原因')}}")
        return "\n".join(out)
    out.append(f"段落数：{result['block_count']}  聚类：{result['groups']}")
    out.append(f"冗余率：{result['redundancy']:.2%}")
    out.append("")
    for g in result["duplicate_groups"]:
        out.append(f"重复组（{len(g)} 份）：{g}")
    if result["clean"]:
        out.append("没有发现重复。")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="compilerfuse_jd425",
        description="对内容做归一化与分片比对，找出编译器与算子融合专家·成本与吞吐的帕累托边界上的重复项并按相似度归并（仅依赖标准库）",
        epilog=(
            "示例:\n"
            "  python compilerfuse_jd425.py --file input.txt\n"
            "  python compilerfuse_jd425.py --text '示例内容'\n"
            "  python compilerfuse_jd425.py --file input.txt --json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="输入文件路径")
    src.add_argument("--text", help="直接给出输入内容")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args(argv)

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            print(f"读不了文件：{{e}}", file=sys.stderr)
            return 2
    else:
        content = args.text

    if not content.strip():
        print("输入是空的。", file=sys.stderr)
        return 2

    result = compilerfuse_jd425_analyze(content)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(render(result))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
