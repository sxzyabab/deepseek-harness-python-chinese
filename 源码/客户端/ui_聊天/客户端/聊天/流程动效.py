from functools import cmp_to_key
from .可搜索隐藏 import 可搜索隐藏席

__all__=['动效开启','正在隐藏或收起','创建流程动效','用流隐藏','用动效隐藏']

淡出毫秒=70
关闭延迟毫秒=50
关闭毫秒=110
收尾余量毫秒=80
动效范围='[data-chat-motion]'
缓动='cubic-bezier(0.4, 0, 0.2, 1)'
文档位置在后=4


def 窗口(元素):
    '元素所在的浏览窗口'
    文档=getattr(元素,'ownerDocument',None)
    视图=getattr(文档,'defaultView',None) if 文档 is not None else None
    return 视图


def 匹配减少动效(元素):
    '用户要求减少动效'
    窗=窗口(元素)
    匹配=getattr(窗,'matchMedia',None) if 窗 is not None else None
    if not callable(匹配):
        return False
    return bool(匹配('(prefers-reduced-motion: reduce)').matches)


def 动效开启(元素):
    '在活动范围内，且没有减少动效，才做淡出再收起'
    if 元素.closest(动效范围) is None:
        return False
    return not 匹配减少动效(元素)


def 正在隐藏或收起(元素):
    '已经隐藏，或正在收起'
    return 元素.hasAttribute('hidden') or 元素.dataset.chatMotion=='collapse'


def 露出份额(盒子,进度):
    '展开盒从自己已经到达的高度继续'
    起点=0 if 盒子['height']==0 else 盒子['fromHeight']/盒子['height']
    return 起点+(1-起点)*进度


def 读上边距(元素):
    '计算后的上外边距'
    窗=窗口(元素)
    样式=窗.getComputedStyle(元素) if 窗 is not None else None
    文=样式.marginTop if 样式 is not None else '0'
    try:
        return float(文) if 文 not in (None,'') else 0
    except ValueError:
        return 0


