# mathlab/core/ Bug 追踪清单

> 生成时间: 2026-06-22
> 修复方法: 修复后将 `[ ]` 改为 `[x]`

---

## P0 致命

- [x] **#1** `ai_manager.py:171` — Tool call 参数从未 JSON 反序列化，所有 Function Calling 工具静默失效 ✅ 2026-06-22
- [x] **#2** `ai_manager.py:226,255` — `QThread.wait()` 无超时，网络慢时冻结 GUI ✅ 2026-06-22

## P1 高危

- [ ] **#3** `ai_manager.py:253-270` — 旧 QThread worker 未 `deleteLater()`，线程资源泄漏
- [ ] **#4** `ai_manager.py:265-267` — 对话记忆不记录 Tool Call 结果
- [ ] **#5** `ai_tools.py:123` — `AGENT_TRANSFER_TOOL` 缺少 `planner`，教研组长不可达
- [ ] **#6** `sandbox.py:113-114` — `stdin.write()` 无 try/except，子进程崩溃时 BrokenPipeError
- [ ] **#7** `sandbox.py:164-187` — `terminate()` 不调用 wait() 也不置空 self.process
- [ ] **#8** `sandbox.py:42-77` — `_monitor_watchdog` 死代码，逻辑内联在 run_code 中
- [ ] **#9** `python_repl.py:44-48` — 隔离模式下 terminate→run_code 竞态条件
- [ ] **#10** `ipc_server.py:37` — 8192 字节 UDP 截断，大数据变量静默丢失
- [ ] **#11** `ipc_server.py:41-50` — 无 seq 字段的 sync_var 首次后被全部丢弃
- [ ] **#12** `ipc_client.py:16` — UDP socket 从未关闭，文件描述符泄漏
- [ ] **#13** `cas_provider.py:17-29` — `_load_sympy` 双重检查锁有缺陷
- [ ] **#14** `octave_bridge.py:237-238` — 双引号字符串保护必然 IndexError
- [ ] **#15** `octave_bridge.py:250` — `*→@` 无界替换破坏字符串和注释
- [ ] **#16** `octave_bridge.py:135` — `fzero` 传标量给需要 bracket 的函数
- [ ] **#17** `error_manager.py:127-144` — sys.excepthook 中弹 Qt 对话框
- [ ] **#18** `plugin_manager.py:46-47` — `__init__.py` 创建失败时静默
- [ ] **#19** `geometry_engine.py:364-365` — 线段交点忽略线段边界

## P2 中危

