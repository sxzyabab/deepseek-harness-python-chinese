from .流程动效 import 创建流程动效
from .用滚动跟随 import 滚动度量,按元素取跟随

__all__=['聊天视口']

阅读意图=('wheel','touchstart','pointerdown','keydown','beforematch')
滚动键={'ArrowUp','ArrowDown','PageUp','PageDown','Home','End',' '}


def 列出(集合):
    '节点列表或 NodeList 都收成普通列表'
    if 集合 is None:
        return []
    if isinstance(集合,list):
        return 集合
    长度=getattr(集合,'length',None)
    if isinstance(长度,int):
        出=[]
        下标=0
        while 下标<长度:
            出.append(集合.item(下标))
            下标+=1
        return 出
    try:
        return list(集合)
    except TypeError:
        return []


def 安全整数(值):
    '能当回合号的整数'
    if isinstance(值,bool) or not isinstance(值,int):
        return False
    return abs(值)<=9007199254740991


class 聊天视口:
    '一份聊天滚动口的几何、监听和折叠时钟'
    def __init__(自身):
        '还没挂上滚动口'
        自身.元素=None
        自身.观察=None
        自身.事件=None
        自身.回合表=[]
        自身.观测={'top':0,'landing':None}
        自身.分页=None
        自身.读者=None
        自身.要贴底=False
        自身.改目标=None
        自身.动效=创建流程动效(自身.折叠驱动,自身.折叠变化)

    def 折叠变化(自身,活动):
        '折叠时关掉滚动锚定'
        if 自身.元素 is not None:
            自身.元素['scroller'].style.overflowAnchor='none' if 活动 else ''

    def 挂上(自身,列表,列):
        '绑到外层会话滚动口，没有就用自己'
        自身.拆下()
        滚动口=列表.closest('[data-conversation-scroll]')
        if 滚动口 is None:
            滚动口=列表
        撰写=滚动口.querySelector('[data-composer-seat]')
        垫=列表.querySelector('[data-chat-turn-spacer]')
        元素={'list':列表,'column':列,'scroller':滚动口,'composer':撰写,'spacer':垫}
        自身.元素=元素
        if 垫 is not None:
            垫.style.height=''
        滚动口.addEventListener('scroll',自身.当滚动,{'passive':True})
        滚动口.addEventListener('scrollend',自身.当滚动结束,{'passive':True,'capture':True})
        for 种类 in 阅读意图:
            滚动口.addEventListener(种类,自身.当意图,{'passive':True,'capture':True})
        窗=滚动口.ownerDocument.defaultView if 滚动口.ownerDocument is not None else None
        if 窗 is not None and hasattr(窗,'ResizeObserver'):
            def 尺寸(条目=None):
                '列或滚动口变了就收回垫高并作废落点'
                if 自身.元素 is not 元素:
                    return
                自身.收回下方()
                自身.作废()
                if 自身.事件 is not None:
                    自身.事件['resize']()
            自身.观察=窗.ResizeObserver(尺寸)
            自身.观察.observe(列)
            自身.观察.observe(滚动口)
            if 撰写 is not None:
                自身.观察.observe(撰写)

    def 拆下(自身):
        '卸监听并清掉折叠'
        自身.停止保留()
        自身.动效['clear']()
        if 自身.元素 is not None:
            滚动口=自身.元素['scroller']
            滚动口.style.overflowAnchor=''
            滚动口.removeEventListener('scroll',自身.当滚动)
            滚动口.removeEventListener('scrollend',自身.当滚动结束,True)
            for 种类 in 阅读意图:
                滚动口.removeEventListener(种类,自身.当意图,True)
        if 自身.观察 is not None:
            自身.观察.disconnect()
        自身.观察=None
        自身.元素=None
        自身.事件=None
        自身.要贴底=False
        自身.改目标=None
        自身.回合表=[]
        自身.观测={'top':0,'landing':None}

    def 连接(自身,事件):
        '业务策略接上。拆的时候只摘这一份'
        自身.事件=事件

        def 断开():
            '只摘当前这一份'
            if 自身.事件 is 事件:
                自身.事件=None

        return 断开

    def 更新回合(自身,回合表):
        '换成已提交的回合锚'
        自身.回合表=list(回合表 or [])

    def 最新回合(自身):
        '已加载窗口的最后一回合'
        if len(自身.回合表)==0:
            return None
        return 自身.回合表[-1].get('turn')

    def 作废(自身):
        '几何变了，落点知识作废，滚动归因还留着'
        自身.观测['landing']=None

    def 垫高(自身):
        '折叠预留的高度'
        垫=None if 自身.元素 is None else 自身.元素.get('spacer')
        if 垫 is None:
            return 0
        try:
            return float(垫.style.height or 0)
        except ValueError:
            return 0

    def 设垫(自身,高度):
        '没有缺口就清空'
        垫=None if 自身.元素 is None else 自身.元素.get('spacer')
        if 垫 is None:
            return
        下一='' if 高度<=0 else str(int(高度+0.999))+'px'
        if 垫.style.height!=下一:
            垫.style.height=下一

    def 绑读者(自身,读者):
        '折叠批次要问跟随意图'
        自身.读者=读者

        def 断开():
            '只摘这一份读者'
            if 自身.读者 is 读者:
                自身.读者=None

        return 断开

    def 跟随输入折叠(自身,跟随):
        '有折叠批次时，贴底请求交给这一批，不再另开滚动'
        if 自身.元素 is None or 自身.读者 is None or not 自身.动效['inputActive']():
            return False
        自身.打断跟随(跟随)
        自身.要贴底=True
        if callable(自身.改目标):
            自身.改目标()
        return True

    def 折叠驱动(自身):
        '一批折叠和滚动口共用一个进度。没挂上或没有阅读策略就不用帧时钟'
        元素=自身.元素
        读者=自身.读者
        if 元素 is None or 读者 is None:
            return None
        跟随=读者['follow']
        态={'贴底':False,'起点':0,'基准':0,'目标':0,'移除':0,'生长':0,'初高':0,'终房':0,'前列高':0,'前进度':0,'段进度':0,'段顶':0,'已写':0}
        收起盒=[]
        旅行=set()
        参照={'值':None,'顶':0,'口顶':0}

        def 屏顶(节点):
            '相对滚动口顶部'
            return 节点.getBoundingClientRect().top-参照['口顶']

        def 瞄准():
            '贴底落到地板，否则停在读者内容还在的位置'
            终高=态['初高']-态['移除']+态['生长']
            高=元素['scroller'].clientHeight or 0
            if 态['贴底']:
                态['目标']=max(态['基准'],终高-高,0)
            else:
                态['目标']=态['基准']
            态['终房']=0 if 态['目标']==0 else max(0,态['目标']+高-终高)

        def 重开段():
            '进度从现在重新算'
            态['段顶']=元素['scroller'].scrollTop or 0
            态['段进度']=态['前进度']

        def 自动(已取消):
            '贴底被阅读手势取消后不再代滚'
            return not (已取消 and 态['贴底'])

        def 位置(进度,已取消):
            '这一段里从段顶插到目标'
            if not 自动(已取消):
                return 元素['scroller'].scrollTop or 0
            if 态['段进度']==1:
                剩余=1
            else:
                剩余=(进度-态['段进度'])/(1-态['段进度'])
            return 态['段顶']+(态['目标']-态['段顶'])*剩余

        def 房间(顶,进度,已取消):
            '落地还缺的高度'
            自动房=态['终房'] if 自动(已取消) else 0
            return max(自动房,顶+(元素['scroller'].clientHeight or 0)-(态['初高']+(态['生长']-态['移除'])*进度))

        def 开始(盒子表):
            '量折叠前的几何，并决定这一批落在尾还是停住读者'
            态['贴底']=自身.要贴底 or (跟随.活动() and not 读者['pending']())
            自身.要贴底=False
            参照['口顶']=元素['scroller'].getBoundingClientRect().top
            态['起点']=元素['scroller'].scrollTop or 0
            原房=自身.垫高()
            态['初高']=max(元素['column'].offsetHeight or 0,(元素['scroller'].scrollHeight or 0)-原房)
            上方=0
            下方=[]
            for 盒 in 盒子表:
                量=盒['height']+盒['marginTop']
                顶=盒['element'].getBoundingClientRect().top-盒['marginTop']
                if 盒['closing']:
                    态['移除']+=量
                    上方+=max(0,min(量,参照['口顶']-顶))
                    if 顶>=参照['口顶']:
                        下方.append(盒['element'])
                    收起盒.append(盒)
                else:
                    态['生长']+=量
                    if 顶<参照['口顶']:
                        上方-=量
            if not 态['贴底']:
                参照['值']=自身.阅读参照()
            参照前=0 if 参照['值'] is None else 屏顶(参照['值'])
            元素['column'].setAttribute('data-input-fold','')
            if 参照['值'] is not None:
                参照['顶']=屏顶(参照['值'])
                上方-=参照['顶']-参照前
            态['基准']=max(0,态['起点']-上方)
            态['段顶']=态['起点']
            态['已写']=态['起点']
            态['前列高']=元素['column'].offsetHeight or 0
            瞄准()
            自身.设垫(max(原房,态['终房'],态['移除']))
            if 态['贴底']:
                跟随.设跟随(True)

            def 改去贴底():
                '更新的贴底请求接管这一批'
                态['贴底']=True
                跟随.设跟随(True)
                自身.动效['resumeInput']()
                瞄准()
                重开段()
                if 态['目标']<=态['段顶']:
                    return
                for 盒 in 收起盒:
                    移文=盒['element'].style.translate or ''
                    段位=移文.split(' ')
                    移=0
                    if len(段位)>1:
                        try:
                            移=float(段位[1])
                        except ValueError:
                            移=0
                    if 盒['element'].getBoundingClientRect().top-移-盒['marginTop']>=参照['口顶']:
                        旅行.add(盒['element'])

            自身.改目标=改去贴底
            if 态['贴底'] and 态['目标']>态['起点']:
                for 节点 in 下方:
                    旅行.add(节点)
            return 旅行

        def 准备(进度,已取消):
            '写高度前先留出滚动范围'
            if 自身.元素 is not 元素:
                return
            if not 态['贴底']:
                漂=(元素['scroller'].scrollTop or 0)-态['已写']
                if abs(漂)>0.5:
                    态['基准']=max(0,态['基准']+漂)
                    态['段顶']+=漂
                    参照['顶']-=漂
                    瞄准()
            增加=(元素['column'].offsetHeight or 0)-态['前列高']
            if 增加!=0:
                态['初高']+=增加
                瞄准()
                重开段()
            顶=位置(进度,已取消)
            自身.设垫(max(自身.垫高(),房间(顶,进度,已取消)))

        def 帧(进度,已取消):
            '盒子写完后再写滚动位置'
            if 自身.元素 is not 元素:
                return 0
            顶=位置(进度,已取消)
            元素['scroller'].scrollTop=顶
            自身.设垫(房间(顶,进度,已取消))
            态['已写']=元素['scroller'].scrollTop or 0
            if 参照['值'] is not None and 进度==1:
                参照['顶']=屏顶(参照['值'])
            if 自动(已取消):
                自身.观测={'top':态['已写'],'landing':None}
            态['前列高']=元素['column'].offsetHeight or 0
            态['前进度']=进度
            return 态['已写']-态['起点']

        def 结束(已取消):
            '最后一帧提交真实间距和落点'
            自身.改目标=None
            自身.要贴底=False
            if 自身.元素 is not 元素:
                return
            元素['column'].offsetHeight
            元素['column'].removeAttribute('data-input-fold')
            if not 态['贴底'] or 已取消:
                if not 态['贴底'] and 参照['值'] is not None and getattr(参照['值'],'isConnected',False) and 参照['值'].closest('[hidden]') is None:
                    移=屏顶(参照['值'])-参照['顶']
                    if abs(移)>0.5:
                        顶=(元素['scroller'].scrollTop or 0)+移
                        内容=(元素['scroller'].scrollHeight or 0)-自身.垫高()
                        自身.设垫(max(自身.垫高(),顶+(元素['scroller'].clientHeight or 0)-内容))
                        元素['scroller'].scrollTop=顶
                度量=滚动度量(元素['scroller'])
                高度=(元素['scroller'].scrollHeight or 0)-自身.垫高()
                自身.设垫(0 if 度量['top']==0 else max(0,度量['top']+度量['height']-高度))
                if 态['贴底']:
                    自身.作废()
                else:
                    自身.观测={'top':元素['scroller'].scrollTop or 0,'landing':None}
                return
            内容=(元素['scroller'].scrollHeight or 0)-自身.垫高()
            客户高=元素['scroller'].clientHeight or 0
            顶=max(态['目标'],内容-客户高,0)
            自身.设垫(0 if 顶==0 else max(0,顶+客户高-内容))
            元素['scroller'].scrollTop=顶
            度量=滚动度量(元素['scroller'])
            落地={'metrics':度量,'position':None,'turn':自身.最新回合()}
            自身.观测={'top':度量['top'],'landing':落地}
            读者['landedAtTail'](落地)

        return {'begin':开始,'prepare':准备,'frame':帧,'finish':结束}

    def 顶层行(自身):
        'display:contents 的槽不占盒子，量它的子节点'
        列=自身.元素['column']
        槽=列.querySelector(':scope > [data-slot="conversation.chat.flow"]')
        if 槽 is None:
            槽=列
        return 列出(槽.children)

    def 阅读参照(自身):
        '滚动口顶上第一行不在这一批里的行'
        if 自身.元素 is None:
            return None
        口=自身.元素['scroller'].getBoundingClientRect()
        行表=自身.顶层行()
        低=0
        高=len(行表)
        while 低<高:
            中=(低+高)//2
            if 行表[中].getBoundingClientRect().bottom>口.top:
                高=中
            else:
                低=中+1
        下标=低
        while 下标<len(行表):
            行=行表[下标]
            if 行.hasAttribute('hidden'):
                下标+=1
                continue
            矩形=行.getBoundingClientRect()
            if 矩形.top>=口.bottom:
                return None
            if 矩形.height==0 or 矩形.bottom<=口.top:
                下标+=1
                continue
            if 行.hasAttribute('data-chat-motion') or 行.querySelector('[data-chat-motion]') is not None:
                下标+=1
                continue
            return 行
        return None

    def 重置下方(自身):
        '显示模式变了，允许滚动范围缩回去'
        自身.设垫(0)
        自身.作废()

    def 收回下方(自身):
        '读者已经承认的滚动或内容长高之后，把用不到的垫还回去'
        if 自身.元素 is None or 自身.元素.get('spacer') is None:
            return
        当前=自身.垫高()
        if 当前==0 or 自身.动效['foldActive']():
            return
        滚动=自身.读滚动()
        if 滚动 is None or 滚动['movedByReader']:
            return
        无垫地板=滚动['metrics']['floor']-当前
        自身.设垫(min(当前,max(0,滚动['metrics']['top']-无垫地板)))

    def 打断跟随(自身,跟随):
        '阅读手势前停在当前位置'
        if not 跟随.动画中():
            return
        度量=自身.度量()
        if 度量 is None or 自身.元素 is None:
            return
        跟随.打断(自身.元素['scroller'],度量)
        自身.观测={'top':度量['top'],'landing':None}

    def 承认(自身,度量):
        '读者位置成为下一次归因的基线'
        自身.观测={'top':度量['top'],'landing':None}
        自身.收回下方()

    def 度量(自身):
        '当前滚动几何'
        if 自身.元素 is None:
            return None
        return 滚动度量(自身.元素['scroller'])

    def 读滚动(自身):
        '和上次承认的位置比，看是不是读者挪的'
        度量=自身.度量()
        if 度量 is None:
            return None
        return {'metrics':度量,'movedByReader':abs(度量['top']-min(自身.观测['top'],度量['floor']))>0.5}

    def 锚(自身,键,身份='position'):
        '阅读锚对上 data-chat-anchor-key。回合导航对上节点键'
        if 自身.元素 is None:
            return None
        节点部分=None
        for 行 in 列出(自身.元素['list'].querySelectorAll('[data-chat-anchor-key]')):
            if 行.closest('[hidden]') is not None and not 行.hasAttribute('hidden'):
                continue
            if 行.hasAttribute('hidden'):
                continue
            if 行.getAttribute('data-chat-anchor-key')==键 or (身份=='node' and 行.getAttribute('data-chat-node-key')==键):
                return 行
            if 节点部分 is None and 行.getAttribute('data-chat-node-key')==键:
                节点部分=行
        return 节点部分

    def 捕获位置(自身):
        '记下视口里第一块内容的锚。回合控件不算'
        if 自身.元素 is None:
            return None
        列表=自身.元素['list']
        滚动口=自身.元素['scroller']
        撰写=自身.元素.get('composer')
        口=滚动口.getBoundingClientRect()
        底=口.bottom
        if 撰写 is not None:
            底=撰写.getBoundingClientRect().top
        锚=None
        文档=列表.ownerDocument
        if 文档 is not None and hasattr(文档,'elementsFromPoint') and 底>口.top:
            内容=列表.getBoundingClientRect()
            左=max(口.left,内容.left)
            右=min(口.right,内容.right)
            for 元素 in 列出(文档.elementsFromPoint(左+max(0,右-左)/2,口.top+1)):
                行=元素.closest('[data-chat-anchor-key]') if hasattr(元素,'closest') else None
                if 行 is not None and 行.getAttribute('data-chat-flow-kind')!='turn-process' and 列表.contains(行):
                    if 行.getAttribute('data-chat-group-key') is None:
                        锚=行
                    else:
                        锚=行.querySelector('[data-step-process-content] > [data-chat-anchor-key]')
                        if 锚 is None:
                            锚=行
                    break
        if 锚 is None:
            行表=列出(列表.querySelectorAll('[data-chat-flow-key]'))
            可用=[]
            for 行 in 行表:
                if 行.getAttribute('data-chat-group-key') is not None:
                    continue
                if 行.getAttribute('data-chat-flow-kind')=='turn-process':
                    continue
                if 行.hasAttribute('hidden') or 行.closest('[hidden]') is not None:
                    continue
                可用.append(行)
            低=0
            高=len(可用)
            while 低<高:
                中=(低+高)//2
                if 可用[中].getBoundingClientRect().bottom>口.top:
                    高=中
                else:
                    低=中+1
            行=可用[低] if 低<len(可用) else None
            if 行 is not None and 行.getBoundingClientRect().top<底:
                锚=行
            elif len(可用)>0:
                锚=可用[0]
        键=None if 锚 is None else 锚.getAttribute('data-chat-anchor-key')
        if 锚 is None or 键 is None:
            return None
        return {'anchorKey':键,'anchorTop':锚.getBoundingClientRect().top-口.top,'scrollTop':滚动口.scrollTop or 0}

    def 读可见回合(自身,度量=None):
        '按阅读线二分顶层行。已知落点且位置没变就不再量'
        if 度量 is None:
            度量=自身.度量()
        已知=None if 自身.观测.get('landing') is None else 自身.观测['landing'].get('turn')
        if 已知 is not None and 度量 is not None and 度量['top']==自身.观测['top']:
            return 已知
        if 自身.元素 is None or 度量 is None or len(自身.回合表)==0:
            return None
        线=自身.元素['scroller'].getBoundingClientRect().top+min(96,度量['height']*0.2)
        行表=自身.顶层行()
        低=0
        高=len(行表)
        读=自身.回合表[0].get('turn')
        while 低<高:
            中=(低+高)//2
            行=行表[中]
            if 行.getBoundingClientRect().top>线:
                高=中
            else:
                值=行.getAttribute('data-chat-turn')
                try:
                    回合=int(值)
                except (TypeError,ValueError):
                    回合=None
                if 安全整数(回合):
                    读=回合
                低=中+1
        return 读

    def 滚到回合(自身,回合):
        '把已加载回合的第一段对齐到顶边下 24 像素'
        项=None
        for 候选 in 自身.回合表:
            if isinstance(候选,dict) and 候选.get('turn')==回合:
                项=候选
                break
        if 项 is None:
            return None
        行=自身.锚(项.get('anchorKey'),'node')
        if 行 is None:
            return None
        return 自身.对齐(行,24,回合)

    def 滚到回合或之后(自身,回合):
        '锚不在时，对齐第一个不早于它的行'
        if 自身.元素 is None:
            return None
        for 行 in 列出(自身.元素['list'].querySelectorAll('[data-chat-turn]')):
            if 行.hasAttribute('hidden') or 行.closest('[hidden]') is not None:
                continue
            try:
                候选=int(行.getAttribute('data-chat-turn'))
            except (TypeError,ValueError):
                continue
            if 安全整数(候选) and 候选>=回合:
                return 自身.对齐(行,24,候选)
        return None

    def 恢复(自身,位置):
        '锚还在就对齐锚，否则用当时的 scrollTop'
        行=自身.锚(位置.get('anchorKey'))
        if 行 is not None:
            return 自身.对齐(行,位置.get('anchorTop') or 0,None)
        度量=自身.度量()
        if 度量 is None:
            return None
        return 自身.写入(位置.get('scrollTop') or 0,度量,None)

    def 开始翻页(自身):
        '留住文档序里第一块还能当锚的行'
        自身.停止保留()
        if 自身.元素 is None:
            return
        行=自身.元素['list'].querySelector('[data-chat-paging-anchor]')
        if 行 is not None and not 行.hasAttribute('hidden'):
            自身.保留(行)

    def 开始保留(自身,位置=None):
        '历史加载期间按语义锚补偿'
        if 位置 is None:
            位置=自身.捕获位置()
        自身.停止保留()
        if 位置 is None:
            return
        行=自身.锚(位置.get('anchorKey'))
        if 行 is None:
            return
        自身.保留(行,位置)

    def 保留(自身,行,位置=None,组顶=None):
        '记下行和它在组里的偏移'
        if 自身.元素 is None:
            return None
        键=行.getAttribute('data-chat-anchor-key')
        if 键 is None:
            return None
        先前=None if 自身.分页 is None else 自身.分页.get('group')
        if 先前 is not None and 自身.观察 is not None:
            自身.观察.unobserve(先前['content'])
        顶=行.getBoundingClientRect().top
        体=行.closest('[data-step-process-body]')
        内容=None if 体 is None else 体.querySelector('[data-step-process-content]')
        组=None
        if 体 is not None and 内容 is not None:
            组={'body':体,'content':内容,'top':组顶 if 组顶 is not None else 顶-体.getBoundingClientRect().top}
        if 位置 is None:
            位置={'anchorKey':键,'anchorTop':顶-自身.元素['scroller'].getBoundingClientRect().top,'scrollTop':自身.元素['scroller'].scrollTop or 0}
        自身.分页={'row':行,'group':组,'position':位置}
        if 组 is not None and 自身.观察 is not None:
            自身.观察.observe(组['content'])
        return 自身.分页

    def 停止保留(自身):
        '放开分页锚'
        组=None if 自身.分页 is None else 自身.分页.get('group')
        if 组 is not None and 自身.观察 is not None:
            自身.观察.unobserve(组['content'])
        自身.分页=None

    def 正在保留(自身):
        '还有分页锚'
        return 自身.分页 is not None

    def 保留位置(自身):
        '先补组内滚动，再补外层滚动口'
        分页=自身.分页
        if 分页 is None or 自身.元素 is None:
            return None
        if not 自身.元素['list'].contains(分页['row']):
            替=自身.锚(分页['position'].get('anchorKey'))
            if 替 is None:
                自身.停止保留()
                return None
            组顶=None if 分页.get('group') is None else 分页['group'].get('top')
            分页=自身.保留(替,分页['position'],组顶)
            if 分页 is None:
                return None
        行=分页['row']
        if 行.closest('[hidden]') is not None:
            自身.停止保留()
            return None
        组=分页.get('group')
        if 组 is not None and 组['body'].contains(行):
            顶=行.getBoundingClientRect().top-组['body'].getBoundingClientRect().top
            度量=滚动度量(组['body'])
            目标=max(0,min(度量['floor'],度量['top']+顶-组['top']))
            if 度量['top']!=目标:
                跟随=按元素取跟随(组['body'])
                if 跟随 is None:
                    组['body'].scrollTop=目标
                else:
                    跟随.跳到(组['body'],度量,目标)
                    跟随.设跟随(False)
        度量=自身.度量()
        if 度量 is None:
            return None
        顶=行.getBoundingClientRect().top-自身.元素['scroller'].getBoundingClientRect().top
        目标=度量['top']+顶-分页['position'].get('anchorTop',0)
        return 自身.写入(目标,度量,None,{'key':分页['position'].get('anchorKey'),'top':顶})

    def 滚到底(自身,跟随,行为='instant'):
        '对齐物理地板，包含还没被新内容填上的垫'
        度量=自身.度量()
        if 度量 is None or 自身.元素 is None:
            return None
        自身.观测={'top':度量['top'],'landing':None}
        自身.收回下方()
        落地={
            'metrics':跟随.到底(自身.元素['scroller'],滚动度量(自身.元素['scroller']),行为),
            'position':None,
            'turn':自身.最新回合(),
        }
        自身.观测={'top':落地['metrics']['top'],'landing':落地}
        return 落地

    def 对齐(自身,行,偏移,回合):
        '把行的顶对齐到给定偏移'
        度量=自身.度量()
        if 度量 is None or 自身.元素 is None:
            return None
        顶=行.getBoundingClientRect().top-自身.元素['scroller'].getBoundingClientRect().top
        return 自身.写入(度量['top']+顶-偏移,度量,回合,{'key':行.getAttribute('data-chat-anchor-key'),'top':顶})

    def 写入(自身,目标,度量,回合,锚=None):
        '夹进滚动范围后写入'
        if 自身.元素 is None:
            return None
        顶=max(0,min(度量['floor'],目标))
        if 顶!=度量['top']:
            自身.元素['scroller'].scrollTop=顶
        实际=自身.元素['scroller'].scrollTop or 0
        位置=None
        if isinstance(锚,dict) and 锚.get('key') is not None:
            位置={'anchorKey':锚['key'],'anchorTop':锚['top']-(实际-度量['top']),'scrollTop':实际}
        落地={'metrics':{'top':实际,'height':度量['height'],'floor':度量['floor']},'turn':回合,'position':位置}
        自身.观测={'top':实际,'landing':落地}
        return 落地

    def 当滚动(自身,事件):
        '只处理这份滚动口。分页中的滚动交给尺寸策略'
        if 自身.元素 is None or getattr(事件,'target',None) is not 自身.元素['scroller']:
            return
        if 自身.观测.get('landing') is not None and (自身.元素['scroller'].scrollTop or 0)==自身.观测['top']:
            return
        自身.作废()
        if 自身.分页 is not None:
            if 自身.事件 is not None:
                自身.事件['resize']()
            return
        滚动=自身.读滚动()
        if 滚动 is not None and 自身.事件 is not None:
            自身.事件['scroll'](滚动)

    def 当滚动结束(自身,事件):
        '外层结束可以收回垫。过程组结束只通知'
        目标=getattr(事件,'target',None)
        if 自身.元素 is not None and 目标 is 自身.元素['scroller']:
            if 自身.事件 is not None:
                自身.事件['scrollEnd'](True)
            自身.收回下方()
        elif 目标 is not None and hasattr(目标,'hasAttribute') and 目标.hasAttribute('data-step-process-body'):
            if 自身.事件 is not None:
                自身.事件['scrollEnd'](False)

    def 当意图(自身,事件):
        '阅读手势。撰写器里的按键不算'
        种类=getattr(事件,'type',None)
        if 种类 in ('keydown','pointerdown'):
            目标=getattr(事件,'target',None)
            if 目标 is not None and hasattr(目标,'closest') and 目标.closest('[data-composer-seat]') is not None:
                return
            if 种类=='keydown' and getattr(事件,'key',None) not in 滚动键:
                return
        if 自身.事件 is not None and callable(自身.事件.get('intent')):
            自身.事件['intent']()
        if 自身.分页 is None:
            return
        自身.停止保留()
        if 自身.事件 is not None:
            自身.事件['interact']()
