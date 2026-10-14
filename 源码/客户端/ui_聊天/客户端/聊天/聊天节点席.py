from ..约定.回合过程 import 回合过程独立种类#过程折叠独立种类
from ..存储 import 已存回合过程条目#持久过程开合
from .可搜索隐藏 import 可搜索隐藏#可搜索隐藏

__all__=['聊天节点席']#仅中文公开名

import json
from nicegui import ui as 界面
from ...异常 import 页面失败文案

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

def 空渲染槽(*位置参数,**关键字参数):
    '未注入槽渲染时不画'
    return None#不画

def 绘制已登记组件(值,回退=None,看见=None):
    '沿槽结果找到组件并调用渲染。回退对象由调用方另行绘制。'
    if 值 is None or 值 is 回退:
        return False
    if 看见 is None:
        看见=set()
    编号=id(值)
    if 编号 in 看见:
        return False
    看见.add(编号)
    if not isinstance(值,(dict,list,tuple,str,bytes)):
        方法=getattr(值,'渲染',None)
        if 方法 is None:
            return False
        方法()
        return True
    画了=False
    序列=值.values() if isinstance(值,dict) else 值
    for 子 in 序列:
        if 绘制已登记组件(子,回退,看见):
            画了=True
    return 画了

def 回合数据(节点):
    '仅 turn/step 位置。节点为 dict'
    位置=节点['location'] if 'location' in 节点 else None#位置
    种=位置['kind'] if 位置 is not None and 'kind' in 位置 else None#种
    if 种 in ('turn','step'):
        回合=位置['turn'] if 'turn' in 位置 else None#回合
        return 回合['data'] if 回合 is not None and 'data' in 回合 else None#数据
    return None#无

def 回合号(节点):
    '仅 turn/step。节点为 dict'
    位置=节点['location'] if 'location' in 节点 else None#位置
    种=位置['kind'] if 位置 is not None and 'kind' in 位置 else None#种
    if 种 in ('turn','step'):
        回合=位置['turn'] if 'turn' in 位置 else None#回合
        return 回合['turn'] if 回合 is not None and 'turn' in 回合 else None#号
    return None#无

