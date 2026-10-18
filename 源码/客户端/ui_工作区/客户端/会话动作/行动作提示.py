'浮层把当前提示交给按种类登记的那一块，自己不解释业务'
from ....模块.客户端.通告 import 取握手窗口
from .派生 import 换上

__all__=['行动作提示','行动作提示组件']

def 挂上(父,产出):
    '渲染器交回来的可能是包装。有节点就挂上'
    if 产出 is None:#空
        return#不挂
    if isinstance(产出,dict):#包装
        if hasattr(产出.get('content'),'tagName'):#出口节点
            父.appendChild(产出['content'])#挂上
            return#完
        if hasattr(产出.get('body'),'tagName'):#体
            父.appendChild(产出['body'])#挂上
            return#完
        for 键 in ('content','body','items'):#再往里
            if 键 in 产出:#有
                挂上(父,产出[键])#递归
        return#完
    if isinstance(产出,(list,tuple)):#多项
        for 项 in 产出:#逐项
            挂上(父,项)#挂
        return#完
    if hasattr(产出,'tagName'):#节点
        父.appendChild(产出)#挂上

class 行动作提示:
    '当前没有提示就不画'
    def __init__(自身,属性):
        '记下属性'
        自身.属性=属性#属性
        自身.根=None#节点

    def 渲染(自身):
        '按 kind 挑选已登记的提示'
        属性=自身.属性#属性
        def 原样(当前):
            '提示本身'
            return 当前#原样
        提示=属性['useToast'](原样)#当前提示
        if 提示 is None:#没有
            return 换上(自身,None)#不画
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        文档=窗口.document#文档
        根=文档.createElement('div')#包裹
        产出=属性['renderSlot']('workspace.toast',{**提示,'dismissToast':属性['dismissToast']},{'entryKey':提示['kind']})#按种类
        挂上(根,产出)#放入
        return 换上(自身,根)#节点

def 行动作提示组件(属性):
    '同一登记只留一份分发'
    if not hasattr(行动作提示组件,'实例'):#第一次
        行动作提示组件.实例=行动作提示(属性)#创建
    else:#再来
        行动作提示组件.实例.属性=属性#更新
    return 行动作提示组件.实例.渲染()#节点
