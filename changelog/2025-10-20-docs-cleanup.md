# 文档清理与重构记录（2025-10-20）

- 变更人: Cascade
- 作用范围: `docs/`
- 目标: 只保留中文版本、删除英文版本、重构设计说明文档（更优雅、便于教学）

## 变更摘要
- 移除英文文档（归档而非直接删除）：
  - `docs/design/bookmark_best_practices.md` → `changelog/removed/bookmark_best_practices.md`
- 重构与增强：
  - `docs/DESIGN.md`：追加“教学导读/术语速览/5分钟上手/常见问题/设计取舍（KISS）”等教学友好章节。
- 保留/复核：
  - `docs/quickstart_zh.md`、`docs/design/ml_design_zh.md`、`docs/design/system_architecture.md`、`docs/guides/development_guide.md`、`docs/technical_report.md` 均为中文，未做删除，仅复核。

## 影响与兼容性
- 链接影响：若外部引用了 `docs/design/bookmark_best_practices.md`，请更新指向或改为引用 `docs/DESIGN.md` 的相关章节。
- 功能影响：纯文档调整，不影响代码与命令行使用。

## 回滚方案
- 可从 `changelog/removed/bookmark_best_practices.md` 恢复英文文档；
- `docs/DESIGN.md` 可通过 Git 回滚到变更前版本。
