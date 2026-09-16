from ..浏览器操作_运行时.mcp import 浏览器mcp配置,挂会话mcp,校验浏览器mcp配置#共享 MCP 挂载

__all__=['名称','注入','配置','应用']#仅中文公开名

名称='experimental-browser-use-playwright-mcp'#插件名
注入=['browserUse','agents','tools','systemPrompt']#依赖
配置=浏览器mcp配置#校验器

def 应用(上下文,配置值):#每 Session 一台 Playwright MCP
    """钉扎的 npm 服务器；DSH 不持久化浏览器状态。"""
    校验浏览器mcp配置(配置值)#端点
    参数=['--browser','chromium']#CLI
    if 配置值['mode']=='attach':#附着
        参数.extend(['--cdp-endpoint',配置值['endpoint']])#CDP
    else:#启动
        参数.append('--isolated')#隔离
        if 配置值.get('headless'):#无窗
            参数.append('--headless')#无窗
        if 配置值.get('executablePath') is not None:#可执行
            参数.extend(['--executable-path',配置值['executablePath']])#路径
    挂选项={#会话 MCP
        'name':'playwright-mcp',#命名空间
        'exclusive':配置值['mode']=='attach',#附着独占
        'command':'node',#Node 可执行
        'args':参数,#参数
        'env':{},#不读进程环境；PLAYWRIGHT_MCP_* 掏空未做
    }#选项
    if 配置值.get('toolCallTimeoutMs') is not None:#超时
        挂选项['toolCallTimeoutMs']=配置值['toolCallTimeoutMs']#超时
    挂会话mcp(上下文,挂选项)#挂

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
Config=配置#框架槽
