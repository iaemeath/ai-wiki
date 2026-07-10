# 🛠️ AI 记忆机制全景透视：从存储、写入到召回

> 版本：V1.0.0 (架构总览)
> 本文档系统地梳理目前 AI 记忆领域的所有主流技术机制与前沿思想。

---

## 🧭 第一部分：记忆存储（Memory Storage）—— 记在哪里？怎么组织？
大模型的原生上下文（Context Window）是“瞬时内存（RAM）”，一旦会话结束就会断电清空。为了实现长期记忆，必须引入外部持久化介质，目前业界主要有以下三种非显式存储思想：

### 1. 层次化金字塔存储（Hierarchical Storage）—— 最推荐 PRO 采纳
* **技术思想**：模仿计算机主板的缓存级数（L1/L2/L3/Disk）。
* **具体架构**：
  * **L1 (超高速缓存)**：常驻系统提示词（System Prompt）中的 Persona 和 Human Profile（只占 ~1K Tokens）。
  * **L2 (内存短记)**：最近 N 轮的原始对话（KV Cache / Rolling Buffer）。
  * **L3 (本地闪存)**：高频结构化规则（如您的 CLAUDE.md）。
  * **Disk (冷数据硬盘)**：外部数据库（SQLite / 向量库），存储历史所有的技术观察和代码快照。

### 2. 图谱化结构存储（Graph-based Storage）
* **技术思想**：人类的记忆不是孤立的文档，而是以网状概念（Concepts）和实体（Entities）相互关联的。
* **具体架构**：使用 Graph 数据库（如 Neo4j，或本地极其轻量的图结构）。
* **示例**：将“项目A —[使用]→ Mojo —[解决]→ GIL锁延迟”存储为三元组。这种结构比纯文本切片更有利于进行深度的逻辑推理召回。

### 3. 时间线/时序流存储（Append-Only Timeline）
* **技术思想**：将所有发生的事件、代码变更、AI 的 Observation 视为不可变流水账（Event Sourcing）。
* **具体架构**：带有高精度时间戳的键值对（Key-Value with Timestamp）或日志型数据库。

---

## 🧭 第二部分：记忆写入与固化（Memory Write & Consolidation）—— 怎么存进去？
如何把冗长的聊天对话和万行代码，变成精炼、高价值的长期记忆？这是区分方案高级与否的关键。

### 1. 异步反射与固化（Asynchronous Reflection / Consolidation）
* **机制思想**：模仿人类的睡眠记忆固化（Sleep Consolidation）。大模型在清醒（回答用户问题）时，不进行复杂的记忆压缩，只做原始日志追加（Append Log）。
* **技术实现**：
  * **后台反思**：在后台（或利用 Mojo 开启独立异步线程），当检测到用户停止输入或会话间歇时，启动一个轻量大模型（如 Claude Haiku 或 Llama 3-8B），对近期的原始对话进行“反思（Reflection）”：
  * **提炼命令**：“总结过去5轮对话中，用户做出的核心技术决策和行为偏好，并以 Observation 格式输出。”
  * **写入**：将提炼出的高浓度知识存入冷存储。

### 2. 遗忘与修剪机制（Forgetting & Eviction / TTL）
* **机制思想**：如果记忆无限增加，向量库会充斥噪声，检索效率下降。必须学会遗忘。
* **技术实现**：
  * **LRU（最近最少使用）**：每次某条记忆被召回，刷新激活计数；长期未被召回的记忆，降低权重或归档到二级硬盘。
  * **语义覆盖（Semantic Overwrite）**：当写入新决策（“改用 SQLite”）时，系统自动搜索冲突的旧决策（“使用 Redis”），并更新旧决策的状态为 [Deprecated]（已废弃），防止后续召回冲突。

---

## 🧭 第三部分：记忆检索与召回（Search & Retrieval）—— 怎么捞出来？
这是您最关心的部分。目前的普通向量检索（纯 RAG）在记忆场景中极其死板，前沿的主流召回技术和思想已经演进到了以下阶段：

### 1. 认知中断与双向主动召回（Agent-Driven Proactive Retrieval / Interruption）
* **技术思想**：不再由外围脚本静态地在模型回答前塞入记忆（被动 RAG），而是由 AI 自主决定何时去翻阅记忆（主动召回）。
* **技术实现**：
  * 为 AI 绑定类似 `query_memory(keyword)`、`read_archive_page(page_id)` 的 Tool。
  * 大模型在思考（Thinking Process）中，如果意识到缺乏背景，会主动停止输出，连续调用多次该 Tool。
  * 外围系统（例如您的 Mojo 逻辑）拦截到调用，从数据库捞出数据返回给 AI，AI 吸收后再继续回答。

### 2. 时序感知检索（Time-Aware / Temporal Retrieval）
* **技术思想**：打破传统 RAG 只看语义相似度（Cos-Similarity）的死结，让时间成为第一等公民。
* **技术实现（双通道混合打分公式）**：
  $$Score = w_1 \cdot \text{Semantic\_Similarity} + w_2 \cdot e^{-\lambda(T_{\text{current}} - T_{\text{memory}})}$$ 
  通过调节 $\lambda$（衰减系数），系统在召回“技术选型/项目配置”这类时效性极强的记忆时，会极度偏向最近写入的内容，彻底解决旧记忆干扰新决策的问题。

### 3. 多模态/多通道混合召回（Hybrid Multi-Route Retrieval）
* **技术思想**：单纯的向量检索（Dense Retrieval）容易丢失精确的类名、函数名；单纯的关键词检索（Sparse Retrieval/BM25）又缺乏语义理解。
* **技术实现（Reciprocal Rank Fusion - RRF 倒数排名融合）**：
  * **通道一**：向量检索（针对模糊概念、隐性意图、历史行为偏好）。
  * **通道二**：精准全文检索/BM25（针对特定代码符号、Bug ID、绝对路径）。
  * **通道三**：图谱检索（根据当前文件，追踪关联实体的上下文）。
  * **RRF 排序**：将三个通道返回的结果通过 RRF 算法进行交叉重新排序（Reranking），得出最终的 Top-K。

### 4. 记忆分页与滑动窗口拼装（Paged Memory Coalescing）
* **技术思想**：这就是您在 OS 记忆工具中看到的逻辑。它解决的是“断章取义”问题。
* **技术实现**：
  * 当向量检索命中某一个特定代码切片或对话切片（Chunk）时。
  * 系统不会只拿这一个 Chunk，而是以此为中心，把该 Chunk 所在的整页（Page）或者它前后相邻的 2 个时序 Chunk 一并动态捞出（类似于虚拟内存的预读 Prefetching）。
  * 在拼装进大模型上下文前，Mojo 层进行去重、按时间重排，确保喂给大模型的是一条连续的、有因果关系的逻辑线。
