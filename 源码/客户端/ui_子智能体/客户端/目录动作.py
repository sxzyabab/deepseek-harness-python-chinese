from nicegui import ui as 界面
from ....基础设施.通用工具 import 当前毫秒
from ...ui_基础界面组件.状态点 import 状态点
from ..异常 import 页面失败文案

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
界面.add_css(样式表,shared=True)

def 格式化令牌(值):#紧凑令牌数
    '与会话统计条同形的紧凑令牌数'
    def 缩放(下):#一位小数或整
        '>=100 取整，否则一位小数'
        if 下>=100:#整
            return str(round(下))#整
        return str(round(下*10)/10)#一位
    if 值<1000:#原样
        return str(值)#原样
    if 值<1000000:#千
        return 缩放(值/1000)+'K'#K
    return 缩放(值/1000000)+'M'#M

def 拆时长(毫秒):#拆时长部件
    '拆成秒分时天与合计'
    总秒=int(max(0,毫秒)//1000)#整秒
    总分=总秒//60#整分
    总时=总分//60#整时
    return {#部件
        'seconds':总秒%60,'minutes':总分%60,'hours':总时%24,'days':总时//24,
        'totalMinutes':总分,'totalHours':总时,
    }#结束

def 格式化时长(毫秒,翻译):#递减精度时长
    '随尺度降低视觉精度'
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
    '保留整秒；跨天走 exactDays'
    部=拆时长(毫秒)#部件
    if 部['days']==0:#未跨天
        return 格式化时长(毫秒,翻译)#同紧凑
    return 翻译('duration.exactDays',{'days':部['days'],'hours':str(部['hours']).zfill(2),'minutes':str(部['minutes']).zfill(2),'seconds':str(部['seconds']).zfill(2)})#精确

def 令牌合计(用量):#四桶合计
    '未缓存入+出+读缓存+写缓存'
    if 用量 is None:#无
        return None#缺席
    未缓存=用量['uncachedInputTokens'] if 'uncachedInputTokens' in 用量 and 用量['uncachedInputTokens'] is not None else 0#未缓存入
    输出=用量['outputTokens'] if 'outputTokens' in 用量 and 用量['outputTokens'] is not None else 0#出
    读缓存=用量['cacheReadTokens'] if 'cacheReadTokens' in 用量 and 用量['cacheReadTokens'] is not None else 0#读缓存
    写缓存=用量['cacheWriteTokens'] if 'cacheWriteTokens' in 用量 and 用量['cacheWriteTokens'] is not None else 0#写缓存
    return 未缓存+输出+读缓存+写缓存#合计

def 活动时长毫秒(摘要,活动,现在):#行活跃时长
    '整秒活跃时长；无 timing 则缺席'
    if 摘要 is None:#无
        return None#缺席
    投影=摘要['projectionValues'] if 'projectionValues' in 摘要 and 摘要['projectionValues'] is not None else {}#投影
    计时=投影['subagentTiming'] if 'subagentTiming' in 投影 else None#计时
    if 计时 is None:#无
        return None#缺席
    活跃=计时['active'] if 'active' in 计时 else None#活跃窗
    已结=计时['settledMs'] if 'settledMs' in 计时 and 计时['settledMs'] is not None else 0#已结
    if 活跃 is None:#无活跃窗
        return 已结#已结
    if 活动=='running':#在跑
        止=现在#到现在
    else:#闲
        止=活跃['through'] if 'through' in 活跃 else None#到 through
    起点=活跃['since'] if 'since' in 活跃 and 活跃['since'] is not None else 0#自
    止值=0 if 止 is None else 止#缺 through 当 0
    return 已结+max(0,止值-起点)#合计

def 诊断原因(条目,翻译):#诊断文案
    'corrupt/unsupported/unavailable'
    原因=条目['reason'] if 'reason' in 条目 else None#原因
    if 原因=='corrupt':#损坏
        return 翻译('diagnostic.corrupt')#损坏
    if 原因=='unsupported':#不支持
        return 翻译('diagnostic.unsupported')#不支持
    return 翻译('diagnostic.unavailable')#不可用

class 目录动作:#会话头目录
    '当前会话直接目录与懒展开后代；无可见证据时渲染空'
    def __init__(自身,属性=None):#可选 props
        '记下 props 与开合态'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.打开=False#菜单开
        自身.现在=当前毫秒()#纪元毫秒
        自身.已展开=set()#展开的子 id
        自身.观察中=set()#已 observe 的父
        自身.画面失败=None
        if isinstance(自身.属性,dict) and 't' in 自身.属性:
            自身.渲染()#槽位只调用构造，键齐了就画

    def 更新(自身,属性):#刷新
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 切换开合(自身):#触发器
        '翻转菜单；开时刷新时钟并 observe'
        下一=not 自身.打开#下一态
        自身.打开=下一#写入
        设开=自身.属性['setCatalogOpen'] if 'setCatalogOpen' in 自身.属性 else None#注入
        已记=自身.目录根 if hasattr(自身,'目录根') else None#谱系用父会话
        会话=已记 if 已记 is not None else (自身.属性['sessionId'] if 'sessionId' in 自身.属性 else None)#父会话
        if 下一:
            自身.现在=当前毫秒()#刷新
            if 设开 is not None and 会话 is not None:#observe
                设开(会话,True)
                自身.观察中.add(会话)#记
        else:#关
            自身.关闭全部()#关
        自身.渲染()#开合后重画

    def 关闭全部(自身):#关全部观察
        '关掉已观察目录并清空展开'
        设开=自身.属性['setCatalogOpen'] if 'setCatalogOpen' in 自身.属性 else None#注入
        for 父 in list(自身.观察中):#逐个
            if 设开 is not None:
                设开(父,False)#关
        自身.观察中.clear()
        自身.已展开.clear()#清展开
        自身.打开=False#关菜单

    def 切换枝(自身,子标识):#展开/收起枝
        '展开则 observe；收起则关整枝'
        设开=自身.属性['setCatalogOpen'] if 'setCatalogOpen' in 自身.属性 else None#注入
        if 子标识 in 自身.已展开:#已展
            自身.已展开.discard(子标识)#收
            if 设开 is not None:#关
                设开(子标识,False)#关
            自身.观察中.discard(子标识)#摘
            自身.渲染()#收起后重画
            return#已
        自身.已展开.add(子标识)#展
        if 设开 is not None:
            设开(子标识,True)
            自身.观察中.add(子标识)#记
        自身.渲染()#展开后重画

    def _安放(自身,界面):
        '复用根，避免开合再叠一层'
        旧=getattr(自身,'根',None)
        if 旧 is not None:
            try:
                旧.clear()
                return 旧
            except Exception as 错误:
                自身.根=None
                自身.画面失败=页面失败文案(错误)
        自身.根=界面.column().classes('subagent-catalog')
        return 自身.根

    def 渲行(自身,目录,目录表,摘要表,层级,翻译):#渲一层
        '返回本层节点结构表'
        节点列表=[]#节点
        条目表=目录['entries'] if 目录 is not None and 'entries' in 目录 and 目录['entries'] is not None else []#条目；空列表保留
        态=目录['state'] if 目录 is not None and 'state' in 目录 else None#态
        空载=态=='loading' and len(条目表)==0#空加载；判的是 length
        if 空载:#加载提示
            节点列表.append({'type':'notice','text':翻译('loading.label')})#提示
        if 态=='error':#错
            错=目录['error'] if 'error' in 目录 else None#错
            节点列表.append({#错行
                'type':'error',
                'text':(页面失败文案(错['message']) if 错 is not None and 'message' in 错 and 错['message'] is not None else 翻译('load.error')),
                'retry':True,
            })#错结束
        预留=False#披露位
        for 候 in 条目表:#扫
            if ('kind' in 候 and 候['kind']=='child' and 'hasChildren' in 候 and 候['hasChildren'] is True):#有子
                预留=True#预留
                break
        for 条目 in 条目表:#逐条
            if 'kind' in 条目 and 条目['kind']=='diagnostic':#诊断
                因=诊断原因(条目,翻译)#原因
                节点列表.append({#诊断行
                    'type':'diagnostic','id':条目['id'] if 'id' in 条目 else None,'reason':因,
                    'level':层级,'reserve':预留,'disabled':True,
                })#结束
                continue#下一条
            子标识=条目['id'] if 'id' in 条目 else None#子 id
            子目录=目录表[子标识] if 子标识 in 目录表 else None#子目录
            已展=子标识 in 自身.已展开#展开
            叶=not ('hasChildren' in 条目 and 条目['hasChildren'] is True)#叶
            摘要=摘要表[子标识] if 子标识 in 摘要表 else None#摘要
            标签=条目['label'] if 'label' in 条目 and 条目['label'] is not None else 子标识#标签
            模式值=条目['mode'] if 'mode' in 条目 else None#模式值
            if 模式值=='one-shot':#一次性
                模式=翻译('mode.oneShot')#一次性
            elif 模式值=='unknown':#未知
                模式=翻译('mode.unknown')#未知
            elif 模式值=='continuable':#可继续
                模式=翻译('mode.continuable')#可继续
            else:#线路字面量，例如 external
                模式=模式值 if isinstance(模式值,str) else 翻译('mode.continuable')#原样
            活动=条目['activity'] if 'activity' in 条目 else None#活动
            投影预=摘要['projectionValues'] if 摘要 is not None and 'projectionValues' in 摘要 else None#投影
            计时预=投影预['subagentTiming'] if isinstance(投影预,dict) and 'subagentTiming' in 投影预 and isinstance(投影预['subagentTiming'],dict) else None#计时
            已完成=活动=='inactive' and 计时预 is not None and 计时预.get('lastTurnCompleted') is True#末轮已结束
            if 活动=='running':#在跑
                活动文=翻译('activity.running')#在跑
            elif 已完成:#已停且末轮结束
                活动文=翻译('activity.completed')#已停
            else:#闲
                活动文=翻译('activity.inactive')#闲
            标题=摘要['title'] if 摘要 is not None and 'title' in 摘要 else None#标题
            次要段=[]#次要
            if 标题 is not None and 标题!='':#有标题
                次要段.append(标题)#收
            次要段.append(模式)#模式
            次要段.append(活动文)#活动
            次要=' · '.join(次要段)#次要
            投影值=摘要['projectionValues'] if 摘要 is not None and 'projectionValues' in 摘要 else None#投影
            用量=投影值['tokenUsage'] if 投影值 is not None and 'tokenUsage' in 投影值 else None#用量
            令牌=令牌合计(用量)#令牌
            时长=活动时长毫秒(摘要,活动,自身.现在)#时长
            令牌文=翻译('tokens.total',{'value':格式化令牌(令牌)}) if 令牌 is not None else None#令牌文
            时长文=None#时长文
            if 时长 is not None:
                时长文={'compact':格式化时长(时长,翻译),'exact':格式化精确时长(时长,翻译)}#双形
            子节点=None#子树
            if 已展 and not 叶:#展开枝
                if 子目录 is None:#仍加载
                    子节点=[{'type':'notice','text':翻译('loading.label')}]#加载
                else:#有目录
                    子节点=自身.渲行(子目录,目录表,摘要表,层级+1,翻译)#递归
            节点列表.append({#子行
                'type':'child','id':子标识,'label':标签,'secondary':次要,
                'token':令牌文,'duration':时长文,'level':层级,'leaf':叶,
                'expanded':已展,'reserve':预留,'activity':活动,
                'mode':条目['mode'] if 'mode' in 条目 else None,'children':子节点,
            })#结束
        return 节点列表#节点表

    def 取目录表(自身,态):#从会话快照取目录图
        'subagentsByParent；缺键当空 dict'
        return 态['subagentsByParent'] if 'subagentsByParent' in 态 and 态['subagentsByParent'] is not None else {}#目录图

    def 取摘要表(自身,态):#从会话快照取摘要图
        'byId；缺键当空 dict'
        return 态['byId'] if 'byId' in 态 and 态['byId'] is not None else {}#摘要图

    def _解析父(自身,谱系,用会话):
        '面包屑上这一级的父会话'
        用本=自身.属性['useSession'] if 'useSession' in 自身.属性 else None
        if callable(用本):
            本=用本(lambda 值:值)
            子=本['subagent'] if isinstance(本,dict) and 'subagent' in 本 and isinstance(本['subagent'],dict) else None
            地址=子['address'] if 子 is not None and 'address' in 子 and isinstance(子['address'],dict) else None
            if 地址 is not None and 地址.get('childSessionId')==谱系 and 'parentSessionId' in 地址:
                return 地址['parentSessionId']
        if not callable(用会话):
            return None
        def 选父(快照,钉=谱系):
            '在目录图里找父'
            if not isinstance(快照,dict):
                return None
            图=快照['subagentsByParent'] if 'subagentsByParent' in 快照 and isinstance(快照['subagentsByParent'],dict) else {}
            for 父,目录 in 图.items():
                条目=目录['entries'] if isinstance(目录,dict) and 'entries' in 目录 and isinstance(目录['entries'],list) else []
                for 候 in 条目:
                    if isinstance(候,dict) and 候.get('id')==钉:
                        return 父
            摘要=快照['byId'][钉] if 'byId' in 快照 and isinstance(快照['byId'],dict) and 钉 in 快照['byId'] else None
            if isinstance(摘要,dict) and 摘要.get('origin')=='subagent' and 'parentId' in 摘要:
                return 摘要['parentId']
            return None
        return 用会话(选父)

    def 渲染(自身):#结构树
        '无可见证据则不画'
        属性=自身.属性#props
        if 't' not in 属性:#槽位还没给文案
            return#不画
        用会话=属性['useSessions'] if 'useSessions' in 属性 else None#选择器
        翻译=属性['t']#文案
        变体='count'#计数
        开关标题=None#切换器标题
        if 'lineageSessionId' in 属性:#谱系槽
            变体='switcher'#切换器
            开关标题=属性['displayTitle'] if 'displayTitle' in 属性 and isinstance(属性['displayTitle'],str) else ''#标题
            会话=自身._解析父(属性['lineageSessionId'],用会话)#父会话
            自身.目录根=会话#开合时观察这一级
            if 会话 is None:#根会话不画面包屑
                return#不画
        else:#目录动作槽
            if callable(用会话) and 'sessionId' in 属性:
                def 选起源(快照,钉=属性['sessionId']):
                    '子会话把目录让给谱系'
                    行=快照['byId'][钉] if isinstance(快照,dict) and 'byId' in 快照 and isinstance(快照['byId'],dict) and 钉 in 快照['byId'] else None
                    return 行['origin'] if isinstance(行,dict) and 'origin' in 行 else None
                if 用会话(选起源)=='subagent':#子会话
                    return#不画
            会话=属性['sessionId'] if 'sessionId' in 属性 else None#会话
            自身.目录根=会话#开合时观察这一级
        if 用会话 is not None:#有会话钩
            目录表=用会话(自身.取目录表)#目录图
            摘要表=用会话(自身.取摘要表)#摘要图
        else:#注入快照
            目录表=属性['catalogs'] if 'catalogs' in 属性 and 属性['catalogs'] is not None else {}#目录
            摘要表=属性['summaries'] if 'summaries' in 属性 and 属性['summaries'] is not None else {}#摘要
        目录=目录表[会话] if 会话 in 目录表 else None#本会话目录
        条目表=目录['entries'] if 目录 is not None and 'entries' in 目录 and 目录['entries'] is not None else []#条目；空列表保留
        健康=[e for e in 条目表 if 'kind' in e and e['kind']=='child']#健康子
        后代=属性['descendants'] if 'descendants' in 属性 else None#后代
        计=后代['count'] if 后代 is not None and 'count' in 后代 and 后代['count'] is not None else 0#计数
        后代计数=max(len(健康),计)#后代；判的是 length
        运行数=后代['runningCount'] if 后代 is not None and 'runningCount' in 后代 and 后代['runningCount'] is not None else 0#运行数
        目录态=目录['state'] if 目录 is not None and 'state' in 目录 else None#态
        摘要背载=(后代计数>0 and (目录 is None or (目录态=='ready' and len(条目表)==0)))#摘要背载
        if 摘要背载:#合成加载目录
            父可用=目录['parentAvailable'] is True if 目录 is not None and 'parentAvailable' in 目录 else False#父可用
            呈现={'entries':[],'parentAvailable':父可用,'state':'loading','error':None}#加载
        else:#原目录
            呈现=目录#原样
        呈现态=呈现['state'] if 呈现 is not None and 'state' in 呈现 else None#呈现态
        呈现条目=呈现['entries'] if 呈现 is not None and 'entries' in 呈现 and 呈现['entries'] is not None else []#呈现条目
        可见=呈现 is not None and (呈现态=='error' or len(呈现条目)>0 or 后代计数>0)#可见；判的是 length
        if not 可见:#不可见
            旧=getattr(自身,'根',None)
            if 旧 is not None:
                try:
                    旧.clear()
                except Exception as 错误:
                    自身.根=None
                    自身.画面失败=页面失败文案(错误)
            return#空
        总数键='count.total.one' if 后代计数==1 else 'count.total.other'#总数键
        def 画节点(节点列表):
            '画出目录节点'
            for 节点 in 节点列表:
                if not isinstance(节点,dict):
                    continue
                种类=节点['type'] if 'type' in 节点 else ''
                if 种类=='notice' and 'text' in 节点 and isinstance(节点['text'],str) and 节点['text']!='':
                    界面.label(节点['text']).classes('notice')
                elif 种类=='error':
                    错文=节点['text'] if 'text' in 节点 and isinstance(节点['text'],str) else ''
                    with 界面.row().classes('error'):
                        if 错文!='':
                            界面.label(错文)
                        if 节点.get('retry') is True:
                            def 重试():
                                '重新拉取本会话目录'
                                刷新=属性['refreshProjection'] if 'refreshProjection' in 属性 else None
                                if 刷新 is not None and 会话 is not None:
                                    刷新(会话)
                            界面.button(翻译('retry'), on_click=重试).classes('refresh')
                elif 种类=='diagnostic':
                    因=节点['reason'] if 'reason' in 节点 and isinstance(节点['reason'],str) else ''
                    if 因!='':
                        界面.label(因).classes('notice')
                elif 种类=='child':
                    标识=节点['id'] if 'id' in 节点 else None
                    with 界面.column().classes('node'):
                        with 界面.row().classes('row'):
                            if 节点.get('activity')=='running':
                                状态点({'state':'ongoing','size':10}).渲染()
                            if 节点.get('leaf') is not True:
                                def 展(钉=标识):
                                    '展开或收起这一枝'
                                    if 钉 is not None:
                                        自身.切换枝(钉)
                                界面.button('›', on_click=展).props('flat dense').classes('disclosure')
                            def 开(钉=标识):
                                '打开该子会话'
                                回调=属性['openChild'] if 'openChild' in 属性 else None
                                if 回调 is not None and 钉 is not None:
                                    回调(钉)
                                    自身.关闭全部()
                                    自身.渲染()
                            文=节点['label'] if 'label' in 节点 and isinstance(节点['label'],str) else ''
                            with 界面.column().classes('content'):
                                if 文!='':
                                    界面.button(文, on_click=开).props('flat no-caps align=left').classes('label')
                                次=节点['secondary'] if 'secondary' in 节点 and isinstance(节点['secondary'],str) else ''
                                if 次!='':
                                    界面.label(次).classes('summary')
                            令牌文=节点['token'] if 'token' in 节点 and isinstance(节点['token'],str) else ''
                            时长=节点['duration'] if 'duration' in 节点 and isinstance(节点['duration'],dict) else None
                            时长文=时长['compact'] if 时长 is not None and 'compact' in 时长 and isinstance(时长['compact'],str) else ''
                            if 令牌文!='' or 时长文!='':
                                with 界面.column().classes('metrics'):
                                    if 令牌文!='':
                                        界面.label(令牌文)
                                    if 时长文!='':
                                        界面.label(时长文)
                            旁开=属性['openChildAside'] if 'openChildAside' in 属性 else None
                            if 旁开 is not None and 标识 is not None:
                                def 旁(钉=标识):
                                    '在侧栏打开该子会话'
                                    旁开(钉)
                                    自身.关闭全部()
                                    自身.渲染()
                                界面.button(翻译('open.sidebar'), on_click=旁).props('flat dense no-caps')
                        if 'children' in 节点 and isinstance(节点['children'],list) and len(节点['children'])>0:
                            with 界面.column().classes('children'):
                                画节点(节点['children'])
                elif 'children' in 节点 and isinstance(节点['children'],list) and len(节点['children'])>0:
                    画节点(节点['children'])
        with 自身._安放(界面):
            if isinstance(自身.画面失败,str) and 自身.画面失败!='':
                界面.label(自身.画面失败).classes('error')
                自身.画面失败=None
            if 变体=='switcher':
                界面.button(开关标题 if isinstance(开关标题,str) and 开关标题!='' else 翻译('sidebar.chat'), on_click=自身.切换开合).props('flat no-caps icon-right=expand_more')
            else:
                with 界面.row().classes('trigger'):
                    if 运行数>0:
                        状态点({'state':'ongoing','size':10}).渲染()
                    界面.button(翻译(总数键,{'count':后代计数}), on_click=自身.切换开合).props('flat no-caps icon-right=expand_more')
            if 自身.打开:
                画节点(自身.渲行(呈现,目录表,摘要表,1,翻译))

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 组件调用'
        if 属性 is not None:
            自身.更新(属性)#刷新
        return 自身.渲染()
