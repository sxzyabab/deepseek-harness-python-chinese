"""面向 provider 中立 webhook 运行时的已签名 GitHub HTTP 适配器。

对齐上游 `webhook-github/src/index.ts`。公开面仅中文名。
"""
from ...依赖.schemastery import 字符串字段,整数字段#配置字段
from ...凭据.凭据 import 凭证引用#凭证引用品牌
from .事件分派 import 创建GitHubWebhook事件分派#HTTP事件分派

名称='webhook-github'#Cordis插件名（字面量）
注入=['webServer','webhookRuntime','credentials']#依赖

配置={#插件配置模式
    'source':字符串字段(),#适配器实例名
    'path':字符串字段(),#绝对路由路径
    'secretEnv':字符串字段(),#凭据引用
    'maxBodyBytes':整数字段(),#正文上限字节
}#配置结束

__all__=['名称','注入','配置','应用']#仅中文公开名

class WebhookGithub配置错误(Exception):
    """路由与来源配置非法。"""

def 断言配置(配置值):
    """校验 Schemastery 表达不了的路由与来源事实。配置为 dict。"""
    来源=配置值['source']#来源
    if (not isinstance(来源,str)) or 来源.strip()!=来源 or 来源=='':#必须非空且已修剪
        raise WebhookGithub配置错误('webhook-github source must be a non-empty trimmed string')#拒绝
    路径=配置值['path']#路径
    if (not isinstance(路径,str)) or (not 路径.startswith('/')) or 路径=='/' or 路径.endswith('/') or '?' in 路径 or '#' in 路径:#非法路径
        raise WebhookGithub配置错误('webhook-github path must be an absolute non-root pathname without a trailing slash, query, or fragment')#拒绝

def 应用(上下文,配置值):
    """在注入的 WebServer 上登记一条已签名 GitHub 端点。"""
    断言配置(配置值)#校验配置
    路由={#路由对象
        'kind':'exact',#精确匹配
        'path':配置值['path'],#路径
        'handler':创建GitHubWebhook事件分派(上下文,{#事件分派
            'source':配置值['source'],#来源
            'secretEnv':凭证引用(配置值['secretEnv']),#密钥引用
            'maxBodyBytes':配置值['maxBodyBytes'],#正文上限
        }),#事件分派结束
    }#路由结束
    def 挂路由():
        """登记精确路径。"""
        return 上下文.webServer.register(路由)#登记路由
    上下文.副作用(挂路由,f"webhook-github: {配置值['path']}")#登记路由

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
Config=配置#框架槽
