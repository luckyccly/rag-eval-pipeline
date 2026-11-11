"""考卷一致性检查：验证 promptfooconfig.yaml 中手抄的 context 与 rag_app.py 语料完全一致。

背景：手抄考卷曾与系统语料脱节，引发间歇性误判（固件案）。
用法：python3 check_fixtures.py  —— 退出码 0=一致，1=有漂移（可供 CI 使用）
"""

import sys

sys.path.insert(0, ".")
import rag_app


def main():
    cfg = open("promptfooconfig.yaml", encoding="utf-8").read()
    all_ok = True
    for d in rag_app.DOCS:
        present = d["text"] in cfg
        print(f"{d['id']} 完整在考卷中: {present}")
        all_ok = all_ok and present
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()