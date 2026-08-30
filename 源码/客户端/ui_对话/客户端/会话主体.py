"""严格会话页眉与主体：谱系面包屑、视图页签与草稿镜像。

对齐上游 `ui-conversation/src/client/skeleton/ConversationSession.tsx`。公开面仅中文名。
"""

__all__=['会话页眉','会话主体','解析活动视图','派生谱系','默认视图标识']#仅中文公开名

默认视图标识='chat'#稳定 Chat 回退

def 取字段(对象,键,缺省=None):#读字段
    """映射或对象。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 解析活动视图(页签们,选中标识):#解析活动页签
    """过期选中回退到 chat。"""
    请求=选中标识 if 选中标识 is not None else 默认视图标识#请求 id
    for 页 in 页签们:#找请求
        if 取字段(页,'id')==请求:#命中
            return 页#活动
    for 页 in 页签们:#回退 chat
        if 取字段(页,'id')==默认视图标识:#命中
            return 页#活动
    return None#无

def 派生谱系(列表,标识):#子代理面包屑链
    """从当前会话沿 parentId 上溯至非 subagent。"""
    链=[]#面包屑
    见过=set()#环防
    游标=标识#当前
    while 游标 is not None:#上溯
        if 游标 in 见过:#环
            break#停
        见过.add(游标)#记
        摘要=取字段(取字段(列表,'byId'),游标)#摘要
        if 摘要 is None:#无
            break#停
        链.insert(0,{'id':取字段(摘要,'id'),'displayTitle':取字段(摘要,'displayTitle')})#头插
        if 取字段(摘要,'origin')!='subagent':#非子代理
            break#停
        游标=取字段(摘要,'parentId')#父
    return 链#谱系

def 面包屑相等(左,右):#浅比面包屑
    """长度与每项 id/标题。"""
    if len(左)!=len(右):#长
        return False#不等
    for 索引,项 in enumerate(左):#逐项
        另=右[索引]#对应
        if 取字段(项,'id')!=取字段(另,'id') or 取字段(项,'displayTitle')!=取字段(另,'displayTitle'):#差
            return False#不等
    return True#等

class 会话页眉:#滚动口上方页眉
    """谱系导航与视图页签。"""

    def __init__(自身,属性=None):#记下 props
        """记下合成 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """空白英雄时隐藏铬。"""
        属性=自身.属性#props
        翻译=取字段(属性,'t',lambda 键,**_:键)#文案
        视图=取字段(属性,'views')#视图账本
        用仓库=取字段(属性,'useStore')#store
        用会话=取字段(属性,'useSession')#会话
        用会话们=取字段(属性,'useSessions')#列表
        动作=取字段(属性,'actions')#store 动作
        打开=取字段(属性,'open')#导航
        渲染槽=取字段(属性,'renderSlot',lambda *a,**k:None)#槽
        会话标识=取字段(属性,'sessionId')#id

        页签=视图.list() if 视图 is not None and callable(getattr(视图,'list',None)) else []#页签
        选中=用仓库(lambda s:取字段(s,'view')) if callable(用仓库) else None#选中视图
        活动=解析活动视图(页签,选中)#活动
        谱系=用会话们(lambda s:派生谱系(s,会话标识),面包屑相等) if callable(用会话们) else []#谱系
        作曲阶段=用会话(lambda s:取字段(s,'composerPhase')) if callable(用会话) else None#相位
        空白=用会话(lambda s:取字段(s,'blank')) if callable(用会话) else False#blank
        藏铬=空白 and 作曲阶段=='blank'#藏

        屑节点=[]#屑
        for 索引,摘要 in enumerate(谱系):#逐级
            末=索引==len(谱系)-1#末级
            屑节点.append({#段
                'id':取字段(摘要,'id'),#id
                'title':取字段(摘要,'displayTitle'),#标题
                'current':末,#当前
                'onClick':None if 末 or not callable(打开) else (lambda 标识=取字段(摘要,'id'):打开(标识)),#导航
            })#结束段
        if len(谱系)==0:#无谱系
            屑节点=[{'id':会话标识,'title':会话标识,'current':True,'onClick':None}]#仅 id

        页签节点=[]#页签按钮
        if len(页签)>1:#多页才画
            for 页 in 页签:#逐页
                标识=取字段(页,'id')#id
                活=活动 is not None and 取字段(活动,'id')==标识#选中
                页签节点.append({#页
                    'id':标识,#id
                    'label':取字段(页,'label'),#标签
                    'active':活,#活动
                    'onClick':(lambda 视=标识:取字段(动作,'setView')(视)) if 动作 is not None and callable(取字段(动作,'setView')) else None,#切页
                })#结束页

        return {#页眉
            'className':('header','headerHidden') if 藏铬 else ('header',),#类
            'aria-hidden':True if 藏铬 else None,#无障碍
            'hidden':藏铬,#藏
            'crumbs':屑节点,#谱系
            'ariaLabel':翻译('session.hierarchy'),#谱系 aria
            'actions':渲染槽('conversation.session.header.actions',{}),#动作
            'utilities':渲染槽('conversation.session.header.utilities',{}),#工具
            'tabs':页签节点,#页签
        }#结束页眉

