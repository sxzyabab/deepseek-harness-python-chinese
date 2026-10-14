from nicegui import ui as 界面
from .异常 import 页面失败文案
from .样式挂载 import 挂到根,读样式

样式表=挂到根(读样式('命令输入视图.module.css'),'目标命令根')
界面.add_css(样式表,shared=True)

__all__=['目标命令输入视图']#仅中文公开名

def 腾出根(自身):
    '清空仍挂着的根。父级已拆掉时丢掉根，并返回要显示的失败句。'
    旧=getattr(自身,'根',None)
    if 旧 is None:
        return None
    try:
        旧.clear()
    except Exception as 错误:
        自身.根=None
        return 页面失败文案(错误)
    return None

def 标出失败(文案):
    '失败句非空时写在当前页面上'
    if isinstance(文案,str) and 文案!='':
        界面.label(文案)

def 缺省翻译(键,_插值=None):#无文案函数
    '原样返回键'
    return 键#键

class 目标命令输入视图:#聊天节点视图
    '渲染 command-input 节点的文本气泡'
    def __init__(自身,属性):#构造
        '记下 props。槽位只调用构造，键齐了就画。'
        自身.属性=属性#合成 props
        if isinstance(自身.属性,dict) and 'node' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):#props 变更
        '刷新'
        自身.属性=属性#最新

    def 卸载(自身):#卸载
        '无状态'
        return#空

    def 视图(自身):#读视图模型
        '投影气泡'
        节点=自身.属性['node'] if 'node' in 自身.属性 and 自身.属性['node'] is not None else {}#节点
        数据=节点['data'] if 'data' in 节点 and 节点['data'] is not None else {}#载荷
        翻译=自身.属性['t'] if 't' in 自身.属性 and 自身.属性['t'] is not None else 缺省翻译#文案
        return {#视图
            'aria':翻译('commandInput.aria'),#无障碍
            'text':数据['text'] if 'text' in 数据 else None,#命令行
            'commandId':数据['commandId'] if 'commandId' in 数据 else None,#命令 id
            'time':数据['time'] if 'time' in 数据 else None,#时刻
        }#视图结束

    def 渲染(自身):
        '命令芯片加其余陈述'
        视=自身.视图()
        文本=视['text'] if isinstance(视['text'],str) else ''
        空白=文本.find(' ')
        头=文本 if 空白==-1 else 文本[:空白]
        余='' if 空白==-1 else 文本[空白:]
        清除失败=腾出根(自身)
        if getattr(自身,'根',None) is None:
            自身.根=界面.element('div').classes('目标命令根 row')
            无障碍=视['aria'] if isinstance(视['aria'],str) else ''
            自身.根.props('role=group aria-label="'+无障碍.replace('"','')+'"')
        with 自身.根:
            标出失败(清除失败)
            with 界面.element('div').classes('stack'):
                with 界面.element('div').classes('bubble'):
                    if 头!='':
                        界面.label(头).classes('token')
                    if 余!='':
                        界面.label(余)

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 组件调用'
        if 属性 is not None:
            自身.更新(属性)#刷新
        return 自身.渲染()
