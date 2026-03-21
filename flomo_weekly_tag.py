#!/usr/bin/env python3
"""
flomo 每周自动打标脚本
按照已建立的三级标签体系，为过去7天新增的 memo 补充标签
"""

import hashlib
import json
import os
import subprocess
import time
import requests
from datetime import datetime, timedelta

# ─── 凭证配置 ─────────────────────────────────────────────────────────────────
# 凭证文件路径（格式见下方说明）
CREDENTIALS_FILE = os.path.expanduser("~/.flomo_credentials")

# 凭证文件格式（JSON）：
# {
#   "access_token": "从浏览器 localStorage 获取的 token（可能定期过期）",
#   "webhook_url": "https://flomoapp.com/iwh/xxx/yyy/"
# }

def load_credentials():
    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(
            f"凭证文件不存在: {CREDENTIALS_FILE}\n"
            "请创建该文件，内容格式：\n"
            '{ "access_token": "xxx", "webhook_url": "https://flomoapp.com/iwh/..." }'
        )
    with open(CREDENTIALS_FILE) as f:
        return json.load(f)


# ─── 标签规则 ─────────────────────────────────────────────────────────────────

TAG_RULES = [
    # 账号类（最高优先级，避免误判）
    ("账号/API", ["api key", "api_key", "apikey", "access_token", "secret_key",
                  "API", "token", "密钥", "key："]),
    ("账号/密码", ["密码", "password", "pwd", "登录", "账号："]),

    # 交易类
    ("交易/订单流", ["订单流", "footprint", "delta", "主力", "吸筹", "派发", "成交量分析"]),
    ("交易/工具",  ["bookmap", "tradingview", "mt4", "mt5", "thinkorswim", "ninja"]),
    ("交易/心态",  ["交易心态", "交易情绪", "纪律", "亏损", "止盈", "止损", "浮亏", "浮盈",
                   "执行力", "交易日记"]),
    ("交易/系统",  ["交易系统", "策略", "交易规则", "仓位", "风控", "回测", "胜率", "盈亏比"]),
    ("交易/市场",  ["美联储", "利率", "通胀", "CPI", "GDP", "经济数据", "宏观", "行情",
                   "大盘", "趋势"]),

    # 工具类
    ("工具/AI",    ["chatgpt", "deepseek", "claude", "gemini", "gpt", "大模型", "llm",
                   "人工智能", "prompt", "ai工具", "ai助手"]),
    ("工具/应用",  ["效率工具", "插件", "工具推荐", "app推荐", "软件", "notion", "obsidian",
                   "思源", "flomo", "语雀"]),

    # 阅读类（有明显引用格式的）
    ("阅读/MorningRocks", ["morningrocks", "morning rocks"]),
    ("阅读/ChunMian",     ["chunmian", "春眠"]),
    ("阅读/ALLBIACK",     ["allbiack"]),
    ("阅读/知乎",         ["来源：知乎", "——知乎", "知乎用户"]),
    ("阅读/尼采",         ["尼采", "nietzsche"]),
    ("阅读/泰戈尔",       ["泰戈尔"]),
    ("阅读/史铁生",       ["史铁生"]),
    ("阅读/加缪",         ["加缪", "camus"]),
    ("阅读/刘擎",         ["刘擎"]),
    ("阅读/博尔赫斯",     ["博尔赫斯"]),
    ("阅读/黑塞",         ["黑塞"]),
    ("阅读/文摘",         ["——", "◎", "书摘", "读书笔记", "摘录"]),  # 通用引用格式

    # 生活类
    ("生活/文艺",  ["音乐", "电影", "艺术", "展览", "画展", "摄影", "诗歌", "诗集",
                   "文学", "小说", "歌词", "乐队"]),
    ("生活/工作",  ["工作", "会议", "客户", "同事", "职场", "项目", "甲方", "汇报"]),
    ("生活/日常",  ["日常", "今天", "昨天", "这周", "随手记", "碎碎念"]),

    # 健康
    ("健康/减重",  ["减肥", "体重", "健身", "运动", "跑步", "卡路里", "饮食", "睡眠",
                   "作息", "健康"]),

    # 内心类（较宽泛，放后面）
    ("内心/哲思",  ["哲学", "命运", "存在", "意义", "灵魂", "死亡", "永恒", "时间",
                   "真理", "自由意志", "虚无"]),
    ("内心/成长",  ["成长", "自律", "坚持", "改变", "突破", "目标", "努力", "自我",
                   "勇气", "天赋", "潜力", "蜕变"]),
    ("内心/感悟",  ["感悟", "领悟", "明白", "意识到", "原来", "发现了", "顿悟",
                   "世界", "人生", "万物"]),
    ("内心/情感",  ["爱", "喜欢", "孤独", "思念", "失恋", "心动", "暗恋", "依赖",
                   "陪伴", "分离", "想你", "爱情", "感情"]),
]


def get_tags_for_memo(content: str) -> list[str]:
    """根据内容匹配应添加的标签（不重复已有标签）"""
    content_lower = content.lower()
    matched = []
    for tag, keywords in TAG_RULES:
        # 跳过已有的层级标签
        parent = tag.split("/")[0]
        if f"#{tag}" in content or f"#{parent}" in content:
            continue
        for kw in keywords:
            if kw.lower() in content_lower:
                matched.append(tag)
                break
    return matched


