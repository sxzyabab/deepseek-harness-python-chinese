'完成回答下面的卡片框架：标题、折叠说明，以及种类正文或只剩暂不需要'
import os
import unicodedata
from ....客户端.模块.客户端.通告 import 取握手窗口
from ....客户端.ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点
from ....客户端.ui_基础界面组件.按钮 import 按钮

__all__=['折叠文本','操作卡片尾','操作卡片']

样式模块='action-card'
折叠宽度=260
编号={'n':0}
宽汉字=(
    (0x3400,0x4DBF),(0x4E00,0x9FFF),(0xF900,0xFAFF),
    (0x20000,0x2A6DF),(0x2A700,0x2B73F),(0x2B740,0x2B81F),
    (0x2B820,0x2CEAF),(0x2CEB0,0x2EBEF),(0x30000,0x3134F),
)
宽假名=((0x3040,0x309F),(0x30A0,0x30FF),(0x31F0,0x31FF))
宽谚文=((0x1100,0x11FF),(0x3130,0x318F),(0xA960,0xA97F),(0xAC00,0xD7AF),(0xD7B0,0xD7FF))
宽标点=((0x3000,0x303F),(0xFF00,0xFF60),(0xFFE0,0xFFE6))


def 下一编号():
    '这一文档里折叠段落的标识'
    编号['n']=编号['n']+1
    return 'action-card-fold-'+str(编号['n'])


def 在区间(码,区间):
    '码位是否落在任一闭区间'
    for 起,止 in 区间:
        if 起<=码<=止:
            return True
    return False


def 是宽字素(字素):
    '汉字、假名、谚文、中日韩标点和全角算两个拉丁字母宽'
    if len(字素)==0:
        return False
    码=ord(字素[0])
    return 在区间(码,宽汉字) or 在区间(码,宽假名) or 在区间(码,宽谚文) or 在区间(码,宽标点)


def 字素列(文本):
    '按组合记号、变异选择符和零宽连接切开。不改原文'
    列=[]
    索引=0
    长度=len(文本)
    while 索引<长度:
        止=索引+1
        while 止<长度 and (unicodedata.combining(文本[止])!=0 or 文本[止] in ('\ufe0e','\ufe0f')):
            止=止+1
        if 0x1F1E6<=ord(文本[索引])<=0x1F1FF and 止<长度 and 0x1F1E6<=ord(文本[止])<=0x1F1FF:
            止=止+1
        while 止<长度 and 文本[止-1]=='\u200d':
            止=止+1
            while 止<长度 and (unicodedata.combining(文本[止])!=0 or 文本[止] in ('\ufe0e','\ufe0f')):
                止=止+1
        if 止<长度 and 0x1F3FB<=ord(文本[止])<=0x1F3FF:
            止=止+1
        列.append(文本[索引:止])
        索引=止
    return 列


def 预览(文本):
    '空白收成单空格。超过约两行就截断并加省略号。短文不截'
    紧凑=' '.join(文本.split())
    字素=字素列(紧凑)
    宽度=0
    下标=0
    while 下标<len(字素):
        宽度=宽度+(2 if 是宽字素(字素[下标]) else 1)
        if 宽度>折叠宽度:
            return ''.join(字素[:下标]).rstrip()+'…'
        下标=下标+1
    return None


def 窗口于(属性):
    '宿主窗口。没有时用当前页'
    if isinstance(属性,dict) and 'window' in 属性:
        return 属性['window']
    return 取握手窗口()


def 确保样式(文档):
    '把卡片样式模块插进文档'
    注入模块样式文件(
        文档,
        '操作卡片样式',
        os.path.join(os.path.dirname(__file__),'卡片.module.css'),
        样式模块,
    )


def 建(文档,标签名,类名):
    '造出带官方类名和样式模块标记的节点'
    return 模块节点(文档,标签名,样式模块,类名)


def 挂上(父,节点):
    '节点或带根的组件挂到父节点'
    if 节点 is None or 父 is None:
        return None
    if hasattr(节点,'tagName'):
        标样式模块(节点,样式模块)
        父.appendChild(节点)
        return 节点
    if hasattr(节点,'渲染'):
        画出=节点.渲染()
        if 画出 is not None and hasattr(画出,'tagName'):
            标样式模块(画出,样式模块)
            父.appendChild(画出)
        return 画出
    if isinstance(节点,(list,tuple)):
        for 项 in 节点:
            挂上(父,项)
    return None


def 换根(自身,新根):
    '已经在页面上就替换，否则只记下'
    旧=自身.根
    if 旧 is not None and 旧.parentNode is not None and 旧 is not 新根:
        旧.parentNode.replaceChild(新根,旧)
    自身.根=新根
    return 新根


