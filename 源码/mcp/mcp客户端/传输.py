"""传输工厂：按插件已解析配置创建对应的 MCP 传输。Stdio 会派生子进程（并擦洗凭证）；Streamable HTTP 连接到 URL。

对齐上游 `mcp-client/src/transport.ts`。公开面仅中文名。
"""
#from subprocess import 擦洗父环境#已擦洗的父进程环境

__all__=['创建传输','合并子环境']#仅中文公开名

def 合并子环境(额外):#合并擦洗后的父环境与显式环境
    """子进程 seam 的已擦洗父环境，再加上规范里显式给出的环境。"""
    环境=擦洗父环境()#先擦洗父环境
    环境.update(额外)#再覆盖显式项
    return 环境#合并结果

def 创建传输(配置):#按配置创建MCP传输
    """从已解析的插件配置创建 MCP 传输（stdio 或 Streamable HTTP）。"""
    种类=配置['transport'] if isinstance(配置,dict) else 配置.transport#传输种类
    if 种类=='stdio':#标准输入输出传输
        from mcp.client.stdio import StdioServerParameters,stdio_client#MCP stdio 客户端
        参数=StdioServerParameters(#stdio 连接参数
            command=配置['command'] if isinstance(配置,dict) else 配置.command,#子进程命令
            args=list(配置['args'] if isinstance(配置,dict) else 配置.args),#命令参数
            env=合并子环境(配置['env'] if isinstance(配置,dict) else 配置.env),#擦洗后的环境
            cwd=(配置['cwd'] if isinstance(配置,dict) else 配置.cwd) or None,#工作目录；空串当缺席
        )#参数结束
        return {'kind':'stdio','params':参数,'factory':stdio_client}#可连接的传输描述
    if 种类=='streamable-http':#可流式HTTP传输
        from mcp.client.streamable_http import streamablehttp_client#MCP HTTP 客户端
        地址=配置['url'] if isinstance(配置,dict) else 配置.url#端点地址
        头=配置['headers'] if isinstance(配置,dict) else 配置.headers#请求头
        return {'kind':'streamable-http','url':地址,'headers':dict(头),'factory':streamablehttp_client}#可连接的传输描述
    raise Exception('mcp-client: unknown transport '+str(种类))#未知传输
