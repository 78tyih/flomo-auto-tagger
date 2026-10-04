# Evidence — flomo-auto-tagger

Updated: 2026-10-05

## Observed（实查）

| 声明 | 证据 |
|---|---|
| 389 行单文件 | `wc -l flomo_weekly_tag.py` → 389 |
| 三级标签体系 7 大类 | TAG_RULES：账号/（API·密码）、交易/（订单流·工具·心态·系统·市场）、工具/（AI·应用）、阅读/（MorningRocks·知乎·尼采·泰戈尔·史铁生·加缪·博尔赫斯·黑塞·文摘…）、生活/（文艺·工作·日常）、健康/减重、内心/（哲思·成长·感悟·情感） |
| 「优先级即顺序」 | 代码注释明示：账号类最高优先级（避免误判）、内心类较宽泛放后面；TAG_RULES 数组顺序即匹配顺序 |
| 去重逻辑 | get_tags_for_memo：`if f"#{tag}" in content or f"#{parent}" in content: continue`（跳过已有层级/父级标签） |
| 游标分页 + 429 退避 | get_recent_memos：latest_updated_at/latest_slug 游标、limit 200、429 时 sleep 5*(attempt+1) |
| MD5 sign 签名 | _build_signed_params：参数按 key 排序拼 qs，sign = md5(qs + FLOMO_SECRET)，注释「反向工程自 flomo web app」 |
| 凭证本地化 | load_credentials 读 ~/.flomo_credentials（JSON：access_token + webhook_url），仓库内无个人凭证 |
| 依赖仅 requests | requirements.txt 单行 requests>=2.28.0 |

## Inferred（推断，附复核方式）

| 声明 | 复核方式 |
|---|---|
| 每周定时运行 | 仓库描述自述「每周定时运行，附本地倒计时仪表盘」；脚本本体不含调度代码（由外部 cron/launchd 驱动），复验=查本机 launchd/cron 配置 |
| 「每周新增自动补标」实际效果 | 需运行时验证；复验=手动跑一轮看 memo diff |

## Unknown

- 仓库描述提到的「本地倒计时仪表盘」文件不在仓库内（仅 flomo_weekly_tag.py + requirements.txt）
- access_token 的有效期与刷新方式（注释称「可能定期过期」）