def 取提案(视图,轮次号):
    '一轮最多一张。多张时取调用标识最小的'
    找到=None
    提案表={}
    if isinstance(视图,dict) and isinstance(视图.get('proposals'),dict):
        提案表=视图['proposals']
    for 提案 in 提案表.values():
        if not isinstance(提案,dict) or 提案.get('turn')!=轮次号:
            continue
        if 找到 is None or str(提案.get('callId'))<str(找到.get('callId')):
            找到=提案
    return 找到


def 取决定(视图,调用号):
    '这一调用已记录的决定。没有就是还没开始'
    if not isinstance(视图,dict) or not isinstance(视图.get('decisions'),dict):
        return None
    if 调用号 not in 视图['decisions']:
        return None
    return 视图['decisions'][调用号]


def 取正文(属性,动作):
    '选择器钩子优先。没有钩子就读注入的正文表'
    钩子=属性.get('useBodies')
    if callable(钩子):
        def 选择(表):
            '取出这一动作的正文'
            if 表 is None:
                return None
            return 表.get(动作)
        return 钩子(选择)
    钩子表=属性.get('hooks')
    if isinstance(钩子表,dict) and 钩子表.get('bodies') is not None:
        return 钩子表['bodies'].getSnapshot().get(动作)
    return None


def 回合可显示(轮次):
    '有结束，并且收尾数据里的 closing 不是空'
    if not isinstance(轮次,dict) or 轮次.get('end') is None:
        return False
    数据=轮次.get('data')
    if 数据 is None or not hasattr(数据,'get'):
        return False
    尾=数据.get('turn-tail')
    if not isinstance(尾,dict):
        return False
    return 尾.get('closing') is not None


class 折叠文本:
    '不量布局。宽字素按两个拉丁字母宽，大约两行后折叠'
    def __init__(自身,属性=None):
        '记下文本。展开状态留在这一份上'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.展开=False
        自身.根=None
        自身.标识=下一编号()
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换上新文本。展开状态保留'
        自身.属性=属性

    def 点切换(自身,事件=None):
        '展开或收起'
        自身.展开=not 自身.展开
        自身.渲染()

    def 渲染(自身):
        '画出段落。被截断时带切换按钮'
        属性=自身.属性
        窗口=窗口于(属性)
        文档=窗口.document
        确保样式(文档)
        文本='' if 属性.get('text') is None else str(属性['text'])
        省略=预览(文本)
        根=建(文档,'div',None)
        段落=建(文档,'p','text')
        段落.id=自身.标识
        if 自身.展开 or 省略 is None:
            段落.textContent=文本
        else:
            段落.textContent=省略
        根.appendChild(段落)
        if 省略 is not None:
            按钮节点=按钮({
                'window':窗口,
                'variant':'ghost',
                'size':'sm',
                'className':'toggle',
                'children':属性.get('collapseLabel') if 自身.展开 else 属性.get('expandLabel'),
                'onClick':自身.点切换,
            }).渲染()
            标样式模块(按钮节点,样式模块)
            按钮节点.setAttribute('aria-expanded','true' if 自身.展开 else 'false')
            按钮节点.setAttribute('aria-controls',自身.标识)
            根.appendChild(按钮节点)
        return 换根(自身,根)


class 兜底正文:
    '没有种类正文时，只留标题、说明和暂不需要'
    def __init__(自身,属性=None):
        '还没点过'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.待定=False
        自身.错误=None
        自身.根=None

    def 更新(自身,属性):
        '换份额'
        自身.属性=属性

    def 点忽略(自身,事件=None):
        '回复丢失或被拒绝时写出错误。丢失不等于失败'
        自身.待定=True
        自身.错误=None
        try:
            结果=自身.属性['act']('dismiss')
            if 结果 is None:
                自身.错误='transport'
            elif isinstance(结果,dict) and 结果.get('status') in ('refused','unconfirmed'):
                自身.错误='unavailable'
        except Exception as 丢失:
            丢失=None
            自身.错误='transport'
        自身.待定=False
        自身.渲染()

    def 渲染(自身):
        '画出摘要、已命名阶段和暂不需要'
        属性=自身.属性
        窗口=窗口于(属性)
        文档=窗口.document
        确保样式(文档)
        译=属性['t']
        决定=属性.get('decision')
        阶段=None
        if isinstance(决定,dict) and 决定.get('phase') in ('dismissed','replaced'):
            阶段=决定['phase']
        根=建(文档,'div','body')
        挂上(根,属性.get('summary'))
        if 阶段 is not None:
            状态=建(文档,'p','status')
            状态.setAttribute('role','status')
            状态.textContent=译(阶段)
            根.appendChild(状态)
        if 自身.错误 is not None:
            警报=建(文档,'p','status')
            警报.setAttribute('role','alert')
            警报.textContent=译(自身.错误)
            根.appendChild(警报)
        if 决定 is None:
            脚=建(文档,'footer','footer')
            按钮节点=按钮({
                'window':窗口,
                'variant':'ghost',
                'size':'sm',
                'disabled':自身.待定,
                'children':译('dismiss'),
                'onClick':自身.点忽略,
            }).渲染()
            标样式模块(按钮节点,样式模块)
            脚.appendChild(按钮节点)
            根.appendChild(脚)
        return 换根(自身,根)


