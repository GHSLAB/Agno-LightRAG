# LightRAG 与 AgentOS 集成

## 当前部署

- LightRAG 镜像：`ghcr.io/hkuds/lightrag:v1.5.7`，固定版本。
- 本机 Web UI/API：`http://localhost:9621`。
- AgentOS 容器访问地址：`http://lightrag:9621`。
- 语言模型：MiniMax-M3，端点 `https://api.minimaxi.com/v1`，复用 `.env` 中的 `MINIMAX_API_KEY`。
- 嵌入模型：本机 Ollama 的 `bge-m3:latest`，1024 维，容器通过 `host.docker.internal:11434` 调用。
- 访问密钥：`.env` 中的 `LIGHTRAG_API_KEY`，请求使用 `X-API-Key` 请求头。
- JWT 签名密钥：`.env` 中的 `LIGHTRAG_TOKEN_SECRET`，独立随机生成并传入服务的 `TOKEN_SECRET`。
- AgentOS agent：`lightrag-knowledge`，在 UI 中显示为 **LightRAG Knowledge**。
- Studio 注册表工具：`search_lightrag`，只读查询共享文档库。
- 存储：现有 `agentos-db` PostgreSQL 服务中的独立 `lightrag` 数据库，账号为 `lightrag`。

## 分工

LightRAG 导入文件后提取实体与关系，并建立向量和图谱索引。AgentOS 的检索工具调用
`POST /query/data` 获取结构化资料和引用，再由 MiniMax 生成最终回答。
检索模式为 `mix`，当前没有配置 reranker，因此查询显式关闭 rerank。

此知识库是共享语料：所有使用该工具的 agent 都可以检索其中资料。
AgentOS 的用户会话隔离不会自动转换为 LightRAG 文档权限。私人或租户专属资料需要另行设计隔离。
工具不提供导入、修改或删除能力；资料管理通过 LightRAG UI/API 进行。

## 使用

1. 确保本机 Ollama 正在运行，`bge-m3:latest` 模型可用。
2. 在项目目录执行 `docker compose up -d`。
3. 打开 `http://localhost:9621`，按页面要求填写 `.env` 中的 LightRAG API 密钥。
4. 上传文档，等待处理状态完成，再开始检索。
5. 在 AgentOS UI 刷新 agent 列表，选择 **LightRAG Knowledge** 提问；也可以通过 Agno 团队调用它。

不要将 `.env` 或包含密钥的文件上传到共享知识库。

## 存储与备份

LightRAG 的四类知识存储现已全部使用 PostgreSQL，配置如下：

| 类型 | 后端 | 内容 |
| --- | --- | --- |
| KV | `PGKVStorage` | 原文、分块、实体与关系映射、模型响应缓存 |
| 文档状态 | `PGDocStatusStorage` | 处理状态、追踪 ID、错误信息 |
| 图谱 | `PGTableGraphStorage` | PostgreSQL 普通表中的节点与边，无需 Apache AGE |
| 向量 | `PGVectorStorage` | pgvector 1024 维向量和 HNSW 索引 |

数据库连接：容器内部 `agentos-db:5432`，数据库 `lightrag`，用户 `lightrag`，
密码为 `.env` 中的 `LIGHTRAG_DB_PASSWORD`。Navicat 从 Windows 连接时使用
`127.0.0.1:5433`，数据库 `lightrag`。数据表位于 `public` Schema。

数据库物理数据保存在 `agent-platform_pgdata` 命名卷。以下 LightRAG 卷仍保留：

| 卷 | 容器路径 | 用途 |
| --- | --- | --- |
| `lightrag-storage` | `/app/data/rag_storage` | 工作目录、辅助文件和迁移前的文件索引；旧索引不再是当前查询的数据源 |
| `lightrag-inputs` | `/app/data/inputs` | 输入文件 |

