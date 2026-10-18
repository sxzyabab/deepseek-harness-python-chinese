'按种类把提示变成展示字段，再交给共享吐司'
from ....模块.客户端.通告 import 取握手窗口
from ....ui_基础界面组件.吐司 import 吐司
from ....ui_基础界面组件.icons import 图标
from ..会话动作.派生 import 换上

__all__=['提示条目','归档提示条目','工作区提示','提示条目组件','归档提示条目组件','工作区提示组件']

def 挂工厂(父,产出):
    '工厂槽交回的节点挂进包裹'
    if 产出 is None:#空
        return#不挂
    if isinstance(产出,dict):#包装
        for 键 in ('content','body'):#常见字段
            if hasattr(产出.get(键),'tagName'):#节点
                父.appendChild(产出[键])#挂上
                return#完
        return#没有节点
    if hasattr(产出,'tagName'):#节点
        父.appendChild(产出)#挂上

class 提示条目:
    '用注入的 display 把这条提示变成吐司字段'
    def __init__(自身,属性):
        '记下属性'
        自身.属性=属性#属性
        自身.根=None#节点

    def 渲染(自身):
        '交给 workspace.toast.content'
        属性=自身.属性#属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        展示=属性['display'](属性,属性.get('t'),属性['dismissToast'])#展示字段
        载荷={**展示,'seq':属性.get('seq'),'onDone':属性['dismissToast']}#带序号
        文档=窗口.document#文档
        根=文档.createElement('div')#包裹
        挂工厂(根,属性['renderFactorySlot']('workspace.toast.content',载荷))#工厂
        return 换上(自身,根)#节点

class 归档提示条目:
    '归档提示在筛选还不是默认以外时，再加一条去筛选的动作'
    def __init__(自身,属性):
        '记下属性'
        自身.属性=属性#属性
        自身.根=None#节点

    def 渲染(自身):
        '筛选已经能看见归档时，不再加筛选动作'
        属性=自身.属性#属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        def 已可见(状态):
            '不是默认隐藏'
            筛选=状态.get('archivedFilter') or 'default'#筛选
            return 筛选!='default'#可见
        可见=属性['useStore'](已可见)#是否已显示归档
        展示=属性['display'](属性,属性.get('t'),属性['dismissToast'])#展示
        动作=list(展示.get('actions') or [])#已有动作
        if not 可见:#还藏着归档
            动作.append(属性['filterAction'](属性.get('t'),属性['dismissToast']))#筛选动作
        载荷={**展示,'actions':动作,'seq':属性.get('seq'),'onDone':属性['dismissToast']}#带动作
        文档=窗口.document#文档
        根=文档.createElement('div')#包裹
        挂工厂(根,属性['renderFactorySlot']('workspace.toast.content',载荷))#工厂
        return 换上(自身,根)#节点

class 工作区提示:
    '共享吐司。成功用成功语气，警告带警告图标'
    def __init__(自身,属性):
        '记下属性'
        自身.属性=属性#属性
        自身.根=None#节点

    def 渲染(自身):
        '按语气和动作画出吐司'
        属性=自身.属性#属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        吐司属性={'window':窗口,'text':属性.get('text') or '','onDone':属性.get('onDone')}#基本
        if 属性.get('tone')=='success':#成功
            吐司属性['tone']='success'#成功语气
        if 属性.get('tone')=='warning':#警告
            吐司属性['icon']=图标('warning-16',{'window':窗口})#警告图标
        if 属性.get('holdMs') is not None:#指定保持
            吐司属性['holdMs']=属性['holdMs']#保持
        if 属性.get('actions') is not None:#有动作
            吐司属性['actions']=属性['actions']#动作
        return 换上(自身,吐司(吐司属性).渲染())#节点

def 提示条目组件(属性):
    '渲染器按函数调用'
    return 提示条目(属性).渲染()#节点

def 归档提示条目组件(属性):
    '渲染器按函数调用'
    return 归档提示条目(属性).渲染()#节点

def 工作区提示组件(属性):
    '工厂每次按序号重画'
    return 工作区提示(属性).渲染()#节点
