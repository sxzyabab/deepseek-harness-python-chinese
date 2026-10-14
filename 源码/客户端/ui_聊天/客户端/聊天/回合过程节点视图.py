from ...异常 import 聊天错误#本包异常
from .消息项 import 打开列,收起列

__all__=['回合过程节点视图']#仅中文公开名

from nicegui import ui as 界面

from nicegui import ui as 界面

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

class 回合过程节点视图:
    '可折叠过程披露按钮'
    def __init__(自身,属性=None):
        '记下合成 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.根=None#列
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '不可折叠则不画'
        属性=自身.属性#props
        节点=属性['node'] if 'node' in 属性 and 属性['node'] is not None else {}#节点
        数据=节点['data'] if 'data' in 节点 and 节点['data'] is not None else 节点#数据
        过程=属性['turnProcess'] if 'turnProcess' in 属性 else None#过程面
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        if 过程 is None:#缺所有者
            raise 聊天错误('turn-process node requires Turn process owner state')#缺
        可折=过程['foldable'] if 'foldable' in 过程 else None#可折
        if 可折 is not True:#不可折
            收起列(自身)
            return
        开=过程['open'] is True if 'open' in 过程 else False#开合
        标签列表=[]#片段
        工具数=数据['toolCallCount'] if 'toolCallCount' in 数据 and 数据['toolCallCount'] is not None else 0#工具
        if 工具数>0:#有工具
            标签列表.append(翻译('message.turnProcess.toolCalls.one' if 工具数==1 else 'message.turnProcess.toolCalls.other',{'count':工具数}))#工具
        消息数=数据['messageCount'] if 'messageCount' in 数据 and 数据['messageCount'] is not None else 0#消息
        if 消息数>0:#有消息
            标签列表.append(翻译('message.turnProcess.messages.one' if 消息数==1 else 'message.turnProcess.messages.other',{'count':消息数}))#消息
        子数=数据['subagentCount'] if 'subagentCount' in 数据 and 数据['subagentCount'] is not None else 0#子代理
        if 子数>0:#有子
            标签列表.append(翻译('message.turnProcess.subagents.one' if 子数==1 else 'message.turnProcess.subagents.other',{'count':子数}))#子
        标签=翻译('message.turnProcess.thoughtForAWhile') if len(标签列表)==0 else 翻译('message.turnProcess.separator').join(标签列表)#标签
        def 点击():
            '先聚焦语义由宿主处理'
            设=过程['setOpen'] if 'setOpen' in 过程 else None#设
            if 设 is not None:
                设(not 开)#翻
        with 打开列(自身,'回合过程'):
            按钮=界面.button(标签,on_click=点击)
            if 开 is True:
                按钮.classes(add='展开')

    def __call__(自身,属性=None):
        '对齐'
        if 属性 is not None:
            自身.更新(属性)#刷
        自身.渲染()#画
