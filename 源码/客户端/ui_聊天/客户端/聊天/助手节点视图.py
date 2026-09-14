from .助手Markdown import 助手Markdown#块体
from .消息图标动作 import 消息图标动作#动作行

__all__=['助手节点视图']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

class 助手节点视图:
    """Markdown 体 + 动作行。"""
    def __init__(自身,属性=None):
        """记下合成 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.体=助手Markdown()#体
        自身.动作=消息图标动作()#动作

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """助手行。"""
        属性=自身.属性#props
        节点=属性['node'] if 'node' in 属性 and 属性['node'] is not None else {}#节点
        数据=节点['data'] if 'data' in 节点 and 节点['data'] is not None else 节点#数据
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        状态=数据['status'] if 'status' in 数据 else None#态
        流式=状态=='running'#流式
        中断=状态=='interrupted'#中断
        块列表=数据['blocks'] if 'blocks' in 数据 else None#块
        加载图=属性['loadImage'] if 'loadImage' in 属性 else None#图
        提及=属性['fileMentions'] if 'fileMentions' in 属性 else None#提及
        分叉=属性['forkAt'] if 'forkAt' in 属性 else None#分叉
        动作=自身.动作({'node':数据,'t':翻译,'forkAt':分叉}) if 流式 is False else None#动作
        return {'type':'assistant-node','status':状态,'body':自身.体({'blocks':块列表,'streaming':流式,'interrupted':中断,'t':翻译,'loadImage':加载图,'mentions':提及}),'actions':动作,'cssModule':'助手节点视图.module.css'}#视图

    def __call__(自身,属性=None):
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
