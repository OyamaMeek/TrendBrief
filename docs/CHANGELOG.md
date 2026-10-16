# 开发记录

## [2026-10-16 15:42] 增加定时漏跑后的补跑机会

- **需求/问题描述**：
  > 用户报告定时未执行并要求修复。

- **实际实现的功能与改动**：
  - 已核实 Actions enabled、workflow active、默认分支及原 cron 正确；14:06 未生成 schedule 运行，具体原因未获 GitHub 提供。
  - 保留每日北京时间 14:06、16:06、17:06，增加 14:36、16:36、17:36；复用当天成功跳过和串行发送机制。该调整缓解漏跑，不保证平台调度可用。
  - YAML 补跑检查先失败后通过；30 项 unittest、pip check、Ruff、格式、编译、工作流 YAML/shell 与 git diff 检查通过。实际 schedule 尚未验收。
  - 真实 Actions 38869017800 成功补发 2026-10-16 简报，Telegram 确认 message_id=51，远端状态 sent，归档校验通过；再次运行 38869396294 成功跳过，日志确认未调用 AI 或 Telegram。

- **涉及文件**：
  - `.github/workflows/trendbrief.yml`、`README.md`、`memory/plan.md`、`memory/progress.md`、`memory/verify.md`、`docs/CHANGELOG.md`
  - 补跑配置检查复用忽略目录 `.local-test/validate_workflow.rb`，未加入 CI。

- **Git 提交**：`1eb4273 fix: add half-hour retries for missed digest schedules`，已普通推送至 origin/main；今日发送最终状态提交为 `431fd02 docs: persist TrendBrief delivery 2026-10-16`。真实验收结果通过后续文档提交补记。

---

## [2026-10-15 19:13] 实现开源趋势简报命令行工具

- **需求/问题描述**：
  > 按 Claude.md 开发；用户确认当前仓库根目录为产品目录。

- **实际实现的功能与改动**：
  - 按 Today 页面顺序提取前 10 名，读取 README 并限制体积，独立生成中文摘要与失败说明。
  - 按 UTF-16 长度分段，生成 massage 日期归档；实现 Git 持久化及 pending/sending/sent/uncertain 状态，失败保守恢复。
  - 配置北京时间三次调度的 Actions 工作流，官方 Actions 固定已核实 SHA；补齐配置、部署及人工恢复说明。
  - 独立审查发现慢速 HTTP 可能突破总预算；增加 CLI 硬截止及真实慢速 HTTP 回归测试。
  - 测试/验证：Python 3.13 固定依赖安装、pip check、29 项 unittest、Ruff、编译检查及工作流 YAML/shell 校验通过；真实 Trending 与 10 个 README 请求成功。详细结果见 memory/verify.md。
  - 未执行用户 AI、Telegram 群组及 Actions 手动/定时真实验收，缺少安全注入配置；未认证权限接口返回 401，尚未确认工作流写入策略。

- **涉及文件**：
  - trending_digest.py、tests/test_digest.py、tests/test_network.py、tests/test_delivery.py、tests/fixtures/
  - requirements.txt、requirements-dev.txt、pyproject.toml、.gitignore、.env.example
  - .github/workflows/trendbrief.yml、README.md、memory/、docs/CHANGELOG.md

- **Git 提交**：`b6369cb feat: implement daily Trending digest and durable Telegram delivery`，已普通推送至 origin/main；提交结果通过后续文档提交补记。

---

## [2026-10-15 19:48] 部署验收并移除推送正文的抓取时间

- **需求/问题描述**：
  > 用户提供本地配置并要求部署，明确授权上传指定 Secrets/Variables；收到简报后要求移除抓取时间。

- **实际实现的功能与改动**：
  - 验证用户 AI 的非流式接口与 max_tokens=1024，补齐本地预算字段；完成真实 dry-run，10 条摘要全部成功。
  - 通过 GitHub 公钥加密配置三项 Secrets，写入三项 Variables；秘密值未提交仓库。
  - 首次 Actions 运行 38728721857 成功发送完整简报，Telegram 确认 message_id=46，最终状态保存至 main，用户确认收到；第二次运行 38729696123 成功跳过。
  - 新推送项目正文移除抓取时间，归档头部保留来源时间；已确认发送的历史正文及状态保持冻结。
  - 测试/验证：30 项 unittest、Ruff、格式及编译检查通过；真实材料重排后 1 段、2487 UTF-16 units、无抓取时间。最新代码的 Actions 运行 38730142089 全部成功并正确跳过已发送简报。实际 schedule 事件仍待验收。

- **涉及文件**：
  - trending_digest.py、tests/test_digest.py、README.md
  - memory/plan.md、memory/progress.md、memory/verify.md、memory/gotchas.md、docs/CHANGELOG.md
  - 本地忽略文件 .env 仅补齐预算字段，不提交；运行生成 massage/2026/10/15/Trending.md 和 .state/2026/10/15/delivery.json，由 Actions 提交。

- **Git 提交**：`9f1b40f fix: remove fetch timestamps from Telegram digest entries`，已推送 origin/main；实际发送状态提交为 `52d65ba docs: persist TrendBrief delivery 2026-10-15`。本记录与最新 Actions 证据通过后续文档提交补记。

---
