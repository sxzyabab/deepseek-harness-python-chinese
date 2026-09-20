from .卡片模型 import 动作卡片#卡模型
from .运行行 import 样式表#共用样式

__all__=['动作行','样式表','前导图标']#仅中文公开名

def 前导图标(态,移除):
    """error/stopped 用 StateDot；否则 Trash 或 Stop。"""
    if 态=='error':#失败
        return {'type':'StateDot','state':'error'}#红点
    if 态=='stopped':#中断
        return {'type':'StateDot','state':'warning'}#琥珀
    if 移除:#移除
        return {'type':'IconTrashOutline16','size':14}#垃圾桶
    return {'type':'IconStopFill16','size':14}#停止

def 去掉空子节点(子节点列表):
    """去掉 None 子节点。"""
    return [子 for 子 in 子节点列表 if 子 is not None]#过滤

def 原样键(键):
    """无翻译函数时返回键本身。"""
    return 键#原样

class 动作行:
    """组装停止或移除卡嵌套 JSX 树。属性为 dict。"""

    def __init__(自身,属性=None):
        """记下 props。"""
        自身.属性={} if 属性 is None else 属性#合成

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性={} if 属性 is None else 属性#新

    def 渲染(自身):
        """与上游 JSX 同构。"""
        p=自身.属性#props dict
        块=p['block'] if 'block' in p else None#调用块
        卡=动作卡片(块)#卡
        if 't' in p and p['t'] is not None:#有翻译
            翻译=p['t']#文案
        else:#缺席
            翻译=原样键#原样键
        工具名=p['toolName'] if 'toolName' in p else None#工具
        移除=工具名=='cordis_undefine'#移除
        if 'errorSummary' in 卡 and 卡['errorSummary'] is not None:#有错误摘要
            摘要=卡['errorSummary']#摘要
        elif 'pluginId' in 卡 and 卡['pluginId'] is not None:#有插件
            摘要=卡['pluginId']#插件
        elif 'callId' in p:#回落调用 id
            摘要=p['callId']#调用 id
        else:#都没有
            摘要=None#空
        巡检=p['inspect'] if 'inspect' in p else None#巡检
        态=卡['state'] if 'state' in 卡 else None#状态
        行子=去掉空子节点([#css.row 子
            {'type':'span','class':'icon','children':[前导图标(态,移除)]},#图标
            {'type':'span','class':'title','children':[翻译('row.removeTitle' if 移除 else 'row.stopTitle')]},#标题
            {'type':'span','class':'separator','aria-hidden':True},#分隔
            {'type':'span','class':'error' if ('errorSummary' in 卡 and 卡['errorSummary'] is not None) else 'summary','children':[摘要]},#摘要
            {'type':'button','class':'inspect','aria-label':'Inspect','onClick':'inspect',
             'children':[{'type':'IconInspectOutline12'}]} if 巡检 is not None else None,#巡检
        ])#行子结束
        卡子=[{'type':'div','class':'row','children':行子}]#顶行
        if 'output' in 卡 and 卡['output'] is not None:#输出
            卡子.append({'type':'pre','class':'output','children':[卡['output']]})#输出
        return {#根
            'type':'div','class':'card','data-tool':工具名,'data-state':态,
            'children':卡子,'css':样式表,
            'handlers':{'inspect':巡检},#动作
            'note':'图标半需浏览器；无法 Python·vm 执行图标原语',#缺口
        }#结束

    def __call__(自身,属性=None):
        """结构树面。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