- [ ] **#20** `ai_manager.py:1` — `import numpy` 无 try/except
- [ ] **#21** `ai_manager.py:37` — `QUIZ_GENERATOR_SCHEMA` 重复定义死代码
- [ ] **#22** `sandbox.py:92-99` — stderr 未重定向
- [ ] **#23** `sandbox.py:123` — except Exception: pass 吞掉诊断信息
- [ ] **#24** `sandbox.py:24-26` — 实例队列分配后从未使用
- [ ] **#25** `sandbox.py:192-224` — SandboxManager 非线程安全
- [ ] **#26** `sandbox_script.py:46,75` — 无输出大小限制
- [ ] **#27** `python_repl.py:26-28` — update_namespace() 对沙箱执行无效
- [ ] **#28** `ipc_server.py:21` — _var_sequence_tracker 无界增长
- [ ] **#29** `ipc_client.py:22` — _seq_counter 非线程安全
- [ ] **#30** `jupyter_manager.py:46-51` — 端口 TOCTOU 竞态
- [ ] **#31** `jupyter_manager.py:175-196` — 进程终止后不关闭管道
- [ ] **#32** `jupyter_manager.py:188-194` — proc.terminate() 未包裹 try/except
- [ ] **#33** `cas_provider.py:120` — 右侧符号未缓存
- [ ] **#34** `cas_provider.py:156-167` — definite_integral 调 float 无保护
- [ ] **#35** `num_engine.py:5-12` — _finite_diff 高阶数值不稳定
- [ ] **#36** `octave_bridge.py:262` — `~→not` 正则无词边界
- [ ] **#37** `octave_bridge.py:54` — `__builtins__={}` 破坏内建函数无提示
- [ ] **#38** `async_workers.py:96-108` — TaskManager 非线程安全
- [ ] **#39** `command_manager.py:108-116` — execute 异常后仍返回 True
- [ ] **#40** `error_manager.py:186-187` — 恢复路径无数据校验
- [ ] **#41** `error_manager.py:153` — 自动保存在系统临时目录
- [ ] **#42** `geometry_engine.py:562` — Polygon.deserialize 裸访问 data['coordinates']
- [ ] **#43** `geometry_engine.py:382-410` — 交点求解器对 None 系数崩溃
- [ ] **#44** `geometry_engine.py:1235-1236` — validate_commands 拒绝合法操作
- [ ] **#45** `geometry_engine.py:773-787` — ConicSection.to_latex 负系数渲染错误
- [ ] **#46** `canvas_tracker.py:73` — 零长度线段显示 null
- [ ] **#47** `canvas_tracker.py:46-49` — objects 为 None 时崩溃
- [ ] **#48** `animation.py:41-42` — 重复动画覆盖引用
- [ ] **#49** `extension_api.py:54-57` — removeDockWidget 无 hasattr 保护
- [ ] **#50** `extension_api.py:41-42` — python_repl 可能为 None
- [ ] **#51** `geogebra_engine.py:85-97` — GeoCircle 双重初始化 parents
- [ ] **#52** `geogebra_engine.py:70-83` — 水平线未简化显示
- [ ] **#53** `smart_guides.py:27` — 逻辑阈值缩放时行为不一致
- [ ] **#54** `context_assembler.py:25` — 画布空检查依赖硬编码 JSON
- [ ] **#55** `prompt_manager.py:53-58` — build_user 未捕获 ValueError

## P3 低危

- [ ] **#56** `geometry_engine.py:262-265` — Line.to_latex 浮点 == 比较 1/-1
- [ ] **#57** `geometry_engine.py:1070-1071` — Locus trail pop(0) O(n)
- [ ] **#58** `ai_manager.py:107,109,136` — _is_cancelled 无内存屏障
- [ ] **#59** `memory_manager.py:39` — 中文字符计数过快裁剪
- [ ] **#60** `memory_manager.py:39-44` — 裁剪可能保留两条同角色消息
- [ ] **#61** `sandbox_script.py:77` — except BaseException 捕获 KeyboardInterrupt
- [ ] **#62** `sandbox_script.py:50` — 全局 safe_globals 变更
- [ ] **#63** `python_repl.py:90` — jedi.Interpreter 接收 module 而非 dict
- [ ] **#64** `ipc_server.py:42-43` — None key 污染 tracker
- [ ] **#65** `ipc_server.py:62-64` — stop() 无超时等待
- [ ] **#66** `ipc_client.py:25` — UDP 无 ACK/重试机制
- [ ] **#67** `jupyter_manager.py:50` — SO_REUSEADDR 在 bind 后无效
- [ ] **#68** `signals.py:3-12` — 信号无 parent 内存泄漏
- [ ] **#69** `error_manager.py:33-35` — exc_type 为 None 时 AttributeError
- [ ] **#70** `smart_guides.py:72-74` — 角度计算坐标系不确定
- [ ] **#71** `algo_animator.py:120-121` — 冒泡排序描述值顺序反
- [ ] **#72** `algo_animator.py:661-670` — K-means 空簇分支 centers 不一致
- [ ] **#73** `geogebra_engine.py:28-31` — notify_update 无循环保护
- [ ] **#74** `geogebra_engine.py:183-195` — 缺少 add_circle/add_line API
- [ ] **#75** `geometry_helpers.py:27` — 极端缩放硬编码阈值
- [ ] **#76** `plugin_manager.py:50-52` — inspect 可能误拾外部类
- [ ] **#77** `plugin_manager.py:77-91` — unload_all cleanup 失败仍删 API
- [ ] **#78** `context_assembler.py:11` — 直接访问 PromptManager._prompts 私有属性