def 创建流程动效(驱动,折叠变化):
    '一个视口一份帧时钟。收起和展开进同一批，用 requestAnimationFrame 改高度'
    运行中={}
    折叠数={'值':0}
    空闲监听=set()
    已排={'值':False}
    盒子={}
    帧号={'值':None}
    批次={'值':False}
    已取消={'值':False}
    清空代={'值':0}
    批次清理={'值':None}
    取消空批={'值':None}
    正在收尾={'值':False}
    锚已关={'值':False}

    def 是批成员(盒):
        '收起祖先里面的行跟着祖先走，不单独进批'
        父=盒['element'].parentElement
        if 父 is None:
            return True
        return 父.closest('[data-chat-motion="collapse"]') is None

    def 通知空闲():
        '折叠结束，恢复滚动锚定并叫醒等待者'
        if 锚已关['值']:
            锚已关['值']=False
            折叠变化(False)
        监听=list(空闲监听)
        空闲监听.clear()
        for 听 in 监听:
            听()

    def 折叠开始():
        '第一行开始折叠时关掉原生滚动锚定'
        折叠数['值']+=1
        if 折叠数['值']!=1 or 锚已关['值']:
            return
        锚已关['值']=True
        折叠变化(True)

    def 折叠结束():
        '最后一行折叠完才通知空闲'
        折叠数['值']=0 if 折叠数['值']<=1 else 折叠数['值']-1
        if 折叠数['值']==0 and not 正在收尾['值']:
            通知空闲()

    def 清动效(元素,结束回调,计时):
        '拆掉过渡和临时样式'
        元素.removeEventListener('transitionend',结束回调)
        窗=窗口(元素)
        if 计时 is not None and 窗 is not None:
            窗.clearTimeout(计时)
        if 元素 in 运行中:
            del 运行中[元素]
        if 元素 in 盒子:
            del 盒子[元素]
        样式=元素.style
        样式.height=''
        样式.marginTop=''
        样式.opacity=''
        样式.overflow=''
        样式.transition=''
        样式.translate=''
        if hasattr(元素.dataset,'chatMotion'):
            del 元素.dataset.chatMotion

    def 跑批(当前):
        '这一帧从各盒现在的高度继续。没有正在收起的盒就不跑'
        for 盒 in list(盒子.values()):
            if not 是批成员(盒):
                continue
            高=盒['element'].offsetHeight
            距=读上边距(盒['element'])
            if not 盒['closing']:
                盒['fromHeight']=高 if 高<盒['height'] else 盒['height']
                盒['fromMarginTop']=距 if 距<盒['marginTop'] else 盒['marginTop']
                continue
            盒['height']=高
            盒['marginTop']=距
            if 高==0 and 距==0:
                盒['finish']()
        拥有=list(盒子.values())
        成员=[盒 for 盒 in 拥有 if 是批成员(盒)]
        成员.sort(key=cmp_to_key(比文档序))
        有收起=False
        for 盒 in 成员:
            if 盒['closing']:
                有收起=True
                break
        if not 有收起:
            return
        批次['值']=True
        已取消['值']=False
        旅行输入=[]
        for 盒 in 成员:
            if 盒['closing']:
                旅行输入.append(盒)
            else:
                旅行输入.append({
                    'element':盒['element'],
                    'height':盒['height']-盒['fromHeight'],
                    'marginTop':盒['marginTop']-盒['fromMarginTop'],
                    'closing':False,
                })
        旅行=当前['begin'](旅行输入)
        批次清理['值']=lambda: 当前['finish'](True)
        for 盒 in 拥有:
            盒['take']()
        for 盒 in 成员:
            盒['element'].style.transition='none'
            盒['element'].style.height=str(盒['height'] if 盒['closing'] else 盒['fromHeight'])+'px'
            盒['element'].style.marginTop=str(盒['marginTop'] if 盒['closing'] else 盒['fromMarginTop'])+'px'
            盒['element'].style.opacity='1' if 盒['closing'] else str(露出份额(盒,0))
        成员集=set(id(盒) for 盒 in 成员)
        已定旅行=set()

        def 冻住旅行():
            '旅行中的盒子裁切内容，里面的收起行先保持尺寸'
            for 元素 in 旅行:
                if 元素 in 已定旅行:
                    continue
                已定旅行.add(元素)
                元素.style.translate=''
                for 盒 in 拥有:
                    if id(盒) in 成员集 or not 元素.contains(盒['element']):
                        continue
                    盒['element'].style.transition='none'
                    盒['element'].style.height=str(盒['height'])+'px'
                    盒['element'].style.marginTop=str(盒['marginTop'])+'px'
                    盒['element'].style.opacity='1'

        冻住旅行()
        减少=匹配减少动效(成员[0]['element']) if len(成员)>0 else False
        开始时间={'值':None}
        位移={'值':0}

        def 收尾(取消完):
            '这一批结束，交还各盒并在还有挂起盒时再排一批'
            批次['值']=False
            批次清理['值']=None
            取消空批['值']=None
            正在收尾['值']=True
            try:
                for 盒 in 拥有:
                    if 盒子.get(盒['element']) is 盒:
                        盒['finish']()
                当前['finish'](取消完)
            finally:
                正在收尾['值']=False
            if 折叠数['值']==0:
                通知空闲()
            还有=False
            for 盒 in 盒子.values():
                if 盒['held']:
                    还有=True
                    break
            if 还有:
                冲刷()

        def 取消空():
            '没有还在收起的成员就停掉这一帧'
            还在=False
            for 盒 in 成员:
                if 盒['closing'] and 盒子.get(盒['element']) is 盒:
                    还在=True
                    break
            if 还在:
                return
            窗=窗口(成员[0]['element']) if len(成员)>0 else None
            if 帧号['值'] is not None and 窗 is not None:
                窗.cancelAnimationFrame(帧号['值'])
            帧号['值']=None
            收尾(True)

        取消空批['值']=取消空

        def 帧(现在):
            '按平滑进度改高度、透明度和位移'
            帧号['值']=None
            if 开始时间['值'] is None:
                开始时间['值']=现在
            经过=关闭延迟毫秒+关闭毫秒 if 减少 else 现在-开始时间['值']
            线性=(经过-关闭延迟毫秒)/关闭毫秒
            if 线性<0:
                线性=0
            if 线性>1:
                线性=1
            进度=线性*线性*(3-2*线性)
            当前['prepare'](进度,已取消['值'])
            冻住旅行()
            for 盒 in 成员:
                if 盒子.get(盒['element']) is not 盒:
                    continue
                if 盒['closing']:
                    盒['element'].style.height=str(盒['height']*(1-进度))+'px'
                    盒['element'].style.marginTop=str(盒['marginTop']*(1-进度))+'px'
                    if 盒['element'] in 旅行:
                        盒['element'].style.opacity='1'
                    else:
                        淡出=1-经过/淡出毫秒
                        if 淡出<0:
                            淡出=0
                        盒['element'].style.opacity=str(淡出)
                else:
                    盒['element'].style.height=str(盒['fromHeight']+(盒['height']-盒['fromHeight'])*进度)+'px'
                    盒['element'].style.marginTop=str(盒['fromMarginTop']+(盒['marginTop']-盒['fromMarginTop'])*进度)+'px'
                    盒['element'].style.opacity=str(露出份额(盒,进度))
            位移['值']=当前['frame'](进度,已取消['值'])
            之前移除=0
            for 盒 in 成员:
                if 盒子.get(盒['element']) is not 盒:
                    continue
                if 盒['closing']:
                    if 盒['element'] not in 旅行:
                        盒['element'].style.translate='0 '+str(位移['值']+之前移除)+'px'
                    之前移除+=(盒['height']+盒['marginTop'])*进度
                else:
                    之前移除-=(盒['height']-盒['fromHeight']+盒['marginTop']-盒['fromMarginTop'])*进度
            if 线性<1:
                窗=窗口(成员[0]['element'])
                帧号['值']=窗.requestAnimationFrame(帧)
                return
            收尾(已取消['值'])

        if 减少:
            帧(0)
        else:
            窗=窗口(成员[0]['element'])
            帧号['值']=窗.requestAnimationFrame(帧)

    def 比文档序(左,右):
        '右节点跟在左节点后面时，左排在前面'
        位=左['element'].compareDocumentPosition(右['element'])
        if 位 & 文档位置在后:
            return -1
        return 1

    def 冲刷():
        '整次提交里的收起和展开都登记完，再开一批'
        已排['值']=False
        if 批次['值']:
            return
        有收起=False
        for 盒 in 盒子.values():
            if 盒['closing']:
                有收起=True
                break
        当前=驱动() if 有收起 else None
        if 当前 is not None:
            跑批(当前)
            return
        减少=False
        for 盒 in list(盒子.values()):
            减少=匹配减少动效(盒['element'])
            break
        for 盒 in list(盒子.values()):
            if 减少 or (盒['held'] and 盒['closing']):
                盒['finish']()
            elif 盒['held']:
                盒['release']()

    def 安排批次():
        '微任务里冲刷，赶在盒子改尺寸之前'
        if 已排['值']:
            return
        已排['值']=True
        代=清空代['值']

        def 稍后():
            '代次没变才冲刷'
            if 代==清空代['值']:
                冲刷()

        窗=None
        for 盒 in 盒子.values():
            窗=窗口(盒['element'])
            break
        if 窗 is not None and callable(getattr(窗,'queueMicrotask',None)):
            窗.queueMicrotask(稍后)
        else:
            稍后()

    def 取消动效(元素):
        '停掉这个元素自己的过渡'
        取消=运行中.get(元素)
        if 取消 is not None:
            取消()
        空=取消空批['值']
        if 空 is not None:
            空()

    def 收起(元素,完成):
        '淡出再把高度收到 0。批次进行中先按住，等下一次冲刷'
        取消动效(元素)
        高=元素.offsetHeight
        距=读上边距(元素)
        if 高==0 and 距==0:
            完成()
            return
        按住=批次['值']
        元素.dataset.chatMotion='collapse'
        折叠开始()
        安排批次()
        样式=元素.style
        样式.transition='none'
        样式.overflow='hidden'
        样式.height=str(高)+'px'
        样式.marginTop=str(距)+'px'
        计时={'值':None}

        def 结束事件(事件):
            '高度过渡结束才真正隐藏'
            if 事件.target is 元素 and 事件.propertyName=='height':
                收完()

        def 收完():
            '隐藏落地，再通知折叠结束'
            if 运行中.get(元素) is not 取消:
                return
            清动效(元素,结束事件,计时['值'])
            完成()
            折叠结束()

        def 取消():
            '中途取消，不提交隐藏'
            清动效(元素,结束事件,计时['值'])
            折叠结束()

        if not 按住:
            元素.offsetHeight
            样式.transition=(
                'opacity '+str(淡出毫秒)+'ms '+缓动+', '
                +'height '+str(关闭毫秒)+'ms '+缓动+' '+str(关闭延迟毫秒)+'ms, '
                +'margin-top '+str(关闭毫秒)+'ms '+缓动+' '+str(关闭延迟毫秒)+'ms'
            )
            样式.opacity='0'
            样式.height='0px'
            样式.marginTop='0px'
            窗=窗口(元素)
            计时['值']=窗.setTimeout(收完,关闭延迟毫秒+关闭毫秒+收尾余量毫秒)
            元素.addEventListener('transitionend',结束事件)
        运行中[元素]=取消
        盒子[元素]={
            'element':元素,
            'height':高,
            'marginTop':距,
            'fromHeight':高,
            'fromMarginTop':距,
            'closing':True,
            'held':按住,
            'finish':收完,
            'release':lambda: None,
            'take':lambda: 拿走(元素,结束事件,计时),
        }

    def 拿走(元素,结束事件,计时):
        '批次接手之前拆掉元素自己的过渡'
        元素.removeEventListener('transitionend',结束事件)
        窗=窗口(元素)
        if 计时['值'] is not None and 窗 is not None:
            窗.clearTimeout(计时['值'])

    def 展开(元素):
        '从 0 长到自然高度。批次进行中先按在 0，等下一次冲刷'
        取消动效(元素)
        高=元素.offsetHeight
        if 高==0:
            return
        距=读上边距(元素)
        安排批次()
        样式=元素.style
        元素.dataset.chatMotion='reveal'
        样式.transition='none'
        样式.overflow='hidden'
        样式.opacity='0'
        样式.height='0px'
        样式.marginTop='0px'
        计时={'值':None}

        def 结束事件(事件):
            '高度过渡结束就清掉临时样式'
            if 事件.target is 元素 and 事件.propertyName=='height':
                长完()

        def 长完():
            '展开完成'
            if 运行中.get(元素) is not 长完:
                return
            清动效(元素,结束事件,计时['值'])

        def 开始过渡():
            '自己的高度和透明度过渡'
            元素.offsetHeight
            样式.transition=(
                'height '+str(关闭毫秒)+'ms '+缓动+' '+str(关闭延迟毫秒)+'ms, '
                +'margin-top '+str(关闭毫秒)+'ms '+缓动+' '+str(关闭延迟毫秒)+'ms, '
                +'opacity '+str(关闭毫秒)+'ms '+缓动+' '+str(关闭延迟毫秒)+'ms'
            )
            样式.height=str(高)+'px'
            样式.marginTop=str(距)+'px'
            样式.opacity='1'
            窗=窗口(元素)
            计时['值']=窗.setTimeout(长完,关闭延迟毫秒+关闭毫秒+收尾余量毫秒)
            元素.addEventListener('transitionend',结束事件)

        按住=批次['值']
        if not 按住:
            开始过渡()
        运行中[元素]=长完

        def 放开():
            '批次结束后再开始自己的过渡'
            盒['held']=False
            开始过渡()

        盒={
            'element':元素,
            'height':高,
            'marginTop':距,
            'fromHeight':0,
            'fromMarginTop':0,
            'closing':False,
            'held':按住,
            'finish':长完,
            'release':放开,
            'take':lambda: 拿走(元素,结束事件,计时),
        }
        盒子[元素]=盒

    def 清空():
        '视口拆掉时停掉全部帧和过渡'
        清空代['值']+=1
        已排['值']=False
        批次['值']=False
        已取消['值']=False
        窗=None
        for 元素 in 运行中:
            窗=窗口(元素)
            break
        if 帧号['值'] is not None and 窗 is not None:
            窗.cancelAnimationFrame(帧号['值'])
        帧号['值']=None
        清理=批次清理['值']
        if 清理 is not None:
            清理()
        批次清理['值']=None
        取消空批['值']=None
        空闲监听.clear()
        for 取消 in list(运行中.values()):
            取消()

    def 折叠中():
        '还有行在折叠'
        return 折叠数['值']>0

    def 折叠空闲(监听):
        '已经空闲就立刻叫，否则等这一批结束'
        if 折叠数['值']==0:
            监听()
        else:
            空闲监听.add(监听)

        def 退订():
            '不再等'
            空闲监听.discard(监听)

        return 退订

    def 取消输入():
        '这一批被新的输入打断'
        if 批次['值']:
            已取消['值']=True

    def 恢复输入():
        '打断结束'
        if 批次['值']:
            已取消['值']=False

    def 输入活动():
        '正在跑批，或已经排了含收起行的批'
        if 批次['值']:
            return True
        if not 已排['值']:
            return False
        for 盒 in 盒子.values():
            if 盒['closing'] and 是批成员(盒):
                return True
        return False

    return {
        'collapse':收起,
        'reveal':展开,
        'cancelMotion':取消动效,
        'foldActive':折叠中,
        'onFoldIdle':折叠空闲,
        'cancelInput':取消输入,
        'resumeInput':恢复输入,
        'clear':清空,
        'inputActive':输入活动,
    }


