# AgentOS 数据库表说明

本文根据当前运行的 Agno 3.1.3 实例整理，核对日期：2026-10-13。

当前 PostgreSQL 数据库名为 `ai`。数据库内的 `ai`、`fs` 是 Schema（命名空间），不是两个独立数据库。以下结构可能随 Agno 版本和启用的功能变化；表存在不代表当前功能已经使用它。

## ai Schema

当前 `ai` Schema 共包含 22 张表。

### 对话、运行与监控

| 表 | 功能 |
| --- | --- |
| `agno_sessions` | 保存会话信息，包括用户、所属 agent/team/workflow、摘要和元数据。一次连续聊天通常对应一个 session。 |
| `agno_runs` | 保存每次执行的状态、运行数据及父子运行关系。一个 session 可以包含多个 run。 |
| `agno_traces` | 保存执行追踪总览，包括耗时、状态和关联的 run、session、用户及组件。 |
| `agno_spans` | 保存追踪中的具体步骤，例如模型请求、工具调用。通过 `trace_id` 和 `parent_span_id` 组成调用链。 |
| `agno_metrics` | 保存聚合统计，包括运行次数、会话数、用户数、Token 和模型用量。 |
| `agno_tool_results` | 保存大型工具结果的索引和摘要，包括路径、预览、内容类型、大小、所属运行及过期时间，供 agent 按需读取。该表没有完整结果正文的 `content` 列。 |
| `agno_eval_runs` | 保存评测输入、评分数据、被评测组件和所用模型信息。 |

### 记忆与学习

| 表 | 功能 |
| --- | --- |
| `agno_learnings` | 保存 LearningMachine 的学习记录。通过学习类型、命名空间、用户和实体等字段区分记录。当前模板采用这一学习机制。 |
| `agno_memories` | 保存 MemoryManager 的用户记忆，包括事实、偏好、主题和反馈。与 `agno_learnings` 属于不同的记忆机制。 |

会话记录用于还原“聊过什么”；学习和记忆记录用于保留“哪些信息值得以后继续使用”。

### 知识库

| 表 | 功能 |
| --- | --- |
| `shared_knowledge` | 保存共享知识库的文本分块、向量 `embedding`、内容哈希和检索元数据。 |
| `shared_knowledge_contents` | 保存共享知识库原始资料的目录、来源元数据、处理状态和大小等信息。 |
| `product_knowledge` | 保存产品知识库的文本分块、向量和检索元数据，供产品问答 agent 使用。 |
| `product_knowledge_contents` | 保存产品知识库原始资料的目录及处理状态。 |
| `agno_knowledge` | 默认知识内容管理表。当前模板的两个知识库指定了各自的 `*_contents` 表，因此不一定使用此表。 |

`*_contents` 管理“导入了哪些资料、处理到哪一步”；向量表管理“资料拆成哪些片段、如何检索”。当前模板的知识库嵌入仍使用 OpenAIEmbedder，需要配置对应密钥；语言模型已改为 MiniMax-M3。

### Studio 创建的组件

| 表 | 功能 |
| --- | --- |
| `agno_components` | 保存运行时创建的 agent、team、workflow 的基本信息、所有者和当前版本指针。 |
| `agno_component_configs` | 保存组件各版本的配置、发布阶段、标签和备注。 |
| `agno_component_links` | 保存组件之间的组合关系，例如团队成员、工作流子组件、关联版本及顺序。 |

这些表主要用于 Builder/Studio 动态创建的组件。源码定义的 agent 仍在 Python 文件中维护。

### 调度、审批与认证

| 表 | 功能 |
| --- | --- |
| `agno_schedules` | 保存定时任务定义，包括 Cron、时区、目标、参数、启用状态、下次运行时间和重试设置。 |
| `agno_schedule_runs` | 保存定时任务每次触发的状态、错误、输入输出、重试次数和关联 run。 |
| `agno_approvals` | 保存待人工确认的操作，包括工具参数、审批要求、状态、处理人及处理结果。 |
| `agno_service_accounts` | 保存服务账号、Token 哈希与前缀、权限范围、有效期和撤销状态。 |
| `agno_schema_versions` | 保存各表的结构版本，供框架管理数据库结构升级。 |

## fs Schema

### fs.agno_fs

`fs.agno_fs` 是 Agno 的数据库文件存储表。它把虚拟文件路径和文本内容持久化到 PostgreSQL，并不是 Docker 磁盘上的普通文件。

