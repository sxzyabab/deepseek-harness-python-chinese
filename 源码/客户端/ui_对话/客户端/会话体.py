"""会话体与页眉：严格会话槽填入常驻滚动口。

对齐上游 `ui-conversation/src/client/skeleton/ConversationSession.tsx`。公开面仅中文名。
属性、快照、页签为 dict；视图环为契约 dict（list/subscribe/version）。
"""

__all__=['会话体','会话页眉','解析活动视图','派生谱系','默认视图标识']#仅中文公开名

默认视图标识='chat'#环回退

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键

def 空渲染槽(*位置参数,**关键字参数):
    """未注入槽渲染时不画。"""
    return None#不画

def 空监听():
    """触碰订阅用。"""
    return None#无事

def 解析活动视图(页签列表,选中标识):
    """按 id；失配回退 chat。页签为 dict 列表。"""
    请求=选中标识 if 选中标识 is not None else 默认视图标识#请求
    for 页 in 页签列表:#扫
        if 页['id']==请求:#命中
            return 页#页
    for 页 in 页签列表:#回退 chat
        if 页['id']==默认视图标识:#命中
            return 页#页
    return None#无

def 派生谱系(列表,会话标识):
    """沿 parentId 上溯至非 subagent。列表为 dict。"""
    链=[]#面包屑
    见过=set()#环防
    游标=会话标识#当前
    while 游标 is not None:#上溯
        if 游标 in 见过:#环
            break#停
        见过.add(游标)#记
        表=列表['byId'] if 列表 is not None and 'byId' in 列表 else None#byId
        摘要=表[游标] if 表 is not None and 游标 in 表 else None#摘要
        if 摘要 is None:#断
            break#停
        链.insert(0,{'id':摘要['id'] if 'id' in 摘要 else None,'displayTitle':摘要['displayTitle'] if 'displayTitle' in 摘要 else None})#头插
        if ('origin' not in 摘要) or 摘要['origin']!='subagent':#顶
            break#停
        游标=摘要['parentId'] if 'parentId' in 摘要 else None#父
    return 链#链

def 面包屑相等(左,右):
    """长度与每项 id/标题。"""
    if len(左)!=len(右):#长；判 length
        return False#不等
    for 索引,项 in enumerate(左):#逐项
        另=右[索引]#对应
        if 项['id']!=另['id'] or 项['displayTitle']!=另['displayTitle']:#差
            return False#不等
    return True#等

def 取视图(态):
    """store.view。态为 dict。"""
    return 态['view'] if 'view' in 态 else None#视图

def 取撰写相位(快照):
    """composerPhase。"""
    return 快照['composerPhase'] if 'composerPhase' in 快照 else None#相位

def 取空白(快照):
    """blank。"""
    return 快照['blank'] if 'blank' in 快照 else None#空白

def 取草稿(态):
    """store.draft。"""
    return 态['draft'] if 'draft' in 态 else None#草稿

def 取检视(态):
    """store.inspect。态为 dict。"""
    return 态['inspect'] if 'inspect' in 态 else None#检视

def 取输入(态):
    """输入快照原样。"""
    return 态#原样

