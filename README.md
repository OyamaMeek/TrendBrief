# TrendBrief · 开源趋势简报

读取 GitHub Trending 所有语言的 Today 日榜，严格按原顺序取前 10 名，生成每项目 100～150 字中文说明，通过 Telegram Bot 推送到一个群组。每天北京时间 14:06、16:06、17:06 计划触发，成功后当天后续运行跳过。不同日期重复上榜的项目继续展示。

这是 Python 命令行工具，无网页、交互式 Bot 或数据库。入口为 `trending_digest.py`。现有 `Claude.md` 保存原始需求，实际配置和操作以本 README 为准。

## 安装和本地预览

需要 Python 3.13 和 Git。

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
cp .env.example .env
```

将 `.env` 占位值替换为实际配置。文件不会自动加载，在受信任的本地终端通过 `set -a; source .env; set +a` 导出。不要提交或分享该文件，也不要开启 shell 命令跟踪。

| 环境变量 | 用途 |
| --- | --- |
| `AI_BASE_URL` | 完整 HTTPS API 前缀，例如服务商文档中的 `/v1`，程序只追加 `/chat/completions` |
| `AI_MODEL` | 服务商实际支持的模型 |
| `AI_API_KEY` | AI 密钥 |
| `AI_TOKEN_BUDGET_FIELD` | 按服务文档及真实请求验证，填写 `max_tokens` 或 `max_completion_tokens`，固定值 1024 |
| `TELEGRAM_BOT_TOKEN` | Bot Token，仅发送模式需要 |
| `TELEGRAM_CHAT_ID` | 群组实际负数 ID，保留完整负号和数字，仅发送模式需要 |

当前尚未验证用户的第三方 AI 接口。必须先确认非流式 Chat Completions、模型和预算字段，程序不会自动更换协议或省略预算。每个项目独立请求，长度不合格时最多纠正一次；可重试 HTTP 请求最多尝试 3 次，因此会产生相应 API 费用。

```bash
.venv/bin/python trending_digest.py --dry-run
```

该命令真实抓取、调用 AI 并输出预览，会使用 API 配额；无需 Telegram 配置，不改变归档或发送记录。本地不带 `--dry-run` 会明确失败。README 使用 GitHub README API 的 raw 内容，最多 256 KiB，传给模型最多 8000 字符；截断和失败会注明。项目摘要失败时保留位置、链接及原始描述，失败标记随当天简报冻结。

## GitHub Actions 部署

在当前产品仓库默认分支 `main` 提交工作流。仓库维护者须确认 Actions 已启用，组织策略允许官方 Actions 及 `GITHUB_TOKEN` 写入默认分支，分支保护允许普通自动提交。程序不会绕过保护或改用 PAT。

在仓库 Settings → Secrets and variables → Actions 配置：

- Secrets：`AI_API_KEY`、`TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHAT_ID`。
- Variables：`AI_BASE_URL`、`AI_MODEL`、`AI_TOKEN_BUDGET_FIELD`。

先将 Bot 加入实际群组并授予发言权限。通过服务商文档和真实预览确认 AI 请求，再在 Actions 页面选择 `TrendBrief` → `Run workflow`，分支选择默认分支。手动运行会发送真实消息，使用实际启动时的北京时间日期。也可以在已安装并认证的 GitHub CLI 中执行：

```bash
gh workflow run trendbrief.yml
gh run list --workflow trendbrief.yml --limit 5
```

获取真实运行 ID 后执行 `gh run watch RUN_ID --exit-status`；失败时执行 `gh run view RUN_ID --log-failed`。验收需要同时核对成功响应保存的 `message_id`、群组实际收到的全部正文和远端最终状态，再运行一次确认跳过。手动触发不能证明定时触发正常，仍需查看 `schedule` 事件运行记录，以及后两次补跑或跳过结果。

cron 为 `6 6,8,9 * * *`，使用 UTC，对应北京时间 14:06、16:06、17:06。每轮脚本预算 30 分钟，job 超时 40 分钟。延迟任务若实际启动早于当天 14:06，会跳过；跨日不补发旧简报。Actions 可能延迟或丢弃任务，公开仓库长期无活动时定时任务也可能自动禁用，三次触发不能保证当天成功。失败通过 Actions 状态和账号的通知设置报告。

工作流只监听 schedule 和 workflow_dispatch，生成记录的 push 不会触发发送。所有运行共用 `trendbrief-delivery` 并发组，不取消进行中的运行。GitHub 并发组仍可能替换排队任务。发送 job 获得资格后重新 checkout 默认分支最新状态，仅默认分支允许发送。

## 归档、发送与恢复

- `massage/YYYY/MM/DD/Trending.md` 保存当天日期、抓取时间、统计及实际分段正文。目录名固定为 `massage`。
- `.state/YYYY/MM/DD/delivery.json` 保存 SHA-256 群组指纹、正文校验值、冻结正文、状态和已确认的 `message_id`，不保存原始群组 ID 或凭证。指纹不属于秘密加密，不应据此推断状态适合存放其他秘密。
- 初始正文和状态同一提交 push 成功后才发送；每段先提交并 push `sending`，确认远端正文后调用 Telegram；收到有效成功响应后提交并 push `sent` 和 ID，再处理下一段。
- 同日补跑复用冻结正文，仅处理 `pending`；全部 `sent` 时不调用 AI 或 Telegram。归档和状态缺失、损坏、校验不一致或目标变化时终止，不覆盖。
- 连接建立失败或明确拒绝的 429 可以有限重试；明确未发送时回存 `pending` 后失败退出。其他明确拒绝的 4xx 也保留 `pending`，修复配置后可补跑。
- 超时、连接中断、5xx、无效成功响应，以及启动时遗留的 `sending`，均作为结果不确定处理，停止自动发送。不能承诺恰好发送一次。Telegram 已收到但状态 push 失败时，远端仍是 `sending`，后续会转为 `uncertain`。

人工恢复必须按下列顺序执行：

1. 暂时禁用日报 workflow，确认没有运行中的发送 job。
2. `git pull --ff-only` 获取默认分支最新状态，备份当天归档及 JSON。核对日期、目标指纹、分段编号和原文；不要删除文件重新生成。
3. 在目标群组核对结果。确认已送达且取得可核对的 `message_id` 后，仅将对应分段的 `status` 改为 `sent`、`message_id` 改为正整数。确认未送达且获得用户重发授权后，仅将该分段恢复 `pending`、ID 保持 `null`。无法确定时保留 `uncertain`。
4. 保持其他正文、校验和和已确认分段不变。可在已导出 Telegram 配置的终端中验证文件：

   ```bash
   .venv/bin/python -c 'import os; from pathlib import Path; import trending_digest as t; day=t.shanghai_now().date().isoformat(); a,s=t.paths(Path.cwd(),day); t.validate_delivery(t.json_object(s.read_bytes()),day,t.fingerprint(os.environ["TELEGRAM_CHAT_ID"]),a.read_bytes()); print("状态校验通过")'
   ```

   历史日期需将 `day` 明确改成待核实的日期；校验不会向外发送消息。
5. 仅暂存对应状态文件，以 Conventional Commits 提交并普通 push；恢复工作流后通过 workflow_dispatch 继续当天剩余分段。旧日期不会自动补发，无法确认时保留历史记录。

普通 Git push 冲突、权限拒绝或状态写入失败均停止后续发送；不会强制推送。日志只包含脱敏的结构化 `status`、`type`、`message`、`suggestion`，不输出原始 HTTP 异常或接口响应中的凭证。

## 开发检查

```bash
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m py_compile trending_digest.py
git diff --check
```

测试使用真实 Trending 页面最小材料、纯函数边界输入、本地 HTTP 协议服务和 `.local-test/` 下真实 Git bare 仓库。离线测试验证逻辑和失败处理，不证明 AI、Telegram 或 GitHub Actions 可用。当前未执行用户 AI 真实预览、Telegram 群组发送、Actions 手动及定时验收。无 UI，无截图要求。

## 官方接口参考

- [GitHub Trending](https://github.com/trending?since=daily)
- [GitHub README API](https://docs.github.com/en/rest/repos/contents#get-a-repository-readme)
- [Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)
- [Telegram sendMessage](https://core.telegram.org/bots/api#sendmessage)
- [Actions schedule](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
- [GITHUB_TOKEN](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token)
- [Actions concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
- [Actions Secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
