from .准备行 import 准备行,画出根
from .卡片模型 import 动作卡片
from .运行行 import 样式表

__all__=['动作行','样式表','前导图标']#仅中文公开名

def 前导图标(态,移除):
    'error/stopped 用 StateDot；否则 Trash 或 Stop'
    if 态=='error':
        return {'type':'StateDot','state':'error'}
    if 态=='stopped':
        return {'type':'StateDot','state':'warning'}
    if 移除:
        return {'type':'IconTrashOutline16','size':14}
    return {'type':'IconStopFill16','size':14}

def 去掉空子节点(子节点列表):
    '去掉 None 子节点'
    return [子 for 子 in 子节点列表 if 子 is not None]

def 原样键(键):
    '无翻译函数时返回键本身'
    return 键

class 动作行:
    '组装停止或移除卡嵌套 JSX 树。属性为 dict'

    def __init__(自身,属性=None):
        '记下 props'
        自身.属性={} if 属性 is None else 属性
        if 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性={} if 属性 is None else 属性

    def 渲染(自身):
        '与上游 JSX 同构；参数未齐时只画准备前缀'
        p=自身.属性
        if p.get('phase')=='preparing':
            if 't' in p and p['t'] is not None:
                翻译=p['t']
            else:
                翻译=原样键
            工具名=p['toolName'] if 'toolName' in p else None
            移除=工具名=='cordis_undefine'
            return 准备行({
                'toolName':工具名,'t':翻译,
                'icon':{'type':'IconTrashOutline16','size':14} if 移除 else {'type':'IconStopFill16','size':14},
                'title':翻译('row.removeTitle' if 移除 else 'row.stopTitle'),
                'className':'card','rowClassName':'row','titleClassName':'title',
            }).渲染()
        块=p['block'] if 'block' in p else None
        卡=动作卡片(块)
        if 't' in p and p['t'] is not None:
            翻译=p['t']
        else:
            翻译=原样键
        工具名=p['toolName'] if 'toolName' in p else None
        移除=工具名=='cordis_undefine'
        if 'errorSummary' in 卡 and 卡['errorSummary'] is not None:
            摘要=卡['errorSummary']
        elif 'pluginId' in 卡 and 卡['pluginId'] is not None:
            摘要=卡['pluginId']
        elif 'callId' in p:
            摘要=p['callId']
        else:
            摘要=None
        巡检=p['inspect'] if 'inspect' in p else None
        态=卡['state'] if 'state' in 卡 else None
        行子=去掉空子节点([
            {'type':'span','class':'icon','children':[前导图标(态,移除)]},
            {'type':'span','class':'title','children':[翻译('row.removeTitle' if 移除 else 'row.stopTitle')]},
            {'type':'span','class':'separator','aria-hidden':True},
            {'type':'span','class':'error' if ('errorSummary' in 卡 and 卡['errorSummary'] is not None) else 'summary','children':[摘要]},
            {'type':'button','class':'inspect','aria-label':'Inspect','onClick':'inspect',
             'children':[{'type':'IconInspectOutline12'}]} if 巡检 is not None else None,
        ])
        卡子=[{'type':'div','class':'row','children':行子}]
        if 'output' in 卡 and 卡['output'] is not None:
            卡子.append({'type':'pre','class':'output','children':[卡['output']]})
        树={
            'type':'div','class':'card','data-tool':工具名,'data-state':态,
            'children':卡子,'css':样式表,
            'handlers':{'inspect':巡检},
            'note':'图标半需浏览器；无法 Python·vm 执行图标原语',
        }
        return 画出根(树)

    def __call__(自身,属性=None):
        '结构树面'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
