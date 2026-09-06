"""传输工厂：按插件已解析配置创建对应的 MCP 传输。Stdio 会派生子进程（并擦洗凭证）；Streamable HTTP 连接到 URL。

对齐上游 `mcp-client/src/transport.ts`。公开面仅中文名。
"""
from ...子进程.子进程 import 擦洗父环境#已擦洗的父进程环境

__all__=['创建传输','合并子环境','MCP错误']#仅中文公开名

class MCP错误(Exception):
    """本包异常基类。"""

def 合并子环境(额外):
    """子进程 seam 的已擦洗父环境，再加上规范里显式给出的环境。"""
    环境=擦洗父环境()#先擦洗父环境
    环境.update(额外)#再覆盖显式项
    return 环境#合并结果

def 创建传输(配置):
    """从已解析的插件配置创建 MCP 传输（stdio 或 Streamable HTTP）。配置为 dict。"""
    种类=配置['transport']#传输种类
    if 种类=='stdio':#标准输入输出传输
        from mcp.client.stdio import StdioServerParameters,stdio_client#MCP stdio 客户端
        工作目录=配置['cwd']#工作目录
        参数=StdioServerParameters(#stdio 连接参数
            command=配置['command'],#子进程命令
            args=list(配置['args']),#命令参数
            env=合并子环境(配置['env']),#擦洗后的环境
            cwd=None if 工作目录=='' else 工作目录,#空串当缺席
        )#参数结束
        return {'kind':'stdio','params':参数,'factory':stdio_client}#可连接的传输描述
    if 种类=='streamable-http':#可流式HTTP传输
        from mcp.client.streamable_http import streamablehttp_client#MCP HTTP 客户端
        return {'kind':'streamable-http','url':配置['url'],'headers':dict(配置['headers']),'factory':streamablehttp_client}#可连接的传输描述
    raise MCP错误('mcp-client: unknown transport '+str(种类))#未知传输
