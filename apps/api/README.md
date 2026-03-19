# API

## 运行
1. 安装依赖：
   `python3 -m pip install -r requirements.txt`
2. 启动：
   `python3 -m uvicorn app.main:app --reload --port 8000`

## 大模型配置（可选但推荐）
在启动前设置环境变量：

```bash
export OPENAI_API_KEY="你的Key"
export OPENAI_MODEL="gpt-4o-mini"
```

未设置 `OPENAI_API_KEY` 时，系统会走无模型降级模式（仍会检索数据，但语言生成能力较弱）。

开启 `OPENAI_API_KEY` 后，`/generate` 会先做自然语言意图解析与球队实体识别，再执行检索，避免手工维护关键词表。

## 接口
- `GET /health`
- `GET /cba/search?q=...&limit=5`
- `POST /generate`（检索增强对话）
- `POST /facts/check`
- `POST /draft/rewrite`（改写选中段落）

返回字段包含 page/para/text/score，可用于在前端做引用标记。