# ─── flomo API ────────────────────────────────────────────────────────────────

FLOMO_API = "https://flomoapp.com/api/v1"
FLOMO_SECRET = "dbbc3dd73364b4084c3a69346e0ce2b2"


def _build_signed_params(extra: dict) -> dict:
    """构建带 sign 的请求参数（反向工程自 flomo web app）"""
    params = {
        "timestamp": int(time.time()),
        "api_key": "flomo_web",
        "app_version": "4.0",
        "platform": "web",
        "webp": "1",
        **extra,
    }
    # 按 key 排序，拼接 query string
    sorted_keys = sorted(params.keys())
    parts = []
    for k in sorted_keys:
        v = params[k]
        if v is None:
            continue
        if isinstance(v, list):
            for item in sorted(v, key=str):
                parts.append(f"{k}[]={item}")
        else:
            parts.append(f"{k}={v}")
    qs = "&".join(parts)
    params["sign"] = hashlib.md5((qs + FLOMO_SECRET).encode()).hexdigest()
    return params


def _session(access_token: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {access_token}"})
    return s


def get_recent_memos(access_token: str, days: int = 7) -> list[dict]:
    """获取最近 N 天创建/更新的 memo"""
    since_ts = int((datetime.now() - timedelta(days=days)).timestamp())
    sess = _session(access_token)
    memos = []
    cursor_ts = since_ts
    cursor_slug = None

    while True:
        extra = {"limit": 200, "latest_updated_at": cursor_ts, "tz": "8:0"}
        if cursor_slug:
            extra["latest_slug"] = cursor_slug
        params = _build_signed_params(extra)

        for attempt in range(3):
            resp = sess.get(f"{FLOMO_API}/memo/updated/", params=params, timeout=15)
            if resp.status_code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            break
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"API 错误: {data.get('message')}")

        raw = data.get("data", [])
        batch = raw if isinstance(raw, list) else raw.get("memos", [])
        if not batch:
            break

        memos.extend(batch)

        if len(batch) < 200:
            break

        # 用最后一条的 updated_at + slug 作为下一页游标
        last = batch[-1]
        cursor_slug = last.get("slug")
        updated_str = last.get("updated_at", "")
        if isinstance(updated_str, str):
            try:
                cursor_ts = int(datetime.strptime(updated_str, "%Y-%m-%d %H:%M:%S").timestamp())
            except Exception:
                cursor_ts = since_ts
        else:
            cursor_ts = int(updated_str)

        if not cursor_slug:
            break
        time.sleep(1)

    return memos


def update_memo(access_token: str, slug: str, new_content: str) -> bool:
    """更新 memo 内容（追加标签）"""
    sess = _session(access_token)
    sess.headers["Content-Type"] = "application/json"
    # PUT 请求的 sign 需要包含 body 参数
    all_params = _build_signed_params({"slug": slug, "content": new_content})
    url_params = {k: v for k, v in all_params.items() if k not in ("slug", "content")}
    payload = {"slug": slug, "content": new_content}
    resp = sess.put(f"{FLOMO_API}/memo/", params=url_params,
                    json=payload, timeout=15)
    if resp.status_code != 200:
        return False
    result = resp.json()
    return result.get("code") == 0


# ─── 主流程 ───────────────────────────────────────────────────────────────────

def main():
    creds = load_credentials()
    access_token = creds["access_token"]

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 获取最近7天 memo...", flush=True)
    memos = get_recent_memos(access_token, days=7)
    print(f"  共找到 {len(memos)} 条", flush=True)

    updated = 0
    skipped = 0
    failed = 0

    for m in memos:
        content = m.get("content", "")
        slug = m.get("slug", "")
        if not slug or not content:
            continue

        new_tags = get_tags_for_memo(content)
        if not new_tags:
            skipped += 1
            continue

        tag_str = " ".join(f"#{t}" for t in new_tags)
        new_content = content.rstrip() + f"\n{tag_str}"

        if update_memo(access_token, slug, new_content):
            print(f"  ✓ {slug[:8]}... 添加: {tag_str}", flush=True)
            updated += 1
        else:
            print(f"  ✗ {slug[:8]}... 更新失败", flush=True)
            failed += 1

        time.sleep(0.2)  # 避免频率限制

    summary = f"更新 {updated} 条，跳过 {skipped} 条，失败 {failed} 条"
    print(f"\n完成：{summary}")

    # macOS 系统通知
    subtitle = "整理完成 ✓" if failed == 0 else f"完成（{failed} 条失败）"
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "{summary}" with title "flomo 标签整理" subtitle "{subtitle}"'
        ], timeout=5)
    except Exception:
        pass  # 非 macOS 或无权限时静默忽略

    # 写入最后一次运行结果到状态文件（供仪表盘读取）
    status = {
        "last_run": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "updated": updated,
        "skipped": skipped,
        "failed": failed,
        "total": len(memos),
    }
    status_file = os.path.expanduser("~/scripts/flomo_status.json")
    with open(status_file, "w") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
