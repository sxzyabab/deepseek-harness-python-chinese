import json
from .文案 import 会话命名空间
from .调用模型 import 派生工具行
from .工具行 import 工具行

__all__=['提问行','提问工具视图','已答摘要','是否答案条目']

def 是否答案条目(值):
    '跨线 result JSON 的答案条目'
    return isinstance(值,dict)

def 已答摘要(文本,翻译):
    '跳过题 selected 空且无 custom；字段非法时 None'
    try:
        解析=json.loads(文本)
    except (TypeError,ValueError,json.JSONDecodeError):
        return None
    if not isinstance(解析,dict):
        return None
    答案列表=解析['answers'] if 'answers' in 解析 else None
    if not isinstance(答案列表,list) or not all(是否答案条目(项) for 项 in 答案列表):
        return None
    已答=0
    for 项 in 答案列表:
        已选=项['selected'] if 'selected' in 项 else None
        自定义=项['custom'] if 'custom' in 项 else None
        if (isinstance(已选,list) and len(已选)>0) or (isinstance(自定义,str) and 自定义!=''):
            已答+=1
    return 翻译('ask.answered',{'answered':已答,'total':len(答案列表)})

class 提问行:
    '整行切换调用的输入输出。槽位只调用构造，键齐了就画'

    def __init__(自身,属性):
        '记下合成 props，并挂上空的工具行。工具行由渲染画出'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.行=工具行()
        if 'block' in 自身.属性 and 't' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性

    def 渲染(自身):
        '派生摘要与状态后交给工具行'
        属性=自身.属性
        工具名=属性['toolName'] if 'toolName' in 属性 and 属性['toolName'] else 'ask_user_question'
        块=属性['block']
        翻译=属性['t']
        检查=属性['inspect'] if 'inspect' in 属性 else None
        切片=dict(块)
        if 'toolName' not in 切片 and 'name' not in 切片:
            切片['toolName']=工具名
        模型=派生工具行(切片)
        摘要=模型['summary']
        状态=模型['state']
        已结算='kind' in 块
        错=块['error'] if 已结算 and 'error' in 块 else None
        码=错['code'] if 错 is not None and 'code' in 错 else None
        if 码=='ASK_CANCELLED':
            摘要=翻译('ask.cancelled')
        elif 码=='ASK_ABORTED':
            摘要=翻译('ask.interrupted')
            状态='stopped'
        elif 模型['state']=='running':
            摘要=翻译('ask.waiting')
        elif 已结算 and 模型['state']=='ok':
            内容=块['content'] if 'content' in 块 and 块['content'] is not None else []
            文本=''.join((b['text'] if 'text' in b and b['text'] is not None else '') for b in 内容 if isinstance(b,dict) and 'type' in b and b['type']=='text')
            摘要=已答摘要(文本,翻译) if 已答摘要(文本,翻译) is not None else 模型['summary']
        行属性={
            't':翻译,
            'variant':模型['variant'],
            'toolName':工具名,
            'icon':'question',
            'title':翻译('ask.rowTitle'),
            'summary':摘要,
            'body':模型['body'],
            'output':模型['output'],
            'state':状态,
            'inspect':检查,
        }
        return 自身.行(行属性)

    def __call__(自身,属性=None):
        '有新属性则刷新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

提问工具视图={
    'name':'ask-question-toolview',
    'inject':['slots'],
}

def 应用提问工具视图(上下文):
    '把提问行写入按键视图槽'
    def 登记():
        '登记 ask_user_question 键'
        return 上下文.slots.register({
            'name':'tool.call.toolview',
            'key':'ask_user_question',
            'locale':会话命名空间,
        },提问行)
    上下文.slots.inject('tool.call.toolview',登记)

提问工具视图['apply']=应用提问工具视图
