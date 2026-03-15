"""
AI 智能诊断分析模块
"""

import logging
from typing import Dict, Any, Optional, List
import pandas as pd
import json

from config.settings import AnalyticsConfig
from .llm_client import LLMClient

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """AI 智能分析器"""
    
    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.ai_config = config.ai_analysis
        self.llm_client = LLMClient(config)
    
    async def analyze(self, df: pd.DataFrame, analysis_results: Dict[str, Any], 
                     charts: Dict[str, Any]) -> Dict[str, Any]:
        """执行 AI 智能分析"""
        
        if not self._is_ai_enabled():
            logger.info("AI 分析未启用")
            return {}
        
        logger.info("开始 AI 智能分析...")
        
        ai_insights = {
            'summary': await self._generate_summary(df, analysis_results),
            'anomaly_analysis': None,
            'root_cause_analysis': None,
            'optimization_suggestions': None,
            'risk_assessment': await self._assess_risks(analysis_results),
        }
        
        # 异常检测分析
        if self.ai_config.enable_anomaly_detection and 'anomalies' in analysis_results:
            ai_insights['anomaly_analysis'] = await self._analyze_anomalies(
                analysis_results['anomalies']
            )
        
        # 根因分析
        if self.ai_config.enable_root_cause_analysis:
            ai_insights['root_cause_analysis'] = await self._root_cause_analysis(
                df, analysis_results
            )
        
        # 优化建议
        if self.ai_config.enable_optimization_suggestions:
            ai_insights['optimization_suggestions'] = await self._generate_optimization_suggestions(
                analysis_results
            )
        
        logger.info("AI 智能分析完成")
        return ai_insights
    
    def _is_ai_enabled(self) -> bool:
        """检查 AI 功能是否启用"""
        if self.ai_config.provider == "openai":
            return bool(self.ai_config.openai_api_key)
        elif self.ai_config.provider == "anthropic":
            return bool(self.ai_config.anthropic_api_key)
        elif self.ai_config.provider == "local":
            return bool(self.ai_config.local_model_url)
        return False
    
    async def _generate_summary(self, df: pd.DataFrame, analysis_results: Dict[str, Any]) -> str:
        """生成性能分析摘要"""
        
        # 构建分析上下文
        context = self._build_analysis_context(df, analysis_results)
        
        prompt = f"""
作为一名资深的系统性能分析专家，请基于以下性能监控数据分析结果，生成一份简洁的中文摘要报告：

## 数据概览
{context['data_overview']}

## 性能指标统计
{context['performance_stats']}

## 趋势分析
{context['trends']}

## 异常情况
{context['anomalies']}

请提供：
1. 系统整体性能状况评估
2. 主要发现和关键指标
3. 需要关注的问题
4. 简要的改进方向

要求：
- 使用专业但易懂的语言
- 重点突出关键问题
- 控制在200字以内
"""
        
        try:
            response = await self.llm_client.generate_response(prompt)
            return response
        except Exception as e:
            logger.error(f"生成摘要失败: {e}")
            return "AI 分析摘要生成失败，请检查配置和网络连接。"
    
    async def _analyze_anomalies(self, anomalies: Dict[str, Any]) -> str:
        """分析异常情况"""
        
        if anomalies['total_anomalies'] == 0:
            return "未检测到明显异常。"
        
        prompt = f"""
作为系统性能专家，请分析以下异常检测结果：

异常总数：{anomalies['total_anomalies']}

异常详情：
{json.dumps(anomalies['anomaly_details'], indent=2, ensure_ascii=False)}

请分析：
1. 异常的严重程度
2. 可能的原因
3. 对系统的潜在影响
4. 建议的处理措施

请用中文回答，控制在150字以内。
"""
        
        try:
            response = await self.llm_client.generate_response(prompt)
            return response
        except Exception as e:
            logger.error(f"异常分析失败: {e}")
            return "异常分析失败。"
    
    async def _root_cause_analysis(self, df: pd.DataFrame, analysis_results: Dict[str, Any]) -> str:
        """根因分析"""
        
        # 识别主要性能问题
        issues = self._identify_performance_issues(analysis_results)
        
        if not issues:
            return "未发现明显的性能问题。"
        
        prompt = f"""
作为系统性能诊断专家，请对以下性能问题进行根因分析：

发现的问题：
{json.dumps(issues, indent=2, ensure_ascii=False)}

系统指标概况：
- 数据记录数：{len(df)}
- 监控时长：{analysis_results.get('summary', {}).get('time_range', {}).get('duration_hours', 'N/A')} 小时

请分析：
1. 最可能的根本原因
2. 问题之间的关联性
3. 影响范围评估
4. 解决优先级建议

请用中文回答，控制在200字以内。
"""
        
        try:
            response = await self.llm_client.generate_response(prompt)
            return response
        except Exception as e:
            logger.error(f"根因分析失败: {e}")
            return "根因分析失败。"
    
    async def _generate_optimization_suggestions(self, analysis_results: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        
        suggestions_context = self._build_optimization_context(analysis_results)
        
        prompt = f"""
作为系统优化专家，基于以下性能分析结果，请提供具体的优化建议：

{suggestions_context}

请提供5-8条具体的优化建议，每条建议包括：
- 优化目标
- 具体措施
- 预期效果

格式要求：
- 每条建议独立成行
- 使用中文
- 按重要性排序
- 每条建议控制在30字以内
"""
        
        try:
            response = await self.llm_client.generate_response(prompt)
            # 解析建议列表
            suggestions = [line.strip() for line in response.split('\n') if line.strip()]
            return suggestions[:8]  # 最多返回8条建议
        except Exception as e:
            logger.error(f"生成优化建议失败: {e}")
            return ["优化建议生成失败，请检查AI配置。"]
    
    async def _assess_risks(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """风险评估"""
        
        risk_assessment = {
            'overall_risk_level': 'low',
            'risk_factors': [],
            'recommendations': []
        }
        
        # 基于分析结果评估风险
        if 'performance_metrics' in analysis_results:
            cpu_metrics = analysis_results['performance_metrics'].get('cpu', {})
            if cpu_metrics.get('high_usage_percentage', 0) > 20:
                risk_assessment['risk_factors'].append('CPU高使用率频繁')
                risk_assessment['overall_risk_level'] = 'medium'
        
        if 'anomalies' in analysis_results:
            if analysis_results['anomalies']['total_anomalies'] > 10:
                risk_assessment['risk_factors'].append('异常数据点过多')
                risk_assessment['overall_risk_level'] = 'high'
        
        return risk_assessment
    
    def _build_analysis_context(self, df: pd.DataFrame, analysis_results: Dict[str, Any]) -> Dict[str, str]:
        """构建分析上下文"""
        
        context = {}
        
        # 数据概览
        summary = analysis_results.get('summary', {})
        context['data_overview'] = f"""
- 总记录数：{summary.get('total_records', 0)}
- 时间范围：{summary.get('time_range', {}).get('duration_hours', 'N/A')} 小时
- 指标类型：{len(summary.get('metric_types', {}))} 种
"""
        
        # 性能统计
        perf_metrics = analysis_results.get('performance_metrics', {})
        context['performance_stats'] = json.dumps(perf_metrics, indent=2, ensure_ascii=False)
        
        # 趋势信息
        trends = analysis_results.get('trends', {})
        context['trends'] = json.dumps(trends, indent=2, ensure_ascii=False)
        
        # 异常信息
        anomalies = analysis_results.get('anomalies', {})
        context['anomalies'] = f"异常总数：{anomalies.get('total_anomalies', 0)}"
        
        return context
    
    def _identify_performance_issues(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别性能问题"""
        
        issues = []
        
        # 检查 CPU 问题
        cpu_metrics = analysis_results.get('performance_metrics', {}).get('cpu', {})
        if cpu_metrics.get('high_usage_percentage', 0) > 15:
            issues.append({
                'type': 'cpu_high_usage',
                'severity': 'medium',
                'description': f"CPU高使用率占比 {cpu_metrics['high_usage_percentage']:.1f}%"
            })
        
        # 检查异常问题
        anomalies = analysis_results.get('anomalies', {})
        if anomalies.get('total_anomalies', 0) > 5:
            issues.append({
                'type': 'data_anomalies',
                'severity': 'low',
                'description': f"检测到 {anomalies['total_anomalies']} 个异常数据点"
            })
        
        return issues
    
    def _build_optimization_context(self, analysis_results: Dict[str, Any]) -> str:
        """构建优化上下文"""
        
        context_parts = []
        
        # 性能指标
        perf_metrics = analysis_results.get('performance_metrics', {})
        if perf_metrics:
            context_parts.append(f"性能指标：{json.dumps(perf_metrics, ensure_ascii=False)}")
        
        # 异常情况
        anomalies = analysis_results.get('anomalies', {})
        if anomalies.get('total_anomalies', 0) > 0:
            context_parts.append(f"异常情况：{anomalies['total_anomalies']} 个异常点")
        
        # 趋势分析
        trends = analysis_results.get('trends', {})
        if trends:
            context_parts.append(f"趋势分析：{len(trends)} 个指标趋势")
        
        return '\n'.join(context_parts)