class 聊天节点席:
    '订阅一 Node 键；兄弟更新不重挂'
    def __init__(自身,属性=None):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.包装=None#可搜索隐藏

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '过程折叠 + 槽分发或 JSON 回退'
        属性=自身.属性#props
        节点键=属性['nodeKey'] if 'nodeKey' in 属性 else None#键
        用节点=属性['useChatNode'] if 'useChatNode' in 属性 else None#读节点
        用过程=属性['useChatNodeProcess'] if 'useChatNodeProcess' in 属性 else None#过程呈现
        用存储=属性['useStore'] if 'useStore' in 属性 else None#UI store
        动作=属性['actions'] if 'actions' in 属性 and 属性['actions'] is not None else {}#动作
        渲染槽=属性['renderSlot'] if 'renderSlot' in 属性 else 空渲染槽#槽
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        紧凑=属性['compactTranscript'] is True if 'compactTranscript' in 属性 else False#紧凑
        历史不全=属性['historyIncomplete'] is True if 'historyIncomplete' in 属性 else False#历史不全
        节点=用节点(节点键) if 用节点 is not None else None#节点
        if 节点 is None:#未物化
            if 自身.包装 is not None and 自身.包装.根 is not None:
                try:
                    自身.包装.根.clear()
                    自身.包装.根.set_visibility(False)
                except Exception as 错误:
                    自身.包装=None
                    界面.label(页面失败文案(错误))
            return
        过程呈现=用过程(节点键) if 用过程 is not None else None#呈现
        规格=过程呈现['spec'] if 过程呈现 is not None and 'spec' in 过程呈现 else None#规格
        存条目=None#存
        if 用存储 is not None and 规格 is not None:#可存
            回合=规格['turn'] if 'turn' in 规格 else None#回合
            def 取存(态):
                '已存过程条目'
                return 已存回合过程条目(态,回合)#存
            存条目=用存储(取存)#存
        答步=规格['answerStep'] if 规格 is not None and 'answerStep' in 规格 else None#答步
        存步=存条目['answerStep'] if 存条目 is not None and 'answerStep' in 存条目 else None#存步
        过程条目=存条目 if 规格 is not None and 答步 is not None and 存步==答步 else None#匹配
        过程开=过程条目 is not None#开合
        def 设开(开):
            '写入 store'
            写=动作['setTurnProcessOpen'] if 'setTurnProcessOpen' in 动作 else None#写
            if 写 is not None and 规格 is not None and 答步 is not None:#可写
                写(规格['turn'] if 'turn' in 规格 else None,答步,开)#写
        锚序=规格['answerAnchorSeq'] if 规格 is not None and 'answerAnchorSeq' in 规格 else None#锚序
        过回合=过程呈现['turn'] if 过程呈现 is not None and 'turn' in 过程呈现 else None#过回合
        规回合=规格['turn'] if 规格 is not None and 'turn' in 规格 else None#规回合
        已关=过程呈现['turnClosed'] is True if 过程呈现 is not None and 'turnClosed' in 过程呈现 else False#已关
        窗口就绪=规格 is not None and 过程呈现 is not None and 紧凑 is True and 锚序 is not None and 过回合==规回合 and 已关 is True and 历史不全 is False#就绪
        锚=节点['anchorSeq'] if 'anchorSeq' in 节点 else None#锚
        种=节点['kind'] if 'kind' in 节点 else None#种
        起序=规格['processStartSeq'] if 规格 is not None and 'processStartSeq' in 规格 else None#起序
        成员=窗口就绪 is True and 种 not in 回合过程独立种类 and 锚 is not None and 起序 is not None and 锚序 is not None and 锚>=起序 and 锚<锚序#成员
        数据=节点['data'] if 'data' in 节点 else None#数据
        步=数据['step'] if 数据 is not None and 'step' in 数据 else None#步
        答案=窗口就绪 is True and 种=='assistant-step' and 步==答步#答案
        持披露=种=='turn-process' or 答案 is True#披露主
        有外=过程呈现['hasExternalProcess'] is True if 过程呈现 is not None and 'hasExternalProcess' in 过程呈现 else False#有外
        内联=规格['inlineReasoning'] is True if 规格 is not None and 'inlineReasoning' in 规格 else False#内联
        可折=窗口就绪 is True and (成员 is True or (持披露 is True and (有外 is True or 内联 is True)))#可折
        过程面={'spec':规格,'foldable':可折,'open':过程开,'setOpen':设开} if 规格 is not None else None#过程面
        控件失活=种=='turn-process' and 可折 is False#失活
        紧凑答=答案 is True and 可折 is True and (过程呈现['compactAnswer'] is True if 过程呈现 is not None and 'compactAnswer' in 过程呈现 else False) and 过程开 is False#紧凑答
        过程隐=控件失活 is True or (可折 is True and 成员 is True and 过程开 is False)#隐藏
        def 揭开():
            '成员则开'
            if 成员 is True:#成员
                设开(True)
        if 自身.包装 is None:
            自身.包装=可搜索隐藏(过程隐,揭开)
        else:
            自身.包装.隐藏=过程隐
            自身.包装.揭示=揭开
        自身.包装.渲染()
        if 成员 is True:
            自身.包装.根.classes(add='过程成员')
        if 紧凑答 is True:
            自身.包装.根.classes(add='过程答案')
        def 截断标签(总):
            'json.truncated'
            return 翻译('json.truncated',{'total':总})#标签
        属主={'selectedCallId':属性['selectedCallId'] if 'selectedCallId' in 属性 else None,'cwd':属性['cwd'] if 'cwd' in 属性 else None,'openFile':属性['openFile'] if 'openFile' in 属性 else None,'inspectCall':属性['inspectCall'] if 'inspectCall' in 属性 else None,'forkAt':属性['forkAt'] if 'forkAt' in 属性 else None,'loadImage':属性['loadImage'] if 'loadImage' in 属性 else None,'renderMessageImages':属性['renderMessageImages'] if 'renderMessageImages' in 属性 else None,'fileMentions':属性['fileMentions'] if 'fileMentions' in 属性 else None,'turnProcess':过程面,'node':节点,'t':翻译}#属主
        回退={'type':'json-block','label':翻译('message.unknownSurface',{'type':种}),'payload':节点['data'] if 'data' in 节点 else None,'truncatedLabel':截断标签}#回退
        with 自身.包装.根:
            画出=渲染槽('conversation.chat.node',属主,{'entryKey':种,'hookContext':回合数据(节点),'fallback':回退})
            if 画出 is 回退:
                界面.label(翻译('message.unknownSurface',{'type':种}))
                载荷=节点['data'] if 'data' in 节点 else None
                if 载荷 is not None:
                    try:
                        原文=json.dumps(载荷,ensure_ascii=False,indent=2)
                    except TypeError:
                        原文=str(载荷)
                    if len(原文)>2000:
                        界面.label(截断标签(len(原文)))
                        原文=原文[:2000]
                    界面.code(原文).classes('载荷')
                return
            绘制已登记组件(画出,回退)

    def __call__(自身,属性=None):
        '对齐'
        if 属性 is not None:
            自身.更新(属性)#刷
        自身.渲染()#画
