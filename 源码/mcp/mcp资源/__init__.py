import json
from ...依赖 import cordis
服务=cordis.服务
from ...内核.作用域 import 创建作用域,获取作用域,具名条目,作用域层集
from .资源工具登记 import 登记资源工具


__all__=['mcp资源错误','mcp资源运行时']

class mcp资源错误(Exception):
    """MCP 资源登记或派发失败。"""
    def __init__(自身,消息):
        """用原样英文消息构造。"""
        super().__init__(消息)

class 资源层:
    """一层作用域内的资源提供方。"""
    def __init__(自身):
        """建空服务器表。"""
        def 重复(名):
            """构造重复登记错误。"""
            return mcp资源错误('MCP resource server "'+名+'" is already registered in this scope')
        自身.服务器=具名条目(重复)
        自身.拆除工具=None
    def 是否空(自身):
        """测试本层是否没有提供方。"""
        return 自身.服务器.是否空()

class mcp资源运行时(服务):
    """作用域资源访问加上三个共享工具。"""
    依赖=['tools']
    def __init__(自身,上下文):
        """登记为 mcpResources，并挂服务器名提示词。"""
        super().__init__(上下文,'mcpResources')
        def 建层(键):
            """建一层空服务器表。"""
            return 资源层()
        def 无通知():
            """本服务不另发变更事件。"""
            return None
        自身.层集=作用域层集(建层,无通知)
        自身.自身上下文=上下文
        def 挂提示(内上下文):
            """按调用方作用域列出服务器名。"""
            def 文案(载荷):
                """拼服务器名列表。"""
                作用域=载荷['scope'] if 'scope' in 载荷 else None
                def 挑服务器(层):
                    """挑选具名服务器表。"""
                    return 层.服务器
                名称表=sorted(自身.层集.合并(作用域,挑服务器).keys())
                if len(名称表)==0:
                    return ''
                return ('## MCP resource servers\n\n'
                    +'Use list_mcp_resources, list_mcp_resource_templates, or read_mcp_resource with one of these names '
                    +'as the server argument: '+json.dumps(名称表,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'.')
            内上下文.systemPrompt.section({
                'name':'mcp-resource-servers',
                'order':内上下文.systemPrompt.getSectionOrder('MCP_SERVERS'),
                'interpolate':False,
                'text':文案,
            })
        上下文.依赖启动(['systemPrompt'],挂提示)
    def 登记(自身,服务器,提供方):
        """登记一台服务器，并在该作用域有提供方时暴露资源工具。"""
        上下文=自身.所属上下文
        作用域=获取作用域(上下文)
        def 执行体():
            """先挂工具拆除再挂提供方。"""
            拆除引用={'值':None}#延后拆除共享工具
            def 延后拆除():
                """工具消失同步。"""
                拆=拆除引用['值']
                if 拆 is not None:
                    拆()
            yield 延后拆除
            def 动作(层):
                """插入提供方；首个提供方登记工具。"""
                首次=层.服务器.是否空()
                撤销=层.服务器.插入(服务器,提供方)
                try:
                    if 首次:
                        层.拆除工具=自身.登记工具(作用域)
                except mcp资源错误:
                    撤销()
                    raise
                def 拆除():
                    """撤销插入；层空则拆除工具。"""
                    撤销()
                    if 层.服务器.是否空():
                        拆除引用['值']=层.拆除工具
                return 拆除
            yield 自身.层集.副作用(上下文,动作,{'标签':'mcpResources.provider('+服务器+')'})
        return 上下文.副作用(执行体,'mcpResources.register('+服务器+')')
    def 登记工具(自身,作用域):
        """独立于配置服务器插件拥有一份作用域的工具。"""
        上下文=自身.自身上下文
        def 执行体():
            """可选铸造作用域后登记工具。"""
            工具上下文=上下文
            if 作用域 is not None:
                已铸=创建作用域(上下文,作用域)
                yield 已铸.原始拆除
                工具上下文=已铸.上下文
            def 请求(服务器,请求体,执行):
                """解析调用方可见服务器。"""
                return 自身.请求(服务器,请求体,执行)
            yield 登记资源工具(工具上下文,请求)
        return 上下文.副作用(执行体,'mcpResources.tools')
    def 请求(自身,服务器,请求体,执行):
        """在开始任何网络操作前解析调用方可见服务器。"""
        def 挑服务器(层):
            """挑选具名服务器表。"""
            return 层.服务器
        智能体=执行['agent'] if 'agent' in 执行 else None
        提供方=自身.层集.合并(智能体,挑服务器)
        if 服务器 not in 提供方:
            raise mcp资源错误('MCP resource server "'+服务器+'" is unavailable in this agent\'s scope')
        return 提供方[服务器]['request'](请求体,执行)

mcp资源运行时.inject=mcp资源运行时.依赖#框架槽
default=mcp资源运行时#框架槽
