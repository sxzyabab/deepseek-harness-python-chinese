from ....ui_基础界面组件.icons import 图标,图标数据16
from ....ui_对话.异常 import 标样式模块
from .令牌格式 import 格式化令牌,格式化精确令牌,格式化缓存命中百分比
from .消息铬 import 格式化每秒令牌
from .统计对话框 import 统计对话框席
from .用披露 import 注入聊天样式
from ..约定.回合指标 import 助手步骤读数

__all__=['派生统计','格式化时长','缓存命中百分','计费输入令牌','活动胶囊','用量胶囊']

样式模块='stats-pills'
对话框模块='stat-dialog'


def 派生统计(节点列表):
    '没有 sessionStats 投影时，按当前窗口里的助手和工具结果合计'
    回合集=set()
    步数=0
    模型毫秒=0
    工具毫秒=0
    首令牌毫秒=0
    首令牌步=0
    解码毫秒=0
    解码令牌=0
    for 节点 in 节点列表 or []:
        if not isinstance(节点,dict):
            continue
        if 节点.get('kind')=='tool-result':
            if 节点.get('callTime') is not None:
                工具毫秒+=max(0,(节点.get('time') or 0)-节点['callTime'])
            continue
        if 节点.get('kind')!='assistant':
            continue
        回合集.add(节点.get('turn'))
        步数+=1
        计时=节点.get('timing')
        if isinstance(计时,dict) and 计时.get('stepStartTime') is not None:
            模型毫秒+=max(0,(计时.get('completedTime') or 0)-计时['stepStartTime'])
        读数=助手步骤读数(节点)
        if 读数.get('ttftMs') is not None:
            首令牌毫秒+=读数['ttftMs']
            首令牌步+=1
        if 读数.get('decodeMs') is not None and 读数.get('outputTokens') is not None:
            解码毫秒+=读数['decodeMs']
            解码令牌+=读数['outputTokens']
    return {
        'turns':len(回合集),'steps':步数,'llmMs':模型毫秒,'toolMs':工具毫秒,
        'ttftMs':首令牌毫秒,'ttftSteps':首令牌步,'decodeMs':解码毫秒,'decodeTokens':解码令牌,
    }


