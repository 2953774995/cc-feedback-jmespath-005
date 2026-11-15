#!/usr/bin/env python3
"""group_by 聚合扩展验收探针。

契约：
  jmespath.search("group_by(items, &tier)", data) -> dict
  分组键规则：str 原样；数字转字符串（1 -> "1"，1.5 -> "1.5"）；True/False -> "true"/"false"；None -> "null"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import jmespath  # noqa: E402
from jmespath.exceptions import JMESPathTypeError  # noqa: E402

FAILED = 0
PASSED = 0


def check(code, desc, fn):
    global FAILED, PASSED
    try:
        fn()
        print(f"[PASS] {code} {desc}")
        PASSED += 1
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] {code} {desc}")
        print(f"        {type(exc).__name__}: {exc}")
        FAILED += 1


DATA = {
    "items": [
        {"id": 1, "tier": "gold", "score": 90},
        {"id": 2, "tier": "silver", "score": 70},
        {"id": 3, "tier": "gold", "score": 85},
    ]
}


def main():
    def p1():
        r = jmespath.search("group_by(items, &tier)", DATA)
        assert set(r) == {"gold", "silver"}, r.keys()
        assert [i["id"] for i in r["gold"]] == [1, 3], r["gold"]
        assert [i["id"] for i in r["silver"]] == [2]

    def p2():
        data = {"items": [{"k": "b"}, {"k": "a"}, {"k": "b"}, {"k": "a"}, {"k": "c"}]}
        r = jmespath.search("group_by(items, &k)", data)
        assert [i["k"] for i in r["b"]] == ["b", "b"]
        assert list(r) == ["b", "a", "c"], list(r)

    def p3():
        assert jmespath.search("group_by(items, &tier)", {"items": []}) == {}

    def p4():
        try:
            jmespath.search("group_by(items, &tier)", {"items": {"a": 1}})
        except JMESPathTypeError:
            return
        raise AssertionError("非数组输入未抛 JMESPathTypeError")

    def p5():
        try:
            jmespath.search("group_by(items, &@)", DATA)
        except JMESPathTypeError:
            return
        raise AssertionError("分组键为对象时未抛错")

    def p6():
        data = {"items": [{"n": 1}, {"n": 1.5}, {"n": True}, {"n": None}]}
        r = jmespath.search("group_by(items, &n)", data)
        assert set(r) == {"1", "1.5", "true", "null"}, set(r)

    def p7():
        try:
            jmespath.search("no_such_function(items)", DATA)
        except Exception as exc:  # noqa: BLE001
            assert "Unknown function" in str(exc) or "unknown" in str(exc).lower(), exc
            return
        raise AssertionError("未知函数调用未报错")

    check("P1", "按字符串键分组", p1)
    check("P2", "组内与组间顺序保持", p2)
    check("P3", "空数组返回空对象", p3)
    check("P4", "非数组输入报错", p4)
    check("P5", "不可哈希分组键报错", p5)
    check("P6", "数值/布尔/空键字符串化", p6)
    check("P7", "未知函数仍按原行为报错", p7)

    print("-" * 60)
    print(f"探针汇总：{PASSED}/{PASSED + FAILED} 通过")
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
