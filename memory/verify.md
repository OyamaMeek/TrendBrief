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
- 未验证：用户 AI 请求及完整 dry-run、Telegram 实际群组收件、GitHub Actions runner 权限、手动与 schedule 事件。缺少安全注入配置，不能把离线协议测试当成外部验收。