class 流过渡:
    '同一个元素第二次才做动画。第一次挂上只提交可见性'
    def __init__(自身,动效,生长):
        '记下视口动效和展开时要不要长高'
        自身.动效=动效
        自身.生长=生长
        自身.当前=None

    def 取消(自身):
        '元素换掉或拆掉时取消'
        if 自身.当前 is not None and 自身.动效 is not None:
            自身.动效['cancelMotion'](自身.当前)
        自身.当前=None

    def __call__(自身,元素,隐藏,提交):
        '隐藏走收起，显示先提交再按需要展开'
        已挂=自身.当前 is 元素
        动画=已挂 and 动效开启(元素)
        自身.当前=元素
        if 隐藏:
            if 正在隐藏或收起(元素):
                return
            if 已挂 and 元素.closest(动效范围) is not None and 自身.动效 is not None:
                自身.动效['collapse'](元素,提交)
            else:
                提交()
            return
        if 自身.动效 is not None:
            自身.动效['cancelMotion'](元素)
        曾隐藏=元素.hasAttribute('hidden')
        提交()
        if 曾隐藏 and 动画 and 自身.生长 and 自身.动效 is not None:
            自身.动效['reveal'](元素)


def 用流隐藏(隐藏,揭示,动效):
    '可搜索隐藏。有视口动效时收起走帧时钟，不长高'
    过渡=None if 动效 is None else 流过渡(动效,False)
    return 可搜索隐藏席(隐藏,揭示,过渡)


def 用动效隐藏(引用,隐藏,动效):
    '组头的 hidden 跟折叠时钟走，新露出的头会长高'
    元素=引用.current if hasattr(引用,'current') else 引用
    if 元素 is None:
        return
    if not hasattr(引用,'流过渡'):
        引用.流过渡=流过渡(动效,True)
    引用.流过渡(元素,隐藏,lambda: 提交隐藏(元素,隐藏))


def 提交隐藏(元素,隐藏):
    '组头最终的 hidden 属性'
    if 隐藏:
        元素.setAttribute('hidden','')
    else:
        元素.removeAttribute('hidden')
