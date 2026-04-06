# Git 提交规则

## 提交信息规范

本项目遵循 [Conventional Commits（约定式提交）](https://www.conventionalcommits.org/) 规范。

### 提交格式

```
<type>(<scope>): <description>

[可选的正文]

[可选的脚注]
```

### Type 类型说明

| type       | 说明                         | 示例                                       |
| ---------- | ---------------------------- | ------------------------------------------ |
| `feat`     | 新增功能或代码特性           | `feat: 添加记忆检索 API 接口`              |
| `fix`      | 修复 Bug                     | `fix: 修复向量搜索结果为空的问题`          |
| `docs`     | 仅文档变更（README、注释等） | `docs: 创建 evermemos 模块的 README 文件`  |
| `style`    | 代码格式调整（不影响逻辑）   | `style: 统一代码缩进格式`                  |
| `refactor` | 代码重构（不新增功能或修复） | `refactor: 重构数据库连接模块`             |
| `test`     | 测试相关                     | `test: 添加记忆存储的单元测试`             |
| `chore`    | 构建、依赖、配置等杂项       | `chore: 更新 pyproject.toml 依赖版本`      |
| `perf`     | 性能优化                     | `perf: 优化向量检索的查询速度`             |
| `ci`       | CI/CD 配置变更               | `ci: 添加 GitHub Actions 工作流`           |
| `build`    | 构建系统或外部依赖变更       | `build: 升级 Python 版本至 3.12`           |
| `revert`   | 回退之前的提交               | `revert: 回退 "feat: 添加记忆检索 API"`    |

### Scope（作用域）

Scope 是可选的，用于描述变更所影响的模块，例如：

- `docs(evermemos)`: evermemos 模块的文档变更
- `feat(mem0)`: mem0 模块的新功能
- `fix(zep)`: zep 模块的 Bug 修复
- `refactor(multi-agent-memory)`: multi-agent-memory 模块的重构

### 文档类操作规范

针对 README 等文档文件，**统一使用 `docs` 类型**：

| 操作         | 提交信息示例                                           |
| ------------ | ------------------------------------------------------ |
| **创建**文档 | `docs: 创建 evermemos 模块的 README 文件`              |
| **更新**文档 | `docs(evermemos): 更新 README 中的架构说明`            |
| **修正**文档 | `docs(evermemos): 修正 README 中的错误链接`            |
| **删除**文档 | `docs: 移除 multi-agent-memory 中过期的 README`        |
| **翻译**文档 | `docs(evermemos): 添加 README 的中文翻译`              |

### 描述（Description）要求

1. **使用中文**描述变更内容
2. 简洁明了，不超过 50 个字符
3. 使用**动词开头**：创建、添加、更新、修复、移除、重构、优化……
4. **不要**以句号结尾

### 完整示例

```bash
# 功能相关
feat: 添加基于 Qdrant 的向量记忆存储
feat(mem0): 实现记忆搜索的 BM25 索引功能

# 文档相关
docs: 创建项目根目录 README 文件
docs(zep): 更新 Zep 模块的部署说明
docs: 为所有子模块添加 README 文件

# 修复相关
fix(evermemos): 修复记忆重复存储的问题

# 重构相关
refactor: 将数据库操作从模型文件中分离

# 杂项
chore: 更新 .gitignore 规则
chore: 添加 .env.example 模板文件
```

## 代码操作约束

### 修改代码
- 修改前必须理解现有代码逻辑
- 保持代码风格一致
- 修改后确保测试通过

### 删除代码
- 确认代码不再被使用
- 删除前搜索引用位置
- 删除后测试相关功能

### 新增代码
- 遵循项目现有架构模式
- 添加必要的类型注解
- 复杂逻辑需添加注释

### 提交前检查
```bash
# 格式检查
uv run ruff format .

# Lint 检查
uv run ruff check .

# 运行测试
uv run pytest -q
```
