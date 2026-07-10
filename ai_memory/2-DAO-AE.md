# 🛠️ “确定性架构编排与原子级代码落地方案”（2-DAO-AE）标准实施白皮书

### 暨 高确定性软件工程交付与原子化任务执行流水线

## 1. 方案概述与核心哲学

在进入软件研发的**实现阶段（Implementation Phase）**时，最大的行业痛点往往不再是“需求不确定”，而是**“执行走样”**。当上游已经交付了“一个准确描述的系统”（包含明确的业务逻辑、详尽的接口契约、清晰的数据结构、以及固化的系统说明书）后，如何保证研发流水线能够 100% 不打折扣、高效率地将这份设计图纸翻译成生产级代码，是本方案攻克的全核核心课题。

### 1.1 核心痛点

- **“图纸与砌砖”的断层：** 哪怕设计文档再准确，研发人员在实际编码时，依然容易按照个人习惯“技术脑补”，有意无意地绕过既定的方案选择、安全红线或异常处理策略。
    
- **大模型的长途疲劳与技术幻觉：** 面对一整份准确但庞大的系统设计说明书，如果直接丢给 AI 编码工具，由于上下文极长、代码改动量大，AI 极易在研发后期出现注意力涣散，产生接口命名冲突或逻辑漏洞。
    
- **内网研发生态的孤岛效应：** 隔离的内网中，代码仓库（Git）、配置中心（Nacos）、私服（Maven/NPM）相互断联，缺乏一套防呆机制来卡死大模型的代码验证路径。
    

### 1.2 2-DAO-AE 核心哲学

2-DAO-AE 方案的核心哲学是：**“工程结构防呆，原子任务隔离，基于单一事实源的确定性翻译”**。

它将“一个准确描述的系统”视为唯一合法的最高图纸（Single Source of Truth），通过自动化编排引擎将其切碎为不可逆、强依赖的原子 Issue 链。利用大模型的大上下文感知力与提示词缓存（Prompt Cache）技术，在极小的原子任务空间内，进行高精度、无幻觉的生产级代码爆破。

## 2. 全栈工具链与运行架构（Tooling & Architecture）

在实现系统的阶段，工具链的重心全面转向“代码编译、依赖注入、质量门禁与任务流转”：

- **任务拆解引擎：内网 LangGraph + 顶尖长文本大模型（如 GLM-5.2 等）**
    
    - _职责：_ 读取“准确描述的系统”文档，通过严谨的有向无环图（DAG）将其拆解为技术视角的 Issue 链。
        
- **分布式状态机：内网 GitLab / Jira Issue 跟踪器**
    
    - _职责：_ 承载任务，利用 Issue 的强依赖关系（Blocks / Blocked by）死锁开发顺序，防止跨层抢跑。
        
- **精密编码执行器：Claude Code + GitLab MCP Server**
    
    - _职责：_ 挂载内网研发生态（Git、Maven、Nacos），专职、高精度地消灭原子 Issue。
        

## 3. 2-DAO-AE 标准流水线流程（Pipeline Framework）

当输入“一个准确描述的系统”后，2-DAO-AE 流水线严格按照“切碎（Tokenize）、认领（Claim）、攻克（Execute）”三个标准动作进行运转。

```
[输入：一个准确描述的系统 (Spec/Schema/DDL)]
                │
                ▼
【动作 1：技术拓扑拆解】 ───> 自动生成 4 层具有依赖关系的 GitLab Issues 链
                                              │
                                              ▼
【动作 2：精准上下文分发】 ─> Claude Code 挂载 MCP，极简化锁定单 Issue 边界
                                              │
                                              ▼
【动作 3：全库感知编码与本地 CI】 ─> 命中 Prompt Cache ──> 本地编译 ──> 自动 Git Push
```

### 动作 1：技术视角的组件级拓扑拆解 (Technical Topology Tokenization)

编排引擎（LangGraph）吃下准确的系统说明书，利用大模型强大的软件工程理解力，拒绝生成“请开发某某功能”这种粗颗粒度的任务，而是**必须严格按照技术层级，拆解出具备强拓扑依赖关系的 4 类原子 Issue**：