class 会话页眉:#滚动口上页眉
    """标题面包屑与视图页签。"""
    def __init__(自身,属性=None):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """隐藏空白英雄页眉或可见标题/页签。"""
        属性=自身.属性#props
        会话标识=属性['sessionId'] if 'sessionId' in 属性 else None#会话
        用会话=属性['useSession'] if 'useSession' in 属性 else None#会话钩
        取会话列表=属性['useSessions'] if 'useSessions' in 属性 else None#列表
        用存储=属性['useStore'] if 'useStore' in 属性 else None#聊天仓
        动作=属性['actions'] if 'actions' in 属性 else None#动作
        渲染槽=属性['renderSlot'] if 'renderSlot' in 属性 else 空渲染槽#槽
        视图=属性['views'] if 'views' in 属性 else None#视图面
        打开=属性['open'] if 'open' in 属性 else None#打开会话
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        页签=[]#页签
        if 视图 is not None:#有面
            视图['subscribe'](空监听)#触碰订阅
            视图['version']()#版本
            页签=视图['list']()#页签
        选中=用存储(取视图) if 用存储 is not None else None#选中视图
        活动=解析活动视图(页签,选中)#活动
        def 取谱系(列表):
            """按会话标识上溯。"""
            return 派生谱系(列表,会话标识)#链
        谱系=取会话列表(取谱系,面包屑相等) if 取会话列表 is not None else []#面包屑
        撰写相位=用会话(取撰写相位) if 用会话 is not None else None#相位
        空白=用会话(取空白) if 用会话 is not None else False#空白
        隐藏=空白 is True and 撰写相位=='blank'#隐铬
        屑节点=[]#屑
        for 索引,摘要 in enumerate(谱系):#逐级
            末=索引==len(谱系)-1#末级
            标识=摘要['id'] if 'id' in 摘要 else None#id
            标题=摘要['displayTitle'] if 'displayTitle' in 摘要 else None#标题
            def 造开(开往=标识):
                """打开该会话。"""
                if 打开 is not None:#有
                    打开(开往)#导航
            屑节点.append({#段
                'id':标识,#id
                'displayTitle':标题,#谱系原字段
                'title':标题,#页眉展示
                'current':末,#当前
                'onClick':None if 末 is True or 打开 is None else 造开,#导航
            })#结束段
        if len(谱系)==0:#无谱系；判 length
            屑节点=[{'id':会话标识,'displayTitle':会话标识,'title':会话标识,'current':True,'onClick':None}]#仅 id
        切视图=动作.setView if 动作 is not None else None#切
        页签列表=[]#页签按钮
        if len(页签)>1:#多页才画；判 length
            for 页 in 页签:#逐页
                标识=页['id'] if 'id' in 页 else None#id
                def 造切(视=标识):
                    """切到该页。"""
                    if 切视图 is not None:#有
                        切视图(视)#切
                页签列表.append({#页签
                    'id':标识,#id
                    'label':页['label'] if 'label' in 页 else None,#标签
                    'active':活动 is not None and (活动['id'] if 'id' in 活动 else None)==标识,#活动
                    'onSelect':造切,#切
                    'onClick':造切,#按钮
                })#结束
        return {#页眉视图
            'type':'conversation-session-header',#类型
            'className':('header','headerHidden') if 隐藏 is True else ('header',),#类
            'aria-hidden':True if 隐藏 is True else None,#无障碍
            'hidden':隐藏,#隐
            'crumbs':屑节点,#面包屑
            'sessionIdFallback':会话标识,#无谱系时
            'ariaHierarchy':翻译('session.hierarchy'),#无障碍
            'ariaLabel':翻译('session.hierarchy'),#谱系 aria
            'actions':渲染槽('conversation.session.header.actions',{}),#动作
            'utilities':渲染槽('conversation.session.header.utilities',{}),#工具
            'tabs':页签列表,#多页才画
            'onOpenCrumb':打开,#点面包屑
            'cssModule':'会话根.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 会话体:#滚动口内活动视图
    """活动视图区；空白英雄时为 None。"""
    def __init__(自身,属性=None):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.已镜像=False#草稿镜像
        自身.解绑镜像=None#镜像拆除

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """活动视图或空白。"""
        属性=自身.属性#props
        会话标识=属性['sessionId'] if 'sessionId' in 属性 else None#会话
        用会话=属性['useSession'] if 'useSession' in 属性 else None#会话钩
        用输入=属性['useInput'] if 'useInput' in 属性 else None#输入
        输入动作=属性['inputActions'] if 'inputActions' in 属性 else None#输入动作
        用存储=属性['useStore'] if 'useStore' in 属性 else None#仓
        动作=属性['actions'] if 'actions' in 属性 else None#动作
        渲染槽=属性['renderSlot'] if 'renderSlot' in 属性 else 空渲染槽#槽
        视图=属性['views'] if 'views' in 属性 else None#视图
        绑镜像=属性['bindDraftMirror'] if 'bindDraftMirror' in 属性 else None#镜像
        释图=属性['releaseSessionImages'] if 'releaseSessionImages' in 属性 else None#释图
        页签=[]#页签
        if 视图 is not None:#有面
            视图['subscribe'](空监听)#触
            视图['version']()#版
            页签=视图['list']()#页签
        选中=用存储(取视图) if 用存储 is not None else None#选中
        活动=解析活动视图(页签,选中)#活动
        撰写相位=用会话(取撰写相位) if 用会话 is not None else None#相位
        空白=用会话(取空白) if 用会话 is not None else False#空白
        输入态=用输入(取输入) if 用输入 is not None else None#输入
        存草稿=用存储(取草稿) if 用存储 is not None else ''#存草稿
        检查=用存储(取检视) if 用存储 is not None else None#检查
        if 自身.已镜像 is False and 输入态 is not None and 输入动作 is not None:#首挂镜像
            草稿=输入态['draft'] if 'draft' in 输入态 else None#现场草稿
            if 草稿=='' and 存草稿 is not None and 存草稿!='':#种子
                设=输入动作['setDraft'] if 'setDraft' in 输入动作 else None#写
                if 设 is not None:#有
                    设(存草稿)#种
            写存储=动作.setDraft if 动作 is not None else None#存储草稿
            if 绑镜像 is not None and 写存储 is not None:#绑
                自身.解绑镜像=绑镜像(写存储)#镜像
            自身.已镜像=True#已
        if 空白 is True and 撰写相位=='blank':#英雄空白
            return None#不画
        活动标识=活动['id'] if 活动 is not None and 'id' in 活动 else None#活动
        清检视=动作.setInspect if 动作 is not None else None#清
        def 检视完成():
            """清 inspect。"""
            if 清检视 is not None:#有
                清检视(None)#清
        def 卸载():
            """解绑镜像并释图。"""
            if 自身.解绑镜像 is not None:#有
                自身.解绑镜像()#解绑
                自身.解绑镜像=None#清
            if 释图 is not None:#有
                释图(会话标识)#释
        return {#视图区
            'type':'conversation-session',#类型
            'className':'viewArea',#类
            'sessionId':会话标识,#会话
            'activeViewId':活动标识,#活动
            'view':None if 活动 is None else 渲染槽('conversation.view',{#视图片
                'inspect':检查,#检查
                'onInspectDone':检视完成,#完成
            },{'only':活动标识}),#仅活动
            'onUnmount':卸载,#卸载释图
            'cssModule':'会话根.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
