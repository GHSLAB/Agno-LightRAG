# 开发目录迁移记录

2026-10-13，将 `D:\DevAgno\agent-platform` 的代码、配置、脚本与文档迁移到
`D:\DevAgno\Agno-LightRAG`，后续开发以本目录为准。保留目标仓库原有 Git 历史；
本次未自动提交。源项目本地 `.env` 已复制到目标目录，仍由 `.gitignore` 排除。

迁移包含 Agno 3.1.3、MiniMax-M3 模型配置、LightRAG 服务和只读检索 Agent、
Studio 工具注册、评测模型配置以及 Shell 脚本 LF 换行设置。

## 运行环境边界

本次没有切换正在运行的 Docker 容器，没有迁移数据库或输入文件，也没有复制
`tmp/`、缓存和 Git 元数据。现有容器的代码挂载仍指向源目录。

两个目录的 Compose 使用相同容器名称和 API 端口，不能直接同时启动。
从新目录启动时，Compose 默认项目名为 `agno-lightrag`，会使用新的命名卷；
`lightrag.md` 中的 `agent-platform_pgdata` 和已验证数据描述属于原部署。
需要延续现有数据时，应先核实实际 Compose 项目名和卷名，再安排容器切换，
避免误用空卷。不要用 `docker compose down -v` 做目录切换。

新数据库环境还需创建 LightRAG 使用的 `lightrag` 数据库及账号；当前 Compose
没有自动初始化这一数据库和账号的脚本。嵌入服务仍依赖主机 Ollama 的 BGE-M3。

## 检查

迁移文件与源文件逐字节核对一致。开发与生产 Compose 配置检查、Ruff 格式与
lint 检查，以及 Python 3.14 对全部 29 个 Python 源文件的语法检查通过。
本次未运行会调用模型或写入数据库的在线评测。
