__all__=['计划卡','计划审阅打开']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键。"""
    return 键#键

def 锚点序号(项):
    """排序键。"""
    return 项['anchorSeq'] if 'anchorSeq' in 项 else 0

class 计划卡:
    """已完成回合的已提交计划卡列表。"""
    def __init__(自身,属性=None):
        """记下合成 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """按调用序投影本回合 submitted-plan。"""
        属性=自身.属性#props
        回合=属性['turn'] if 'turn' in 属性 else None#回合
        用聊天=属性['useChat'] if 'useChat' in 属性 else None#选择器
        打开计划=属性['openPlan'] if 'openPlan' in 属性 else None#打开
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        if 用聊天 is None or 回合 is None:#缺
            return None#无
        def 选(快照):
            """筛本回合计划。"""
            节点源=快照['nodes'] if 'nodes' in 快照 else None#节点源
            节点表=list(节点源.values()) if 节点源 is not None else []
            结果=[]
            for 节点 in 节点表:
                if (节点['kind'] if 'kind' in 节点 else None)!='submitted-plan':
                    continue
                位=节点['location'] if 'location' in 节点 else None
                if not isinstance(位,dict):
                    continue
                位种=位['kind'] if 'kind' in 位 else None
                if 位种 not in ('turn','step'):
                    continue
                回=位['turn'] if 'turn' in 位 else None
                if not isinstance(回,dict) or (回['turn'] if 'turn' in 回 else None)!=(回合['turn'] if 'turn' in 回合 else None):
                    continue
                结果.append(节点)
            结果.sort(key=锚点序号)#序
            return 结果#列表
        计划表=用聊天(选)#选
        if len(计划表)==0:#无
            return None#无卡
        卡表=[]#视图卡
        for 项 in 计划表:#逐
            计划=项['data'] if 'data' in 项 else 项#数据
            卡表.append({
                'type':'plan-card','callId':计划['callId'] if 'callId' in 计划 else None,'title':计划['title'] if 'title' in 计划 else None,
                'description':翻译('preview.document'),'action':翻译('preview.action'),
                'ariaLabel':翻译('preview.openNamed',{'title':计划['title'] if 'title' in 计划 else None}),
                'onOpen':打开计划,
                'cssModule':'计划预览.module.css',
            })
        return {'type':'plan-cards','cards':卡表,'cssModule':'计划预览.module.css'}#列表

    def __call__(自身,属性=None):
        """有新属性则刷新后再渲染。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 计划审阅打开:
    """待审计划自动打开与手动打开器。"""
    def __init__(自身,属性=None):
        """记下合成 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.已自动=False#是否已自动开

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """自动打开一次，并返回手动打开按钮视图。"""
        属性=自身.属性#props
        审阅=属性['review'] if 'review' in 属性 else {}#审阅
        请求键=属性['requestKey'] if 'requestKey' in 属性 else ''#键
        打开审阅=属性['openReview'] if 'openReview' in 属性 else None#打开
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        用存储=属性['useStore'] if 'useStore' in 属性 else None#store
        动作=属性['actions'] if 'actions' in 属性 else None#动作
        身份=('call:'+str(审阅['callId'])) if 'callId' in 审阅 and 审阅['callId'] is not None else ('review:'+请求键)
        已开=False
        if 用存储 is not None:
            def 读已开(态):
                """是否已标记打开。"""
                已开表=态['opened'] if 'opened' in 态 else {}
                return (已开表[身份] if 身份 in 已开表 else None) is True
            已开=用存储(读已开) is True
        if not 已开 and not 自身.已自动 and 打开审阅 is not None:
            打开审阅(审阅,请求键)
            if 动作 is not None and 'markOpened' in 动作:
                动作['markOpened'](身份)
            自身.已自动=True
        return {#按钮
            'type':'plan-review-open','label':翻译('preview.full'),#文案
            'title':翻译('preview.open'),'ariaLabel':翻译('preview.open'),#无障碍
            'onOpen':打开审阅,'review':审阅,'requestKey':请求键,#打开
            'cssModule':'计划预览.module.css',#样式
        }#视图

    def __call__(自身,属性=None):
        """有新属性则刷新后再渲染。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