class 会话主体:#滚动口内活动视图
    """绑定草稿镜像；空白英雄时返回 None。"""

    def __init__(自身,属性=None):#记下 props
        """记下合成 props。"""
        自身.属性=属性 or {}#合成
        自身.已绑镜像=False#镜像闩

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 挂载效应(自身):#草稿镜像与图片释放
        """种子草稿并绑定镜像；返回拆除。"""
        属性=自身.属性#props
        用输入=取字段(属性,'useInput')#输入
        输入动作=取字段(属性,'inputActions')#动作
        用仓库=取字段(属性,'useStore')#store
        动作=取字段(属性,'actions')#store 动作
        绑镜像=取字段(属性,'bindDraftMirror')#镜像
        释图=取字段(属性,'releaseSessionImages')#释图
        会话标识=取字段(属性,'sessionId')#id
        输入态=用输入(lambda s:s) if callable(用输入) else None#输入
        存草稿=用仓库(lambda s:取字段(s,'draft')) if callable(用仓库) else ''#草稿
        if 输入态 is not None and 取字段(输入态,'draft')=='' and 存草稿 not in (None,''):#种子
            if 输入动作 is not None and callable(取字段(输入动作,'setDraft')):#可写
                输入动作.setDraft(存草稿)#灌入
        解绑=绑镜像(取字段(动作,'setDraft')) if callable(绑镜像) and 动作 is not None else (lambda:None)#镜像
        自身.已绑镜像=True#闩

        def 拆除():#卸载
            """解绑并释图。"""
            解绑()#解绑
            if callable(释图):#有
                释图(会话标识)#释
        return 拆除#拆除器

    def 渲染(自身):#结构树
        """空白英雄返回 None。"""
        属性=自身.属性#props
        视图=取字段(属性,'views')#账本
        用仓库=取字段(属性,'useStore')#store
        用会话=取字段(属性,'useSession')#会话
        动作=取字段(属性,'actions')#动作
        渲染槽=取字段(属性,'renderSlot',lambda *a,**k:None)#槽
        页签=视图.list() if 视图 is not None and callable(getattr(视图,'list',None)) else []#页签
        选中=用仓库(lambda s:取字段(s,'view')) if callable(用仓库) else None#选中
        活动=解析活动视图(页签,选中)#活动
        作曲阶段=用会话(lambda s:取字段(s,'composerPhase')) if callable(用会话) else None#相位
        空白=用会话(lambda s:取字段(s,'blank')) if callable(用会话) else False#blank
        检视=用仓库(lambda s:取字段(s,'inspect') if 'inspect' in (s if isinstance(s,dict) else {}) or hasattr(s,'inspect') else None) if callable(用仓库) else None#inspect
        if 空白 and 作曲阶段=='blank':#英雄空白
            return None#不画视图区
        清检视=取字段(动作,'setInspect')#清 inspect
        return {#视图区
            'className':'viewArea',#类
            'view':None if 活动 is None else 渲染槽('conversation.view',{#活动视图
                'inspect':检视,#检视
                'onInspectDone':(lambda:清检视(None)) if callable(清检视) else None,#确认
            },{'only':取字段(活动,'id')}),#仅活动 id
        }#结束视图区
