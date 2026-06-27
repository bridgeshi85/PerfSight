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
- Rust 代码：编译通过 `cargo build`
- Python 代码：语法通过，不强制写 UT
- 如果有现有测试套件，改完后运行验证不破坏
- 不做 spec 范围外的假设性改动，有疑问先确认

## 分支策略

- **禁止直接提交 main 分支**
- 所有修改必须按以下流程：
  1. 从 main 创建新分支（`fix/`、`feat/`、`chore/` 开头）
  2. 完成修改并提交
  3. 推送到 GitHub 后创建 PR
  4. 告知改动内容并附 PR 链接
- **例外**：如果当前已在其他非 main 分支上工作，可以直接在该分支上提交，无需新建分支或 PR

## Rust Agent 修改验证流程

修改 `rust-agent/` 目录下的代码后，**必须执行以下验证步骤**：

1. **构建验证**
   ```bash
   cd rust-agent
   cargo build
   ```
   - 确保代码编译通过，无错误或警告（如有必要的警告，应在 commit message 中说明）

2. **测试验证**
   ```bash
   cd rust-agent
   cargo test
   ```
   - 运行全部测试用例，确保改动不破坏现有功能
   - 若有新增功能，应添加对应的测试用例

3. **验证完成后**
   - 在 PR 描述中明确标注：✅ `cargo build` 通过 / ✅ `cargo test` 通过
   - 如有特殊情况（如已知的编译警告或跳过的测试），需在 PR 中详细说明

