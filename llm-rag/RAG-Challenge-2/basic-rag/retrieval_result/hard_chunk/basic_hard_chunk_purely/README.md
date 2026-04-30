# Basic Hard Chunk Purely 测试汇总

本目录包含了基于纯文本硬切分（Hard Chunk）的 RAG 检索与问答实验记录和生成数据。针对 5 个测试 PDF 文档，分别测试了两种不同粒度的切分策略，以验证基础硬切分在复杂财报问答场景下的表现。

## 目录结构与实验配置

- **`chunk-1000-overlap-200-5-files/`**
  采用 `chunk_size=1000`, `chunk_overlap=200` 的配置。该目录 README 主要复盘了单纯硬切分方案下暴露的典型缺陷（如由于缺乏 metadata 过滤导致的跨文档检索混淆、硬截断引发的上下文丢失等）。

- **`chunk-1500-overlap-300-5-files/`**
  采用 `chunk_size=1500`, `chunk_overlap=300` 的配置。该目录 README 详细记录了针对 5 个具体问题的测试 case。测试表明，尽管在更大的 Chunk 尺寸下模型可能偶尔猜对（如 Boolean 类型判断），但实际检索召回（Recall）的内容往往与正确答案（Evidence）不匹配，主要依赖字面语义的弱相关（Cosine Similarity 偏低）。

## 核心实验结论

1. **向量检索必须辅以元数据过滤（Metadata Filtering）**：在年报问答等多文档场景中，直接全库检索会导致极其严重的张冠李戴（比如问 A 公司的财务数据却召回 B 公司的内容）。必须在切分时注入 `company`, `ticker` 或 `doc_id` 等 metadata。
2. **硬切分破坏文档语义结构**：固定字数切分会对表格、跨页段落产生破坏，也缺乏章节层级概念，导致关键指标、年份或单位分散在不同 Chunk，LLM 极易被污染的或不完整的上下文误导。
3. **缺少检索置信度控制**：低相似度的强行召回会将错误信息塞给 LLM，导致模型基于错误事实进行推导。

## 实验总结与下一步计划

**本目录的纯硬切分（Hard Chunk）实验到此结束。**

结论表明，单纯依赖固定大小的文本分块无法满足复杂金融年报（RAG Challenge）的高质量问答需求。因此就不再进行 precision 以及 recall 等参数的分析了，下一步将转向更为精细的**结构化解析与切分方案**（如结合 MinerU、RAGFlow 等工具），通过保留文档层级、表格等 Markdown 语义特征，并引入如前置路由过滤、Parent Document Retrieval 与 Reranking 等机制，从根本上提升系统的检索能力。
