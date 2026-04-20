# RAG Challenge 标本测试结果 (Chunk-1500-Overlap-300)

本目录记录了在 `chunk_size=1500` 和 `chunk_overlap=300` 配置下，针对 5 个测试文档的检索与问答结果。

---

## 问答测试详情

### 1. Mercia Asset Management - 并购查询
**问题**：Did Mercia Asset Management PLC mention any mergers or acquisitions in the annual report?

**测试结果：**
- **判定**: `true`
- **逻辑**: 报告在“财务报表”章节提到了“业务合并（business combinations）”，并明确说明了使用收购法进行核算。

```json
{
  "question_text": "Did Mercia Asset Management PLC mention any mergers or acquisitions in the annual report?",
  "kind": "boolean",
  "value": true,
  "references": [
    {
      "pdf_sha1": "ac9aa244462c80705c3ff046542c02c459989742",
      "page_index": 82
    }
  ],
  "retrieval_results": [
    {
      "pdf_sha1": "ac9aa244462c80705c3ff046542c02c459989742",
      "page_index": 82,
      "document": "ac9aa244462c80705c3ff046542c02c459989742",
      "chunk_no": 342,
      "cosine_similarity": 0.769862,
      "content": "Annual Report & Accounts 2022 Mercia Asset Management PLC 81 Financial statements Business combinations The Group accounts for business combinations using the acquisition method from the date that control is transferred to the Group. Both the identifiable net assets and the consideration transferred in the acquisition are measured at fair value with transaction costs expensed as incurred. Goodwill arising on acquisitions is tested annually for impairment."
    },
    {
      "pdf_sha1": "ac9aa244462c80705c3ff046542c02c459989742",
      "page_index": 80,
      "document": "ac9aa244462c80705c3ff046542c02c459989742",
      "chunk_no": 331,
      "cosine_similarity": 0.780158,
      "content": "Annual Report & Accounts 2022 Mercia Asset Management PLC 79 Financial statements Notes to the consolidated financial statements For the year ended 31 March 2022 1. Accounting policies The principal accounting policies applied in the presentation of these consolidated financial statements are set out below. These policies have been consistently applied throughout the year unless otherwise stated."
    }
  ],
  "reasoning_process": "The annual report mentions 'business combinations' under the section 'Financial statements', which refers to mergers or acquisitions. Specifically, it states that 'The Group accounts for business combinations using the acquisition method from the date that control is transferred to the Group.' This indicates that Mercia Asset Management PLC did mention mergers or acquisitions in the annual report."
}
```

#### 效果评价与分析
这个是对的，其实它这个 RAG 的召回率，正确答案应该是 page index 82。它召回的 content 基本上是对的，但是余弦值只有 76% 左右。

你要说相关也相关，但要说强相关，其实也不算强相关。甚至底下相似度更高，但内容却是错的，结果并不相关。

---

### 2. Tradition - 营业利润率
**问题**：According to the annual report, what is the Operating margin (%) for Tradition (within the last period or at the end of the last period)?

**测试结果：**
- **判定**: `N/A`
- **逻辑**: 检索到的文本分块中未直接提及具体的营业利润率百分比。

```json
{
  "question_text": "According to the annual report, what is the Operating margin (%) for Tradition (within the last period or at the end of the last period)? If data is not available, return 'N/A'.",   
  "kind": "number",
  "value": "N/A",
  "references": [],
  "retrieval_results": [
    {
      "pdf_sha1": "2779336b845a41544348abb7b3e6e5bd2ff893a2",
      "page_index": 98,
      "document": "2779336b845a41544348abb7b3e6e5bd2ff893a2",
      "chunk_no": 330,
      "cosine_similarity": 0.663065,
      "content": "A N N U A L R E P O R T 99 At 31 December 2021 CHF 000 Tradition-ICAP Tradition Energy Other companies Total Place of business London, New York, Singapore Stamford Percentage holding in non-controlling interests 50.0% 40.0%1) Non-current assets 3,749 487 Current assets 40,900 65,791 Non-current liabilities 8,668 84 Current liabilities 11,540 25,211 Net assets 24,441 40,983 Book value of non-controlling interests 3,848 16,865 1,557 22,270 Revenue 53,427 52,148 Net profit/comprehensive income for the year 8,232 10,207 Share in the net profit/comprehensive income attributable to non-controlling interests: 1,517 4,110 619 6,246 Net operating cash flows 6,005 7,157 Net investing cash flows -271 - Net financing cash flows (excl. dividends paid to non-controlling interests) -515 -3,138 Dividends paid to non-controlling interests -2,184 -2,141 Movement in cash and cash equivalents 3,036 1,878 1) In addition, 2.5% of the share capital is held through non-voting shares. 18. DIVIDENDS Dividends a"
    }
  ],
  "reasoning_process": "The provided context does not contain specific information about the Operating margin (%) for Tradition. There is no direct mention of the Operating margin in the retrieved chunks. Therefore, the value is 'N/A'."
}
```

