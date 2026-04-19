# Basic RAG 检索问题复盘

## 1. 检索出来的结果

当前系统对 5 个问题做了 Top 5 检索，并将检索结果塞入 LLM prompt 然后我去看了一下结果。

观察到的结果，RAG 的结果似乎非常受文档大小的影响：

| 问题 | 期望文档/公司 | 实际主要召回文档 | 结果 |
|---|---|---|---|
| Mercia Asset Management PLC 是否提到并购 | Mercia Asset Management PLC | `e2b19d2cc2ccab2fd9022326b56b38fb0e772e73` | 召回到 CrossFirst Bank 相关内容，回答 `false` |
| Tradition 的 Operating margin (%) | Tradition | `e2b19d2cc2ccab2fd9022326b56b38fb0e772e73` | 没召回 Tradition，回答 `N/A` |
| TSX_Y 是否宣布股票回购计划 | Yellow Pages / TSX:Y | `e2b19d2cc2ccab2fd9022326b56b38fb0e772e73` | 召回到其他公司的 share repurchase 内容，回答 `true` |
| CrossFirst Bank 最大单笔高管薪酬支出 | CrossFirst Bank | `e2b19d2cc2ccab2fd9022326b56b38fb0e772e73` | 召回到高管履历和财务页，但没有薪酬表，回答 `N/A` |
| Holley Inc. 是否提到并购 | Holley Inc. | `e2b19d2cc2ccab2fd9022326b56b38fb0e772e73` | 召回到 CrossFirst/Central acquisition，错误回答 `true` |

一个特别扯的地方是：不同的问题，全都召回了同一个文档，虽然一开始我是不太想去做 Hard Chunk 的，但是没有想到这么夸张：

```text
e2b19d2cc2ccab2fd9022326b56b38fb0e772e73
```

检索分数也不高，很多 Top 5 的 cosine similarity 大约在：

```text
0.50 - 0.58
```

这说明当前召回只是弱相关，不是强命中。

## 2. 存在的问题

### 2.1 检索范围错误

现在是全库向量检索：

```sql
ORDER BY embedding <=> query_vector
LIMIT top_k
```

但问题本身通常指定了公司，例如：

```text
Mercia Asset Management PLC
Tradition
Holley Inc.
CrossFirst Bank
TSX_Y
```

当前检索没有先限定公司或文档，因此很容易从错误公司中召回语义相似 chunk。

### 2.2 缺少公司名

例如：

```text
TSX_Y
```

实际对应 Yellow Pages / TSX:Y，但是因为是硬切片性质的测试，就没有加上 multi-agent-design-patterns 里面的公司名称，而是纯原始的直接硬切

### 2.3 metadata 不足以支持过滤

当前 chunk 里主要有：

```text
doc_id
source
label
page
```
这当然是我最初纯 vibe 出来的嘛，没有进行仔细地想一下，又忘了之前怎么做的

其实事实上应该采取某一种手段，把一些元数据给搞出来。但还是那句话，这只是实验性的，因此我就没有去做。

接下来的 Recall 和忠诚度报告测试我也不做了，因为 HIT 是 0，我就不做了

```text
company
ticker
year
filename
doc_type
```

导致查询时无法写出类似：

```sql
WHERE metadata->>'company' = 'Holley Inc.'
```

### 2.4 估计是纯硬切片造成的一个上下文的大量缺失和混淆

当前 parser 基本是按固定字符长度切片。

问题：

- 表格容易被切断
- 指标名、年份、单位、数值可能分散在不同 chunk
- 高管履历和高管薪酬表容易混淆
- 目录页、页眉页脚、说明性文本可能污染 embedding


### 2.5 LLM 被错误上下文带偏

例如 Holley Inc. 的并购问题，召回内容是 CrossFirst/Central acquisition。

LLM 看到 merger/acquisition 证据后回答 `true`，但这个证据属于错误公司。

这说明 prompt 无法修复错误召回。

## 3. 可能的原因

### 3.1 向量检索缺少前置过滤

向量检索只负责语义相似。

如果问题问的是：

```text
Did Holley Inc. mention acquisitions?
```

全库检索会优先找和 `acquisitions` 语义最接近的文本，而不是先找 Holley Inc. 的文档。

因此最核心的问题是：

```text
先找公司/文档，再做向量检索
```

而不是：

```text
直接全库向量检索
```

### 3.2 chunk 组织粒度不适合年报问答

企业年报问题经常依赖页级、表格级、章节级信息。

固定长度 chunk 对这些结构不敏感。

### 3.3 metadata 没有承担检索过滤职责

现在 metadata 只存了 page。

它还应该承担：

```text
company
ticker
year
doc_type
filename
```

这些字段用于先过滤候选文档。

### 3.4 检索结果没有阈值判断

如果 Top 1 similarity 只有 0.55 左右，说明召回不可靠。

当前系统仍然把这些弱相关结果交给 LLM，导致模型被迫作答。

## 4. 如何改进

### 4.1 增加文档级 metadata

parser 或 writer 阶段为每个 chunk 写入：

```json
{
  "company": "CrossFirst Bank",
  "ticker": "CFB",
  "year": 2022,
  "filename": "e2b19d2cc2ccab2fd9022326b56b38fb0e772e73.pdf",
  "page": 35,
  "doc_type": "annual_report"
}
```

### 4.2 建立 company / ticker / alias 到 doc_id 的映射

例如：

```text
TSX_Y -> 9d7a72445aba6860402c3acce75af02dc045f74d
Mercia Asset Management PLC -> ac9aa244462c80705c3ff046542c02c459989742
Holley Inc. -> 194000c9109c6fa628f1fed33b44ae4c2b8365f4
```

然后查询时先定位目标 doc_id。

### 4.3 检索 SQL 增加 doc_id / company filter

理想流程：

```text
question -> extract company/ticker -> doc_id -> filtered vector search
```

SQL：

```sql
SELECT
    doc_id,
    chunk_no,
    content,
    metadata,
    1 - (embedding <=> CAST(:query_vector AS vector)) AS cosine_similarity
FROM public.rag_chunk
WHERE doc_id = :doc_id
ORDER BY embedding <=> CAST(:query_vector AS vector)
LIMIT :top_k;
```

### 4.4 调整 chunk 策略

```text
chunk_size = 500
chunk_overlap = 100
```


```text
按页切
按章节切
表格单独保留
重要表格页扩大上下文
```

## 5. 改进完以后的下一步计划

下边我就开始用更结构化的方式，比如用 MinerU 那个库，或者参考 RAGFlow 的策略，去形成 Markdown 形式的有层级的切割方式。

这样的话，能够在很大程度上保证上下文语义的完整性，也可以避免很多情况（比如 Tail 这些问题）。这方面应该考虑得更细一点，当然本次实验主要是用作对比.

而且本来想省一套的，发现省不掉。
最后还是用 Milvus 吧，不想加这一块，感觉很难受。