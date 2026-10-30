"""极简 RAG 应用（mock 版）——作为被评测对象

流水线：检索（字符二元组重叠打分）→ 生成（摘录式 mock，不调用任何模型，零成本）
后续升级路线：生成器换 Ollama 本地模型 → 检索换 embedding
"""

DOCS = [
    {"id": "D1", "text": "云雀音箱开机后，长按机身顶部静音键5秒进入配网模式，打开云雀App选择添加设备，输入Wi-Fi密码即可完成配网。配网失败时请确认手机与音箱连接同一Wi-Fi。"},
    {"id": "D2", "text": "调节音量可以说『小韵，音量调到50』，或旋转音箱顶部音量环。音量环顺时针增大，逆时针减小，静音时音量环指示灯为红色。"},
    {"id": "D3", "text": "蓝牙连接：对音箱说『小韵，打开蓝牙』，指示灯变为蓝色闪烁后在手机蓝牙列表选择Yunque-Speaker完成配对。蓝牙模式下不支持语音点歌。"},
    {"id": "D4", "text": "固件升级：云雀App中进入设备设置，点击固件更新，升级过程中请保持音箱通电，全程约10分钟。云雀音箱自购买日起保修一年。"},
    {"id": "D5", "text": "隐私说明：语音数据仅在唤醒词触发后上传云端处理，可在App中开启本地模式，本地模式下语音不出设备，录音缓存可在App中一键清除。"},
]

REFUSAL = "抱歉，产品资料中没有找到相关信息，无法回答该问题。"


def _bigrams(s):
    """把文本拆成字符二元组集合（简易中文切分，后续升级为 embedding）"""
    s = "".join(s.split())
    return {s[i:i + 2] for i in range(len(s) - 1)} if len(s) > 1 else {s}


def retrieve(question):
    """按二元组重叠数给文档打分，返回 (最高分, 最相关文档)"""
    q = _bigrams(question)
    scored = sorted(
        ((max(len(q & _bigrams(s)) for s in d["text"].split("。")), d) for d in DOCS),
        key=lambda x: x[0], reverse=True)
    return scored[0] if scored and scored[0][0] > 0 else (0, None)


import json
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:3b"

PROMPT_TEMPLATE = """你是一个智能客服，只根据下面的产品资料回答用户问题。
如果资料中没有答案，回答：抱歉，产品资料中没有找到相关信息。

产品资料：
{context}

用户问题：{question}

回答："""


def generate(question, doc):
    """调用本地 Ollama 模型，基于检索到的文档生成回答（temperature=0 降低随机性）"""
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": PROMPT_TEMPLATE.format(context=doc["text"], question=question),
        "stream": False,
        "options": {"temperature": 0},
    }).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))["response"].strip()


def ask_full(question):
    """返回 (回答, 检索到的资料原文)；拒答时原文为空"""
    score, doc = retrieve(question)
    if doc is None or score < 2:
        return REFUSAL, ""
    return generate(question, doc), doc["text"]


def ask(question):
    """兼容旧接口：只返回回答"""
    return ask_full(question)[0]


def call_api(prompt, options, context):
    """promptfoo Python provider 标准接口；context 字段供 faithfulness 断言使用"""
    answer, ctx = ask_full(context["vars"]["question"])
    return {"output": answer, "context": ctx}
