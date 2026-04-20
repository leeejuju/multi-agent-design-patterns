# very_hard_chunk_purely

纯粹的 **Hard Chunk**（硬切片）标本目录。

## 目录说明
这里的 JSON 文件直接来自原始文本的**截断式硬切片**结果。其特点是：
- 不做语义分段（Semantic Splitting）。
- 不补充复杂的结构化 Metadata。
- 不进行公司名、Ticker、年份等关键字段的自动抽取。
- 文件名即为 `doc_id`，每个文件包含对应文档的所有分块。

## 切片配置
- **Chunk Size**: 1000
- **Overlap**: 200

## 数据结构
每个分块（Chunk）包含以下字段：

| 字段名 | 说明 |
| :--- | :--- |
| `doc_id` | 文档唯一标识符 |
| `chunk_no` | 分块序号 |
| `content` | 分块文本内容 |
| `page` | 对应原始 PDF 页码 |
| `token_count` | Token 数量 |
| `char_count` | 字符数量 |
| `source` | 源文件路径 |
| `label` | 分块标签 |
| `metadata` | 基础元数据（这块啥没有） |

## 当前样本
目录中包含以下 4 份文档的 JSON 标本：
- `194000c9109c6fa628f1fed33b44ae4c2b8365f4.json`
- `2779336b845a41544348abb7b3e6e5bd2ff893a2.json`
- `ac9aa244462c80705c3ff046542c02c459989742.json`
- `e2b19d2cc2ccab2fd9022326b56b38fb0e772e73.json`

> [!NOTE]
> 实际上测试集共有 **5 份**文档。由于另一份以 `9d7a72445aba6860402c3acce75af02dc045f74d.pdf` 开头的文档已经转换完成，因此未放入此同步目录中。
