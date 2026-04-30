# Structural RAG 检索问题复盘

## 1. 检索出来的结果

当前系统对 4 个问题通过 **BM25 + Milvus 向量混合检索（RRF 融合）+ LLM 生成答案**进行了端到端测试（Holley Inc. 未测）。

对比 Hard Chunk（5 个问题全军覆没），Structural RAG 的结果：

| 问题 | 期望文档/公司 | 实际召回文档 | 最高 cosine | 结果 |
|---|---|---|---|---|
| Mercia Asset Management PLC 是否提到并购 | Mercia Asset Management PLC | `ac9aa2...9742` | **0.74** | 所有 chunk 标记不相关，回答 `false` ✓ |
| Tradition 的 Operating margin (%) | Tradition | `277933...93a2` | **0.0**（纯 BM25 命中） | 召回第 44 页 "operating margin of 9.9%"，回答 `9.9` ✓ |
| TSX_Y 是否宣布股票回购计划 | Yellow Pages / TSX:Y | `9d7a72...f74d` | **0.61** | 召回第 20、68 页 Board 批准的 share repurchase，回答 `true` ✓ |
| CrossFirst Bank 最大单笔高管薪酬支出 | CrossFirst Bank | `e2b19d...e73` | **0.65** | 召回薪酬描述和财报但无数额细节，回答 `N/A` ✓ |
| Holley Inc. 是否提到并购 | Holley Inc. | — | — | 未测试 |

和 Hard Chunk 的最大区别：

- **cosine similarity 从 0.50-0.58 提升到了 0.61-0.74**，语义匹配质量明显更好
- **不再所有问题都召回到同一个文档**（Hard Chunk 全回到 `e2b19d...e73` / CrossFirst Bank）
- **metadata 里有 `company_name` 字段**，LLM 可以区分不同公司的 chunk，不再因为关键词巧合把 CrossFirst Bank 的内容当成 Holley Inc. 的答案

## 2. 存在的问题

### 2.1 BM25 命中但向量相似度为 0 的 chunk 仍然被交给 LLM

例如 Tradition 的 Operating margin 问题：

```text
cosine_similarity: 0.0
bm25_score: 0.0
final_score: 0.0
```

这个 chunk 既没有向量命中也没有 BM25 得分，但 `final_score` 为 0 仍被放入了 top_k，然后 LLM 恰好从里面提取出了正确答案。

**风险**：如果 BM25-only 的 chunk 内容与问题无关（例如关键词巧合），LLM 可能被误导。这就是 Mercia M&A 早期测试中 cosine=0.031、0.0 的 chunk 被 LLM 编造成 `true` 的原因。

### 2.2 缺少相似度阈值过滤

当前检索流程没有对 cosine similarity 做下限过滤：

```python
# processor.py _merge_results — 之前的代码
merged = list(by_id.values())  # 不管 cosine 多少都保留
```

导致 cosine=0.031、0.0 的弱相关/不相关 chunk 也进入 LLM prompt。

**已修复**：加了 `MIN_COSINE_SIMILARITY=0.25` 阈值，`_merge_results` 过滤掉不达标的 chunk。

### 2.3 Prompt 未充分利用检索质量信号

prompt 给了 LLM cosine_similarity、bm25_score、final_score，但没教它怎么用这些信号。LLM 把分数当装饰，只看正文 text。

**已修复**：prompt 新增了相似度信号说明，要求 LLM 先检查相似度再判断相关性，相似度 < 0.3 直接标记不相关并跳过。

### 2.4 缺少文档级预过滤

和 Hard Chunk 一样，当前检索是对全 Milvus collection 做向量搜索 + BM25 全文搜索：

```python
# processor.py _vector_search
hits = self.milvus_client.search(
    collection_name=self.milvus_collection,  # 全库
    data=[query_vector],
    anns_field="embedding",
    limit=self.top_k,
)
```

问题虽然指定了公司名（Mercia、Tradition、Holley 等），但检索没有先限定公司再搜索。不过和 Hard Chunk 不同的是，Structural RAG 的 metadata 里**已经有 company_name 字段**，可以做过滤——只是代码还没写。

### 2.5 LLM 仍然可能在弱证据下强行作答

即使所有 chunk 都标记为不相关，LLM 有时还是会根据关键词印象给出答案。例如未加阈值时，Mercia M&A 问题的 cosine=0.031、0.0 的 chunk 被 LLM 解读为"提到了 M&A"并回答 `true`。

## 3. 可能的原因

### 3.1 向量检索的语义质量取决于 chunk 结构

