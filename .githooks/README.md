# Git Hooks

本项目使用 `.githooks/` 目录管理 Git hooks，确保所有提交信息符合
[Conventional Commits](https://www.conventionalcommits.org/) 规范。

## 启用 hooks

克隆仓库后，执行以下命令将 Git 的 hooks 路径指向本目录：

```bash
git config core.hooksPath .githooks
```

## 已有 hooks

### commit-msg

校验提交信息格式，规则如下：

| 规则 | 说明 |
|------|------|
| 必填 `<type>` | feat / fix / docs / style / refactor / test / chore / perf / ci / build / revert |
| 可选 `(<scope>)` | 模块名，用括号包裹 |
| `: ` 分隔符 | type(scope) 后必须跟英文冒号 + 一个空格 |
| 描述不为空 | 冒号空格后至少一个字符 |
| 描述不以句号结尾 | 避免末尾 `.` |

**合法示例：**
```text
feat: add commit-msg validation hook
docs(rag): update retrieval module README
fix: resolve empty result crash in vector search
refactor(memory): extract storage layer
chore: update pyproject.toml dependencies
```

**自动放行：** `Merge` 和 `Revert` 开头的提交信息不做校验。
