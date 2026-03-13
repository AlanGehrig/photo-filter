# -*- coding: utf-8 -*-
"""
AI迭代管理器 - 理解用户需求并优化筛选规则
"""
import json
import os
from datetime import datetime


# AI交互的Prompt模板
AI_PROMPT_TEMPLATE = """
你是一个摄影师专用照片筛选工具的智能迭代助手，需要理解用户需求并优化筛选规则。
请按以下信息完成迭代任务：

【基础信息】
1. 工具核心功能：自动筛选照片，支持按用途（人像/婚礼/风光）分档，输出精修候选/可直出/废片
2. 当前筛选规则权重：{current_weights}
3. 历史用户操作记录：{user_operation_logs}
4. 近期筛选准确率统计：{accuracy_stats}

【用户当前指令】
{user_command}

【任务要求】
1. 若用户是调整规则：输出新的权重配置（JSON格式），并说明调整理由（适配摄影师审美）；
2. 若用户是标记修正：分析用户偏好，输出规则迭代建议；
3. 若用户是新增需求：设计对应的筛选维度+规则，并给出实现逻辑（轻量化，适配现场使用）；
4. 所有输出优先保证：离线可用、速度快、不删原图、适配摄影师现场选片场景。

【输出格式】
请先输出调整理由，然后用JSON格式输出新的权重配置：
```json
{{
  "blur_score": 0.3,
  "exposure": 0.25,
  "face_quality": 0.35,
  "composition": 0.1
}}
```
"""


class IterationAI:
    """AI迭代核心类"""
    
    def __init__(self, ai_type="local", api_key=None):
        """
        初始化
        
        Args:
            ai_type: AI类型 - local/chatgpt/claude
            api_key: API密钥（云端AI需要）
        """
        self.ai_type = ai_type
        self.api_key = api_key
    
    def generate_iteration_plan(self, intent_data: dict, current_weights: dict, 
                                  user_logs: list, accuracy_stats: dict) -> tuple:
        """
        调用AI生成迭代方案
        
        Args:
            intent_data: 解析后的用户意图
            current_weights: 当前权重配置
            user_logs: 用户操作日志
            accuracy_stats: 准确率统计
            
        Returns:
            (new_weights, reason): 新的权重配置和调整理由
        """
        # 拼接Prompt
        prompt = AI_PROMPT_TEMPLATE.format(
            current_weights=json.dumps(current_weights, ensure_ascii=False, indent=2),
            user_operation_logs=json.dumps(user_logs[:5], ensure_ascii=False),
            accuracy_stats=json.dumps(accuracy_stats, ensure_ascii=False),
            user_command=intent_data.get("detail", "")
        )
        
        # 根据AI类型调用
        if self.ai_type == "chatgpt":
            ai_output = self._call_openai(prompt)
        elif self.ai_type == "claude":
            ai_output = self._call_claude(prompt)
        else:
            # 本地模拟AI响应（实际项目中替换为本地模型调用）
            ai_output = self._local_ai_response(intent_data, current_weights)
        
        # 解析AI输出
        return self._parse_ai_output(ai_output, current_weights)
    
    def _call_openai(self, prompt: str) -> str:
        """调用OpenAI API"""
        import requests
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3
                },
                timeout=30
            )
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"API调用失败: {e}"
    
    def _call_claude(self, prompt: str) -> str:
        """调用Claude API"""
        # 类似实现
        return self._local_ai_response({}, {})
    
    def _local_ai_response(self, intent_data: dict, current_weights: dict) -> str:
        """
        本地AI响应（轻量级实现）
        根据用户意图直接生成规则调整建议
        """
        action = intent_data.get("user_action", "")
        purpose = intent_data.get("photo_purpose", "通用")
        dimensions = intent_data.get("filter_dimension", [])
        
        # 根据意图生成响应
        if action == "调整权重":
            weights = current_weights.copy()
            reason = f"根据{purpose}场景调整权重"
            
            if "模糊度" in dimensions:
                weights["blur_score"] = 0.3
                reason += "，降低模糊度权重"
            if "人脸质量" in dimensions:
                weights["face_quality"] = 0.35
                reason += "，提高人脸质量权重"
            if "曝光度" in dimensions:
                weights["exposure"] = 0.25
                
            return f"{reason}\n{json.dumps(weights, ensure_ascii=False, indent=2)}"
            
        elif action == "新增规则":
            return f"新增筛选维度：{', '.join(dimensions)}\n{json.dumps(current_weights, ensure_ascii=False)}"
            
        elif action == "标记修正":
            return "分析用户偏好，建议优化模糊度检测阈值"
            
        else:
            return json.dumps(current_weights, ensure_ascii=False, indent=2)
    
    def _parse_ai_output(self, ai_output: str, default_weights: dict) -> tuple:
        """
        解析AI输出
        
        Args:
            ai_output: AI返回的文本
            default_weights: 默认权重（解析失败时使用）
            
        Returns:
            (new_weights, reason)
        """
        try:
            # 尝试提取JSON
            json_start = ai_output.find("{")
            json_end = ai_output.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = ai_output[json_start:json_end]
                new_weights = json.loads(json_str)
                reason = ai_output[:json_start].strip()
                return new_weights, reason
            
        except json.JSONDecodeError:
            pass
        
        # 解析失败，返回默认
        return default_weights, "使用默认配置"


