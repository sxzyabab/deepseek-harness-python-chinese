"""子智能体会话头目录动作：直接子项树与懒展开后代。

对齐上游 `ui-subagent/src/client/SubagentCatalogAction.tsx` 的展示与格式化逻辑。
公开面仅中文名。DOM 焦点导航/指针外关闭需浏览器宿主；本模块落盘结构树与样式。
"""
import time#活动时长 now

__all__=[#仅中文公开名
    '目录动作','格式化令牌','格式化时长','格式化精确时长','令牌合计','活动时长毫秒','样式表',
]#公开面结束

样式表='''#对齐 SubagentCatalogAction.module.css
.root{position:relative}
.trigger{display:inline-flex;align-items:center;gap:3px;min-height:28px;padding:3px 2px;border:0;border-radius:6px;background:transparent;color:var(--dsw-alias-label-tertiary);font-size:12px;line-height:18px;cursor:pointer}
.count{margin:0 5px}
.activitySlot{display:inline-flex;flex:none;width:10px;height:10px}
.trigger:hover,.trigger:focus-visible{color:var(--dsw-alias-label-secondary)}
.triggerOpen{transform:rotate(180deg)}
.menu{position:absolute;top:calc(100% + 5px);left:0;z-index:100;box-sizing:border-box;display:flex;flex-direction:column;width:336px;max-width:min(400px,calc(100vw - 32px));max-height:min(560px,calc(100vh - 140px));padding:4px;overflow:auto;border-radius:12px;background:var(--dsw-specific-menu);--dsh-scrollbar-thumb:var(--dsw-alias-scrollbar-bg-l2);--dsh-scrollbar-thumb-hover:var(--dsw-alias-scrollbar-hover-l2);box-shadow:var(--dsw-shadow-lv3)}
.node{position:relative;min-width:0}
.row{position:relative;display:flex;align-items:flex-start;gap:8px;box-sizing:border-box;width:100%;min-height:50px;padding:7px 8px 7px 11px;border:0;border-radius:8px;background:transparent;color:var(--dsw-alias-label-primary);font-size:13px;line-height:18px;text-align:left;cursor:pointer;outline:none}
.clickarea{box-sizing:border-box;display:flex;flex:1;align-self:stretch;align-items:flex-start;gap:8px;min-width:0;margin:-7px -8px -7px;padding:7px 8px;border-radius:8px}
.disabled{color:var(--dsw-alias-label-dimmed);cursor:not-allowed}
.disclosure,.disclosureSpace{flex:none;width:14px;height:18px}
.disclosure{display:inline-flex;align-items:center;justify-content:center;padding:0;border:0;background:transparent;color:var(--dsw-alias-label-tertiary);cursor:pointer}
.disclosureOpen{transform:rotate(90deg)}
.content{display:flex;flex:1;flex-direction:column;min-width:0}
.label,.summary{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.summary,.metrics{color:var(--dsw-alias-label-tertiary);font-size:11px;line-height:16px}
.metrics{display:grid;grid-template-rows:18px 16px;flex:none;font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}
.children{position:relative;margin-left:18px;padding-left:4px}
.notice,.error{padding:10px 12px;color:var(--dsw-alias-label-tertiary);font-size:12px;line-height:18px}
.error{display:flex;align-items:center;justify-content:space-between;gap:12px;color:var(--dsw-alias-state-error-primary)}
.refresh{display:inline-flex;flex:none;align-items:center;gap:4px;padding:4px 6px;border:0;border-radius:6px;background:transparent;color:inherit;cursor:pointer}
'''#样式表结束

无后代={'count':0,'runningCount':0}#空后代计数

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 格式化令牌(值):#紧凑令牌数
    """与会话统计条同形的紧凑令牌数。"""
    def 缩放(下):#一位小数或整
        """>=100 取整，否则一位小数。"""
        if 下>=100:#整
            return str(round(下))#整
        return str(round(下*10)/10)#一位
    if 值<1000:#原样
        return str(值)#原样
    if 值<1000000:#千
        return 缩放(值/1000)+'K'#K
    return 缩放(值/1000000)+'M'#M

