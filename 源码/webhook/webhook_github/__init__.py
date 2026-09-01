"""Signed GitHub HTTP adapter for the provider-neutral webhook runtime. 对齐上游 `webhook-github/src/index.ts`。"""
from ...依赖 import cordis#外部依赖胶水
from ...依赖 import schemastery#配置字段
字符串字段=schemastery.字符串字段#配置字段
整数字段=schemastery.整数字段#配置字段
from ...凭据.凭据 import 凭据引用#凭据引用品牌
from ..webhook.品牌 import Webhook来源标识,Webhook投递标识#webhook品牌
from .处理器 import 创建GitHubWebhook处理器#HTTP处理器

名称='webhook-github'#Cordis插件名（字面量）
注入=['webServer','webhookRuntime','credentials']#依赖

配置={#插件配置模式
    'source':字符串字段(),#适配器实例名
    'path':字符串字段(),#绝对路由路径
    'secretEnv':字符串字段(),#凭据引用
    'maxBodyBytes':整数字段(),#正文上限字节
}#配置结束

__all__=['名称','注入','配置','应用','apply']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 断言配置(配置值):#校验路由与来源
    """Validate route and source facts that Schemastery cannot express."""
    来源=取字段(配置值,'source')#来源
    if (not isinstance(来源,str)) or 来源.strip()!=来源 or 来源=='':#必须非空且已修剪
        raise Exception('webhook-github source must be a non-empty trimmed string')#拒绝
    路径=取字段(配置值,'path')#路径
    if (not isinstance(路径,str)) or (not 路径.startswith('/')) or 路径=='/' or 路径.endswith('/') or '?' in 路径 or '#' in 路径:#非法路径
        raise Exception('webhook-github path must be an absolute non-root pathname without a trailing slash, query, or fragment')#拒绝

def 应用(上下文,配置值):#注册GitHub端点
    """Register one signed GitHub endpoint on the injected WebServer."""
    断言配置(配置值)#校验配置
    路由={
        'kind':'exact',
        'path':取字段(配置值,'path'),
        'handler':创建GitHubWebhook处理器(上下文,{
            'source':取字段(配置值,'source'),
            'secretEnv':凭据引用(取字段(配置值,'secretEnv')),
            'maxBodyBytes':取字段(配置值,'maxBodyBytes'),
        }),
    }#路由对象
    上下文.effect(lambda:上下文.webServer.register(路由),f"webhook-github: {取字段(配置值,'path')}")#登记路由

apply=应用#Cordis插件入口
