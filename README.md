# rag-eval-pipeline — RAG 质量评测流水线

面向 RAG 问答系统的自动化评测项目。

## 这是什么

- **被测对象**：`rag_app.py` —— 极简 RAG 问答应用（虚构产品「云雀音箱」说明书问答），当前为 mock 生成器（字符二元组检索 + 摘录式回答），计划升级 Ollama 本地模型
- **评测框架**：[promptfoo](https://promptfoo.dev)，配置见 `promptfooconfig.yaml`
- **评测集**：6 条用例 —— 5 条正常问答 + 1 条对抗性拒答用例（资料外问题必须拒答）

## 运行

```bash
npx promptfoo@latest eval     # 跑评测
npx promptfoo@latest view     # 网页版报告
```

## 已抓到并修复的一个真实缺陷

对抗用例「音箱支持退款吗？」曾误命中蓝牙文档：词汇级二元组匹配把「**不**支持语音点歌」中的「支持」误计为命中，导致系统未拒答、答非所问。

**修复**：检索打分粒度从整篇文档降到单句，零散误撞词凑不齐阈值，正确触发拒答，回归 6/6 通过。此案例也是后续升级 embedding 语义检索的动机。


## LLM-as-Judge 裁判缺陷记录

引入 llm-rubric 语义断言后，对手工裁判做了「评裁判」实验（qwen2.5:3b 同模型互判）：

| 判卷 prompt 版本 | 忠实回答 | 编造回答 | 准确率 |
|---|---|---|---|
| v1：评分标准 + 回答 | ❌ 误判不合格 | ✅ 不合格 | 1/2 |
| v2：注入产品资料原文 ground truth | ✅ 逐条引证判合格 | ✅ 正确指认编造 | 2/2 |

**发现**：
1. 无 ground truth 时，裁判以先验代替标准（"资料通常不会包含这种步骤"），误杀忠实回答
2. 裁判判决对判卷 prompt 措辞高度敏感（同模型同答案：v1 手工判 FAIL，promptfoo 内置判 PASS）
3. 修复 = 判卷 prompt 注入资料原文 + 显式判定规则，判案方式从「凭感觉」变为「引证据」


## 路线图

- [x] mock 版流水线跑通（6/6 全绿）
- [x] 接入 Ollama 本地 LLM 替换 mock 生成器
- [x] LLM-as-Judge 裁判验证与修复（手工实验，详见上方缺陷记录）
- [ ] 工程化 faithfulness：rag_app 返回 context，接入 promptfoo 的 context-faithfulness 断言
- [ ] 评测集扩充 + bad case 归因报告