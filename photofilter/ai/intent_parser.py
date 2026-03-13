# -*- coding: utf-8 -*-
"""
意图解析器 - 将用户自然语言需求转为AI可识别的语义标签
"""
import re


class IntentParser:
    """将用户自然语言需求转为AI可识别的语义标签"""
    
    def __init__(self):
        # 照片用途匹配模式
        self.purpose_patterns = {
            "人像写真": r"人像|写真|模特|肖像",
            "婚礼跟拍": r"婚礼|婚庆|跟拍|婚纱",
            "风光摄影": r"风光|风景|山水|自然",
            "证件照": r"证件|身份证|护照|签证",
            "儿童摄影": r"儿童|宝宝|小孩|婴幼儿",
            "商业摄影": r"商业|产品|广告|电商"
        }
        
        # 筛选维度匹配模式
        self.dimension_patterns = {
            "模糊度": r"模糊|清晰|糊片|虚焦|对焦",
            "曝光度": r"曝光|过曝|欠曝|亮度|明暗",
            "人脸质量": r"人脸|表情|闭眼|遮挡|笑脸",
            "逆光": r"逆光|剪影|背光|暗部",
            "构图": r"构图|全景|特写|三分法",
            "画质": r"画质|噪点|颗粒|ISO",
            "色彩": r"色彩|白平衡|色调|偏色",
            "人脸数量": r"人脸数量|单人|多人|合影"
        }
        
        # 用户操作匹配模式
        self.action_patterns = {
            "调整权重": r"权重|优先|降低|提高|增加|减少",
            "标记修正": r"标记|选错|漏选|好片|废片|不对",
            "新增规则": r"新增|添加|想要|需要|增加",
            "优化规则": r"优化|改进|更准|提升|调整",
            "查询状态": r"查看|当前|现在|有什么"
        }
    
    def parse(self, user_input: str) -> dict:
        """
        解析用户输入
        
        示例：
        输入："我想让婚礼照片优先选人脸清晰的，降低模糊度的权重"
        输出：{
            "photo_purpose": "婚礼跟拍",
            "filter_dimension": ["人脸质量", "模糊度"],
            "user_action": "调整权重",
            "detail": "我想让婚礼照片优先选人脸清晰的，降低模糊度的权重"
        }
        
        Args:
            user_input: 用户自然语言输入
            
        Returns:
            解析后的语义标签字典
        """
        result = {
            "photo_purpose": None,
            "filter_dimension": [],
            "user_action": None,
            "detail": user_input.strip()
        }
        
        # 匹配照片用途
        for purpose, pattern in self.purpose_patterns.items():
            if re.search(pattern, user_input):
                result["photo_purpose"] = purpose
                break
        
        # 匹配筛选维度
        for dimension, pattern in self.dimension_patterns.items():
            if re.search(pattern, user_input):
                result["filter_dimension"].append(dimension)
        
        # 匹配用户操作
        for action, pattern in self.action_patterns.items():
            if re.search(pattern, user_input):
                result["user_action"] = action
                break
        
        # 如果没有匹配到操作，默认设为查询
        if result["user_action"] is None:
            result["user_action"] = "查询状态"
        
        return result


# 测试代码
if __name__ == "__main__":
    parser = IntentParser()
    
    test_inputs = [
        "我想让婚礼照片优先选人脸清晰的，降低模糊度的权重",
        "人像写真筛选要新增人脸数量维度",
        "查看当前筛选规则",
        "刚才筛选的照片里第3张是糊片却选上了"
    ]
    
    for text in test_inputs:
        result = parser.parse(text)
        print(f"输入: {text}")
        print(f"输出: {result}")
        print("-" * 40)