class 操作卡片:
    '一张卡片的外框'
    def __init__(自身,属性=None):
        '记下份额'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.正文=None
        自身.正文动作=None
        自身.折叠=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换份额'
        自身.属性=属性

    def 渲染(自身):
        '有正文就交给它。没有就用兜底'
        属性=自身.属性
        窗口=窗口于(属性)
        文档=窗口.document
        确保样式(文档)
        提案=属性['proposal']
        译=属性['t']
        摘要标题=建(文档,'strong','title')
        摘要标题.textContent='' if 提案.get('title') is None else str(提案.get('title'))
        折叠份额={
            'window':窗口,
            'text':'' if 提案.get('brief') is None else str(提案.get('brief')),
            'expandLabel':译('expandBrief'),
            'collapseLabel':译('collapseBrief'),
        }
        if 自身.折叠 is None:
            自身.折叠=折叠文本(折叠份额)
        else:
            自身.折叠.更新(折叠份额)
            自身.折叠.渲染()
        摘要=[摘要标题,自身.折叠]
        正文记录=取正文(属性,提案.get('action'))
        份额={
            'proposal':提案,
            'decision':属性.get('decision'),
            'sessionId':属性.get('sessionId'),
            'summary':摘要,
            'Folded':折叠文本,
            'act':属性.get('act'),
            'window':窗口,
        }
        if 正文记录 is None:
            份额['t']=译
            if not isinstance(自身.正文,兜底正文):
                自身.正文=兜底正文(份额)
                自身.正文动作=None
            else:
                自身.正文.更新(份额)
            内容=自身.正文.渲染()
        else:
            种类译=属性['bind'](正文记录['locale'])
            份额['t']=种类译
            if 自身.正文动作!=提案.get('action') or 自身.正文 is None or isinstance(自身.正文,兜底正文):
                自身.正文=正文记录['render'](份额,种类译)
                自身.正文动作=提案.get('action')
            elif hasattr(自身.正文,'更新'):
                自身.正文.更新(份额)
            if hasattr(自身.正文,'渲染'):
                内容=自身.正文.渲染()
            else:
                内容=自身.正文
        根=建(文档,'section','card')
        根.setAttribute('aria-label','' if 提案.get('title') is None else str(提案.get('title')))
        根.setAttribute('data-action-card','' if 提案.get('callId') is None else str(提案.get('callId')))
        根.setAttribute('data-action','' if 提案.get('action') is None else str(提案.get('action')))
        挂上(根,内容)
        return 换根(自身,根)


class 操作卡片尾:
    '回合以最终回答结束后，把这一轮的卡片放在回答下面'
    def __init__(自身,属性=None):
        '记下回合份额'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.卡片=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换回合份额'
        自身.属性=属性

    def 渲染(自身):
        '回合还开着，或结束时没有回答，就不画'
        属性=自身.属性
        窗口=窗口于(属性)
        文档=窗口.document
        轮次=属性.get('turn')
        视图=None
        if callable(属性.get('useProjection')) and isinstance(轮次,dict):
            视图=属性['useProjection']('actionCards')
        提案=None
        if isinstance(轮次,dict):
            提案=取提案(视图,轮次.get('turn'))
        if 提案 is None or not 回合可显示(轮次):
            根=文档.createElement('span')
            根.setAttribute('hidden','')
            return 换根(自身,根)
        卡片属性=dict(属性)
        卡片属性['window']=窗口
        卡片属性['proposal']=提案
        卡片属性['decision']=取决定(视图,提案.get('callId'))
        if 自身.卡片 is None:
            自身.卡片=操作卡片(卡片属性)
        else:
            自身.卡片.更新(卡片属性)
        return 换根(自身,自身.卡片.渲染())
