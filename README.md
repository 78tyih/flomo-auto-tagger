# flomo-auto-tagger

自动为 [flomo（浮墨）](https://flomoapp.com) 笔记补充三级标签，每周定时运行，附带本地仪表盘。

## 功能

- 自动抓取过去 7 天新增/更新的 memo
- 按关键词匹配规则批量追加三级标签（如 `#内心/感悟`、`#交易/心态`）
- 完成后发送 macOS 系统通知
- 本地 HTML 仪表盘：实时倒计时 + 上次运行数据
- 搭配 crontab 每周一自动执行

## 标签体系

| 一级 | 二级示例 |
|------|---------|
| 内心 | 情感 / 感悟 / 成长 / 哲思 |
| 阅读 | 文摘 / 尼采 / 史铁生 / MorningRocks … |
| 交易 | 心态 / 系统 / 订单流 / 工具 / 市场 |
| 工具 | AI / 应用 |
| 生活 | 文艺 / 日常 / 工作 |
| 健康 | 减重 |
| 账号 | API / 密码 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置凭证

在 `~/.flomo_credentials` 创建 JSON 文件（格式如下）：

```json
{
  "access_token": "从浏览器 localStorage 获取（flomoapp.com → F12 → Application → Local Storage → token）",
  "webhook_url": "https://flomoapp.com/iwh/xxx/yyy/"
}
```

设置权限：

```bash
chmod 600 ~/.flomo_credentials
```

> `access_token` 可能定期过期，需重新获取。`webhook_url` 长期有效（flomo 设置页获取）。

### 3. 手动运行

```bash
python3 flomo_weekly_tag.py
```

### 4. 设置每周自动运行（macOS crontab）

```bash
crontab -e
```

添加以下行（每周一 09:07 运行）：

```
7 9 * * 1 /opt/homebrew/bin/python3 /path/to/flomo_weekly_tag.py >> /path/to/flomo_weekly_tag.log 2>&1
```

### 5. 打开仪表盘

```bash
cd /path/to/flomo-auto-tagger
python3 -m http.server 7788
# 浏览器访问 http://localhost:7788/flomo_dashboard.html
```

仪表盘显示距下次运行的实时倒计时，以及上次运行的统计数据。

## 文件说明

| 文件 | 说明 |
|------|------|
| `flomo_weekly_tag.py` | 主脚本：拉取 memo、匹配标签、更新 flomo |
| `flomo_dashboard.html` | 本地仪表盘（倒计时 + 运行统计） |
| `requirements.txt` | Python 依赖 |
| `~/.flomo_credentials` | 凭证文件（本地保存，不纳入版本控制） |
| `flomo_status.json` | 运行状态缓存（自动生成，不纳入版本控制） |

## 注意事项

- **凭证安全**：`~/.flomo_credentials` 已加入 `.gitignore`，请勿手动提交
- **API 限制**：脚本每次请求间隔 0.2s，避免触发频率限制
- 标签规则在 `flomo_weekly_tag.py` 的 `TAG_RULES` 列表中，可按需修改
