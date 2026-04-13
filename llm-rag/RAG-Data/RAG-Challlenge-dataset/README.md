# RAG Challenge Dataset

来源于 [Enterprise RAG Challenge 2](https://github.com/trustbit/enterprise-rag-challenge)（Round 2, Feb 2025），由 TimeToAct / Trustbit / IBM 主办。

## 数据集概况

- 主办方公开 **7496 份公开年度报告 PDF**（约 46GB），含公司名称和文件 SHA1 哈希（`dataset.csv`）
- 竞赛日从中随机抽取 **100 份 PDF**，每份最长可达 **1000 页**
- 使用公共区块链 API 生成不可预测的随机种子，保证公平性


## 问题 Schema

```python
class Question(BaseModel):
    text: str
    kind: Literal["number", "name", "boolean", "names"]
```

### 问题类型

| kind | 含义 | 示例 |
|---|---|---|
| `number` | 数值型指标 | How many stores did "Accuray Incorporated" have in the end of fiscal year 2021? |
| `name` | 单个名称 | Who is the CEO in the company "Zegona Communications plc"? |
| `names` | 多个名称 | What new products were launched in 2023? |
| `boolean` | 是/否 | Did "Global Medical REIT Inc." have a greater Debt-to-Equity ratio than "Zegona Communications plc" in Q2 2021? |

## 回答规则

### 通用规则

- 所有类型均允许返回 `N/A` 或 `n/a`，表示"不适用"或"即使对人类来说也没有足够信息回答"
- 系统不应对无意义的问题编造合理答案（如问能源公司有多少门店），应返回 `N/A`
- 如果问题提到的公司不在竞赛 PDF 中，必须返回 `N/A`（用于检测幻觉）

### Number 回答规则

- 仅返回数字，**不含**注释、货币符号、小数逗号或分隔符
- 正确: `122333`，错误: `122k`, `122 233`
- 货币不匹配时返回 `N/A`（如问题问美元但报告用英镑）
- 即使可以从上下文中推算出来，只要未直接陈述就返回 `N/A`
- 必须注意上下文中单位标注（units / thousands / millions），据此补零：
  - 报告写 `$4970.5 (in thousands)` → 答案应为 `4970500`
  - 报告写 `$1352 (in millions)` → 答案应为 `1352000000`
- 括号中的值表示负数

### Name 回答规则

- 仅返回名称本身，不含附加信息

### Names 回答规则

**职位问题：**
- 仅返回职位名称，**不含**人名或其他附加信息
- 新任命到领导岗位也算作职位变动
- 同一职位的多次变动只返回一次
- 职位名称使用单数形式

**产品问题：**
- 仅返回上下文中出现的产品原始名称
- 候选产品或测试阶段的产品不算已发布产品

### Boolean 回答规则

- 仅 `yes`/`no` 或 `true`/`false`，大小写不敏感

### Comparative（多公司比较）

- 需分别查找每家公司的指标，再进行比较回答

## 引用要求

每个答案**必须附带引用页码**，证明系统确实从文档中找到了答案而非幻觉。

```python
class SourceReference(BaseModel):
    pdf_sha1: str        # PDF 文件的 SHA1 哈希
    page_index: int      # PDF 中的零基物理页码

class Answer(BaseModel):
    question_text: Optional[str]
    kind: Optional[Literal["number", "name", "boolean", "names"]]
    value: Union[float, str, bool, List[str], Literal["N/A"]]
    references: List[SourceReference] = []
```


## 参考资料

- [trustbit/enterprise-rag-challenge](https://github.com/trustbit/enterprise-rag-challenge) — 官方规则仓库
- [IlyaRice/RAG-Challenge-2](https://github.com/IlyaRice/RAG-Challenge-2) — 冠军方案代码（MIT License）
- [How I Won the Enterprise RAG Challenge](https://abdullin.com/ilya/how-to-build-best-rag/) — 冠军方案详解
- [Enterprise RAG Challenge Leaderboards](https://www.timetoact-group.at/en/insights/erc3-leaderboards) — 排行榜
