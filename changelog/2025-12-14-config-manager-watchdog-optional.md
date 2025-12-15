# 2025-12-14 配置热更新依赖降级（watchdog 可选）

- 修改 `src/config_manager.py`：
  - 将 `watchdog` 改为可选依赖（import 失败时不阻断模块加载）；
  - 在未安装 `watchdog` 时，`EnhancedConfigManager.start_file_monitoring()` 会打印 warning 并跳过文件监控。

兼容性：
- 已安装 `watchdog` 的环境行为不变；
- 未安装 `watchdog` 的环境可继续使用配置管理能力（仅缺少热更新监听）。
