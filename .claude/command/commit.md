# Commit 命令规范

## 快速提交

```bash
git add .
git commit -m "<type>(<scope>): <description>"
git push origin main
```

## 提交前检查清单

- [ ] 代码已格式化 (`uv run ruff format .`)
- [ ] 通过 Lint 检查 (`uv run ruff check .`)
- [ ] 相关测试已通过
- [ ] 提交信息符合规范
- [ ] 已更新相关文档

## 常用提交类型

```bash
# 新功能
feat: 添加 XXX 功能

# Bug 修复
fix: 修复 XXX 问题

# 文档更新
docs: 更新 README 说明

# 代码重构
refactor: 重构 XXX 模块

# 依赖更新
chore: 更新依赖版本
```
