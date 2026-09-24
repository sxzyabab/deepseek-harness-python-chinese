import builtins
from .用滚动跟随 import 滚动度量,滚动跟随

__all__=['聊天视口','用聊天视口']

阅读意图=('wheel','touchstart','pointerdown','keydown','beforematch')
滚动键=frozenset(['ArrowUp','ArrowDown','PageUp','PageDown','Home','End',' '])

class 聊天视口:
    """一个聊天滚动口的 DOM 操作、监听与尺寸观察，不含历史加载或跟随策略。"""
    def __init__(自身):
        """未附着。"""
        自身.元素=None
        自身.观察=None
        自身.事件=None
        自身.回合表=()
        自身.观测={'top':0,'landing':None}
        自身.分页=None

    def 附着(自身,列表,列):
        """绑到含滚动口并观察内容与视口尺寸。"""
        自身.卸下()
        滚动口=列表.closest('[data-conversation-scroll]')
        if 滚动口 is None:
            滚动口=列表
        撰写=滚动口.querySelector('[data-composer-seat]')
        元素={'list':列表,'column':列,'scroller':滚动口,'composer':撰写}
        自身.元素=元素
        滚动口.addEventListener('scroll',自身.滚动中,{'passive':True})
        滚动口.addEventListener('scrollend',自身.滚动结束,{'passive':True,'capture':True})
        for 种 in 阅读意图:
            滚动口.addEventListener(种,自身.意图,{'passive':True,'capture':True})
        观察类=getattr(builtins,'ResizeObserver',None)
        if 观察类 is not None:
            def 尺寸():
                """内容或视口尺寸变化。"""
                if 自身.元素 is not 元素:
                    return
                自身.作废()
                if 自身.事件 is not None:
                    自身.事件['resize']()
            自身.观察=观察类(尺寸)
            自身.观察.observe(列)
            自身.观察.observe(滚动口)
            if 撰写 is not None:
                自身.观察.observe(撰写)

    def 卸下(自身):
        """断开 DOM 资源并清观察。"""
        自身.停止保留()
        if 自身.元素 is not None:
            滚动口=自身.元素['scroller']
            滚动口.removeEventListener('scroll',自身.滚动中)
            滚动口.removeEventListener('scrollend',自身.滚动结束,True)
            for 种 in 阅读意图:
                滚动口.removeEventListener(种,自身.意图,True)
        if 自身.观察 is not None:
            自身.观察.disconnect()
            自身.观察=None
        自身.元素=None
        自身.事件=None
        自身.回合表=()
        自身.观测={'top':0,'landing':None}

    def 连接(自身,事件):
        """接业务策略，不改 DOM 监听所有权。"""
        自身.事件=事件
        def 断开():
            """只断开这批处理器。"""
            if 自身.事件 is 事件:
                自身.事件=None
        return 断开

    def 更新回合(自身,回合表):
        """采纳已加载回合锚，不查 DOM。"""
        自身.回合表=回合表

    @property
    def latestTurn(自身):
        """已加载最后一轮；空窗为 None。"""
        if len(自身.回合表)==0:
            return None
        return 自身.回合表[-1]['turn']

    def 作废(自身):
        """丢掉依赖几何的落地知识，保留滚动归属。"""
        自身.观测['landing']=None

    def 确认(自身,度量):
        """接受已采样读者位置，不保留已知落地。"""
        自身.观测={'top':度量['top'],'landing':None}

    def 读滚动(自身):
        """当前几何与相对上次确认位置的移动归属。"""
        度量=自身.度量()
        if 度量 is None:
            return None
        return {'metrics':度量,'movedByReader':abs(度量['top']-min(自身.观测['top'],度量['floor']))>0.5}

    def 度量(自身):
        """滚动口几何。"""
        if 自身.元素 is None:
            return None
        return 滚动度量(自身.元素['scroller'])

    def 锚(自身,键,身份='position'):
        """按锚键或节点键找可见行。"""
        if 自身.元素 is None:
            return None
        节点局部=None
        for 行 in 自身.元素['list'].querySelectorAll('[data-chat-anchor-key]:not([hidden]):not([hidden] *)'):
            锚键=行.dataset.chatAnchorKey
            节点键=行.dataset.chatNodeKey
            if 锚键==键 or (身份=='node' and 节点键==键):
                return 行
            if 节点局部 is None and 节点键==键:
                节点局部=行
        return 节点局部

    def 捕获位置(自身):
        """捕获可见转录内容，排除历史展开时会挪位的回合控件。"""
        元素=自身.元素
        if 元素 is None:
            return None
        列表=元素['list']
        滚动口=元素['scroller']
        撰写=元素['composer']
        视口=滚动口.getBoundingClientRect()
        底=撰写.getBoundingClientRect().top if 撰写 is not None else 视口.bottom
        锚点=None
        取点=getattr(builtins.document,'elementsFromPoint',None) if hasattr(builtins,'document') else None
        if callable(取点) and 底>视口.top:
            内容=列表.getBoundingClientRect()
            左=max(视口.left,内容.left)
            右=min(视口.right,内容.right)
            for 元素项 in 取点(左+max(0,右-左)/2,视口.top+1):
                行=元素项.closest('[data-chat-anchor-key]') if hasattr(元素项,'closest') else None
                if 行 is not None and 行.dataset.chatFlowKind!='turn-process' and 列表.contains(行):
                    if 行.dataset.chatGroupKey is None:
                        锚点=行
                    else:
                        内=行.querySelector('[data-step-process-content] > [data-chat-anchor-key]:not(:empty):not([hidden]):not([hidden] *)')
                        锚点=行 if 内 is None else 内
                    break
        if 锚点 is None:
            行表=列表.querySelectorAll(
                '[data-chat-flow-key]:not([data-chat-group-key]):not([data-chat-flow-kind="turn-process"])'
                +':not(:empty):not([hidden]):not([hidden] *)',
            )
            数=行表.length
            低=0
            高=数
            while 低<高:
                中=(低+高)//2
                if 行表.item(中).getBoundingClientRect().bottom>视口.top:
                    高=中
                else:
                    低=中+1
            行=行表.item(低) if 低<数 else None
            if 行 is not None and 行.getBoundingClientRect().top<底:
                锚点=行
            else:
                锚点=行表.item(0) if 数>0 else None
        键=None if 锚点 is None else 锚点.dataset.chatAnchorKey
        if 锚点 is None or 键 is None:
            return None
        return {
            'anchorKey':键,
            'anchorTop':锚点.getBoundingClientRect().top-视口.top,
            'scrollTop':滚动口.scrollTop,
        }

    def 读可见回合(自身,度量=None):
        """二分外层节点/组盒子近似当前回合。"""
        if 度量 is None:
            度量=自身.度量()
        已知=自身.观测['landing']['turn'] if 自身.观测['landing'] is not None else None
        if 已知 is not None and 度量 is not None and 度量['top']==自身.观测['top']:
            return 已知
        元素=自身.元素
        if 元素 is None or 度量 is None or len(自身.回合表)==0:
            return None
        首=自身.回合表[0]['turn']
        线=元素['scroller'].getBoundingClientRect().top+min(96,度量['height']*0.2)
        行表=元素['column'].children
        低=0
        高=len(行表)
        读=首
        while 低<高:
            中=(低+高)//2
            行=行表[中]
            if 行.getBoundingClientRect().top>线:
                高=中
            else:
                值=行.getAttribute('data-chat-turn')
                try:
                    回合=int(值) if 值 is not None else None
                except ValueError:
                    回合=None
                if 回合 is not None and not isinstance(回合,bool):
                    读=回合
                低=中+1
        return 读

    def 滚到回合(自身,回合):
        """对齐已加载回合并返回夹紧后的实际位置。"""
        项=None
        for 候选 in 自身.回合表:
            if 候选['turn']==回合:
                项=候选
                break
        if 项 is None:
            return None
        行=自身.锚(项['anchorKey'],'node')
        if 行 is None:
            return None
        return 自身.对齐(行,24,回合)

    def 滚到回合或之后(自身,回合):
        """对齐不可用锚的最近已挂载回退行。"""
        if 自身.元素 is None:
            return None
        for 行 in 自身.元素['list'].querySelectorAll('[data-chat-turn]:not([hidden]):not([hidden] *)'):
            try:
                候选=int(行.dataset.chatTurn)
            except (TypeError,ValueError):
                continue
            if not isinstance(候选,bool) and 候选>=回合:
                return 自身.对齐(行,24,候选)
        return None

    def 恢复(自身,位置):
        """按语义锚恢复；行缺席则退回原始顶。位置为 dict。"""
        行=自身.锚(位置['anchorKey'])
        if 行 is not None:
            return 自身.对齐(行,位置['anchorTop'],None)
        度量=自身.度量()
        if 度量 is None:
            return None
        return 自身.写入(位置['scrollTop'],度量,None)

    def 开始分页(自身):
        """按 DOM 序保留第一个合格转录席，不读几何。"""
        自身.停止保留()
        if 自身.元素 is None:
            return
        行=自身.元素['list'].querySelector('[data-chat-paging-anchor]:not(:empty):not([hidden]):not([hidden] *)')
        if 行 is not None:
            自身.留住(行)

    def 开始保留(自身,位置=None):
        """留住一行及其内外偏移。"""
        自身.停止保留()
        if 位置 is None:
            位置=自身.捕获位置()
        if 位置 is None:
            return
        行=自身.锚(位置['anchorKey'])
        if 行 is None:
            return
        自身.留住(行,位置)

    def 留住(自身,行,位置=None,组顶=None):
        """记下分页行与可选组内偏移。"""
        元素=自身.元素
        键=行.dataset.chatAnchorKey
        if 元素 is None or 键 is None:
            return None
        先前组=自身.分页['group'] if 自身.分页 is not None else None
        if 先前组 is not None and 自身.观察 is not None:
            自身.观察.unobserve(先前组['content'])
        顶=行.getBoundingClientRect().top
        正文=行.closest('[data-step-process-body]')
        内容=None if 正文 is None else 正文.querySelector('[data-step-process-content]')
        if 正文 is None or 内容 is None:
            组=None
        else:
            组={'body':正文,'content':内容,'top':顶-正文.getBoundingClientRect().top if 组顶 is None else 组顶}
        自身.分页={
            'row':行,'group':组,
            'position':位置 if 位置 is not None else {
                'anchorKey':键,
                'anchorTop':顶-元素['scroller'].getBoundingClientRect().top,
                'scrollTop':元素['scroller'].scrollTop,
            },
        }
        if 组 is not None and 自身.观察 is not None:
            自身.观察.observe(组['content'])
        return 自身.分页

    def 停止保留(自身):
        """释放分页所有权及其内容尺寸观察。"""
        组=自身.分页['group'] if 自身.分页 is not None else None
        if 组 is not None and 自身.观察 is not None:
            自身.观察.unobserve(组['content'])
        自身.分页=None

    @property
    def preserving(自身):
        """是否仍留着分页行。"""
        return 自身.分页 is not None

    def 保留(自身):
        """先补偿内层滚动再补偿外层，夹在实际范围内。"""
        分页=自身.分页
        元素=自身.元素
        if 分页 is None or 元素 is None:
            return None
        if not 元素['list'].contains(分页['row']):
            替=自身.锚(分页['position']['anchorKey'])
            if 替 is None:
                自身.停止保留()
                return None
            组顶=分页['group']['top'] if 分页['group'] is not None else None
            分页=自身.留住(替,分页['position'],组顶)
            if 分页 is None:
                return None
        行=分页['row']
        组=分页['group']
        位置=分页['position']
        if 行.closest('[hidden]') is not None or 行.matches(':empty'):
            自身.停止保留()
            return None
        if 组 is not None and 组['body'].contains(行):
            顶=行.getBoundingClientRect().top-组['body'].getBoundingClientRect().top
            度量=滚动度量(组['body'])
            目标=max(0,min(度量['floor'],度量['top']+顶-组['top']))
            if 度量['top']!=目标:
                跟随=滚动跟随.按元素(组['body'])
                if 跟随 is None:
                    组['body'].scrollTop=目标
                else:
                    跟随.跳转(组['body'],度量,目标)
                    跟随.设跟随(False)
        度量=自身.度量()
        if 度量 is None:
            return None
        顶=行.getBoundingClientRect().top-元素['scroller'].getBoundingClientRect().top
        目标=度量['top']+顶-位置['anchorTop']
        return 自身.写入(目标,度量,None,{'key':位置['anchorKey'],'top':顶})

    def 滚到底(自身,跟随):
        """把滚动口对齐当前底部。"""
        度量=自身.度量()
        if 度量 is None or 自身.元素 is None:
            return None
        落地={
            'metrics':跟随.到底(自身.元素['scroller'],度量,'instant'),
            'position':None,
            'turn':自身.latestTurn,
        }
        自身.观测={'top':落地['metrics']['top'],'landing':落地}
        return 落地

    def 对齐(自身,行,偏移,回合):
        """把滚动口顶对齐到行减去偏移。"""
        度量=自身.度量()
        if 度量 is None or 自身.元素 is None:
            return None
        顶=行.getBoundingClientRect().top-自身.元素['scroller'].getBoundingClientRect().top
        return 自身.写入(度量['top']+顶-偏移,度量,回合,{'key':行.dataset.chatAnchorKey,'top':顶})

    def 写入(自身,目标,度量,回合,锚=None):
        """夹紧写入滚动顶并记下落地。"""
        if 自身.元素 is None:
            return None
        顶=max(0,min(度量['floor'],目标))
        if 顶!=度量['top']:
            自身.元素['scroller'].scrollTop=顶
        实际=自身.元素['scroller'].scrollTop
        键=None if 锚 is None else 锚['key']
        落地={
            'metrics':{'top':实际,'height':度量['height'],'floor':度量['floor']},
            'turn':回合,
            'position':None if 键 is None else {
                'anchorKey':键,
                'anchorTop':锚['top']-(实际-度量['top']),
                'scrollTop':实际,
            },
        }
        自身.观测={'top':实际,'landing':落地}
        return 落地

    def 滚动中(自身,事件):
        """滚动口滚动。"""
        if 自身.元素 is None or 事件.target is not 自身.元素['scroller']:
            return
        if 自身.观测['landing'] is not None and 自身.元素['scroller'].scrollTop==自身.观测['top']:
            return
        自身.作废()
        if 自身.分页 is not None:
            if 自身.事件 is not None:
                自身.事件['resize']()
            return
        滚动=自身.读滚动()
        if 滚动 is not None and 自身.事件 is not None:
            自身.事件['scroll'](滚动)

    def 滚动结束(自身,事件):
        """滚动口或过程正文 scrollend。"""
        目标=事件.target
        if 目标 is (自身.元素['scroller'] if 自身.元素 is not None else None):
            if 自身.事件 is not None:
                自身.事件['scrollEnd']()
            return
        if hasattr(目标,'hasAttribute') and 目标.hasAttribute('data-step-process-body'):
            if 自身.事件 is not None:
                自身.事件['scrollEnd']()

    def 意图(自身,事件):
        """读者手势取消分页保留。"""
        if 事件.type=='keydown' or 事件.type=='pointerdown':
            目标=事件.target
            if hasattr(目标,'closest') and 目标.closest('[data-composer-seat]') is not None:
                return
            if 事件.type=='keydown' and (not hasattr(事件,'key') or 事件.key not in 滚动键):
                return
        if 自身.分页 is None:
            return
        自身.停止保留()
        if 自身.事件 is not None:
            自身.事件['interact']()

def 用聊天视口():
    """铸造视口与元素引用。"""
    视口=聊天视口()
    return {'viewport':视口,'listRef':{'current':None},'columnRef':{'current':None}}
