"""传输工厂：按插件已解析配置创建对应的 MCP 传输。

stdio 派生子进程并擦洗凭证；streamable-http 连到 URL。
"""
from ...子进程.子进程 import 擦洗父环境#已擦洗的父进程环境

__all__=['创建传输','合并子环境','MCP错误']

class MCP错误(Exception):
    """本包异常基类。"""

def 合并子环境(额外):
    """已擦洗的父进程环境，再叠加上配置里显式给出的环境项。"""
    环境=擦洗父环境()
    环境.update(额外)
    return 环境

def 创建传输(配置):
    """从已解析的插件配置创建 MCP 传输（stdio 或 streamable-http）。配置为 dict。"""
    种类=配置['transport']
    if 种类=='stdio':
        from mcp.client.stdio import StdioServerParameters,stdio_client
        工作目录=配置['cwd']
        参数=StdioServerParameters(
            command=配置['command'],
            args=list(配置['args']),
            env=合并子环境(配置['env']),
            cwd=None if 工作目录=='' else 工作目录,#空串表示不设 cwd
        )
        return {'kind':'stdio','params':参数,'factory':stdio_client}
    if 种类=='streamable-http':
        from mcp.client.streamable_http import streamablehttp_client
        return {'kind':'streamable-http','url':配置['url'],'headers':dict(配置['headers']),'factory':streamablehttp_client}
    raise MCP错误('mcp-client: unknown transport '+str(种类))
