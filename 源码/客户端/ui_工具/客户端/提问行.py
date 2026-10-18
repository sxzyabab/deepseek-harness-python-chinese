import json
from ...ui_基础界面组件.icons import 图标提问14
from .文案 import 会话命名空间,中文文案
from .原始工具调用 import 单结果文本
from .调用模型 import 工具行模型
from .工具行 import 工具行
from .问题工具表行 import 问题工具表行
from .槽 import 槽名工具调用视图

__all__=['提问行','提问工具视图']

def 是记录(值):
    '非空对象'
    return isinstance(值,dict)

def 解析json(文本):
    '非法 JSON 为 None'
    try:
        return json.loads(文本)
    except json.JSONDecodeError:
        return None

def 答案条目(文本):
    '结果 JSON 里的答案。畸形则 None'
    已解析=解析json(文本)
    if not 是记录(已解析) or not isinstance(已解析.get('answers'),list):
        return None
    条目表=[]
    for 答案 in 已解析['answers']:
        if not 是记录(答案) or not isinstance(答案.get('id'),str) or not isinstance(答案.get('selected'),list):
            return None
        for 项 in 答案['selected']:
            if not isinstance(项,str):
                return None
        if 'custom' in 答案 and not isinstance(答案.get('custom'),str):
            return None
        条目={'id':答案['id'],'selected':答案['selected']}
        if 'custom' in 答案:
            条目['custom']=答案['custom']
        条目表.append(条目)
    return 条目表

def 排队答案(消息,调用标识):
    '还没进入步骤的插话答案'
    if not 是记录(消息) or not isinstance(消息.get('content'),list) or len(消息['content'])==0:
        return None
    内容=消息['content'][0]
    if not 是记录(内容) or 内容.get('type')!='text' or not isinstance(内容.get('text'),str):
        return None
    已解析=解析json(内容['text'])
    if not 是记录(已解析) or 已解析.get('kind')!='answer_to_pending_question' or 已解析.get('callId')!=调用标识:
        return None
    return 答案条目(内容['text'])

def 选项条目(值):
    '选项列表。任一条畸形则整组不要'
    if not isinstance(值,list):
        return None
    选项表=[]
    for 选项 in 值:
        if not 是记录(选项) or not isinstance(选项.get('label'),str):
            return None
        条目={'label':选项['label']}
        if isinstance(选项.get('description'),str):
            条目['description']=选项['description']
        选项表.append(条目)
    return 选项表

def 问题条目(参数原文):
    '调用 JSON 里的问题。编号重复或字段非法则 None'
    已解析=解析json(参数原文)
    if not 是记录(已解析) or not isinstance(已解析.get('questions'),list) or len(已解析['questions'])==0:
        return None
    问题表=[]
    编号=set()
    for 问题 in 已解析['questions']:
        if not 是记录(问题) or not isinstance(问题.get('id'),str) or not isinstance(问题.get('question'),str):
            return None
        if 问题['id'] in 编号:
            return None
        编号.add(问题['id'])
        条目={'id':问题['id'],'question':问题['question']}
        if isinstance(问题.get('header'),str):
            条目['header']=问题['header']
        if isinstance(问题.get('detail'),str):
            条目['detail']=问题['detail']
        选项=选项条目(问题.get('options'))
        if 选项 is not None:
            条目['options']=选项
        if isinstance(问题.get('multi_select'),bool):
            条目['multiSelect']=问题['multi_select']
        问题表.append(条目)
    return 问题表

def 配对答案(问题表,答案表):
    '按稳定编号把问题和答案配上。对不上则 None'
    if len(问题表)!=len(答案表):
        return None
    按编号={}
    for 答案 in 答案表:
        if 答案['id'] in 按编号:
            return None
        按编号[答案['id']]=答案
    配对=[]
    for 问题 in 问题表:
        答案=按编号.get(问题['id'])
        if 答案 is None:
            return None
        答文=list(答案['selected'])
        自定=答案.get('custom')
        if isinstance(自定,str) and 自定!='':
            答文.append(自定)
        配对.append({'id':问题['id'],'question':问题['question'],'answers':答文})
    return 配对

def 已答呈现(问题表,答案表):
    '已答摘要、记录卡和只读面板材料'
    已答=0
    for 答案 in 答案表:
        自定=答案.get('custom') or ''
        if len(答案['selected'])>0 or 自定!='':
            已答=已答+1
    配对=None if 问题表 is None else 配对答案(问题表,答案表)
    记录=None
    if 配对 is not None and 问题表 is not None:
        记录={'questions':问题表,'answers':答案表}
    转录=None
    if 配对 is not None:
        转录={'kind':'answered','questions':配对,'skippedLabel':中文文案('ask.skipped')}
    return {
        'summary':中文文案('ask.answered',{'answered':已答,'total':len(答案表)}),
        'transcript':转录,
        'record':记录,
    }

