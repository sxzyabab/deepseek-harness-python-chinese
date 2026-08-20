"""`@deepseek-ai/dsh-web-search-exa`：向 `ctx.web` 注册 Exa 后端的 `WebSearchProvider`。这是函数/命名空间插件（不是默认导出服务）：搜索提供方不拥有 `ctx.web` 键——它注册进 seam 的提供方注册表，正如 `@deepseek-ai/dsh-llm-deepseek` 把适配器注册进 `ctx.llm`。该键由 `@deepseek-ai/dsh-web` 拥有。"""
from schemastery import 模式#导入配置校验
from launch_environment import 取启动环境#导入启动环境快照
from .提供方 import (
    Exa搜索提供方,#Exa搜索提供方类
    默认基址,#默认端点基址
    默认每条高亮数,#默认每条高亮句数
    默认检索模式,#默认检索模式
    提供方标识,#提供方稳定id
    映射Exa结果,#结果映射
    映射Exa响应,#响应映射
)#从提供方模块导入实现与默认值

名称='web-search-exa'#loader 诊断所用的 Cordis 插件名
注入=['web']#本提供方注册进去的 web seam
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
配置=模式.对象({#插件配置（全部可选——应用 填环境变量与常量默认值）
    'apiKey':模式.字符串(),#Exa API 密钥；回退到 $EXA_API_KEY；空 → 提供方不可用
    'baseURL':模式.字符串(),#端点基址；会接上 /search；默认是公开 API
    'searchType':模式.联合([模式.常量('auto'),模式.常量('keyword'),模式.常量('neural')]),#作为 Exa type 发送的检索模式；默认 auto
    'numResults':模式.数字().步进(1).最小(1),#请求未带 maxResults 时的默认结果数；省略 = 无
    'highlightsPerResult':模式.数字().步进(1).最小(1),#每条结果请求的高亮句子数；默认 1
})#配置模式结束
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

def 应用(上下文,配置值):#向 ctx.web 注册 Exa 搜索提供方
    """向 `ctx.web` 注册 Exa 搜索提供方。"""
    密钥=取字段(配置值,'apiKey')#配置层密钥
    if 密钥 is None:#配置未给
        环境项=取启动环境(上下文).取('EXA_API_KEY')#启动环境
        if 环境项 is not None:#有环境项
            密钥=取字段(环境项,'value')#取值
        else:#无环境
            密钥=''#空 → 不可用
    基址=取字段(配置值,'baseURL')#配置基址
    if 基址 is None:#未给
        基址=默认基址#公开 API
    检索=取字段(配置值,'searchType')#配置检索模式
    if 检索 is None:#未给
        检索=默认检索模式#默认 auto
    高亮数=取字段(配置值,'highlightsPerResult')#配置高亮句数
    if 高亮数 is None:#未给
        高亮数=默认每条高亮数#默认 1
    选项={#已解析提供方选项
        'apiKey':密钥,#密钥
        'baseURL':基址,#基址
        'searchType':检索,#检索模式
        'highlightsPerResult':高亮数,#高亮句数
    }#选项骨架
    条数=取字段(配置值,'numResults')#可选默认结果数
    if 条数 is not None:#有默认结果数才传入
        选项['numResults']=条数#带上
    上下文.web.注册搜索提供方(Exa搜索提供方(选项))#注册进搜索注册表

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出