def 拆时长(毫秒):#拆时长部件
    """拆成秒分时天与合计。"""
    总秒=int(max(0,毫秒)//1000)#整秒
    总分=总秒//60#整分
    总时=总分//60#整时
    return {#部件
        'seconds':总秒%60,'minutes':总分%60,'hours':总时%24,'days':总时//24,
        'totalMinutes':总分,'totalHours':总时,
    }#结束

def 格式化时长(毫秒,翻译):#递减精度时长
    """随尺度降低视觉精度。"""
    部=拆时长(毫秒)#部件
    天=部['days']#天
    if 天>=365:#年
        年=天//365#年
        月=(天%365)//30#月
        if 月==0:#整年
            return 翻译('duration.years',{'years':年})#年
        return 翻译('duration.yearsMonths',{'years':年,'months':月})#年月
    if 天>=30:#月
        月=天//30#月
        余=天%30#余天
        if 余==0:#整月
            return 翻译('duration.months',{'months':月})#月
        return 翻译('duration.monthsDays',{'months':月,'days':余})#月天
    if 天>0:#天
        if 部['hours']==0:#整天
            return 翻译('duration.days',{'days':天})#天
        return 翻译('duration.daysHours',{'days':天,'hours':部['hours']})#天时
    if 部['totalHours']>0:#时
        return 翻译('duration.hours',{'hours':部['totalHours'],'minutes':str(部['minutes']).zfill(2),'seconds':str(部['seconds']).zfill(2)})#时分秒
    if 部['totalMinutes']>0:#分
        return 翻译('duration.minutes',{'minutes':部['totalMinutes'],'seconds':str(部['seconds']).zfill(2)})#分秒
    return 翻译('duration.seconds',{'seconds':部['seconds']})#秒

def 格式化精确时长(毫秒,翻译):#悬停精确时长
    """保留整秒；跨天走 exactDays。"""
    部=拆时长(毫秒)#部件
    if 部['days']==0:#未跨天
        return 格式化时长(毫秒,翻译)#同紧凑
    return 翻译('duration.exactDays',{'days':部['days'],'hours':str(部['hours']).zfill(2),'minutes':str(部['minutes']).zfill(2),'seconds':str(部['seconds']).zfill(2)})#精确

def 令牌合计(用量):#四桶合计
    """未缓存入+出+读缓存+写缓存。"""
    if 用量 is None:#无
        return None#缺席
    return (取字段(用量,'uncachedInputTokens',0)+取字段(用量,'outputTokens',0)
            +取字段(用量,'cacheReadTokens',0)+取字段(用量,'cacheWriteTokens',0))#合计

def 活动时长毫秒(摘要,活动,现在):#行活跃时长
    """整秒活跃时长；无 timing 则缺席。"""
    if 摘要 is None:#无
        return None#缺席
    投影=取字段(摘要,'projectionValues') or {}#投影
    计时=投影.get('subagentTiming') if isinstance(投影,dict) else 取字段(投影,'subagentTiming')#计时
    if 计时 is None:#无
        return None#缺席
    活跃=取字段(计时,'active')#活跃窗
    已结=取字段(计时,'settledMs',0) or 0#已结
    if 活跃 is None:#无活跃窗
        return 已结#已结
    if 活动=='running':#在跑
        止=现在#到现在
    else:#闲
        止=取字段(活跃,'through')#到 through
    return 已结+max(0,(止 or 0)-取字段(活跃,'since',0))#合计

def 诊断原因(条目,翻译):#诊断文案
    """corrupt/unsupported/unavailable。"""
    原因=取字段(条目,'reason')#原因
    if 原因=='corrupt':#损坏
        return 翻译('diagnostic.corrupt')#损坏
    if 原因=='unsupported':#不支持
        return 翻译('diagnostic.unsupported')#不支持
    return 翻译('diagnostic.unavailable')#不可用

class 目录动作:#会话头目录
    """当前会话直接目录与懒展开后代；无可见证据时渲染空。"""
    def __init__(自身,属性=None):#可选 props
        """记下 props 与开合态。"""
        自身.属性=属性 or {}#合成
        自身.打开=False#菜单开
        自身.现在=int(time.time()*1000)#时钟
        自身.已展开=set()#展开的子 id
        自身.观察中=set()#已 observe 的父

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 切换开合(自身):#触发器
        """翻转菜单；开时刷新时钟并 observe。"""
        下一=not 自身.打开#下一态
        自身.打开=下一#写入
        设开=取字段(自身.属性,'setCatalogOpen')#注入
        会话=取字段(自身.属性,'sessionId')#父会话
        if 下一:#开
            自身.现在=int(time.time()*1000)#刷新
            if callable(设开) and 会话 is not None:#observe
                设开(会话,True)#开
                自身.观察中.add(会话)#记
        else:#关
            自身.关闭全部()#关

    def 关闭全部(自身):#关全部观察
        """关掉已观察目录并清空展开。"""
        设开=取字段(自身.属性,'setCatalogOpen')#注入
        for 父 in list(自身.观察中):#逐个
            if callable(设开):#有
                设开(父,False)#关
        自身.观察中.clear()#清
        自身.已展开.clear()#清展开
        自身.打开=False#关菜单

    def 切换枝(自身,子标识):#展开/收起枝
        """展开则 observe；收起则关整枝。"""
        设开=取字段(自身.属性,'setCatalogOpen')#注入
        if 子标识 in 自身.已展开:#已展
            自身.已展开.discard(子标识)#收
            if callable(设开):#关
                设开(子标识,False)#关
            自身.观察中.discard(子标识)#摘
            return#已
        自身.已展开.add(子标识)#展
        if callable(设开):#开
            设开(子标识,True)#开
            自身.观察中.add(子标识)#记

    def 渲行(自身,目录,目录表,摘要表,层级,翻译):#渲一层
        """返回本层节点结构表。"""
        节点们=[]#节点
        条目们=取字段(目录,'entries') or []#条目
        空载=取字段(目录,'state')=='loading' and len(条目们)==0#空加载
        if 空载:#加载提示
            节点们.append({'type':'notice','text':翻译('loading.label')})#提示
        if 取字段(目录,'state')=='error':#错
            错=取字段(目录,'error')#错
            节点们.append({#错行
                'type':'error',
                'text':取字段(错,'message') if 错 else 翻译('load.error'),
                'retry':True,
            })#错结束
        预留=any(取字段(e,'kind')=='child' and 取字段(e,'hasChildren') for e in 条目们)#披露位
        for 条目 in 条目们:#逐条
            if 取字段(条目,'kind')=='diagnostic':#诊断
                因=诊断原因(条目,翻译)#原因
                节点们.append({#诊断行
                    'type':'diagnostic','id':取字段(条目,'id'),'reason':因,
                    'level':层级,'reserve':预留,'disabled':True,
                })#结束
                continue#下一条
            子标识=取字段(条目,'id')#子 id
            子目录=目录表.get(子标识) if isinstance(目录表,dict) else None#子目录
            已展=子标识 in 自身.已展开#展开
            叶=not 取字段(条目,'hasChildren')#叶
            摘要=摘要表.get(子标识) if isinstance(摘要表,dict) else None#摘要
            标签=取字段(条目,'label') or 子标识#标签
            模式=翻译('mode.oneShot') if 取字段(条目,'mode')=='one-shot' else 翻译('mode.continuable')#模式
            活动文=翻译('activity.running') if 取字段(条目,'activity')=='running' else 翻译('activity.inactive')#活动
            次要=' · '.join([x for x in [取字段(摘要,'title'),模式,活动文] if x])#次要
            令牌=令牌合计(取字段(取字段(摘要,'projectionValues'),'tokenUsage') if 摘要 else None)#令牌
            时长=活动时长毫秒(摘要,取字段(条目,'activity'),自身.现在)#时长
            令牌文=(格式化令牌(令牌)+' tok') if 令牌 is not None else None#令牌文
            时长文=None#时长文
            if 时长 is not None:#有
                时长文={'compact':格式化时长(时长,翻译),'exact':格式化精确时长(时长,翻译)}#双形
            子节点=None#子树
            if 已展 and not 叶:#展开枝
                if 子目录 is None:#仍加载
                    子节点=[{'type':'notice','text':翻译('loading.label')}]#加载
                else:#有目录
                    子节点=自身.渲行(子目录,目录表,摘要表,层级+1,翻译)#递归
            节点们.append({#子行
                'type':'child','id':子标识,'label':标签,'secondary':次要,
                'token':令牌文,'duration':时长文,'level':层级,'leaf':叶,
                'expanded':已展,'reserve':预留,'activity':取字段(条目,'activity'),
                'mode':取字段(条目,'mode'),'children':子节点,
            })#结束
        return 节点们#节点表

    def 渲染(自身):#结构树
        """无可见证据则 None。"""
        属性=自身.属性#props
        会话=取字段(属性,'sessionId')#会话
        用会话=取字段(属性,'useSessions')#选择器
        翻译=取字段(属性,'t') or (lambda 键,*_a,**_k:键)#文案
        if callable(用会话):#有会话钩
            目录表=用会话(lambda 态:取字段(态,'subagentsByParent') or {})#目录图
            摘要表=用会话(lambda 态:取字段(态,'byId') or {})#摘要图
        else:#注入快照
            目录表=取字段(属性,'catalogs') or {}#目录
            摘要表=取字段(属性,'summaries') or {}#摘要
        目录=目录表.get(会话) if isinstance(目录表,dict) else None#本会话目录
        健康=[e for e in (取字段(目录,'entries') or []) if 取字段(e,'kind')=='child']#健康子
        后代计数=max(len(健康),取字段(取字段(属性,'descendants'),'count',0) or 0)#后代
        运行数=取字段(取字段(属性,'descendants'),'runningCount',0) or 0#运行数
        摘要背载=(后代计数>0 and (目录 is None or (取字段(目录,'state')=='ready' and len(取字段(目录,'entries') or [])==0)))#摘要背载
        if 摘要背载:#合成加载目录
            呈现={'entries':[],'parentAvailable':取字段(目录,'parentAvailable',False) if 目录 else False,'state':'loading','error':None}#加载
        else:#原目录
            呈现=目录#原样
        可见=呈现 is not None and (取字段(呈现,'state')=='error' or len(取字段(呈现,'entries') or [])>0 or 后代计数>0)#可见
        if not 可见:#不可见
            return None#空
        总数键='count.total.one' if 后代计数==1 else 'count.total.other'#总数键
        return {#结构树
            'type':'subagent-catalog-action',#类型
            'open':自身.打开,#开合
            'countLabel':翻译(总数键,{'count':后代计数}),#计数
            'running':运行数>0,#有运行点
            'tree':自身.渲行(呈现,目录表,摘要表,1,翻译) if 自身.打开 else None,#树
            'css':样式表,#样式
            'toggle':自身.切换开合,#触发
            'toggleBranch':自身.切换枝,#枝
            'openChild':取字段(属性,'openChild'),#打开子
            'refresh':取字段(属性,'refresh'),#刷新
        }#结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷新
        return 自身.渲染()#渲
