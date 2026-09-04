"""语言环境查找链的测试替身。

对齐上游 `client-runtime/src/translate.ts`。公开面仅中文名。
"""
import re#模板插值

__all__=['制作翻译']#仅中文公开名

占位模式=re.compile(r'\{(\w+)\}')#占位模式

def 制作翻译(*字典们):#构建 translate 桩
    """按序经字典解析的 translate 桩，回退到键本身。"""
    def 翻译(键,参数=None):#解析键
        """查字典并插值。"""
        模板=键#默认回退到键
        for 字典 in 字典们:#按序查字典
            if 键 in 字典:#命中
                模板=字典[键]#首个命中胜出
                break#停止
        if not 参数:#无参数
            return 模板#无参数
        return 占位模式.sub(lambda 匹配:str(参数[匹配.group(1)]) if 匹配.group(1) in 参数 else 匹配.group(0),模板)#插值
    return 翻译#返回函数

makeTranslate=制作翻译#上游名
