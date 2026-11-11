"""自研 faithfulness 断言 v3——修订记录：
- v1：格式模板无示例锚定，3B 裁判复读模板交白卷（隐私案）
- v2：未强制引用原句，判词无法审计（蓝牙案教训）
- v3：例题锚定 + 强制引用原句
"""

import json
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:7b"
FAITHFUL_THRESHOLD = 1.0

JUDGE_PROMPT = """对照【资料】逐条检查【回答】中的事实陈述。对每一条：先原样引用回答中的该句话，再给出判定。每条一行。

判定标准（最重要）：只判断陈述内容是否在【资料】原文中出现，原句或同义表述均算有依据。陈述与提问主题是否相关、是否答到点子上，不影响判定。

示例（示例内容与本次任务无关）：
【资料】云雀音箱支持7天无理由退货，需保持包装完好。音箱产地为深圳。
【回答】云雀音箱可以退货，但需要保持包装完好。音箱产地是广州。
正确输出：
云雀音箱可以退货，但需要保持包装完好。 → 有依据
音箱产地是广州。 → 无依据

现在处理真实任务：
【资料】{context}

【回答】{output}

输出（每条一行，先引用回答原句，再给判定）："""


def _call_judge(context_text, output):
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": JUDGE_PROMPT.format(context=context_text, output=output),
        "stream": False,
        "options": {"temperature": 0},
    }).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))["response"].strip()


def get_assert(output, context):
    """promptfoo Python 断言标准接口"""
    ctx = context["vars"].get("context", "")
    if not ctx:
        return {"pass": True, "score": 1.0, "reason": "无 context（拒答类用例），跳过忠实度检查"}

    judge_resp = _call_judge(ctx, output)
    claims = []
    for ln in judge_resp.splitlines():
        if "→" not in ln:
            continue
        left, right = ln.split("→", 1)
        claim = left.strip().strip("「」\"“”")
        verdict = right.strip()
        grounded = ("有依据" in verdict) and ("无依据" not in verdict)
        claims.append((claim, grounded))

    if not claims:
        return {"pass": False, "score": 0.0,
                "reason": f"裁判输出无法解析，原始输出: {judge_resp}"}

    total = len(claims)
    grounded_n = sum(1 for c in claims if c[1])
    score = round(grounded_n / total, 2)
    detail = "；".join(f"{c[0]} → {'有依据' if c[1] else '无依据'}" for c in claims)
    return {
        "pass": score >= FAITHFUL_THRESHOLD,
        "score": score,
        "reason": f"共 {total} 条陈述，有依据 {grounded_n} 条。逐条判定: {detail}",
    }