#### 效果评价与分析
According to the annual report, what is the operating margin for the tradition within the latest period? Or at the end of the last period, if date is not available, return 9.

答案是 9.9%，但是他那什么没召回出來啊，所以我去检查了一下这个文档，发现这个问题属于 March for the Tradition。

1. 这个 Tradition 指的是 Tradition 这家公司。
2. 因为做的是纯 Hard Chunk，因此就没有这些公司的元信息。

本质上，你上下文切片上可能说这个 Tradition for the Tradition，语义上会有混淆。

---

### 3. TSX_Y - 股票回购计划
**问题**：Did TSX_Y announce a share buyback plan in the annual report?

**测试结果：**
- **判定**: `true`
- **逻辑**: 董事会于 2022 年 8 月 4 日批准了约 1 亿美元的正式股票回购计划，并已于 10 月执行。

```json
{
    "question_text": "Did TSX_Y announce a share buyback plan in the annual report?",
    "kind": "boolean",
    "value": true,
    "references": [
        {
            "pdf_sha1": "9d7a72445aba6860402c3acce75af02dc045f74d",
            "page_index": 19
        },
        {
            "pdf_sha1": "9d7a72445aba6860402c3acce75af02dc045f74d",
            "page_index": 67
        }
    ],
    "retrieval_results": [
        {
            "pdf_sha1": "9d7a72445aba6860402c3acce75af02dc045f74d",
            "page_index": 19,
            "document": "9d7a72445aba6860402c3acce75af02dc045f74d",
            "cosine_similarity": 0.603176,
            "content": "On August 4, 2022, the Board approved a distribution to shareholders of approximately $100.0 million by way of a share repurchase from all shareholders pursuant to a statutory arrangement under the Business Corporations Act (British Columbia) (the Arrangement )."
        },
        {
            "pdf_sha1": "9d7a72445aba6860402c3acce75af02dc045f74d",
            "page_index": 67,
            "document": "9d7a72445aba6860402c3acce75af02dc045f74d",
            "cosine_similarity": 0.609038,
            "content": "On October 4, 2022, the Company repurchased from shareholders pro rata an aggregate of 7,949,125 common shares (including 388,082 shares holder in treasury) at a purchase price of $12.58 per share pursuant to the Arrangement for a total of $101.0 million, including $1.0 million of transaction costs."
        }
    ],
    "reasoning_process": "The context clearly states that on August 4, 2022, the Board approved a share repurchase plan for approximately $100 million. Additionally, it mentions that on October 4, 2022, the company repurchased 7,949,125 common shares at $12.58 per share for a total of $101 million, which confirms the execution of the announced buyback plan."
}
```

#### 效果评价与分析
但是你可以看到，虽然对得上标准答案，因为是召回了这两标准答案页，但是 reasoning process 以及召回的 content 里边，其实并没有能够体现出整个 RAG 的质量。你的答案是对的，但你召回不是高质量召回。你缺少那些语义上的连接，没有特别多的 evidence召回的原理更多是基于 content 里面有 share repurchases 以及 shareholders 这些东西，所以才能召回。

我猜大概是这个原因，更多是语义上的 match，而不是说 RAG really found the answer

因为你看，它的问题是：Did TSXY announce a share buyback plan in the annual report? 对吧？但是 you never explained what is TSXY.

The original answer is:
1. TSXY refers to the company, blah blah blah blah.
2. And on the page, blah blah blah, there is the discussion about something.

So the RAG quality 不怎么地，totally failed。

---

### 4. CrossFirst Bank - 高管薪酬
**问题**：What was the largest single spending of CrossFirst Bank on executive compensation in USD?

**测试结果：**
- **判定**: `N/A`
- **逻辑**: 检索到的分块仅包含高管的履历和职位调整，没有涉及具体金额的薪酬数据。

