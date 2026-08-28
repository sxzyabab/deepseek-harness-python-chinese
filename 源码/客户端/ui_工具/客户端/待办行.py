"""待办工具行：todo_write 计划风味摘要行，替换通用 Tool call 卡。

对齐上游 `ui-tool/src/client/tool/toolviews/todo-row.tsx`。公开面仅中文名。
登记进按键 tool.call.toolview 洞；持久列表在 TodoPanel，本行保持单行直至展开。
"""
import json#解析 args JSON
from .文案 import 会话命名空间#conversation 词典席
from .调用模型 import 派生工具行,取字段#行模型
from .计划摘要 import 计划摘要#计划推导
from .工具行 import 工具行#摘要行外壳

__all__=['待办行','待办工具视图','是否计划条目','汇总']#仅中文公开名

def 是否计划条目(值):#形检查一条计划项
    """来自未校验模型 JSON 的列表项。"""
    return isinstance(值,dict) and 值 is not None#普通对象

def 汇总(文本,翻译):#从 args JSON 派生摘要两半
    """非法字段时 None，行回退通用摘要。"""
    try:#解析
        解析=json.loads(文本)#JSON
    except Exception:#非 JSON
        return None#无效
    if not isinstance(解析,dict) or 解析 is None:#非对象
        return None#无效
    待办们=解析.get('todos')#待办数组
    if not isinstance(待办们,list) or not all(是否计划条目(项) for 项 in 待办们):#非法
        return None#无效
    摘要=计划摘要(待办们)#个数与活跃
    头=翻译('todo.completed',{'done':摘要['done'],'total':摘要['total']}) if callable(翻译) else str(摘要['done'])+'/'+str(摘要['total'])#已完成头
    活跃=摘要['activeContent']#活跃正文
    文本半=头 if 活跃 is None else 头+' · '+活跃#可截断半
    return {'text':文本半,'extra':摘要['activeExtra']}#两半

class 待办行:#计划更新行
    """整行切换调用的 Input/Output；非 ok 态保留共享行点语义。"""

    def __init__(自身,属性=None):#记下 props
        """记下合成 props；内嵌工具行。"""
        自身.属性=属性 or {}#合成
        自身.行=工具行()#外壳

    def 更新(自身,属性):#刷新
        """刷新合成 props。"""
        自身.属性=属性#新

    def 渲染(自身):#结构树
        """派生摘要/态后交给工具行。"""
        属性=自身.属性#props
        工具名=取字段(属性,'toolName') or 'todo_write'#工具名
        块=取字段(属性,'block')#工具块
        翻译=取字段(属性,'t')#文案
        检查=取字段(属性,'inspect')#检查
        模型=派生工具行(工具名,块)#行模型
        已结算=(isinstance(块,dict) and 'kind' in 块) or (not isinstance(块,dict) and 取字段(块,'kind') is not None)#是否已结算
        if 已结算:#已结算取 call.argsRaw
            原始=取字段(取字段(块,'call'),'argsRaw') or ''#args
        else:#进行中
            原始=取字段(块,'argsRaw') or ''#args
        摘要=汇总(原始,翻译) or {'text':取字段(模型,'summary'),'extra':0}#摘要两半
        额外=摘要['extra']#并行额外数
        行属性={#交给工具行
            't':翻译,#文案
            'variant':取字段(模型,'variant'),#变体
            'toolName':工具名,#工具名
            'icon':'checklist',#清单图标
            'title':翻译('todo.rowTitle') if callable(翻译) else 'todo.rowTitle',#行标题
            'summary':摘要['text'],#可截断摘要
            'summarySuffix':('+'+str(额外)) if 额外>0 else None,#不收缩后缀
            'body':取字段(模型,'body'),#输入
            'output':取字段(模型,'output'),#输出
            'errorSummary':取字段(模型,'errorSummary'),#错摘要
            'state':取字段(模型,'state'),#态
            'inspect':检查,#检查
        }#结束
        return 自身.行(行属性)#渲染外壳

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

待办工具视图={#按键 toolview 登记插件
    'name':'todo-toolview',#插件名
    'inject':['slots'],#依赖槽位
}#插件描述

def 应用待办工具视图(上下文):#登记待办行
    """把待办行写入 Tool 拥有的按键视图槽。"""
    def 登记():#等槽出现再登记
        """登记 todo_write 键。"""
        return 上下文.slots.register({#按键条目
            'name':'tool.call.toolview','key':'todo_write','locale':会话命名空间,#选项
        },待办行)#组件
    上下文.slots.inject('tool.call.toolview',登记)#等槽

待办工具视图['apply']=应用待办工具视图#挂 apply
