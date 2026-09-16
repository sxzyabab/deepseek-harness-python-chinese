"""发布连接拥有的 MCP 资源与字面服务器指令。"""
__all__=['登记服务器上下文']#仅中文公开名

def 登记服务器上下文(上下文,服务器,连接):
    """向本组合启用的服务贡献服务器上下文。连接为 dict。"""
    def 登记资源(内部):
        """把当前世代的资源访问挂到 mcpResources。"""
        内部.mcpResources.登记(服务器,连接['resources'])#按服务器名登记
    上下文.注入(['mcpResources'],登记资源)#有资源服务才登记
    def 登记提示(内部):
        """把已连通服务器的指令挂到系统提示词。"""
        内部.systemPrompt.段落({#段落
            'name':'mcp:'+服务器,#线协议段落名
            'order':内部.systemPrompt.取段落序号('MCP_SERVERS'),#MCP 服务器段序
            'interpolate':False,#字面量
            'text':连接['instructions'],#读快照
        })#段落结束
    上下文.注入(['systemPrompt'],登记提示)#有提示词服务才登记
