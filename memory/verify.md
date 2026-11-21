# 验证要求

- DeepSeek：真实本地 HTTP 检查 deepseek-flash 请求关闭思考，首轮与长度纠正均携带 max_tokens=1024、Bearer 认证和非流式参数；其他模型不新增 DeepSeek 参数。完整 unittest、pip check、Ruff、格式、编译、工作流 YAML/shell、git diff 检查。官方密钥到位后使用产品 summarize 和 --dry-run 验证实际返回与 100～150 字限制，再加密配置 Actions 并回读非秘密变量；不把本地 HTTP 测试视作官方验收。

- 话题发送：真实本地 HTTP 检查 payload 的 message_thread_id=43，未配置时字段缺省；真实 Git 状态检查不同话题指纹隔离、无效配置拒绝和同日已发送跳过。更新工作流 YAML 校验并运行完整检查。真实 Telegram 确认消息返回的 chat.id 与 message_thread_id 必须分别匹配本地配置和 43；Actions Variable 回读为 43。

- unittest 先失败再实现；真实页面材料注明来源与采集时间。
- 检查榜单原顺序/前十、字段缺失、异常结构、Unicode、100～150 字、日期/调度。
- 检查损坏状态、指纹、校验和、孤立文件、sent/sending/uncertain、补跑冻结正文。
- 真实本地 bare Git 仓库验证提交/push/远端确认，以及 push 失败停止后续发送。
- pip check、unittest、ruff check、ruff format --check、py_compile、git diff --check。
- 无 UI，不进行截图。离线测试不能作为 AI/Telegram/GitHub Actions 的真实验收。
- 定时补跑：YAML 解析检查 UTC 06/08/09 时的 06/36 分、并发组、权限、SHA 及 shell 语法；完整测试确认同日已发送跳过和不确定发送停止。手动验收与实际 schedule 验收分别记录。

## 已执行证据

- 2026-11-21 DeepSeek：test_ai_length_correction_and_explicit_budget 的 deepseek-flash 子测试先因缺少 thinking.disabled 失败，实现后通过；检查首轮和纠正请求的模型、Bearer、非流式及 1024 tokens 参数，普通模型不新增 thinking。实际长度反馈测试也先失败再通过。全部 32 项 unittest、pip check、Ruff、格式、py_compile、工作流 YAML/shell 和 git diff 检查重跑通过。
- 用户更新官方密钥后，产品 summarize 真实返回 114 字、finish_reason=stop；完整 --dry-run 最终 10 条摘要全部通过、失败 0，字数依次为 114、105、145、102、110、111、104、123、113、117。真实预览和日志位于忽略目录 .local-test/dry-run.md、dry-run.log。未写入归档或发送状态。
- Actions 已配置官方地址、deepseek-flash、max_tokens，三项 Variables 回读匹配；AI_API_KEY 使用仓库公钥加密上传，元数据 updated_at=2026-11-21T03:44:07Z，话题 43 保持不变。上传前确认 workflow 无运行或排队任务。证据 .local-test/deepseek-deployment.json 不含秘密。未手动触发 Actions 或发送 Telegram 消息；DeepSeek 在 runner 中的实际定时运行尚未验收。

- 2026-10-30 话题发送：路由与指纹测试因尚无话题参数失败，无效话题 0 被错误接受的断言失败；实现后完整 32 项 unittest 通过。pip check、Ruff check、format --check、py_compile、工作流 YAML/shell、git diff --check 通过。
- 本地 TELEGRAM_MESSAGE_THREAD_ID=43；GitHub Actions Variable 写入后 GET 回读为 43。产品 Telegram.send 真实发送确认消息，返回 message_id=135、message_thread_id=43、is_topic_message=true，chat.id 与截图及本地配置一致；证据存于忽略目录 .local-test/topic-confirmation.json。未手动触发完整简报，不把本地确认作为下一轮 Actions 定时验收。

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
- 2026-10-16：补跑 YAML 检查先因 missing half-hour retries 失败，修改 cron 后通过；30 项 unittest、pip check、Ruff、格式、编译及 git diff 检查通过。Actions 设置已重新核对，无禁用或配置缺失；漏触发具体原因未获 GitHub 提供。
- 配置提交 1eb4273 已推送；真实运行 38869017800 的 verify/deliver 均成功，日志确认 1/1 段送达并保存到远端；状态 message_id=51、sent，默认分支最终归档提交 431fd02，本地 validate_delivery 校验通过。第二次运行 38869396294 的 verify/deliver 均成功，job 116869803770 日志明确 skipped、无需调用 AI 或 Telegram。以上均为 workflow_dispatch，尚无 schedule 验收证据。
