# KnowledgeOS

一个面向研究主题的自动化知识整理流水线项目。输入一个主题后，系统会完成资料检索、来源整理、知识构建和产物落盘，并提供可测试、可观测、可持续集成的工程化能力。

## 1. 项目目标

- 根据输入主题自动生成研究笔记与结构化元数据
- 建立稳定的工程流程（测试、契约校验、CI）
- 在外部依赖不稳定（例如网络/SSL）时，保持核心回归流程可执行

## 2. 目录结构

- `agents/`：核心流水线与各阶段 Agent
  - `research_agent.py`：检索来源并归一化
  - `analysis_agent.py`：提取 URL 并生成 NotebookLM 输入
  - `knowledge_agent.py`：构建知识内容
  - `writer_agent.py`：写入 Markdown/JSON/run 元数据
  - `orchestrator.py`：流水线编排
  - `research.py`：CLI 入口
- `tools/`
  - `youtube_search.py`：YouTube 检索封装（支持参数化配置）
  - `notebooklm/notebooklm_prompt.py`：提示词构建
- `tests/`：单元测试与契约测试
- `.github/workflows/ci.yml`：CI 工作流
- `Makefile`：标准化命令入口

## 3. 运行环境

- Python 3.12（项目当前验证环境）
- macOS（当前开发环境）

安装依赖：

```bash
python -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m pip install -U pytest
```

## 4. 快速开始

运行研究流水线：

```bash
make run TOPIC="AI Agent Framework"
```

或直接运行入口：

```bash
./.venv/bin/python -m agents.research "AI Agent Framework"
```

## 5. 常用命令

- `make install`：安装依赖
- `make test`：执行全部测试
- `make contract`：执行契约相关测试
- `make ci`：执行稳定回归（不依赖外网）
- `make smoke`：联网冒烟验证（依赖外网和本机 SSL 环境）
- `make run TOPIC="..."`：执行完整流水线

## 6. 输出产物

默认输出目录：`02_Research/`

会生成以下文件（按 topic slug 命名）：

- `*.md`：最终笔记
- `*.json`：结构化内容
- `*.run.json`：运行元数据

`run.json` 当前契约版本：`schema_version = "1.1"`，包含：

- `run_id`
- `status`
- `duration_ms`
- `topic`
- `source_count`
- `generated_at`
- `artifacts`（markdown/json/run 三个路径）

## 7. 配置项（环境变量）

`tools/youtube_search.py` 支持以下环境变量：

- `YOUTUBE_MAX_RESULTS`（默认 5，范围 1~50）
- `YOUTUBE_TIMEOUT_SECONDS`（默认 20，范围 1~120）
- `YOUTUBE_RETRIES`（默认 3，范围 0~10）

示例：

```bash
export YOUTUBE_MAX_RESULTS=8
export YOUTUBE_TIMEOUT_SECONDS=25
export YOUTUBE_RETRIES=4
make smoke
```

## 8. 测试与质量保障

当前已覆盖的关键测试包括：

- Research 结果归一化
- 依赖缺失异常处理（`yt-dlp`）
- SSL 证书失败场景错误提示
- Analysis 空来源处理
- Orchestrator 执行顺序与容错
- Writer 产物与契约字段校验

推荐每次开发提交前执行：

```bash
make test
make contract
make ci
```

## 9. 常见问题

### 9.1 `make smoke` 出现 SSL 证书错误

现象：`CERTIFICATE_VERIFY_FAILED`

处理建议：

1. 更新依赖：
   ```bash
   ./.venv/bin/python -m pip install -U certifi yt-dlp
   ```
2. 配置证书环境变量：
   ```bash
   export SSL_CERT_FILE="$(./.venv/bin/python -c 'import certifi; print(certifi.where())')"
   export REQUESTS_CA_BUNDLE="$SSL_CERT_FILE"
   export CURL_CA_BUNDLE="$SSL_CERT_FILE"
   ```

### 9.2 为什么 `make ci` 不包含联网步骤？

`ci` 目标强调稳定回归，不受外网波动影响。联网验证已拆分到 `make smoke`，按需手动执行。

## 10. 后续迭代建议

- 抽离统一 `Source` schema 校验模块
- 增加网络失败降级策略（更细粒度错误码/状态）
- 推进日志 JSON 化，便于检索和观测平台接入