def 已答摘要(文本):
    '配不上整份记录时，仍尽量数已答数'
    已解析=解析json(文本)
    if not 是记录(已解析) or not isinstance(已解析.get('answers'),list):
        return None
    已答=0
    for 答案 in 已解析['answers']:
        if not 是记录(答案):
            return None
        选自=答案.get('selected')
        自定=答案.get('custom')
        if (isinstance(选自,list) and len(选自)>0) or (isinstance(自定,str) and 自定!=''):
            已答=已答+1
    return 中文文案('ask.answered',{'answered':已答,'total':len(已解析['answers'])})

def 是待答结果(文本):
    '成功结果仍可回答'
    已解析=解析json(文本)
    return 是记录(已解析) and 已解析.get('pending') is True and isinstance(已解析.get('callId'),str)

class 提问行:
    '待答、已答、取消或中断的提问'
    def __new__(类,属性):
        '派生摘要后画提问行或普通工具行'
        自身=object.__new__(类)
        自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '能打开面板时用提问行，否则用工具行'
        属性=自身.属性
        调用标识=属性['callId']
        模型=工具行模型(属性['toolName'],属性['block'])
        块=属性['block']
        可答=False
        已结算=None
        排队=None
        if 'useProjection' in 属性 and 属性['useProjection'] is not None:
            def 取可答(视图,调用标识=调用标识):
                '投影里仍可回答'
                if not isinstance(视图,dict):
                    return False
                活跃=视图.get('active') or []
                for 行 in 活跃:
                    if isinstance(行,dict) and 行.get('callId')==调用标识:
                        return True
                return False
            def 取已结算(视图,调用标识=调用标识):
                '投影里已结算的这一次'
                if not isinstance(视图,dict):
                    return None
                for 行 in 视图.get('settled') or []:
                    if isinstance(行,dict) and 行.get('callId')==调用标识:
                        return 行
                return None
            def 取排队(视图,调用标识=调用标识):
                '收件箱里还没被接纳的回答'
                if not isinstance(视图,dict):
                    return None
                def 匹配(消息,调用标识=调用标识):
                    '来源是这次提问的回复'
                    if not 是记录(消息):
                        return False
                    来源=消息.get('source')
                    return 是记录(来源) and 来源.get('kind')=='user-question-reply' and 来源.get('callId')==调用标识
                下一步=视图.get('next-step') or []
                for 消息 in 下一步:
                    if 匹配(消息):
                        return 消息
                下一轮=视图.get('next-turn') or []
                for 消息 in 下一轮:
                    if 匹配(消息):
                        return 消息
                return None
            可答=属性['useProjection']('userQuestions',取可答) is True
            已结算=属性['useProjection']('userQuestions',取已结算)
            排队=属性['useProjection']('inbox',取排队)
        def 重开(调用标识=调用标识):
            '把回答面板放回输入框'
            揭示=属性.get('revealPanel')
            if 揭示 is None:
                return False
            return 揭示(调用标识) is True
        错误=块.get('error') if 'kind' in 块 else None
        码=错误.get('code') if isinstance(错误,dict) else None
        参数原文=模型['bodyRaw'] or ''
        摘要=模型['summary']
        状态=模型['state']
        转录=None
        行动=None
        行动文=中文文案('ask.reopen')
        if 码=='ASK_CANCELLED':
            摘要=中文文案('ask.cancelled')
            状态='ok'
            问题=问题条目(参数原文)
            if 问题 is not None:
                转录={'kind':'unanswered','questions':问题,'verdict':中文文案('ask.cancelledDetail')}
        elif 码=='ASK_ABORTED':
            摘要=中文文案('ask.interrupted')
            状态='stopped'
            问题=问题条目(参数原文)
            if 问题 is not None:
                转录={'kind':'unanswered','questions':问题,'verdict':中文文案('ask.interruptedDetail')}
        elif 模型['state']=='running':
            摘要=中文文案('ask.waiting')
            if 可答:
                行动=重开
        elif 码=='TOOL_OUTCOME_UNKNOWN' and (可答 or 已结算 is not None):
            状态='ok'
            问题=问题条目(参数原文)
            if 可答:
                摘要=中文文案('ask.pending')
                if 问题 is not None:
                    转录={'kind':'unanswered','questions':问题,'verdict':中文文案('ask.pendingDetail')}
                行动=重开
            elif isinstance(已结算,dict) and len(已结算.get('answers') or [])==0:
                摘要=中文文案('ask.closed')
                if 问题 is not None:
                    转录={'kind':'unanswered','questions':问题,'verdict':中文文案('ask.closedDetail')}
            elif 已结算 is not None:
                呈现=已答呈现(问题,已结算.get('answers') or [])
                摘要=呈现['summary']
                转录=呈现['transcript']
                记录=呈现['record']
                if 记录 is not None:
                    def 复查(记录=记录,调用标识=调用标识):
                        '打开只读回答面板'
                        复核=属性.get('reviewPanel')
                        if 复核 is None:
                            return False
                        return 复核(调用标识,记录) is True
                    行动=复查
                    行动文=中文文案('ask.review')
        elif 'kind' in 块 and 模型['state']=='ok':
            文本=单结果文本(块)
            if 文本 is not None:
                问题=问题条目(参数原文)
                待答=是待答结果(文本)
                if 待答 and 可答:
                    摘要=中文文案('ask.pending')
                    if 问题 is not None:
                        转录={'kind':'unanswered','questions':问题,'verdict':中文文案('ask.pendingDetail')}
                    行动=重开
                elif 待答 and (已结算 is None or len(已结算.get('answers') or [])==0):
                    摘要=中文文案('ask.closed')
                    if 问题 is not None:
                        转录={'kind':'unanswered','questions':问题,'verdict':中文文案('ask.closedDetail')}
                else:
                    if isinstance(已结算,dict):
                        答案=已结算.get('answers')
                    else:
                        答案=答案条目(文本)
                    呈现=None if 答案 is None else 已答呈现(问题,答案)
                    if 呈现 is not None:
                        摘要=呈现['summary']
                    else:
                        备选=已答摘要(文本)
                        摘要=模型['summary'] if 备选 is None else 备选
                    转录=None if 呈现 is None else 呈现['transcript']
                    记录=None
                    if 已结算 is not None and 呈现 is not None:
                        记录=呈现['record']
                    if 记录 is not None:
                        def 复查(记录=记录,调用标识=调用标识):
                            '打开只读回答面板'
                            复核=属性.get('reviewPanel')
                            if 复核 is None:
                                return False
                            return 复核(调用标识,记录) is True
                        行动=复查
                        行动文=中文文案('ask.review')
        if 可答 and 排队 is not None and 行动 is 重开:
            答案=排队答案(排队,调用标识)
            呈现=None if 答案 is None else 已答呈现(问题条目(参数原文),答案)
            if 呈现 is not None and 呈现['record'] is not None:
                摘要=呈现['summary']
                转录=呈现['transcript']
                def 不打开():
                    '排队回复只在这一行查看'
                    return False
                行动=不打开
                行动文=中文文案('ask.review')
        体原文=模型['bodyRaw'] if 转录 is None else None
        输出=模型['output'] if 转录 is None else None
        if 行动 is not None:
            return 问题工具表行({
                'window':属性['window'],
                'useDisclosure':属性['useDisclosure'],
                'summary':摘要,
                'bodyRaw':体原文,
                'output':输出,
                'askQuestion':转录,
                'state':状态,
                'inspect':属性.get('inspect'),
                'openPanel':行动,
                'panelLabel':行动文,
            })
        return 工具行({
            'window':属性['window'],
            'useDisclosure':属性['useDisclosure'],
            'variant':模型['variant'],
            'toolName':属性['toolName'],
            'icon':图标提问14({'window':属性['window']}),
            'title':中文文案(模型['titleKey']),
            'summary':摘要,
            'bodyRaw':体原文,
            'output':输出,
            'askQuestion':转录,
            'state':状态,
            'inspect':属性.get('inspect'),
        })

def 应用提问工具视图(上下文,配置=None):
    '登记 ask_user_question。面板在点击时再读'
    def 登记():
        '注入本会话的面板动作'
        def 注入(会话标识):
            '没有提问界面时两个动作都是假'
            def 揭示(调用标识,会话标识=会话标识):
                '把面板放回输入框'
                面板=上下文.get('userQuestionPanels')
                if 面板 is None:
                    return False
                return 面板.reveal(会话标识,调用标识) is True
            def 复核(调用标识,记录,会话标识=会话标识):
                '打开只读记录'
                面板=上下文.get('userQuestionPanels')
                if 面板 is None:
                    return False
                return 面板.review(会话标识,调用标识,记录) is True
            return {'revealPanel':揭示,'reviewPanel':复核}
        return 上下文.slots.register({
            'name':槽名工具调用视图,
            'key':'ask_user_question',
            'locale':会话命名空间,
            'inject':注入,
        },提问行)
    上下文.slots.inject(槽名工具调用视图,登记)

提问工具视图={
    'name':'ask-question-toolview',
    'inject':['slots'],
    'apply':应用提问工具视图,
}
