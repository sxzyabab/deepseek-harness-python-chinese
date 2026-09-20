"""向 web 注册 Perplexity 搜索提供方。"""
from ...依赖.schemastery import 字符串字段,整数字段,枚举字段
from ...工具.启动环境 import 取启动环境
from .提供方 import (
    Perplexity搜索提供方,
    默认基址,
    默认最大令牌,
    默认模型,
    提供方标识,
    新近窗口,
    映射Perplexity结果,
    映射Perplexity响应,
)

__all__=['包名','名称','依赖','应用','默认']

包名='@deepseek-ai/dsh-web-search-perplexity'
名称='web-search-perplexity'
依赖=['web']
配置={
    'apiKey':字符串字段(),#回退到 $PERPLEXITY_API_KEY；空串表示不可用
    'baseURL':字符串字段(),#端点基址，会接上 /chat/completions
    'model':字符串字段(),#搜索模型名；默认 sonar
    'maxTokens':整数字段(默认值=1024),#生成回答 token 上限
    'searchRecency':枚举字段('day','week','month','year'),#作为 search_recency_filter；省略则无过滤
}

def 应用(上下文,配置值):
    """向 web 注册 Perplexity 搜索提供方。配置值为 dict。"""
    密钥=配置值['apiKey'] if 'apiKey' in 配置值 else None
    if 密钥 is None:
        环境项=取启动环境(上下文).取('PERPLEXITY_API_KEY')
        if 环境项 is not None:
            密钥=环境项['value']
        else:
            密钥=''
    基址=配置值['baseURL'] if 'baseURL' in 配置值 else None
    if 基址 is None:
        基址=默认基址
    模型=配置值['model'] if 'model' in 配置值 else None
    if 模型 is None:
        模型=默认模型
    最大令牌=配置值['maxTokens'] if 'maxTokens' in 配置值 else None
    if 最大令牌 is None:
        最大令牌=默认最大令牌
    选项={
        'apiKey':密钥,
        'baseURL':基址,
        'model':模型,
        'maxTokens':最大令牌,
    }
    if 'searchRecency' in 配置值 and 配置值['searchRecency'] is not None:
        选项['searchRecency']=配置值['searchRecency']
    上下文.web.注册搜索提供方(Perplexity搜索提供方(选项))

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=默认#框架槽
