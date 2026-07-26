# PerfSight Python Analytics — 单元测试计划 (UT Plan Spec)

> 基于 [python-testing-patterns](https://www.skills.sh/wshobson/agents/python-testing-patterns) skill 制定

## 1. 测试范围与优先级

| 优先级 | 模块 | 文件 | 测试类型 | 预估用例数 |
|:---:|------|------|:---:|:---:|
| P0 | 基础分析器 | `analyzers/base_analyzer.py` | Unit | 12 |
| P0 | 工具函数 | `utils.py` | Unit | 8 |
| P1 | 配置管理 | `config/settings.py` | Unit | 7 |
| P1 | 数据清洗 | `data_processor/cleaner.py` | Unit | 10 |
| P2 | CPU 分析器 | `analyzers/cpu_analyzer.py` | Unit | 6 |
| P2 | Memory 分析器 | `analyzers/memory_analyzer.py` | Unit | 5 |
| P2 | Network 分析器 | `analyzers/network_analyzer.py` | Unit | 4 |
| P2 | Disk 分析器 | `analyzers/disk_analyzer.py` | Unit | 7 |
| P3 | 指标处理器 | `data_processor/metrics_processor.py` | Unit (Mock) | 5 |
| P3 | 报告构建器 | `report_generator/report_builder.py` | Unit (Mock) | 4 |

**总计：约 68 个测试用例**

## 2. 测试目录结构

```
python-analytics/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # 共享 fixtures
│   ├── test_base_analyzer.py          # P0
│   ├── test_utils.py                  # P0
│   ├── test_settings.py               # P1
│   ├── test_cleaner.py                # P1
│   ├── test_cpu_analyzer.py           # P2
│   ├── test_memory_analyzer.py        # P2
│   ├── test_network_analyzer.py       # P2
│   ├── test_disk_analyzer.py          # P2
│   ├── test_metrics_processor.py      # P3
│   └── test_report_builder.py         # P3
├── pytest.ini                         # pytest 配置
├── .pylintrc                          # pylint 配置
└── UT_PLAN.md                         # 本文档
```

## 3. 各模块详细测试用例

### 3.1 `base_analyzer.py` (P0) — 纯函数，无外部依赖

| 用例 ID | 测试名称 | 模式 | 说明 |
|---------|---------|------|------|
| TC-BA-01 | `test_calculate_basic_stats_normal` | AAA | 正常数值序列的统计计算 |
| TC-BA-02 | `test_calculate_basic_stats_empty_series` | AAA | 空 Series 返回空 dict |
| TC-BA-03 | `test_calculate_basic_stats_with_nan` | AAA | 含 NaN 的序列自动跳过 |
| TC-BA-04 | `test_detect_anomalies_iqr_no_anomalies` | AAA | 均匀数据无异常点 |
| TC-BA-05 | `test_detect_anomalies_iqr_with_outliers` | AAA | 注入极端值后检测到异常 |
| TC-BA-06 | `test_detect_anomalies_iqr_empty_series` | AAA | 空序列返回 count=0 |
| TC-BA-07 | `test_detect_anomalies_iqr_zero_std` | AAA | 标准差为 0 时安全返回 |
| TC-BA-08 | `test_calculate_trend_increasing` | AAA | 上升趋势检测 |
| TC-BA-09 | `test_calculate_trend_decreasing` | AAA | 下降趋势检测 |
| TC-BA-10 | `test_calculate_trend_insufficient_data` | AAA | 少于 2 个点返回空 dict |
| TC-BA-11 | `test_calculate_basic_stats_single_value` | Parametrize | 单值序列 |
| TC-BA-12 | `test_calculate_basic_stats_all_same` | Parametrize | 全部相同值 std=0 |

**关键模式**: Fixtures (共享 sample Series), Parameterized, AAA

### 3.2 `utils.py` (P0) — 纯函数

| 用例 ID | 测试名称 | 模式 | 说明 |
|---------|---------|------|------|
| TC-UT-01 | `test_parse_labels_with_dict` | AAA | 输入已是 dict，直接返回 |
| TC-UT-02 | `test_parse_labels_with_json_string` | AAA | JSON 字符串正确解析 |
| TC-UT-03 | `test_parse_labels_with_nan` | AAA | NaN 输入返回空 dict |
| TC-UT-04 | `test_parse_labels_with_invalid_string` | AAA | 非法字符串返回空 dict |
| TC-UT-05 | `test_extract_disk_name_with_disk_key` | Parametrize | 从 labels 提取 disk 名称 |
| TC-UT-06 | `test_extract_disk_name_with_disk_name_key` | Parametrize | 从 labels 提取 disk_name |
| TC-UT-07 | `test_extract_disk_name_missing_keys` | AAA | 无相关 key 返回 'unknown' |
| TC-UT-08 | `test_extract_disk_name_non_dict` | AAA | 非 dict 输入返回 'unknown' |

**关键模式**: Parametrize, AAA

### 3.3 `config/settings.py` (P1) — 配置管理

| 用例 ID | 测试名称 | 模式 | 说明 |
|---------|---------|------|------|
| TC-CF-01 | `test_default_config_values` | AAA | 默认配置值正确 |
| TC-CF-02 | `test_load_from_file_valid_yaml` | tmp_path | 正常 YAML 文件加载 |
| TC-CF-03 | `test_load_from_file_missing` | tmp_path | 文件不存在返回默认配置 |
| TC-CF-04 | `test_load_from_file_partial` | tmp_path | 部分配置覆盖，其余默认 |
| TC-CF-05 | `test_save_and_reload_roundtrip` | tmp_path | 保存后重新加载数据一致 |
| TC-CF-06 | `test_data_processing_config_override` | AAA | 自定义 outlier_threshold |
| TC-CF-07 | `test_visualization_config_defaults` | AAA | 可视化默认开关正确 |

**关键模式**: tmp_path (文件 I/O), AAA

### 3.4 `data_processor/cleaner.py` (P1) — 数据清洗管道

| 用例 ID | 测试名称 | 模式 | 说明 |
|---------|---------|------|------|
| TC-CL-01 | `test_clean_directory_not_found` | Exception | 目录不存在抛 FileNotFoundError |
| TC-CL-02 | `test_clean_directory_empty` | tmp_path | 空目录返回空 DataFrame |
| TC-CL-03 | `test_clean_file_valid_csv` | tmp_path | 正常 CSV 清洗成功 |
| TC-CL-04 | `test_normalize_timestamp` | Fixture | 时间戳正确标准化并排序 |
| TC-CL-05 | `test_convert_values_numeric` | Fixture | 字符串值转浮点数 |
| TC-CL-06 | `test_convert_values_drop_invalid` | Fixture | 无法转换的行被丢弃 |
| TC-CL-07 | `test_parse_labels_pipeline` | Fixture | labels JSON 正确解析为 dict |
| TC-CL-08 | `test_handle_outliers_zscore` | Fixture | Z-score 异常值被中位数替换 |
| TC-CL-09 | `test_handle_outliers_disabled` | AAA | threshold<=0 时不做处理 |
| TC-CL-10 | `test_clean_file_not_found` | Exception | 文件不存在抛异常 |

**关键模式**: tmp_path, Fixtures (构造样本 DataFrame), Exception testing

### 3.5 `analyzers/cpu_analyzer.py` (P2)

| 用例 ID | 测试名称 | 模式 | 说明 |
|---------|---------|------|------|
| TC-CA-01 | `test_analyze_normal_cpu_data` | Fixture | 正常 CPU 数据统计正确 |
| TC-CA-02 | `test_analyze_high_load_warning` | Fixture | mean>75 触发 warning insight |
| TC-CA-03 | `test_analyze_high_load_ratio` | Fixture | >80% 比例计算正确 |
| TC-CA-04 | `test_analyze_empty_dataframe` | AAA | 空数据返回空 metrics |
| TC-CA-05 | `test_analyze_with_load_average` | Fixture | load_average 指标被处理 |
| TC-CA-06 | `test_analyze_no_cpu_usage_metric` | AAA | 无 cpu_usage_percent 数据 |

**关键模式**: Fixtures (构造 CPU DataFrame), AAA

### 3.6 `analyzers/memory_analyzer.py` (P2)

| 用例 ID | 测试名称 | 模式 | 说明 |
|---------|---------|------|------|
| TC-MA-01 | `test_analyze_normal_memory` | Fixture | 正常内存数据统计 |
| TC-MA-02 | `test_analyze_oom_risk_ratio` | Fixture | >90% 的 OOM 风险比例 |
| TC-MA-03 | `test_analyze_memory_leak_detection` | Fixture | 上升趋势+r²>0.7 触发 critical |
| TC-MA-04 | `test_analyze_empty_dataframe` | AAA | 空数据返回空结果 |
| TC-MA-05 | `test_analyze_uses_value_parsed` | Fixture | 优先使用 value_parsed 列 |

**关键模式**: Fixtures, AAA

### 3.7 `analyzers/network_analyzer.py` (P2)

| 用例 ID | 测试名称 | 模式 | 说明 |
|---------|---------|------|------|
| TC-NA-01 | `test_analyze_rx_tx_data` | Fixture | 收发字节数据统计 |
| TC-NA-02 | `test_analyze_empty_dataframe` | AAA | 空数据返回空 |
| TC-NA-03 | `test_analyze_only_rx` | Fixture | 仅有接收数据 |
| TC-NA-04 | `test_analyze_only_tx` | Fixture | 仅有发送数据 |

### 3.8 `analyzers/disk_analyzer.py` (P2)

| 用例 ID | 测试名称 | 模式 | 说明 |
|---------|---------|------|------|
| TC-DA-01 | `test_analyze_normal_disk_io` | Fixture | 正常磁盘读写分析 |
| TC-DA-02 | `test_analyze_empty_dataframe` | AAA | 空数据返回 summary |
| TC-DA-03 | `test_analyze_high_read_warning` | Fixture | 平均读>100MB/s 触发告警 |
| TC-DA-04 | `test_analyze_high_write_warning` | Fixture | 平均写>50MB/s 触发告警 |
| TC-DA-05 | `test_analyze_multiple_disks` | Fixture | 多磁盘分组分析 |
| TC-DA-06 | `test_analyze_io_spike_detection` | Fixture | IQR 异常突刺检测 |
| TC-DA-07 | `test_analyze_no_disk_data` | AAA | metric_type 无 disk 数据 |

**关键模式**: Fixtures (构造含 labels 的磁盘 DataFrame), Mock (parse_labels)

### 3.9 `data_processor/metrics_processor.py` (P3)

| 用例 ID | 测试名称 | 模式 | 说明 |
|---------|---------|------|------|
| TC-MP-01 | `test_process_empty_dataframe` | AAA | 空 DataFrame 返回空 dict |
| TC-MP-02 | `test_process_routes_to_analyzers` | Mock | 验证数据正确分发给各分析器 |
| TC-MP-03 | `test_process_builds_summary` | Fixture | summary 包含 total_records 和 time_range |
| TC-MP-04 | `test_process_unknown_metric_type` | Fixture | 未知 metric_type 被跳过 |
| TC-MP-05 | `test_process_aggregates_results` | Mock | 各分析器结果正确聚合 |

**关键模式**: Mock (patch analyzers), Fixture

### 3.10 `report_generator/report_builder.py` (P3)

| 用例 ID | 测试名称 | 模式 | 说明 |
|---------|---------|------|------|
| TC-RB-01 | `test_build_overview_cards` | AAA | 概览卡片 HTML 包含关键数据 |
| TC-RB-02 | `test_build_plotly_charts_empty` | AAA | 空 charts 返回提示文本 |
| TC-RB-03 | `test_generate_report_missing_template` | Exception | 模板不存在抛 FileNotFoundError |
| TC-RB-04 | `test_generate_html_report_success` | tmp_path+Mock | 完整报告生成流程 |

**关键模式**: tmp_path, Mock (Plotly figures), Exception testing

## 4. 基础设施配置

### 4.1 pytest 配置 (`pytest.ini`)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: 单元测试
    integration: 集成测试
    slow: 慢速测试
```

### 4.2 pylint 配置 (`.pylintrc`)

- 初始阈值: `fail-under=6.0`（逐步提升至 8.0）
- 禁用与测试文件冲突的规则
- 适配 pandas/numpy 命名风格

### 4.3 依赖 (`requirements-test.txt`)

```
pytest>=7.0
pytest-cov>=4.0
pylint>=3.0
```

## 5. 执行策略

1. **Phase 1** (本次): P0 + P1 模块 — base_analyzer, utils, settings, cleaner
2. **Phase 2** (后续): P2 模块 — 四个分析器
3. **Phase 3** (后续): P3 模块 — metrics_processor, report_builder
4. **CI 集成**: 后续可添加 GitHub Actions workflow

## 6. 测试原则

- 遵循 **AAA 模式** (Arrange-Act-Assert)
- 每个测试只验证**一个行为**
- 同时覆盖**正常路径和异常路径**
- 使用 **Fixture** 复用样本数据，避免重复构造
- 使用 **tmp_path** 隔离文件 I/O 测试
- 使用 **Mock** 隔离外部依赖
- 命名规范: `test_<方法>_<场景>_<预期>`