class AIIterationManager:
    """AI迭代管理器 - 完整迭代流程"""
    
    def __init__(self, config_path="./config/rules.yaml"):
        self.config_path = config_path
        self.ai = IterationAI(ai_type="local")
        self.intent_parser = None  # 延迟导入避免循环依赖
        
        # 日志文件路径
        self.log_dir = "./logs"
        os.makedirs(self.log_dir, exist_ok=True)
    
    def _get_intent_parser(self):
        """延迟加载IntentParser"""
        if self.intent_parser is None:
            from .intent_parser import IntentParser
            self.intent_parser = IntentParser()
        return self.intent_parser
    
    def iterate(self, user_input: str) -> dict:
        """
        完整AI迭代流程：解析需求→调用AI→更新配置
        
        Args:
            user_input: 用户自然语言输入
            
        Returns:
            迭代结果字典
        """
        # 1. 解析用户需求为语义标签
        parser = self._get_intent_parser()
        intent_data = parser.parse(user_input)
        print(f"[AI] 解析用户需求：{intent_data}")
        
        # 2. 加载当前规则权重
        current_weights = self._load_current_weights()
        
        # 3. 加载用户操作日志和准确率统计
        user_logs = self._load_user_logs()
        accuracy_stats = self._load_accuracy_stats()
        
        # 4. 调用AI生成迭代方案
        new_weights, reason = self.ai.generate_iteration_plan(
            intent_data, current_weights, user_logs, accuracy_stats
        )
        print(f"[AI] 迭代建议：{reason}")
        
        # 5. 记录操作日志
        self._save_user_log(user_input, intent_data, new_weights)
        
        # 6. 更新配置文件
        self._update_weights(new_weights)
        
        return {
            "success": True,
            "intent": intent_data,
            "new_weights": new_weights,
            "reason": reason
        }
    
    def _load_current_weights(self) -> dict:
        """加载当前规则权重"""
        # 尝试从配置文件读取
        config_file = self.config_path.replace(".yaml", "_weights.json")
        
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        
        # 默认权重
        return {
            "blur_score": 0.4,
            "exposure": 0.3,
            "face_quality": 0.2,
            "composition": 0.1
        }
    
    def _update_weights(self, weights: dict):
        """更新配置文件"""
        config_file = self.config_path.replace(".yaml", "_weights.json")
        
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(weights, f, ensure_ascii=False, indent=2)
            print(f"[AI] 权重已更新：{weights}")
        except Exception as e:
            print(f"[AI] 更新权重失败：{e}")
    
    def _load_user_logs(self) -> list:
        """加载用户操作日志"""
        log_file = os.path.join(self.log_dir, "user_logs.json")
        
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        
        return []
    
    def _save_user_log(self, user_input: str, intent_data: dict, new_weights: dict):
        """保存用户操作日志"""
        log_file = os.path.join(self.log_dir, "user_logs.json")
        
        logs = self._load_user_logs()
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "intent": intent_data,
            "new_weights": new_weights
        }
        
        logs.append(log_entry)
        
        # 只保留最近100条
        logs = logs[-100:]
        
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def _load_accuracy_stats(self) -> dict:
        """加载筛选准确率统计"""
        stats_file = os.path.join(self.log_dir, "accuracy_stats.json")
        
        if os.path.exists(stats_file):
            try:
                with open(stats_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        
        return {"total": 0, "correct": 0, "accuracy": 0.0}
    
    def get_current_config(self) -> dict:
        """获取当前配置状态"""
        return {
            "weights": self._load_current_weights(),
            "logs_count": len(self._load_user_logs()),
            "accuracy": self._load_accuracy_stats()
        }


# 测试代码
if __name__ == "__main__":
    manager = AIIterationManager()
    
    # 测试意图解析
    test_inputs = [
        "我想让婚礼照片优先选人脸清晰的，降低模糊度的权重",
        "人像写真筛选要新增人脸数量维度",
        "查看当前筛选规则"
    ]
    
    for text in test_inputs:
        result = manager.iterate(text)
        print(f"输入: {text}")
        print(f"结果: {result}")
        print("-" * 50)