```json
{
  "question_text": "What was the largest single spending of CrossFirst Bank on executive compensation in USD?",
  "kind": "number",
  "value": "N/A",
  "references": [],
  "retrieval_results": [
    {
      "pdf_sha1": "e2b19d2cc2ccab2fd9022326b56b38fb0e772e73",
      "page_index": 35,
      "document": "e2b19d2cc2ccab2fd9022326b56b38fb0e772e73",
      "chunk_no": 225,
      "cosine_similarity": 0.713785,
      "content": "er 2015. From 2006 to 2012 and from 2002 to 2005, he served in various roles with H&R Block, Inc., a tax preparation company in Kansas City, Missouri, including Assistant Vice President Audit Services and Assistant Vice President and Controller Tax Services..."
    }
  ],
  "reasoning_process": "The provided context does not contain specific information about the executive compensation amounts paid by CrossFirst Bank. The retrieved chunks provide details about the executives' roles and their previous employment history but do not mention any figures related to their compensation."
}
```

#### 效果评价与分析
这个回答倒也对，但是还是那句话，召回的没有看到想要的东西，内容上不能很好地去 match query，也没有能够提供特别好的思维 process。这个后续我换一下 process 吧，当前的模型毕竟是比较老的。

---

### 5. Holley Inc. - 并购查询
**问题**：Did Holley Inc. mention any mergers or acquisitions in the annual report?

**测试结果：**
- **判定**: `true`
- **逻辑**: 报告提到 2020 至 2022 年间完成了 15 项收购，并详细说明了 2021 年 7 月涉及 Empower Ltd. 的业务合并。

```json
{
  "question_text": "Did Holley Inc. mention any mergers or acquisitions in the annual report?",
  "kind": "boolean",
  "value": true,
  "references": [
    {
      "pdf_sha1": "194000c9109c6fa628f1fed33b44ae4c2b8365f4",
      "page_index": 33
    },
    {
      "pdf_sha1": "194000c9109c6fa628f1fed33b44ae4c2b8365f4",
      "page_index": 35
    },
    {
      "pdf_sha1": "194000c9109c6fa628f1fed33b44ae4c2b8365f4",
      "page_index": 5
    },
    {
      "pdf_sha1": "194000c9109c6fa628f1fed33b44ae4c2b8365f4",
      "page_index": 63
    }
  ],
  "retrieval_results": [
    {
      "pdf_sha1": "194000c9109c6fa628f1fed33b44ae4c2b8365f4",
      "page_index": 33,
      "document": "194000c9109c6fa628f1fed33b44ae4c2b8365f4",
      "cosine_similarity": 0.738479
    }
  ],
  "reasoning_process": "Holley Inc. mentioned multiple acquisitions in the annual report. Specifically, it noted that from 2020 through 2022, the company completed 15 acquisitions. Additionally, the report discussed the business combination that occurred on July 16, 2021, involving Empower Ltd. and other entities, which is considered a significant acquisition. Furthermore, the report highlighted specific acquisitions like Baer, Inc. and Brothers Mail Order Industries, Inc."
}
```

#### 效果评价与分析
这个更多的也是一些语义上的问题，就不再详谈了。

关于 HardChunk的实验到此为止，不会再往后进行了。下一部分我会尝试用 RAGFlow 以及其他 RAG 的方式，按照我自己的思路把整个东西做出来，看看 RAG 的 Recall、Precision 和 Faithfulness 能不能达到比赛的水准。

---

## 提交信息对照 (Submission Metadata)
- **Submission Name**: Ilia Ris v.4
- **Details**: Custom pdf parsing + vDB + Router + Parent Document Retrieval + reranking + SO CoT; llm = o3-mini

## 参考标准答案汇总
```json
{
  "answers": [
    {
      "question_text": "Did Mercia Asset Management PLC mention any mergers or acquisitions in the annual report?",
      "kind": "boolean",
      "value": false,
      "reasoning_process": "The report discusses accounting policies for business combinations but does not announce specific recent merger/acquisition events."
    },
    {
      "question_text": "According to the annual report, what is the Operating margin (%) for Tradition...",
      "kind": "number",
      "value": 9.9,
      "reasoning_process": "The Reported operating margin in the 2022 table is 9.9%."
    },
    {
      "question_text": "Did TSX_Y announce a share buyback plan in the annual report?",
      "kind": "boolean",
      "value": true,
      "reasoning_process": "On August 4, 2022, the Board approved a repurchase plan of approximately $100.0 million."
    },
    {
      "question_text": "What was the largest single spending of CrossFirst Bank on executive compensation in USD?",
      "kind": "name",
      "value": "N/A",
      "reasoning_process": "Numeric data for executive compensation is not found in the provided context."
    },
    {
      "question_text": "Did Holley Inc. mention any mergers or acquisitions in the annual report?",
      "kind": "boolean",
      "value": true,
      "reasoning_process": "The report lists multiple acquisitions and a business combination in 2021."
    }
  ]
}
```