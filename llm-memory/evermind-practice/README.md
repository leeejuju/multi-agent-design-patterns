# EverMemOS Practice

> 基于 [EverMemOS](https://github.com/EverMind-AI/EverMemOS) 的记忆系统实践模块。

## EverMemOS 简介

EverMemOS 是由 EverMind-AI 开源的 **Memory OS**（记忆操作系统），为 AI Agent 提供持久化、可检索的长期记忆能力，同时优化 token 消耗。

### 四层架构（类脑设计）

| 层级 | 功能 | 类比脑区 |
|------|------|----------|
| Agentic Layer | 任务规划与执行 | 前额叶皮层 |
| Memory Layer | 长期存储与召回 | 皮层网络 |
| Index Layer | 关联检索、embedding、KV 搜索 | 海马体 |
| API/MCP Interface | 外部集成接口 | 感觉皮层 |

### 记忆生命周期

1. **Episodic Trace Formation** — 对话流 → MemCell（情景记忆单元、原子事实、前瞻信号）
2. **Semantic Consolidation** — MemCell → MemScene（主题聚合、用户画像更新）
3. **Reconstructive Recollection** — MemScene 引导的上下文重组检索

### 核心能力

- 跨会话长期记忆持久化
- 混合检索（hybrid retrieval）：向量 + 关键词
- 支持群聊、批量操作、对话元数据控制
- LoCoMo 基准 93% 准确率，优于 Mem0 / Zep 等方案
- 提供 REST API，端口 `1995`

## 本模块目标

- 部署并运行 EverMemOS 服务
- 实践记忆存储/检索 API
- 探索与 Agent 集成的记忆增强模式

## 参考链接

- **仓库**: https://github.com/EverMind-AI/EverMemOS (⭐ 3.5k)
- **文档**: [API Reference](https://github.com/EverMind-AI/EverMemOS/blob/main/docs/api_docs/memory_api.md)
- **论文**: [Memory Sparse Attention (MSA)](https://github.com/EverMind-AI/MSA) — 100M token 上下文框架
- **许可**: Apache-2.0

## 状态

🚧 **开发中** — 示例代码与实验内容将陆续补充。