当前模板在 `app/notes.py` 中创建 `FileSystem`，使用 `shared-notes` 命名空间实现共享笔记本。Agent 可以记录和读取项目决定、工作笔记、日志或收集的资料。

| 字段 | 含义 |
| --- | --- |
| `namespace` | 文件所属空间，例如 `shared-notes`。 |
| `path` | 虚拟文件路径。 |
| `content` | 文件文本内容。 |
| `size_bytes` | 内容字节数。 |
| `version` | 文件版本号。 |
| `created_at` | 创建时间，数据库类型为 bigint。 |
| `updated_at` | 更新时间，数据库类型为 bigint，可为空。 |
| `user_id` | 用户隔离标识，默认值为空字符串。 |

主键为 `(namespace, user_id, path)`，因此不同空间或用户可以拥有同名路径。共享笔记、聊天会话和用户记忆分别由各自的存储机制管理。

## lightrag 数据库（PostgreSQL）

2026-10-13，LightRAG 已切换为同一 `agentos-db` 实例中的独立 `lightrag` 数据库。
它使用自己的 `lightrag` 账号和 `public` Schema，与上面的 `ai` 数据库隔离。
Navicat 连接使用主机 `127.0.0.1`、端口 `5433`、数据库和用户名 `lightrag`，
密码见本机 `.env` 中的 `LIGHTRAG_DB_PASSWORD`。

| 表 | 功能 |
| --- | --- |
| `lightrag_doc_full` | 原始文档内容、来源、解析方式和分块配置。 |
| `lightrag_doc_chunks` | 文本分块、顺序、所属文档、Token 数和相关缓存 ID。 |
| `lightrag_doc_status` | 文档处理状态、追踪 ID、分块清单、处理元数据和错误信息。 |
| `lightrag_full_entities` | 每份文档关联的实体名称清单。 |
| `lightrag_full_relations` | 每份文档关联的关系端点清单。 |
| `lightrag_entity_chunks` | 实体与来源文本分块的映射。 |
| `lightrag_relation_chunks` | 关系与来源文本分块的映射。 |
| `lightrag_graph_nodes` | 图谱节点 ID、属性，以及 workspace/namespace 隔离字段。 |
| `lightrag_graph_edges` | 图谱边的起点、终点、属性及 workspace/namespace。 |
| `lightrag_llm_cache` | 模型响应缓存，包括原始提示、返回内容、缓存类型和查询参数。 |
| `lightrag_vdb_chunks_bge_m3_latest_1024d` | 文本分块的 1024 维 pgvector 向量与检索内容。 |
| `lightrag_vdb_entity_bge_m3_latest_1024d` | 实体的 1024 维向量、名称、描述及来源分块。 |
| `lightrag_vdb_relation_bge_m3_latest_1024d` | 关系的 1024 维向量、端点、描述及来源分块。 |

向量表名的模型/维度后缀由 LightRAG 生成，换用其他嵌入配置时名称可能变化。
图谱使用 `PGTableGraphStorage` 普通表实现，没有启用 Apache AGE。
旧 LightRAG 文件索引卷保留用于回退，但不再是运行中的知识数据源。

## 常见查询路径

- 排查一次对话：先查看 `agno_sessions`，再通过 `session_id` 查找 `agno_runs`。
- 排查执行耗时和工具调用：查看关联的 `agno_traces`、`agno_spans`。
- 排查定时任务：查看 `agno_schedules` 的定义和 `agno_schedule_runs` 的执行结果。
- 查看评测：查询 `agno_eval_runs`。
- 检查知识导入：先看对应的 `*_contents` 状态，再看向量表中的分块。
- 查看共享笔记：查询 `fs.agno_fs` 中 `namespace = 'shared-notes'` 的记录。

## 维护注意事项

这些表由 Agno 管理。Navicat 适合查询和检查；组件配置、审批、调度和运行状态的修改优先通过 AgentOS UI/API，避免破坏版本关系或执行状态。直接删除会话、记忆、知识或笔记记录，会影响 agent 后续读取的数据。数据库结构升级前应备份数据。

## 依据

- 当前 PostgreSQL 实例的 `information_schema.columns` 和 `fs.agno_fs` 表结构。
- 模板源码：`app/main.py`、`app/knowledge.py`、`app/learning.py`、`app/notes.py`、`db/session.py`、`app/registry.py`。
