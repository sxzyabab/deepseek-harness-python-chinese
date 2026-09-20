"""向 web seam 注册 Exa 搜索提供方。"""
from ...依赖.schemastery import 字符串字段,整数字段,枚举字段
from ...工具.启动环境 import 取启动环境
from .提供方 import (
    Exa搜索提供方,
    默认基址,
    默认每条高亮数,
    默认检索模式,
    提供方标识,
    映射Exa结果,
    映射Exa响应,
)

__all__=['包名','名称','依赖','应用','默认']

包名='@deepseek-ai/dsh-web-search-exa'
名称='web-search-exa'
依赖=['web']
配置={
    'apiKey':字符串字段(),#回退到 $EXA_API_KEY；空 → 提供方不可用
    'baseURL':字符串字段(),#端点基址，会接上 /search
    'searchType':枚举字段('auto','keyword','neural'),#作为 Exa type 发送的检索模式
    'numResults':整数字段(默认值=1),#请求未带 maxResults 时的默认结果数
    'highlightsPerResult':整数字段(默认值=1),#每条结果请求的高亮句子数
}

def 应用(上下文,配置值):
    """配置值为 dict；密钥缺失时回退到启动环境的 EXA_API_KEY。"""
    密钥=配置值['apiKey'] if 'apiKey' in 配置值 else None
    if 密钥 is None:
        环境项=取启动环境(上下文).取('EXA_API_KEY')
        if 环境项 is not None:
            密钥=环境项['value']
        else:
            密钥=''
    基址=配置值['baseURL'] if 'baseURL' in 配置值 else None
    if 基址 is None:
        基址=默认基址
    检索=配置值['searchType'] if 'searchType' in 配置值 else None
    if 检索 is None:
        检索=默认检索模式
    高亮数=配置值['highlightsPerResult'] if 'highlightsPerResult' in 配置值 else None
    if 高亮数 is None:
        高亮数=默认每条高亮数
    选项={
        'apiKey':密钥,
        'baseURL':基址,
        'searchType':检索,
        'highlightsPerResult':高亮数,
    }
    if 'numResults' in 配置值 and 配置值['numResults'] is not None:
        选项['numResults']=配置值['numResults']
    上下文.web.注册搜索提供方(Exa搜索提供方(选项))

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=默认#框架槽