1. **[DDL 构筑层] Issue：** 严格根据说明书中的数据库模型，编写 SQL、Liquibase 或 Flyway 脚本，在数据库中建表、加索引。
    
2. **[核心算法与内核层] Issue：** 专门负责编写底层的硬核业务算法类、核心计算逻辑、状态机引擎或自动纠错线程池。
    
3. **[API 控制与边界层] Issue：** 专门负责编写 Spring Boot Controller / Controller 接口、配置 Nacos 动态参数、打上属地化数据权限拦截器（RBAC Row-level Filter）。
    
4. **[生产级应用重构层] Issue：** 专门负责将前端视图、路由、全局状态管理（Pinia/Vuex）与后端的 API 契约进行严丝合缝的联调对接。
    

> **拓扑卡门禁规则：** 在 GitLab 中，`[API控制层] Issue` 必须声明 `Blocked by [核心算法层] Issue`。上游未通过编译，下游任务在看板上自动置灰锁定，从项目管理层面卡死大模型的技术冒进。

### 动作 2：基于基座 MCP 的精准上下文分发 (Context-Isolated Claiming)

开发人员在本地 IDE 唤醒 **Claude Code**。此时，开发人员无需再向 AI 描述任何宏观业务背景，而是通过挂载的 GitLab MCP Server 敲入确定性指令：

> `claude "请读取内网 GitLab 项目的 Issue #105（实现台账增量差异比对算法），并检查其上游依赖。"`

- **上下文极限瘦身：** 此时，通过 MCP 插件的过滤，发给大模型的上下文空间被精准限制在：**当前的 Issue #105 描述 + 达成该 Issue 所必需的单体类文件 + 系统说明书中对应的特定章节**。
    
- 大模型不再需要去分心理解整套庞大系统的非相关模块，其全部智力被 100% 聚焦在当前这几十行原子代码的编写上。
    

### 动作 3：全库感知编码与自动化本地 CI (Atomic Execution & Local CI)

1. **Prompt Cache（提示词缓存）爆发：** 尽管每次调用都会携带系统说明书作为图纸，但由于大模型网关层配置了 Prompt Caching 技术，Claude Code 频繁因不同 Issue 唤醒大模型时，重复读取的基础说明书将 100% 命中缓存。首字响应（TTFT）进入毫秒级，编码毫无卡顿。
    
2. **全库语义感知（Global RAG）：** 大模型凭借大上下文能力，在编写当前原子类时，能瞬间感知到内网 Maven/NPM 私服中已经存在的通用工具包（如标准时间转换类、加密类），直接进行调用，绝不重复造轮子。
    
3. **防御性本地编译（Defensive Compilation）：** 代码编写完成后，Claude Code 会在本地静默调用内网研发基础设施进行跑测防呆：
    
    - 后端执行：`mvn clean test -Dtest=LedgerComparatorTest`
        
    - 前端执行：`npm run lint && npm run build`
        
4. **自动提交闭环：** 本地编译与单元测试 100% 通过后，Claude Code 利用 Tool Call 自动执行 Git 提交：
    
    `git add . && git commit -m "feat: implement ledger diff comparator, close #105" && git push`
    
    该 Issue 在 GitLab 看板上自动流转至 `Review` 或 `Done` 状态，完美闭环。
    

## 4. 开发防呆质量红线（Quality Gates）

为了确保交付产物与“准确描述的系统”达成 100% 的契约一致性，2-DAO-AE 方案在持续集成（CI）流水线中设立了严格的“代码随动硬门禁”：

1. **断言覆盖率红线（Assert-Coverage Line）：**
    
    任何涉及 `[核心算法与内核层]` 的 Issue，AI 在提交代码时，**必须同时提交对应的单元测试类（如 JUnit）**。测试用例中必须包含不少于 3 个针对说明书中列出的 Edge Cases（边缘场景，如报文为空、数值越界、并发冲突）的 `assertEquals` 或 `assertThrows` 断言。未达标者，CI 流水线直接打回。
    
