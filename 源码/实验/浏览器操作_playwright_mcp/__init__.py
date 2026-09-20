from ..浏览器操作_运行时.mcp import 浏览器mcp配置,挂会话mcp,校验浏览器mcp配置

__all__=['名称','依赖','配置','应用']

名称='experimental-browser-use-playwright-mcp'
依赖=['browserUse','agents','tools','systemPrompt']
配置=浏览器mcp配置

def 应用(上下文,配置值):
    """钉扎的 npm 服务器；DSH 不持久化浏览器状态。"""
    校验浏览器mcp配置(配置值)
    参数=['--browser','chromium']
    if 配置值['mode']=='attach':
        参数.extend(['--cdp-endpoint',配置值['endpoint']])
    else:
        参数.append('--isolated')
        if 'headless' in 配置值 and 配置值['headless']:
            参数.append('--headless')
        if 'executablePath' in 配置值 and 配置值['executablePath'] is not None:
            参数.extend(['--executable-path',配置值['executablePath']])
    挂选项={
        'name':'playwright-mcp',
        'exclusive':配置值['mode']=='attach',
        'command':'node',
        'args':参数,
        'env':{},#不读进程环境；PLAYWRIGHT_MCP_* 掏空未做
    }
    if 'toolCallTimeoutMs' in 配置值 and 配置值['toolCallTimeoutMs'] is not None:
        挂选项['toolCallTimeoutMs']=配置值['toolCallTimeoutMs']
    挂会话mcp(上下文,挂选项)

name=名称
inject=依赖
apply=应用
Config=配置
