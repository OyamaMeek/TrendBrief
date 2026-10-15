# 验证要求

- unittest 先失败再实现；真实页面材料注明来源与采集时间。
- 检查榜单原顺序/前十、字段缺失、异常结构、Unicode、100～150 字、日期/调度。
- 检查损坏状态、指纹、校验和、孤立文件、sent/sending/uncertain、补跑冻结正文。
- 真实本地 bare Git 仓库验证提交/push/远端确认，以及 push 失败停止后续发送。
- pip check、unittest、ruff check、ruff format --check、py_compile、git diff --check。
- 无 UI，不进行截图。离线测试不能作为 AI/Telegram/GitHub Actions 的真实验收。

## 已执行证据

- Python 3.13.16 安装在项目忽略目录 .runtime，虚拟环境 .venv；固定依赖安装及 pip check 成功。
- 首轮纯函数和随后 HTTP、状态测试均先出现缺失实现失败，再通过；独立审查发现的慢速 HTTP 问题补充失败回归测试后修复。
- 真实 GitHub Trending HTTP 200，10 个项目顺序校验通过，10 个 README 获取成功，8 个按 8000 字符限制明确标注截断。
- 本地真实 HTTP 验证协议、429、连接中断和硬截止；真实 bare Git 仓库验证初始提交、分段确认、恢复、commit/push/回存失败。
- 完整 unittest 套件 29 项通过；Ruff check、format --check、py_compile 和 pip check 通过。
- 工作流 YAML 由系统 Ruby Psych 解析，核对事件、cron、并发组、权限、40位 SHA，并对各 run 步骤执行 bash -n。
- 用户 AI 接口真实请求已验证：max_tokens=1024、finish_reason=stop、146 字中文说明；本地 .env 配置校验通过，已补齐预算字段。
- 完整真实 dry-run 退出码 0：10 项中文摘要全部成功，长度依次为 145、144、133、131、137、149、133、138、146、112；排名 1～10，失败标记 0。
- GitHub 认证后核实 Actions 已启用、工作流 active；用户明确授权后配置三项 Secrets 和三项 Variables，API 已核对名称及预算参数。
- 真实 workflow_dispatch 运行 38728721857 成功：runner 全部检查通过，10 条摘要无失败，1 段确认 sent、message_id=46，归档与状态普通 push 至 main，最终提交 52d65ba。Bot 为目标 supergroup 管理员且有发言权限；用户确认收到完整简报。
- 第二次真实运行 38729696123 成功；日志明确当天已确认送达，不调用 AI 或 Telegram。远端无新增正文或状态提交。
- 移除新推送中的抓取时间：回归测试先失败后通过；完整套件 30 项通过，Ruff、格式、编译通过。使用真实十项目及已生成摘要重排，1 段 2487 UTF-16 units、无抓取时间，未再次调用 AI 或 Telegram。
- 最新代码提交 9f1b40f 对应真实运行 38730142089 成功：verify job 116405628676 明确输出 Ran 30 tests、All checks passed；deliver job 116405783493 明确输出 skipped，无需调用 AI 或 Telegram。
- 已发送当天归档及状态保持冻结并校验通过。实际 schedule 事件尚未验收。