2. **Nacos 与网关契约核验（Nacos-Schema Match）：**
    
    如果 API 层代码中使用了任何动态配置项或特定的路由 Gateway 前缀，CI 流水线会自动通过脚本去内网 Nacos配置中心或网关服务校验是否存在该 Data ID 且格式完全正确。若不匹配，直接触发 Webhook 向 GitLab Issue 报错，强制打回重修。
    

## 5. 方案实施规范与维护指南

1. **Issue 唯一事实源原则：** 严禁开发人员跳过编排阶段，手动去本地编写与说明书不符的代码。所有开发行为必须由 Issue 触发，且代码中的关键注释必须附带 `SIP-Ref: Issue #ID`，确保每一行生产代码都可以追溯至最初的系统设计图纸。
    
2. **隔离调试隔离：** 负责中转和执行的脚本在调用 GitLab API时，所有调试和 Debug 日志必须重定向输出到本地文件（如 `logs/dao_ae_pipeline.log`），绝对不能混入标准输出（`stdout`），以防止破坏 Claude Code 的 MCP 协议 JSON-RPC 流。
    
3. **依赖拓扑刷新：** 当系统说明书在后续迭代中发生局部变更时，需由编排引擎重新运行动作 1，动态更新 GitLab 上的 Issue 依赖树，并自动对处于 `Blocked` 状态的下游任务进行解封或挂起。

## 🛠️ 2-DAO-AE（实现系统）的全球开源组件雷达

在第二阶段（2-DAO-AE），由于输入是“一个准确描述的系统”，我们的核心目标是**确定性架构拆解、任务防呆控制与代码高精度翻译**。以下是除了 LangGraph 之外，专门在这个阶段大放异彩的 3 类顶级开源组件：

### ❶ 架构与规范 Lint 级控制组件：ArchUnit

- **底层技术栈：** Java (支持完全离线私服)
    
- **它怎么解决 2-DAO-AE 的痛点：** 哪怕 Issue 拆得再好，大模型编码时仍可能把代码写错地方（例如把 Service 层的逻辑写进 Controller）。ArchUnit 是一个开源的**架构契约测试框架**。
    
- **2-DAO-AE 场景用法：** 你的流水线可以用它在内网 CI 中写一段防呆测试：“禁止任何 Controller 直接访问数据库”、“所有 Service 必须打上分布式锁注解”。一旦 Claude Code 脑补了不合规的结构，ArchUnit 会在编译期直接让 `mvn test` 报错打回，强行卡死代码合规红线。
    
- **GitHub:** `https://github.com/TNG/ArchUnit`
    

### ❷ 确定性图纸驱动的脚手架引擎：ZenWave 360

- **底层技术栈：** Java / TypeScript / OpenAPI / JDL (JHipster Domain Language)
    
- **它怎么解决 2-DAO-AE 的痛点：** 它是目前开源界将“准确的系统设计”转化为“代码骨架”最严谨的工具。它支持通过标准的 OpenAPI（Swagger）或 JDL 建模语言作为输入。
    
- **2-DAO-AE 场景用法：** 在动作 1（技术拓扑拆解）中，让大模型把准确的系统说明书翻译成标准 API 契约文本，ZenWave 能够 100% 零幻觉地一键生成所有 Spring Boot 的 Entity、Repository、Mapper 接口以及 DDL。它负责把“确定性的骨架”瞬间生成完，再把复杂的“业务核心算法 Issue”留给 Claude Code 去填空，效率与精准度拉满。
    
- **GitHub:** `https://github.com/zenwave360/zenwave-code-generator`
    

### ❸ 智能 Git 自动化合并与代码审查组件：Mergify / Govulncheck

- **底层技术栈：** Python / Go / GitHub Actions / GitLab Runner
    
- **它怎么解决 2-DAO-AE 的痛点：** 当 Claude Code 完成原子 Issue 并 Push 代码后，需要自动化组件来代替人类进行硬核审查。
    
- **2-DAO-AE 场景用法：** 利用离线部署的依赖安全检测工具，在沙箱编译通过后，自动审计代码中是否引入了不合规的内网包、是否有内存泄露风险，并根据预设规则自动决定该 Issue 对应的 PR 是自动合并，还是退回重写。
    
