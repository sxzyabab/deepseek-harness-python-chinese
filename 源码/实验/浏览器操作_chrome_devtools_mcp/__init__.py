from ..浏览器操作_运行时.mcp import 浏览器mcp配置,挂会话mcp,校验浏览器mcp配置#共享 MCP 挂载

__all__=['名称','注入','配置','应用']#仅中文公开名

名称='experimental-browser-use-chrome-devtools-mcp'#插件名
注入=['browserUse','agents','tools','systemPrompt']#依赖
配置=浏览器mcp配置#校验器

def 应用(上下文,配置值):#每 Session 一台 Chrome DevTools MCP
    """附着浏览器仍由外部拥有；服务器关闭用量统计。"""
    校验浏览器mcp配置(配置值)#端点
    参数=['--no-usage-statistics']#CLI
    if 配置值['mode']=='attach':#附着
        端点=配置值['endpoint']#端点
        if 端点.startswith('ws:') or 端点.startswith('wss:'):#websocket
            参数.extend(['--ws-endpoint',端点])#ws
        else:#HTTP
            参数.extend(['--browser-url',端点])#url
    else:#启动
        参数.extend(['--isolated','--headless='+str(配置值['headless'])])#隔离无窗
        if 配置值.get('executablePath') is not None:#可执行
            参数.extend(['--executable-path',配置值['executablePath']])#路径
    挂选项={#会话 MCP
        'name':'chrome-devtools-mcp',#命名空间
        'exclusive':配置值['mode']=='attach',#附着独占
        'command':'node',#Node 可执行
        'args':参数,#参数
    }#选项
    if 配置值.get('toolCallTimeoutMs') is not None:#超时
        挂选项['toolCallTimeoutMs']=配置值['toolCallTimeoutMs']#超时
    挂会话mcp(上下文,挂选项)#挂

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
Config=配置#框架槽
