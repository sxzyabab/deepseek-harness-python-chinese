"""面向 provider 中立 webhook 运行时的已签名 GitHub HTTP 适配器。"""
from ...依赖.schemastery import 字符串字段,整数字段
from ...凭据.凭据 import 凭证引用
from .事件分派 import 创建GitHubWebhook事件分派

包名='@deepseek-ai/dsh-webhook-github'
名称='webhook-github'
依赖=['webServer','webhookRuntime','credentials']

配置={
    'source':字符串字段(),
    'path':字符串字段(),
    'secretEnv':字符串字段(),
    'maxBodyBytes':整数字段(),
}

__all__=['包名','名称','依赖','应用','默认','配置']

class WebhookGithub配置错误(Exception):
    """路由与来源配置非法。"""

def 断言配置(配置值):
    """校验 Schemastery 表达不了的路由与来源事实。配置为 dict。"""
    来源=配置值['source']
    if (not isinstance(来源,str)) or 来源.strip()!=来源 or 来源=='':
        raise WebhookGithub配置错误('webhook-github source must be a non-empty trimmed string')
    路径=配置值['path']
    if (not isinstance(路径,str)) or (not 路径.startswith('/')) or 路径=='/' or 路径.endswith('/') or '?' in 路径 or '#' in 路径:
        raise WebhookGithub配置错误('webhook-github path must be an absolute non-root pathname without a trailing slash, query, or fragment')

def 应用(上下文,配置值):
    """在依赖的 WebServer 上登记一条已签名 GitHub 端点。"""
    断言配置(配置值)
    路由={
        'kind':'exact',
        'path':配置值['path'],
        'handler':创建GitHubWebhook事件分派(上下文,{
            'source':配置值['source'],
            'secretEnv':凭证引用(配置值['secretEnv']),
            'maxBodyBytes':配置值['maxBodyBytes'],
        }),
    }
    def 挂路由():
        """登记精确路径。"""
        return 上下文.webServer.register(路由)
    上下文.副作用(挂路由,f"webhook-github: {配置值['path']}")

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=默认#框架槽
