"""`@deepseek-ai/dsh-web-search-perplexity`：向 `ctx.web` 注册 Perplexity 后端的 `WebSearchProvider`。这是函数/命名空间插件（不是默认导出服务）：它注册进 seam 的提供方注册表，正如 `@deepseek-ai/dsh-llm-deepseek` 把适配器注册进 `ctx.llm`。"""
from ...依赖.schemastery import 字符串字段,整数字段,枚举字段#配置字段
from ...工具.启动环境 import 取启动环境#导入启动环境快照
from .提供方 import (
    Perplexity搜索提供方,#Perplexity搜索提供方类
    默认基址,#默认端点基址
    默认最大令牌,#默认生成上限
    默认模型,#默认模型名
    提供方标识,#提供方稳定id
    新近窗口,#新近窗口联合
    映射Perplexity结果,#结果映射
    映射Perplexity响应,#响应映射
)#从提供方模块导入实现与默认值

__all__=['名称','注入','应用','Config','name','inject']#公开面

名称='web-search-perplexity'#loader 诊断所用的 Cordis 插件名
注入=['web']#本提供方注册进去的 web seam
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
配置={#插件配置（全部可选——应用 填环境变量与常量默认值）
    'apiKey':字符串字段(),#Perplexity API 密钥；回退到 $PERPLEXITY_API_KEY；空 → 不可用
    'baseURL':字符串字段(),#端点基址；会接上 /chat/completions；默认是公开 API
    'model':字符串字段(),#搜索模型名；默认 sonar
    'maxTokens':整数字段(默认值=1024),#生成回答 token 上限；默认 1024
    'searchRecency':枚举字段('day','week','month','year'),#作为 search_recency_filter 发送的新旧窗口；省略 = 无过滤
}#配置模式结束
Config=配置#Cordis配置模式

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 应用(上下文,配置值):#向 ctx.web 注册 Perplexity 搜索提供方
    """向 `ctx.web` 注册 Perplexity 搜索提供方。"""
    密钥=取字段(配置值,'apiKey')#配置层密钥
    if 密钥 is None:#配置未给
        环境项=取启动环境(上下文).取('PERPLEXITY_API_KEY')#启动环境
        if 环境项 is not None:#有环境项
            密钥=取字段(环境项,'value')#取值
        else:#无环境
            密钥=''#空 → 不可用
    基址=取字段(配置值,'baseURL')#配置基址
    if 基址 is None:#未给
        基址=默认基址#公开 API
    模型=取字段(配置值,'model')#配置模型
    if 模型 is None:#未给
        模型=默认模型#默认 sonar
    最大令牌=取字段(配置值,'maxTokens')#配置生成上限
    if 最大令牌 is None:#未给
        最大令牌=默认最大令牌#默认 1024
    选项={#已解析提供方选项
        'apiKey':密钥,#密钥
        'baseURL':基址,#基址
        'model':模型,#模型
        'maxTokens':最大令牌,#生成上限
    }#选项骨架
    新近=取字段(配置值,'searchRecency')#可选新旧窗口
    if 新近 is not None:#有新旧窗口才传入
        选项['searchRecency']=新近#带上
    上下文.web.注册搜索提供方(Perplexity搜索提供方(选项))#注册进搜索注册表

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出
