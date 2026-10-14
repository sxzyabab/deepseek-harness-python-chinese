
__all__=['会话体','会话页眉','解析活动视图','派生谱系','默认视图标识']#仅中文公开名

默认视图标识='chat'#环回退

from nicegui import ui as 界面
from .文案 import 中文 as 对话文案
from ..异常 import 页面失败文案,贴出失败

def 恒等翻译(键,参数=None):
    '无宿主文案时用本包中文词典，没有则返回键本身。'
    if 键 not in 对话文案:#词典没有
        return 键#键
    文本=对话文案[键]#词条
    if 参数 is None:#无参数
        return 文本#原文
    for 名 in 参数:#替换占位
        文本=文本.replace('{'+名+'}',str(参数[名]))#替换
    return 文本#译完

def 空渲染槽(*位置参数,**关键字参数):
    '未注入槽渲染时不画'
    return None#不画

def 空监听():
    '触碰订阅用'
    return None#无事

def 解析活动视图(页签列表,选中标识):
    '按 id；失配回退 chat。页签为 dict 列表'
    请求=选中标识 if 选中标识 is not None else 默认视图标识#请求
    for 页 in 页签列表:#扫
        if 页['id']==请求:#命中
            return 页#页
    for 页 in 页签列表:#回退 chat
        if 页['id']==默认视图标识:#命中
            return 页#页
    return None#无

def 派生谱系(列表,会话标识):
    '沿 parentId 上溯至非 subagent。列表为 dict'
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
    '长度与每项 id/标题'
    if len(左)!=len(右):#长；判 length
        return False#不等
    for 索引,项 in enumerate(左):#逐项
        另=右[索引]#对应
        if 项['id']!=另['id'] or 项['displayTitle']!=另['displayTitle']:#差
            return False#不等
    return True#等

def 取视图(态):
    'store.view。态为 dict'
    return 态['view'] if 'view' in 态 else None#视图

def 取撰写相位(快照):
    'composerPhase'
    return 快照['composerPhase'] if 'composerPhase' in 快照 else None#相位

def 取空白(快照):
    'blank'
    return 快照['blank'] if 'blank' in 快照 else None#空白

def 取草稿(态):
    'store.draft'
    return 态['draft'] if 'draft' in 态 else None#草稿

def 取检视(态):
    'store.inspect。态为 dict'
    return 态['inspect'] if 'inspect' in 态 else None#检视

def 取输入(态):
    '输入快照原样'
    return 态#原样

class 会话页眉:#滚动口上页眉
    '标题面包屑与视图页签'
    def __init__(自身,属性=None):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.画面=None#可反复清空的画面
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '隐藏空白英雄页眉或可见标题/页签'
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
            '按会话标识上溯'
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
                '打开该会话'
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
                    '切到该页'
                    if 切视图 is not None:#有
                        切视图(视)#切
                页签列表.append({#页签
                    'id':标识,#id
                    'label':页['label'] if 'label' in 页 else None,#标签
                    'active':活动 is not None and (活动['id'] if 'id' in 活动 else None)==标识,#活动
                    'onSelect':造切,#切
                    'onClick':造切,#按钮
                })#结束
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('header')#页眉
        自身.画面.clear()#清空
        自身.画面.set_visibility(隐藏 is not True)#空白英雄时藏起
        with 自身.画面:#页眉
            贴出失败(自身)
            界面.label(翻译('session.hierarchy')).classes('谱系')#谱系
            with 界面.row().classes('面包屑'):#屑
                for 段 in 屑节点:#逐级
                    标题=段['title'] if 'title' in 段 and 段['title'] is not None else ''#标题
                    if 标题=='':#无标题
                        标题=str(段['id']) if 'id' in 段 and 段['id'] is not None else 翻译('session.hierarchy')#回退
                    点=段['onClick'] if 'onClick' in 段 else None#导航
                    if 点 is None:#当前
                        界面.label(标题)#当前
                    else:#可点
                        def 造点(钉点=点):
                            '打开这一级会话。'
                            def 点屑():
                                '导航。'
                                钉点()#开
                            return 点屑#回调
                        界面.button(标题,on_click=造点())#屑
            渲染槽('conversation.session.header.actions',{})#动作自己画
            渲染槽('conversation.session.header.utilities',{})#工具自己画
            if len(页签列表)>1:#多页
                with 界面.row().classes('页签'):#页签
                    for 页 in 页签列表:#逐页
                        页标=页['label'] if 'label' in 页 and 页['label'] is not None else ''#标签
                        if 页标=='':#无标签
                            页标=str(页['id']) if 'id' in 页 else ''#id
                        切=页['onSelect'] if 'onSelect' in 页 else None#切
                        def 造切(钉切=切):
                            '切到该页。'
                            def 点页():
                                '切换视图。'
                                if 钉切 is not None:#有
                                    钉切()#切
                            return 点页#回调
                        界面.button(页标,on_click=造切())#页签

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 会话体:#滚动口内活动视图
    '活动视图区；空白英雄时为 None'
    def __init__(自身,属性=None):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.已镜像=False#草稿镜像
        自身.解绑镜像=None#镜像拆除
        自身.画面=None#可反复清空的画面
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '活动视图或空白'
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
            return#不画
        活动标识=活动['id'] if 活动 is not None and 'id' in 活动 else None#活动
        清检视=动作.setInspect if 动作 is not None else None#清
        def 检视完成():
            '清 inspect'
            if 清检视 is not None:#有
                清检视(None)#清
        def 卸载():
            '解绑镜像并释图。'
            if 自身.解绑镜像 is not None:#有
                自身.解绑镜像()#解绑
                自身.解绑镜像=None#清
            if 释图 is not None:#有
                释图(会话标识)#释
        自身.卸载=卸载#离开会话时调用
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('viewArea')#视图区
        自身.画面.clear()#清空
        with 自身.画面:#视图区
            贴出失败(自身)
            if 活动 is None:#没有活动视图
                界面.label(恒等翻译('placeholder.unavailable'))#空态
            else:#活动视图自己画
                渲染槽('conversation.view',{'inspect':检查,'onInspectDone':检视完成},{'only':活动标识})#视图

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
