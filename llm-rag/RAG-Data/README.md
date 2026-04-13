# RAG-Data

RAG 实验所用的数据集存放目录。

## 数据集组成

### RAG-Challenge-dataset

来源于 [Enterprise RAG Challenge 2](https://github.com/IlyaRice/RAG-Challenge-2)（IBM 主办的企业级 RAG 竞赛）。

- 选取了 **10 篇超过 100 页的长文档**（公司年度报告 PDF）
- 每篇文档可达数百甚至上千页，包含大量表格、图表等复杂排版
- 适用于测试长文档场景下的 PDF 解析、文本分块、向量检索与问答能力

> 当前仅包含 RAG-Challenge-2 的部分数据集，后续可扩展其他数据源。

## 目录结构

```
RAG-Data/
└── RAG-Challlenge-dataset/   # Enterprise RAG Challenge 2 数据集
```

## 相关链接

- [IlyaRice/RAG-Challenge-2](https://github.com/IlyaRice/RAG-Challenge-2) — 竞赛冠军方案（MIT License）
- [How I Won the Enterprise RAG Challenge](https://abdullin.com/ilya/how-to-build-best-rag/) — 冠军方案详解