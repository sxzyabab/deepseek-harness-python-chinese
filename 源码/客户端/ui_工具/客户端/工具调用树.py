"""工具调用树：根/子调用共用一条 keyed 原子派发路径。

对齐上游 `ui-tool/src/client/tool/ToolCallTree.tsx`。公开面仅中文名。
renderSlot 由宿主注入；缺登记时回退工具卡。
"""
from .回退工具卡 import 回退工具卡#回退卡

__all__=['工具调用树','工具调用枝','工具调用','调用名']#仅中文公开名

def 调用名(节点):#线名
    """从生命周期任一侧解析工具名。"""
    if 'kind' in 节点:#已结算
        调用=节点['call'] if 'call' in 节点 else None#调用头
        名=调用['name'] if 调用 is not None and 'name' in 调用 else None#name
        return 名 if 名 else ''#空则空串
    名=节点['name'] if 'name' in 节点 else None#进行中 name
    return 名 if 名 else ''#空则空串

class 工具调用:#单原子调用行
    """经 tool.call.toolview 洞派发；无登记则回退卡。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性={} if 属性 is None else 属性#合成

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性#新

    def 渲染(自身):#结构树
        """派发槽或回退。"""
        属性=自身.属性#props
        调用标识=属性['callId'] if 'callId' in 属性 else None#callId
        工具名=属性['toolName'] if 'toolName' in 属性 else None#名
        块=属性['block'] if 'block' in 属性 else None#块
        开文件=属性['openFile'] if 'openFile' in 属性 else None#开文件
        工作目录=属性['cwd'] if 'cwd' in 属性 else None#cwd
        检查调用=属性['inspectCall'] if 'inspectCall' in 属性 else None#检查
        翻译=属性['t'] if 't' in 属性 else None#文案
        渲槽=属性['renderSlot'] if 'renderSlot' in 属性 else None#槽
        选中=bool(属性['selected']) if 'selected' in 属性 else False#选中
        子列表=属性['children'] if 'children' in 属性 else None#子
        def 检查本调用():#本行检查
            """转调 inspectCall(callId)。"""
            return 检查调用(调用标识)#检查
        所有者={#owner props
            'callId':调用标识,#id
            'toolName':工具名,#名
            'block':块,#块
            'openFile':开文件,#开文件
            'cwd':工作目录,#cwd
            'inspect':检查本调用 if callable(检查调用) else None,#检查
        }#所有者结束
        视图=None#视图
        if callable(渲槽):#有槽
            视图=渲槽('tool.call.toolview',所有者,{'entryKey':工具名})#派发
        if 视图 is None:#无登记
            卡=回退工具卡()#回退
            载荷=dict(所有者)#拷
            载荷['t']=翻译#文案
            视图=卡(载荷)#渲
        return {#结构树
            'type':'tool-call-row',#类型
            'callId':调用标识,#id
            'selected':选中,#选中
            'anchorKey':'call:'+str(调用标识),#锚
            'view':视图,#视图
            'children':子列表,#子
            'cssModule':'工具调用树.module.css',#样式
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 工具调用枝:#递归枝
    """一块调用及其 subCalls。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性={} if 属性 is None else 属性#合成

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性#新

    def 渲染(自身):#结构树
        """递归渲子调用。"""
        属性=自身.属性#props
        块=属性['block']#块
        选中标识=属性['selectedCallId'] if 'selectedCallId' in 属性 else None#选中
        渲槽=属性['renderSlot'] if 'renderSlot' in 属性 else None#槽
        工作目录=属性['cwd'] if 'cwd' in 属性 else None#cwd
        开文件=属性['openFile'] if 'openFile' in 属性 else None#开文件
        检查调用=属性['inspectCall'] if 'inspectCall' in 属性 else None#检查
        翻译=属性['t'] if 't' in 属性 else None#文案
        调用标识=块['callId'] if 'callId' in 块 else None#id
        子调用=块['subCalls'] if 'subCalls' in 块 and 块['subCalls'] is not None else []#子
        子树=[]#子结构
        for 子 in 子调用:#逐子
            枝=工具调用枝()#枝
            子树.append(枝({#渲
                'renderSlot':渲槽,#槽
                'block':子,#块
                'selectedCallId':选中标识,#选中
                'cwd':工作目录,#cwd
                'openFile':开文件,#开文件
                'inspectCall':检查调用,#检查
                't':翻译,#文案
            }))#加
        行=工具调用()#行
        return 行({#渲
            'renderSlot':渲槽,#槽
            'callId':调用标识,#id
            'toolName':调用名(块),#名
            'block':块,#块
            'openFile':开文件,#开文件
            'selected':调用标识==选中标识,#选中
            'cwd':工作目录,#cwd
            'inspectCall':检查调用,#检查
            't':翻译,#文案
            'children':{'type':'sub-calls','items':子树} if len(子树)>0 else None,#子
        })#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 工具调用树:#根树
    """渲一根工具调用及其递归子。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性={} if 属性 is None else 属性#合成

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性#新

    def 渲染(自身):#结构树
        """取 node.data.root 交给枝。"""
        属性=自身.属性#props
        节点=属性['node']#节点
        数据=节点['data'] if 'data' in 节点 else None#data
        根=数据['root'] if 数据 is not None and 'root' in 数据 else None#根块
        枝=工具调用枝()#枝
        return {#结构树
            'type':'tool-call-tree',#类型
            'branch':枝({#枝
                'renderSlot':属性['renderSlot'] if 'renderSlot' in 属性 else None,#槽
                'block':根,#块
                'selectedCallId':属性['selectedCallId'] if 'selectedCallId' in 属性 else None,#选中
                'cwd':属性['cwd'] if 'cwd' in 属性 else None,#cwd
                'openFile':属性['openFile'] if 'openFile' in 属性 else None,#开文件
                'inspectCall':属性['inspectCall'] if 'inspectCall' in 属性 else None,#检查
                't':属性['t'] if 't' in 属性 else None,#文案
            }),#枝结束
            'cssModule':'工具调用树.module.css',#样式
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
