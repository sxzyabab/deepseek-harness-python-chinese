from .回退命令卡 import 回退命令卡#回退
from .压缩命令卡 import 压缩命令卡#手动压缩

__all__=['命令节点视图','手动压缩节点视图']#仅中文公开名

from nicegui import ui as 界面
from ..异常 import 页面失败文案,贴出失败

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

class 命令节点视图:
    'renderSlot commandview；缺登记走回退卡'

    def __init__(自身,属性=None):
        '记下 props 与回退卡'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.回退=回退命令卡()#回退
        自身.画面=None#可反复清空的画面
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        'callRow 包一层'
        属性=自身.属性#props
        节点=属性['node'] if 'node' in 属性 else None#ChatNode
        命令=节点['data'] if 节点 is not None and 'data' in 节点 else None#命令数据
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        渲染槽=属性['renderSlot'] if 'renderSlot' in 属性 else None#槽
        属主={'node':命令}#属主份额
        名=命令['name'] if 命令 is not None and 'name' in 命令 and 命令['name'] is not None else ''#键
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('callRow')#行
        自身.画面.clear()#清空
        with 自身.画面:#行
            贴出失败(自身)
            结果=None#槽结果
            if 渲染槽 is not None:#有槽
                结果=渲染槽('conversation.chat.commandview',属主,{'entryKey':名})#登记视图自己画
            if 结果 is None:#没有登记
                自身.回退.更新({**属主,'t':翻译})#回退
                自身.回退.渲染()#自己画

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 手动压缩节点视图:
    '集成 /compact 与压缩事务'

    def __init__(自身,属性=None):
        '记下 props 与卡'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.卡=压缩命令卡()#卡
        自身.画面=None#可反复清空的画面
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        'callRow + 压缩命令卡'
        属性=自身.属性#props
        节点=属性['node'] if 'node' in 属性 else None#节点
        数据=节点['data'] if 节点 is not None and 'data' in 节点 else None#数据
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        命令=数据['command'] if 数据 is not None and 'command' in 数据 else None#命令
        载荷={'node':命令,'t':翻译}#载荷
        压缩=数据['compaction'] if 数据 is not None and 'compaction' in 数据 else None#压缩
        if 压缩 is not None:#有
            载荷['compaction']=压缩#附
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('callRow')#行
        自身.画面.clear()#清空
        with 自身.画面:#行
            贴出失败(自身)
            自身.卡.更新(载荷)#灌入
            自身.卡.渲染()#自己画

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