def 格式化时长(毫秒,翻译):
    '不足一分钟带一位小数的秒，之后是分和秒'
    秒=毫秒/1000
    if 秒<60:
        return 翻译('duration.compactSeconds',{'seconds':round(秒*10)/10})
    整=round(秒)
    return 翻译('duration.compactMinutes',{'minutes':整//60,'seconds':整%60})


def 计费输入令牌(用量):
    '未缓存、缓存读、缓存写三份互斥的提示侧计费'
    return 用量['uncachedInputTokens']+用量['cacheReadTokens']+用量['cacheWriteTokens']


def 缓存命中百分(用量):
    '整份日志的缓存命中。没有计费输入时没有百分比'
    return 格式化缓存命中百分比(用量['cacheReadTokens'],计费输入令牌(用量))


def 取遗留节点(快照):
    '窗口折叠用的 legacy.nodes'
    if not isinstance(快照,dict):
        return []
    遗留=快照.get('legacy')
    if not isinstance(遗留,dict) or not isinstance(遗留.get('nodes'),list):
        return []
    return 遗留['nodes']


def 会话统计(用聊天,用投影):
    '投影优先。没有投影才折当前窗口'
    投影=用投影('sessionStats') if callable(用投影) else None
    if 投影 is not None:
        return 投影
    节点=用聊天(取遗留节点) if callable(用聊天) else []
    return 派生统计(节点)


def 解码速度(统计,翻译):
    '按有输出令牌的解码墙钟算每秒令牌'
    速率=格式化每秒令牌(统计['decodeTokens']/(统计['decodeMs']/1000))
    return 翻译('message.tokensPerSecond',{'tps':速率})


def 精确计数(值,翻译):
    '精确分组再套计数文案'
    return 翻译('message.turnUsage.count',{'count':格式化精确令牌(值,翻译)})


def 恒等(键,参数=None):
    '没有文案表时返回键'
    return 键


def 准备样式(文档):
    '胶囊和共用对话框'
    注入聊天样式(文档,样式模块,'统计行.module.css')
    注入聊天样式(文档,对话框模块,'统计对话框.module.css')


def 拼标签(文档,第一,第二):
    '两项之间放一个不进无障碍名的间隔点'
    盒=文档.createElement('span')
    盒.appendChild(文档.createTextNode(第一))
    if 第二 is not None:
        点=文档.createElement('span')
        点.className='sep'
        标样式模块(点,样式模块)
        点.setAttribute('aria-hidden','true')
        点.textContent='·'
        盒.appendChild(点)
        盒.appendChild(文档.createTextNode(第二))
    return 盒


def 平胶囊(文档,窗口,种类,图标节点,标签):
    '没有对话框时的静态读数'
    锚=文档.createElement('span')
    锚.className='anchor'
    标样式模块(锚,样式模块)
    锚.setAttribute('data-composer-stat',种类)
    丸=文档.createElement('span')
    丸.className='pill'
    标样式模块(丸,样式模块)
    if 图标节点 is not None:
        丸.appendChild(图标节点)
    文=文档.createElement('span')
    文.className='label'
    标样式模块(文,样式模块)
    if hasattr(标签,'tagName'):
        文.appendChild(标签)
    else:
        文.textContent=str(标签)
    丸.appendChild(文)
    锚.appendChild(丸)
    return 锚


class 对话胶囊:
    '点开自己的对话框。Esc 和外部点击由统计对话框席关掉'
    def __init__(自身):
        '每个胶囊一份开关'
        自身.席=统计对话框席()
        自身.根=None
        自身.面板=None

    def 放下(自身):
        '改成静态胶囊时关掉还开着的面板'
        自身.席.打开=False
        if 自身.面板 is not None and 自身.面板.parentNode is not None:
            自身.面板.remove()
        自身.面板=None

    def 画(自身,文档,窗口,种类,图标节点,标签,无障碍名,标题,标题值,行表):
        '锚上是按钮。打开时把面板挂到 body'
        if 自身.根 is not None:
            自身.根.remove()
        if 自身.面板 is not None and 自身.面板.parentNode is not None:
            自身.面板.remove()
            自身.面板=None
        锚=文档.createElement('span')
        锚.className='anchor'
        标样式模块(锚,样式模块)
        锚.setAttribute('data-composer-stat',种类)
        钮=文档.createElement('button')
        钮.type='button'
        钮.className='pill'
        标样式模块(钮,样式模块)
        钮.setAttribute('aria-haspopup','dialog')
        钮.setAttribute('aria-expanded','true' if 自身.席.打开 else 'false')
        钮.setAttribute('aria-label',无障碍名)
        if 图标节点 is not None:
            钮.appendChild(图标节点)
        文=文档.createElement('span')
        文.className='label'
        标样式模块(文,样式模块)
        if hasattr(标签,'tagName'):
            文.appendChild(标签)
        else:
            文.textContent=str(标签)
        钮.appendChild(文)

        def 切换(事件=None):
            '开关这一份对话框'
            自身.席.设打开(not 自身.席.打开)
            自身.变化()

        钮.addEventListener('click',切换)
        锚.appendChild(钮)
        自身.根=锚
        自身.席.根=锚
        自身.席.变化=自身.变化
        if 自身.席.打开:
            面板=文档.createElement('div')
            面板.className='panel'
            标样式模块(面板,对话框模块)
            面板.setAttribute('role','dialog')
            面板.setAttribute('aria-label',标题)
            题=文档.createElement('div')
            题.className='title'
            标样式模块(题,对话框模块)
            题标=文档.createElement('span')
            题标.className='titleLabel'
            标样式模块(题标,对话框模块)
            题图=图标数据16({'window':窗口}) if 种类=='usage' else 图标('enhance-16',{'window':窗口})
            if 题图 is not None:
                题标.appendChild(题图)
            题标.appendChild(文档.createTextNode(标题))
            题.appendChild(题标)
            if 标题值 is not None:
                题值=文档.createElement('span')
                题值.className='titleValue'
                标样式模块(题值,对话框模块)
                题值.textContent=标题值
                题.appendChild(题值)
            面板.appendChild(题)
            线=文档.createElement('div')
            线.className='titleRule'
            标样式模块(线,对话框模块)
            线.setAttribute('aria-hidden','true')
            面板.appendChild(线)
            表=文档.createElement('dl')
            表.className='details'
            标样式模块(表,对话框模块)
            表.setAttribute('data-session-stats-details' if 种类=='activity' else 'data-session-stats-usage','')
            for 名,值 in 行表:
                名节=文档.createElement('dt')
                名节.textContent=名
                值节=文档.createElement('dd')
                值节.textContent=值
                表.appendChild(名节)
                表.appendChild(值节)
            面板.appendChild(表)
            文档.body.appendChild(面板)
            自身.面板=面板
            自身.席.面板=面板
            自身.席.监听(文档)
            自身.席.放置()
            自身.席.套样式(面板)
        return 锚


class 活动胶囊:
    '轮次、步数和整段会话的输出速度。简洁档只留速度'
    def __init__(自身,属性=None):
        '记下钩子'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.对话=对话胶囊()
        自身.对话.变化=自身.渲染
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 收起(自身):
        '这一档没有可读数字'
        if 自身.根 is not None and 自身.根.parentNode is not None:
            自身.根.remove()
        自身.根=None
        if 自身.对话.面板 is not None and 自身.对话.面板.parentNode is not None:
            自身.对话.面板.remove()
        自身.对话.面板=None
        return None

    def 渲染(自身):
        '没有计时行时保持静态胶囊，不打开空对话框'
        属性=自身.属性
        if 'window' not in 属性:
            return 自身.根
        窗口=属性['window']
        文档=窗口.document
        准备样式(文档)
        翻译=属性.get('t') if callable(属性.get('t')) else 恒等
        用量钩=属性.get('usePerformanceUsage')

        def 原样(值):
            '用量档原样返回'
            return 值

        模式=用量钩(原样) if callable(用量钩) else 'detailed'
        统计=会话统计(属性.get('useChat'),属性.get('useProjection'))
        if not isinstance(统计,dict):
            统计=派生统计([])
        速度=解码速度(统计,翻译) if (统计.get('decodeMs') or 0)>0 else None
        图=图标('enhance-16',{'window':窗口})
        if 模式=='compact':
            if 速度 is None:
                return 自身.收起()
            自身.对话.放下()
            根=平胶囊(文档,窗口,'activity',图,速度)
        elif (统计.get('steps') or 0)==0:
            return 自身.收起()
        else:
            计数=翻译('stats.counts',{'turns':统计.get('turns') or 0,'steps':统计.get('steps') or 0})
            标签=拼标签(文档,计数,速度)
            无行=(统计.get('llmMs') or 0)<=0 and (统计.get('toolMs') or 0)<=0 and (统计.get('ttftSteps') or 0)<=0 and 速度 is None
            if 无行:
                自身.对话.放下()
                根=平胶囊(文档,窗口,'activity',图,标签)
            else:
                行表=[]
                if (统计.get('llmMs') or 0)>0:
                    行表.append((翻译('stats.dialog.llmTime'),格式化时长(统计['llmMs'],翻译)))
                if (统计.get('toolMs') or 0)>0:
                    行表.append((翻译('stats.dialog.toolTime'),格式化时长(统计['toolMs'],翻译)))
                if (统计.get('ttftSteps') or 0)>0:
                    行表.append((翻译('stats.dialog.ttft'),格式化时长(统计['ttftMs']/统计['ttftSteps'],翻译)))
                if 速度 is not None:
                    行表.append((翻译('stats.dialog.speed'),速度))
                无障碍名=计数 if 速度 is None else 计数+' · '+速度
                根=自身.对话.画(文档,窗口,'activity',图,标签,无障碍名,翻译('stats.dialog.title'),None,行表)
        自身.根=根
        if 属性.get('parent') is not None and 根.parentNode is None:
            属性['parent'].appendChild(根)
        return 根


class 用量胶囊:
    '整份日志的令牌总量和缓存命中。简洁档只留命中率'
    def __init__(自身,属性=None):
        '记下钩子'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.对话=对话胶囊()
        自身.对话.变化=自身.渲染
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 收起(自身):
        '没有计费活动'
        if 自身.根 is not None and 自身.根.parentNode is not None:
            自身.根.remove()
        自身.根=None
        if 自身.对话.面板 is not None and 自身.对话.面板.parentNode is not None:
            自身.对话.面板.remove()
        自身.对话.面板=None
        return None

    def 渲染(自身):
        '输入和输出都是 0 时不显示'
        属性=自身.属性
        if 'window' not in 属性:
            return 自身.根
        窗口=属性['window']
        文档=窗口.document
        准备样式(文档)
        翻译=属性.get('t') if callable(属性.get('t')) else 恒等
        用量钩=属性.get('usePerformanceUsage')

        def 原样(值):
            '用量档原样返回'
            return 值

        模式=用量钩(原样) if callable(用量钩) else 'detailed'
        投影=属性.get('useProjection')
        用量=投影('tokenUsage') if callable(投影) else None
        if not isinstance(用量,dict) or (计费输入令牌(用量)==0 and 用量.get('outputTokens')==0):
            return 自身.收起()
        命中=缓存命中百分(用量)
        命中文=None if 命中 is None else 翻译('stats.cacheHit',{'percent':命中})
        图=图标数据16({'window':窗口})
        if 模式=='compact':
            if 命中文 is None:
                return 自身.收起()
            自身.对话.放下()
            根=平胶囊(文档,窗口,'usage',图,命中文)
        else:
            总计=计费输入令牌(用量)+用量['outputTokens']
            总数=翻译('message.turnUsage.count',{'count':格式化令牌(总计,翻译)})
            标签=拼标签(文档,总数,命中文)
            行表=[]
            if 命中 is not None:
                行表.append((翻译('message.turnUsage.cacheHit'),命中+'%'))
            行表.append((翻译('message.turnUsage.input'),精确计数(用量['uncachedInputTokens'],翻译)))
            行表.append((翻译('message.turnUsage.cacheRead'),精确计数(用量['cacheReadTokens'],翻译)))
            if 用量.get('cacheWriteTokens')!=0:
                行表.append((翻译('message.turnUsage.cacheWrite'),精确计数(用量['cacheWriteTokens'],翻译)))
            行表.append((翻译('message.turnUsage.output'),精确计数(用量['outputTokens'],翻译)))
            无障碍名=总数 if 命中文 is None else 总数+' · '+命中文
            根=自身.对话.画(文档,窗口,'usage',图,标签,无障碍名,翻译('stats.dialog.usageTitle'),精确计数(总计,翻译),行表)
        自身.根=根
        if 属性.get('parent') is not None and 根.parentNode is None:
            属性['parent'].appendChild(根)
        return 根