Hard Chunk 的固定 1000 字符切法导致上下文断裂：表格被切断、数值和指标名分离、公司名没注入。Structural RAG 按 Markdown 标题层级切 + 注入 metadata（company_name、title），让 embedding 质量从 0.5 提升到了 0.6-0.74。

```text
Hard Chunk 固定长度切 → cosine 0.50-0.58 → 弱相关
Structural RAG 标题级切 + metadata → cosine 0.61-0.74 → 中等偏强相关
```

### 3.2 BM25 在精确关键词匹配上仍有价值，但需要向量验证

Tradition 的 "Operating margin" 直接被 BM25 关键词命中（operating margin 出现在 chunk 正文中），虽然是 0 向量相似度，但内容恰好正确。

这说明 BM25 + 向量**互补**是对的，但 BM25-only 的 chunk 需要有额外的验证机制。

### 3.3 metadata 承担了公司识别职责

Hard Chunk 的 CrossFirst Bank 收购信息被当成 Holley Inc. 的答案，因为 LLM 分不清 chunk 属于哪家公司。

Structural RAG 在每个 chunk 里注入了 `company_name`：

```json
{
  "company_name": "CrossFirst Bank",
  "doc_id": "e2b19d...e73",
  "page_index": 104,
  "chunk_type": "text"
}
```

LLM 在 evidence_analysis 里能判断 "this pertains to a different company (CrossFirst Bank), not TSX_Y (Yellow Pages Limited)" 并正确排除。

### 3.4 父子 chunk 回溯未完整实现

当前 `processor.py` 的 `_expand_siblings` 是按 `doc_id + page_index` 捞同页所有 chunk，不是真正的父子关系回溯。chunker 生成的 chunk 没有 `parent_id` 字段，所以无法实现"命中 child chunk → 回溯 parent chunk"的设计意图。

## 4. 如何改进

### 4.1 相似度阈值（已完成）

```python
# processor.py
MIN_COSINE_SIMILARITY = 0.25

# _merge_results 中过滤
merged = [r for r in by_id.values() if r.milvus_score >= MIN_COSINE_SIMILARITY]
```

低于阈值的 chunk 不进入 LLM prompt，从源头消灭弱相关噪音。

### 4.2 Prompt 教会 LLM 使用相似度（已完成）

- 新增相似度信号说明（>= 0.5 可信、0.3-0.5 谨慎、< 0.3 不相关）
- 要求 LLM 先检查相似度再分析内容
- 检索结果为空时显式提示返回 N/A

### 4.3 增加文档级预过滤

在当前 metadata 已有 `company_name` 的基础上，实现"先定位文档，再向量检索"：

```text
question → extract company name → lookup doc_id → filter Milvus search
```

实现方式：

```python
# 步骤 1：从问题中提取公司名
company = extract_company(query)  # 或用 LLM 提取

# 步骤 2：Milvus 过滤搜索
hits = client.search(
    collection_name=collection,
    data=[query_vector],
    filter=f'company_name == "{company}"',
    ...
)
```

### 4.4 实现真正的父子 chunk 回溯

当前 chunker 按标题层级切，但没有记录 chunk 之间的父子关系。可以增加 `parent_id` 字段：

```python
# chunker 中为每个 chunk 记录所属章节
metadata = {
    "chunk_id": "...",
    "parent_id": "section_hash",  # 所属章节/父 chunk
    "section_title": "## Item 11. Executive Compensation",
    ...
}
```

检索命中 child chunk 后，按 `parent_id` 拉取整个章节内容给 LLM。

### 4.5 区分 chunk 类型权重

当前 chunker 区分了 `text` 和 `table` 类型，但检索时权重相同。表格类 chunk 含财务数据，对 number 类问题权重应更高。

## 5. 改进完以后的下一步计划

- [ ] 用 5 个文件跑完整的 Holley Inc. 测试
- [ ] 实现 `extract_company` → Milvus filter 的预过滤管线
- [ ] chunker 增加 `parent_id`，实现真正的父子回溯
- [ ] 跑 Recall / Precision 对比报告（Structural RAG vs Hard Chunk）
- [ ] 如果效果仍不理想，考虑用 MinerU 替换当前 pdf_parser，或参考 RAGFlow 的 DeepRAG 策略增强表格理解

当前阶段对比结论：**Structural RAG 的 Markdown 层级切片 + metadata 注入在语义检索质量上显著优于纯硬切片**。主要差距已经从"召回错误文档"变成了"召回正确文档但相似度不够高"和"LLM 不会用相似度信号"——这两点已通过阈值过滤和 prompt 改进修复。
