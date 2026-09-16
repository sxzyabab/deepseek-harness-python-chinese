import json#紧凑 JSON
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
from ...内核.作用域 import 创建作用域,获取作用域,具名条目,作用域层集#作用域登记
from .工具 import 登记资源工具#三个共享工具


__all__=['mcp资源错误','mcp资源运行时']#仅中文公开名

class mcp资源错误(Exception):#本包异常基类
    """MCP 资源登记或派发失败。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

class 资源层:#一个作用域的服务器表
    """一层作用域内的资源提供方。"""
    def __init__(自身):#建空层
        """建空服务器表。"""
        def 重复(名):#重复名诊断
            """构造重复登记错误。"""
            return mcp资源错误('MCP resource server "'+名+'" is already registered in this scope')#重复
        自身.服务器=具名条目(重复)#具名表
        自身.拆除工具=None#共享工具拆除器
    def 是否空(自身):#层是否空
        """测试本层是否没有提供方。"""
        return 自身.服务器.是否空()#空表

class mcp资源运行时(服务):#作用域资源访问加三个共享工具
    """作用域资源访问加上三个共享工具。"""
    注入=['tools']#依赖 tools
    def __init__(自身,上下文对象):#登记为 mcpResources
        """登记为 ctx.mcpResources，并挂服务器名提示词。"""
        super().__init__(上下文对象,'mcpResources')#挂服务
        def 建层(键):#新建资源层
            """建一层空服务器表。"""
            return 资源层()#空层
        def 无通知():#层变更无额外观测
            """本服务不另发变更事件。"""
            return None#空
        自身.层集=作用域层集(建层,无通知)#全局加作用域层
        自身.自身上下文=上下文对象#共享工具所有权上下文
        def 挂提示(内上下文):#systemPrompt 就绪后挂段落
            """按调用方作用域列出服务器名。"""
            def 文案(载荷):#动态段落
                """拼服务器名列表。"""
                作用域=载荷['scope'] if 'scope' in 载荷 else None#调用方作用域
                def 挑服务器(层):#取本层服务器表
                    """挑选具名服务器表。"""
                    return 层.服务器#表
                名称表=sorted(自身.层集.合并(作用域,挑服务器).keys())#可见名
                if len(名称表)==0:#没有服务器
                    return ''#空段落
                return ('## MCP resource servers\n\n'
                    +'Use list_mcp_resources, list_mcp_resource_templates, or read_mcp_resource with one of these names '
                    +'as the server argument: '+json.dumps(名称表,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'.')#名单
            内上下文.systemPrompt.section({#登记段落
                'name':'mcp-resource-servers',#段落名
                'order':内上下文.systemPrompt.getSectionOrder('MCP_SERVERS'),#顺序
                'interpolate':False,#不插值
                'text':文案,#动态文案
            })#section
        上下文对象.注入(['systemPrompt'],挂提示)#等 systemPrompt
    def 登记(自身,服务器,提供方):#登记一台服务器
        """登记一台服务器，并在该作用域有提供方时暴露资源工具。"""
        上下文=自身.所属上下文#当前上下文
        作用域=获取作用域(上下文)#作用域标签
        def 执行体():#生成器副作用
            """先挂工具拆除再挂提供方。"""
            拆除引用={'值':None}#延后拆除共享工具
            def 延后拆除():#跑已记下的拆除
                """工具消失同步。"""
                拆=拆除引用['值']#取出
                if 拆 is not None:#有拆除器
                    拆()#拆除
            yield 延后拆除#先登记延后拆除
            def 动作(层):#变更本层
                """插入提供方；首个提供方登记工具。"""
                首次=层.服务器.是否空()#是否第一个
                撤销=层.服务器.插入(服务器,提供方)#插入
                try:#登记工具
                    if 首次:#首个提供方
                        层.拆除工具=自身.登记工具(作用域)#共享工具
                except Exception:#工具登记失败
                    撤销()#回滚插入
                    raise#原样抛
                def 拆除():#撤销本提供方
                    """撤销插入；层空则拆除工具。"""
                    撤销()#撤销插入
                    if 层.服务器.是否空():#最后一个
                        拆除引用['值']=层.拆除工具#记下拆除
                return 拆除#层变更撤销
            yield 自身.层集.副作用(上下文,动作,{'标签':'mcpResources.provider('+服务器+')'})#层副作用
        return 上下文.副作用(执行体,'mcpResources.register('+服务器+')')#外层副作用
    def 登记工具(自身,作用域):#为一份作用域登记工具
        """独立于配置服务器插件拥有一份作用域的工具。"""
        上下文=自身.自身上下文#共享工具上下文
        def 执行体():#生成器副作用
            """可选铸造作用域后登记工具。"""
            工具上下文=上下文#默认
            if 作用域 is not None:#有作用域
                已铸=创建作用域(上下文,作用域)#铸造
                yield 已铸.原始拆除#精确拆除
                工具上下文=已铸.上下文#作用域上下文
            def 请求(服务器,请求体,执行):#派发
                """解析调用方可见服务器。"""
                return 自身.请求(服务器,请求体,执行)#本服务派发
            yield 登记资源工具(工具上下文,请求)#三个工具
        return 上下文.副作用(执行体,'mcpResources.tools')#工具副作用
    def 请求(自身,服务器,请求体,执行):#解析后派发
        """在开始任何网络操作前解析调用方可见服务器。"""
        def 挑服务器(层):#取本层服务器表
            """挑选具名服务器表。"""
            return 层.服务器#表
        智能体=执行['agent'] if 'agent' in 执行 else None#调用方
        提供方=自身.层集.合并(智能体,挑服务器)#合并表
        if 服务器 not in 提供方:#不可见
            raise mcp资源错误('MCP resource server "'+服务器+'" is unavailable in this agent\'s scope')#不可用
        return 提供方[服务器]['request'](请求体,执行)#提供方操作

mcp资源运行时.inject=mcp资源运行时.注入#框架槽
default=mcp资源运行时#框架槽