Compose 会为卷名添加项目名前缀。重建容器会保留这些卷。
当前知识数据备份应使用 PostgreSQL 的 `pg_dump` 导出 `lightrag` 数据库，
并备份输入文件和需要保留的工作目录；恢复时使用相同版本与嵌入配置。
`docker compose down -v` 会删除包括 AgentOS 数据库在内的持久化卷，不用于日常重启。

这些索引不写入 `ai.product_knowledge` 或其他 Agno 知识表。
向量表名称包含嵌入模型与维度，例如 `lightrag_vdb_chunks_bge_m3_latest_1024d`。
`ai` 和 `lightrag` 是同一 PostgreSQL 实例中的两个独立数据库；Agno 表没有被迁移或修改。

### 本次迁移

2026-10-13 从文件存储迁移到 PostgreSQL。迁移前停止写入，旧工作目录和输入文件已备份到
`tmp/lightrag-pg-backup/`，旧 Docker 卷保留。旧模型响应缓存通过官方 PGKVStorage API 复制，
原有文档通过 LightRAG 文档接口重新索引。当前索引的 `db.md` 是迁移前文档内容的快照。

核对结果：1 份文档、2 个分块、52 个图谱节点、53 条关系，
对应的分块/实体/关系向量记录数分别为 2/52/53，文档状态为 processed。

## 模型配置

配置集中在 `compose.yaml` 的 `lightrag.environment`：

- `LLM_BINDING_HOST` / `LLM_MODEL`：MiniMax 端点与模型名。
- `EMBEDDING_BINDING_HOST` / `EMBEDDING_MODEL` / `EMBEDDING_DIM`：Ollama 地址、嵌入模型及维度。
- `OPENAI_LLM_EXTRA_BODY`：开启 `reasoning_split`，将思考内容与结果分开。

修改配置后执行 `docker compose up -d lightrag`，让 Compose 重建服务。
已有索引后不要直接更换嵌入模型或维度：新旧向量不可混用，需要按 LightRAG 的重建流程重新索引。

当前 Ollama 在 Windows 主机运行。迁移到生产主机时，需要让相同嵌入模型在该主机可用，
或调整为经过验证的远程/容器嵌入服务。LightRAG API 密钥独立于 AgentOS 的 JWT。

## 检查与故障排查

```powershell
docker compose ps lightrag
docker compose logs --tail 80 lightrag
```

- `/health` 是免认证存活检查；文档、查询和 Ollama 兼容 API 需要 API 密钥。
- 连接失败：检查 Ollama、Docker 网络和 `host.docker.internal:11434`。
- 无检索结果：检查文件是否处理完成，及问题是否被资料覆盖。
- 无法连接 AgentOS 中的工具：确认 `.env` 包含 `LIGHTRAG_URL=http://lightrag:9621` 和 API 密钥，
  环境变量修改后重新创建 `agentos-api` 容器。
- AgentOS 的 traces 可以查看检索工具调用；LightRAG 内部索引过程需要查看自身日志。

## 已验证的本地结果

核对日期：2026-10-13。

- LightRAG 健康检查通过，Web UI 与 AgentOS API 文档返回 HTTP 200。
- 未携带 API 密钥的查询返回 HTTP 403。
- 已导入 `docs/db.md`，文档处理完成，检索返回 2 个文本分块。
  LightRAG 将该来源路径规范化为 `db.md`，回答中引用此名称是正常行为。
- `lightrag-knowledge` 实际调用 `search_lightrag`，正确解释 `agno_schedule_runs` 并引用 `db.md`。
- 询问未记载的生产域名/上线日期和天气预报时，agent 明确说明资料不覆盖。
- 重建 LightRAG 容器后索引仍可检索；迁移后知识数据由 PostgreSQL 存储。
- 新增代码通过格式、lint 和 mypy 检查。

## 官方资料

- [LightRAG 项目](https://github.com/HKUDS/LightRAG)
- [v1.5.7 环境配置](https://github.com/HKUDS/LightRAG/blob/v1.5.7/env.example)
- [v1.5.7 查询接口](https://github.com/HKUDS/LightRAG/blob/v1.5.7/lightrag/api/routers/query_routes.py)
