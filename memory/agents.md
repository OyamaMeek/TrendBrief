# 开发环境

- Codex 使用 Ponytail full、executing-plans 与 test-driven-development 方式实施。
- 用户已确认当前 OyamaMeek/TrendBrief 根目录作为产品目录，保留 AGENTS.md 和 Claude.md。
- Python 3.13、httpx、BeautifulSoup、unittest、Ruff；GitHub Actions 定时执行。
- 用户在本地 .env 提供配置并明确授权上传 Actions；凭证仅用于认证或加密上传，不打印、不提交。
- 部署使用 Git credential helper 认证官方 GitHub API；本地辅助脚本和 python-dotenv/PyNaCl 仅在忽略目录中，不增加产品依赖。
