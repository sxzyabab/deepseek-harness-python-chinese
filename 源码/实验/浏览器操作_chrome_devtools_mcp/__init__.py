from ..浏览器操作_运行时.mcp import 浏览器mcp配置,挂会话mcp,校验浏览器mcp配置

__all__=['名称','依赖','配置','应用']

名称='experimental-browser-use-chrome-devtools-mcp'
依赖=['browserUse','agents','tools','systemPrompt']
配置=浏览器mcp配置

def 应用(上下文,配置值):
    """附着浏览器仍由外部拥有；服务器关闭用量统计。"""
    校验浏览器mcp配置(配置值)
    参数=['--no-usage-statistics']
    if 配置值['mode']=='attach':
        端点=配置值['endpoint']
        if 端点.startswith('ws:') or 端点.startswith('wss:'):
            参数.extend(['--ws-endpoint',端点])
        else:
            参数.extend(['--browser-url',端点])
    else:
        参数.extend(['--isolated','--headless='+str(配置值['headless'])])
        if 'executablePath' in 配置值 and 配置值['executablePath'] is not None:
            参数.extend(['--executable-path',配置值['executablePath']])
    挂选项={
        'name':'chrome-devtools-mcp',
        'exclusive':配置值['mode']=='attach',
        'command':'node',
        'args':参数,
    }
    if 'toolCallTimeoutMs' in 配置值 and 配置值['toolCallTimeoutMs'] is not None:
        挂选项['toolCallTimeoutMs']=配置值['toolCallTimeoutMs']
    挂会话mcp(上下文,挂选项)

name=名称
inject=依赖
apply=应用
Config=配置
