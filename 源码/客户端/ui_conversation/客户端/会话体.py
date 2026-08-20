"""会话体与页眉：严格会话槽填入常驻滚动口。

对齐上游 `ui-conversation/src/client/skeleton/ConversationSession.tsx`。公开面仅中文名。
"""

__all__=['会话体','会话页眉','解析活动视图','派生血统','默认视图标识']#仅中文公开名

默认视图标识='chat'#环回退

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 解析活动视图(页签们,选中标识):#解析活动页签
    """按 id；失配回退 chat。"""
    请求=选中标识 if 选中标识 is not None else 默认视图标识#请求
    for 页 in 页签们:#扫
        if 取字段(页,'id')==请求:#命中
            return 页#页
    for 页 in 页签们:#回退 chat
        if 取字段(页,'id')==默认视图标识:#命中
            return 页#页
    return None#无

def 派生血统(列表,会话标识):#面包屑
    """沿 parentId 上溯至非 subagent。"""
    链=[]#面包屑
    见过=set()#环防
    游标=会话标识#当前
    while 游标 is not None:#上溯
        if 游标 in 见过:#环
            break#停
        见过.add(游标)#记
        摘要=取字段(取字段(列表,'byId'),游标)#摘要
        if 摘要 is None:#断
            break#停
        链.insert(0,{'id':取字段(摘要,'id'),'displayTitle':取字段(摘要,'displayTitle')})#头插
        if 取字段(摘要,'origin')!='subagent':#顶
            break#停
        游标=取字段(摘要,'parentId')#父
    return 链#链

class 会话页眉:#滚动口上页眉
    """标题面包屑与视图页签。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """隐藏空白英雄页眉或可见标题/页签。"""
        属性=自身.属性#props
        会话标识=取字段(属性,'sessionId')#会话
        用会话=取字段(属性,'useSession')#会话钩
        用会话们=取字段(属性,'useSessions')#列表
        用仓=取字段(属性,'useStore')#聊天仓
        动作=取字段(属性,'actions') or {}#动作
        渲染槽=取字段(属性,'renderSlot',lambda *_a,**_k:None)#槽
        视图=取字段(属性,'views') or {}#视图面
        打开=取字段(属性,'open')#打开会话
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        if hasattr(视图,'subscribe') and hasattr(视图,'version'):#订阅版本
            视图.subscribe(lambda:None)#触碰订阅
            视图.version()#版本
        页签=视图.list() if hasattr(视图,'list') else 取字段(视图,'list',lambda: [])()#页签
        选中=用仓(lambda s:取字段(s,'view')) if 用仓 is not None else None#选中视图
        活动=解析活动视图(页签,选中)#活动
        血统=用会话们(lambda s:派生血统(s,会话标识)) if 用会话们 is not None else []#面包屑
        撰写相位=用会话(lambda s:取字段(s,'composerPhase')) if 用会话 is not None else 'blank'#相位
        空白=用会话(lambda s:取字段(s,'blank')) if 用会话 is not None else True#空白
        隐藏=bool(空白) and 撰写相位=='blank'#隐铬
        return {#页眉视图
            'type':'conversation-session-header',#类型
            'hidden':隐藏,#隐
            'crumbs':血统,#面包屑
            'sessionIdFallback':会话标识,#无血统时
            'ariaHierarchy':翻译('session.hierarchy'),#无障碍
            'actions':渲染槽('conversation.session.header.actions',{}),#动作
            'utilities':渲染槽('conversation.session.header.utilities',{}),#工具
            'tabs':[{#页签
                'id':取字段(页,'id'),#id
                'label':取字段(页,'label'),#标签
                'active':活动 is not None and 取字段(页,'id')==取字段(活动,'id'),#活动
                'onSelect':(lambda 标识:取字段(动作,'setView')(标识) if 取字段(动作,'setView') is not None else None),#切
            } for 页 in 页签] if len(页签)>1 else [],#多页才画
            'onOpenCrumb':打开,#点面包屑
            'cssModule':'会话根.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 会话体:#滚动口内活动视图
    """活动视图区；空白英雄时为 None。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成
        自身.已镜像=False#草稿镜像

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """活动视图或空白。"""
        属性=自身.属性#props
        会话标识=取字段(属性,'sessionId')#会话
        用会话=取字段(属性,'useSession')#会话钩
        用输入=取字段(属性,'useInput')#输入
        输入动作=取字段(属性,'inputActions')#输入动作
        用仓=取字段(属性,'useStore')#仓
        动作=取字段(属性,'actions') or {}#动作
        渲染槽=取字段(属性,'renderSlot',lambda *_a,**_k:None)#槽
        视图=取字段(属性,'views') or {}#视图
        绑镜像=取字段(属性,'bindDraftMirror')#镜像
        释图=取字段(属性,'releaseSessionImages')#释图
        if hasattr(视图,'subscribe') and hasattr(视图,'version'):#订阅
            视图.subscribe(lambda:None)#触
            视图.version()#版
        页签=视图.list() if hasattr(视图,'list') else 取字段(视图,'list',lambda: [])()#页签
        选中=用仓(lambda s:取字段(s,'view')) if 用仓 is not None else None#选中
        活动=解析活动视图(页签,选中)#活动
        撰写相位=用会话(lambda s:取字段(s,'composerPhase')) if 用会话 is not None else 'blank'#相位
        空白=用会话(lambda s:取字段(s,'blank')) if 用会话 is not None else True#空白
        输入态=用输入(lambda s:s) if 用输入 is not None else None#输入
        存草稿=用仓(lambda s:取字段(s,'draft')) if 用仓 is not None else ''#存草稿
        检查=用仓(lambda s:取字段(s,'inspect') if 'inspect' in (s if isinstance(s,dict) else {}) or hasattr(s,'inspect') else None) if 用仓 is not None else None#检查
        if not 自身.已镜像 and 输入态 is not None and 输入动作 is not None:#首挂镜像
            if 取字段(输入态,'draft')=='' and 存草稿 not in (None,''):#种子
                设=取字段(输入动作,'setDraft')#写
                if 设 is not None:#有
                    设(存草稿)#种
            if 绑镜像 is not None and 取字段(动作,'setDraft') is not None:#绑
                绑镜像(动作['setDraft'] if isinstance(动作,dict) else 取字段(动作,'setDraft'))#镜像
            自身.已镜像=True#已
        if 空白 and 撰写相位=='blank':#英雄空白
            return None#不画
        return {#视图区
            'type':'conversation-session',#类型
            'sessionId':会话标识,#会话
            'activeViewId':取字段(活动,'id') if 活动 is not None else None,#活动
            'view':None if 活动 is None else 渲染槽('conversation.view',{#视图片
                'inspect':检查,#检查
                'onInspectDone':lambda:(取字段(动作,'setInspect')(None) if 取字段(动作,'setInspect') is not None else None),#完成
            },{'only':取字段(活动,'id')}),#仅活动
            'onUnmount':lambda:(释图(会话标识) if 释图 is not None else None),#卸载释图
            'cssModule':'会话根.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
