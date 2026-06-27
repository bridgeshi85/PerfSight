# PerfSight

性能监控与分析系统，包含 Rust Agent 和 Python 分析引擎。

---

## 仓库结构

```
PerfSight/
├── database-monitor/  ← 数据库监控
├── examples/          ← 使用示例
├── python-analytics/  ← Python 分析引擎
└── rust-agent/        ← Rust 性能采集 Agent
```

## 核心约束

- commit message 遵循 conventional commits（`fix:` / `feat:` / `chore:`）
- 代码变更必须附带对应测试
- 不做 spec 范围外的假设性改动，有疑问先确认

## 分支策略

- **禁止直接提交 main 分支**
- 所有修改必须按以下流程：
  1. 从 main 创建新分支（`fix/`、`feat/`、`chore/` 开头）
  2. 完成修改并提交
  3. 推送到 GitHub 后创建 PR
  4. 告知改动内容并附 PR 链接
- **例外**：如果当前已在其他非 main 分支上工作，可以直接在该分支上提交，无需新建分支或 PR
