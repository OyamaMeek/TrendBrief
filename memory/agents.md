# 开发环境

- 本次 Codex 使用 Ponytail full 与 test-driven-development；复用现有 httpx，不新增产品依赖。
- 本地与 Actions 已配置 DeepSeek 官方 https://api.deepseek.com、deepseek-flash，显式关闭思考并使用 max_tokens=1024；用户更新官方密钥后完成真实十项目预览，Secret 加密上传、变量回读成功。
- 用户已确认当前 OyamaMeek/TrendBrief 根目录作为产品目录，保留 AGENTS.md 和 Claude.md。
- Python 3.13、httpx、BeautifulSoup、unittest、Ruff；GitHub Actions 定时执行。
- 用户在本地 .env 提供配置并明确授权上传 Actions；凭证仅用于认证或加密上传，不打印、不提交。
- 部署使用 Git credential helper 认证官方 GitHub API；本地辅助脚本和 python-dotenv/PyNaCl 仅在忽略目录中，不增加产品依赖。
- Telegram 话题发送使用现有 httpx 和 Bot API message_thread_id；本地与 Actions Variable TELEGRAM_MESSAGE_THREAD_ID 均配置为 43。
