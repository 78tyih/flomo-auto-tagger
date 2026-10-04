# flomo-auto-tagger

> **一句话**：flomo 笔记每周自动打标——按自定义三级标签体系关键词匹配补标，不重复已有标签，凭证本地化。
>
> **展示页**：https://78tyih.github.io/flomo-auto-tagger/showcase.html

| | |
|---|---|
| 类型 | 个人自动化脚本（Python 单文件 389 行） |
| 状态 | 本人在用（flomo 非官方接口，改版可能失效） |
| 依赖 | requests>=2.28.0（唯一依赖） |

## ① 解决什么问题

flomo 记得快但标签靠手补，积压一周就再也不想整理，笔记库失去可检索性。脚本按你定好的三级体系每周自动补标。

## ② 什么场景 → 什么结果

每周定时跑（cron/launchd 自排）：过去 7 天新增 memo 自动带上 `#交易/订单流` 这类三级标签；同层不重复、已有标签不覆盖。

## ③ 什么结构

单文件 `flomo_weekly_tag.py`：

```text
TAG_RULES                # 三级标签关键词表（优先级即顺序）
  账号/                   # API · 密码（最高优先级，避免误判）
  交易/                   # 订单流 · 工具 · 心态 · 系统 · 市场
  工具/                   # AI · 应用
  阅读/                   # MorningRocks · 知乎 · 尼采 · 泰戈尔 · 史铁生 · 加缪 …
  生活/ · 健康/           # 文艺 · 工作 · 日常 / 减重
  内心/                   # 哲思 · 成长 · 感悟 · 情感（较宽泛，放最后）
get_tags_for_memo()      # 匹配 + 去重（跳过已有层级/父级标签）
flomo API 客户端          # 游标分页 + MD5 sign 签名（逆向自 flomo web app）
编辑写回                  # 追加 #标签
```

## ④ 能复用什么

- **「优先级即顺序」的规则表写法**——安全类规则永远先匹配
- **flomo 非官方 API 配方**：sign = md5(sorted qs + secret)、latest_updated_at/latest_slug 游标分页
- **父级标签去重逻辑**
- **凭证本地文件化习惯**：access_token 只存 `~/.flomo_credentials`（JSON），永不进仓库

## 使用

```bash
pip install -r requirements.txt
# 1) 创建凭证文件 ~/.flomo_credentials：
#    { "access_token": "从浏览器 localStorage 获取", "webhook_url": "https://flomoapp.com/iwh/xxx/yyy/" }
# 2) 按自己的体系改 TAG_RULES
# 3) 手动跑一轮验证，再挂 cron/launchd 每周执行
python3 flomo_weekly_tag.py
```

## 边界

- flomo 非官方接口，flomo 改版可能失效
- 脚本内硬编码的 sign 密钥是 flomo web 端全局签名常量（逆向所得），**非个人凭证**
- 个人 access_token 可能定期过期，需从浏览器 localStorage 重新获取
