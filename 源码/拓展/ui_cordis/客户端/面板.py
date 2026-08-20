"""Cordis 面板：清单、审批、版本与生命周期动作的嵌套 JSX 结构树。

对齐上游 `ui-cordis/src/client/CordisPanel.tsx`。公开面仅中文名。
DOM 嵌套与 class/data-* 来自上游；图标/Tooltip 半需浏览器。
无法 JS·vm 执行：真实按钮交互与侧栏挂载像素。
"""
import os#读样式
from .状态 import 可见状态,取包,取字段 as 状态取字段#状态面

__all__=['面板','选定包标识','面板可见状态','阻塞优先','样式表','渲染失败文案键','动作图标']#仅中文公开名

取字段=状态取字段#统一读字段

_本目录=os.path.dirname(os.path.abspath(__file__))#本目录
with open(os.path.join(_本目录,'面板.module.css'),'r',encoding='utf-8') as _样式文件:#原文
    样式表=_样式文件.read()#全文

状态文案键={#展示状态 → 词典键
    'idle':'status.idle',
    'awaiting-approval':'status.awaitingApproval',
    'client-pending':'status.clientPending',
    'running':'status.running',
    'failed':'status.failed',
}#结束

渲染失败文案键={#渲染崩溃 → 词典键
    'abdicated':'render.failedAbdicated',
    'held':'render.failedHeld',
}#结束

def 滤子(子们):#去掉 None
    """保留真值子节点。"""
    return [子 for 子 in 子们 if 子 is not None]#过滤

def 动作图标(种):#RowAction 子图标
    """对齐上游各动作按钮内图标。"""
    if 种=='approveOnce':#仅此版
        return {'type':'IconCheckOutline16','size':14}#勾
    if 种=='approvePlugin':#后续
        return {'type':'span','class':'doubleCheck','aria-hidden':True,'children':[#双勾
            {'type':'IconCheckOutline16','size':12},{'type':'IconCheckOutline16','size':12},
        ]}#结束
    if 种=='decline':#拒
        return {'type':'IconCloseOutline16','size':14}#叉
    if 种=='run':#跑
        return {'type':'IconPlayOutline16','size':14}#播放
    if 种=='stop':#停
        return {'type':'IconStopFill16','size':14}#停
    if 种=='remove':#移除
        return {'type':'IconTrashOutline16','size':14}#垃圾桶
    return None#未知

def 选定包标识(视图,已选):#解析当前选中包
    """已选仍在列表则用已选，否则 next/current/末包/活动包。"""
    插件=取字段(视图,'pluginId')#插件
    列=取字段(视图,'listed')#清单行
    活动=取字段(视图,'activity')#活动
    已=已选.get(插件) if isinstance(已选,dict) else None#已选
    if 已 is not None and 列 is not None:#校验仍在
        if any(取字段(p,'packageId')==已 for p in (取字段(列,'packages') or [])):#仍在
            return 已#已选
    if 列 is not None:#有清单
        return (取字段(列,'nextPackageId') or 取字段(列,'currentPackageId')
                or (取字段((取字段(列,'packages') or [None])[-1],'packageId') if 取字段(列,'packages') else None)
                or 取字段(活动,'packageId'))#回退链
    return 取字段(活动,'packageId')#仅活动

def 面板可见状态(视图,选中包,已加载):#面板状态
    """含 awaiting-approval / failed。"""
    列=取字段(视图,'listed')#清单
    活动=取字段(视图,'activity')#活动
    最近=取字段(列,'latestRun') if 列 else None#最近
    if 取字段(活动,'phase')=='awaiting-approval' or 取字段(最近,'status')=='awaiting-approval':#审批
        return 'awaiting-approval'#审批
    if 取字段(最近,'status')=='failed' and 取字段(最近,'packageId')==选中包:#失败
        return 'failed'#失败
    if 列 is None or 取字段(列,'activeRun') is None:#无激活
        return 'idle'#空闲
    return 可见状态(列,取字段(取字段(列,'activeRun'),'packageId'),已加载)#三态

def 阻塞优先(行们):#审批行置顶
    """awaiting-approval 在前。"""
    前=[r for r in 行们 if 取字段(取字段(r,'activity'),'phase')=='awaiting-approval']#审批
    后=[r for r in 行们 if 取字段(取字段(r,'activity'),'phase')!='awaiting-approval']#其余
    return 前+后#合并

def 组装行树(视,选中包,已加载,翻译,忙碌,失败图,渲染失败图,动作错误图):#一行 li 树
    """对齐 renderRow 的嵌套 JSX。"""
    列=取字段(视,'listed')#清单
    活动=取字段(视,'activity')#活动
    插件=取字段(视,'pluginId')#id
    选中包元=取包(列,选中包) if 列 is not None and 选中包 is not None else None#选中包
    活动包=取包(列,取字段(取字段(列,'activeRun'),'packageId')) if 列 is not None and 取字段(列,'activeRun') else None#活动包
    名=(取字段(选中包元,'name') if 选中包元 else None) or (取字段(活动,'name') if 取字段(活动,'phase')=='awaiting-approval' else 插件)#名
    用途=(取字段(选中包元,'purpose') if 选中包元 else None) or (取字段(活动,'purpose') if 取字段(活动,'phase')=='awaiting-approval' else '')#用途
    最近=取字段(列,'latestRun') if 列 else None#最近
    审批=(取字段(活动,'requestId') if 取字段(活动,'phase')=='awaiting-approval'
         else 取字段(最近,'approvalRequestId') if 取字段(最近,'status')=='awaiting-approval' else None)#审批 id
    态=面板可见状态(视,选中包,已加载)#状态
    忙=忙碌 or 取字段(活动,'phase')=='orchestrating'#忙
    失败=失败图.get(插件) if isinstance(失败图,dict) else None#页侧失败
    宿主失败=取字段(最近,'error') if 取字段(最近,'status')=='failed' else None#宿主失败
    渲染失败=渲染失败图.get(插件) if isinstance(渲染失败图,dict) else None#渲染崩溃
    动作错=动作错误图.get(插件) if isinstance(动作错误图,dict) else None#动作错
    下包=取字段(列,'nextPackageId') if 列 and 取字段(列,'nextPackageId')!=取字段(列,'currentPackageId') else None#待切换
    当前包=取字段(列,'currentPackageId') if 列 else None#当前
    模式='update' if 列 and 当前包 is not None and 选中包!=当前包 else 'run'#运行模式
    动作钮=[]#rowActions 子
    if 审批 is not None:#审批三键
        for 种,标,属 in (#种/文案键/data 属性
            ('approveOnce','action.approveOnce',{'data-cordis-approve':审批}),
            ('approvePlugin','action.approvePlugin',{'data-cordis-approve-plugin':审批}),
            ('decline','action.decline',{'data-cordis-decline':审批}),
        ):#三键
            钮={#RowAction → button
                'type':'button','class':'actionButton','aria-label':翻译(标),'disabled':忙,
                'onClick':('action',种,插件,审批),'children':[动作图标(种)],
            }#基
            钮.update(属)#data-*
            动作钮.append({'type':'Tooltip','label':翻译(标),'side':'bottom','delayMs':500,'children':[钮]})#Tooltip
    elif 列 is not None:#非审批生命周期
        if 选中包 is not None and 取字段(列,'activeRun') is None:#未跑
            钮={'type':'button','class':'actionButton','aria-label':翻译('action.run'),'disabled':忙,
                'data-cordis-switch':'run','onClick':('action','run',插件,选中包,模式,取字段(选中包元,'hasClientHalf') is True),
                'children':[动作图标('run')]}#跑
            动作钮.append({'type':'Tooltip','label':翻译('action.run'),'side':'bottom','delayMs':500,'children':[钮]})#Tooltip
        if 取字段(列,'activeRun') is not None and 选中包!=取字段(取字段(列,'activeRun'),'packageId') and 选中包元 is not None:#切包
            钮={'type':'button','class':'actionButton','aria-label':翻译('action.run'),'disabled':忙,
                'data-cordis-switch':'run','onClick':('action','run',插件,取字段(选中包元,'packageId'),模式,取字段(选中包元,'hasClientHalf')),
                'children':[动作图标('run')]}#跑
            动作钮.append({'type':'Tooltip','label':翻译('action.run'),'side':'bottom','delayMs':500,'children':[钮]})#Tooltip
        if (取字段(列,'activeRun') is not None and 态=='client-pending' and 活动包 is not None
            and 选中包==取字段(取字段(列,'activeRun'),'packageId')):#待客户端
            钮={'type':'button','class':'actionButton','aria-label':翻译('action.run'),'disabled':忙,
                'data-cordis-switch':'run','onClick':('action','run',插件,取字段(活动包,'packageId'),'run',True),
                'children':[动作图标('run')]}#再跑
            动作钮.append({'type':'Tooltip','label':翻译('action.run'),'side':'bottom','delayMs':500,'children':[钮]})#Tooltip
        if 取字段(列,'activeRun') is not None:#停止
            钮={'type':'button','class':'actionButton','aria-label':翻译('action.stop'),'disabled':忙,
                'data-cordis-switch':'stop','onClick':('action','stop',插件),
                'children':[动作图标('stop')]}#停
            动作钮.append({'type':'Tooltip','label':翻译('action.stop'),'side':'bottom','delayMs':500,'children':[钮]})#Tooltip
        钮={'type':'button','class':'actionButton','aria-label':翻译('action.remove'),'disabled':忙,
            'data-cordis-remove':插件,'onClick':('action','remove',插件),
            'children':[动作图标('remove')]}#移除
        动作钮.append({'type':'Tooltip','label':翻译('action.remove'),'side':'bottom','delayMs':500,'children':[钮]})#Tooltip
    行子=[{#rowHead
        'type':'div','class':'rowHead','children':[
            {'type':'span','class':'rowId','children':[插件]},#id
            {'type':'span','class':'rowName','children':[名]},#名
            {'type':'span','class':'rowStatus','children':[翻译(状态文案键.get(态,态))]},#状态
        ],
    }]#头
    if 列 is not None and len(取字段(列,'packages') or [])>1 and 选中包 is not None:#版本选择
        行子.append({'type':'label','class':'versionPicker','children':[#选择器
            {'type':'span','children':[翻译('panel.version')]},#标签
            {'type':'select','value':选中包,'disabled':忙,'onChange':('selectPackage',插件),
             'children':[{'type':'option','value':取字段(p,'packageId'),
                          'children':[f"{取字段(p,'name')} · {取字段(p,'packageId')}"]}
                         for p in (取字段(列,'packages') or [])]},#选项
        ]})#结束
    行子.append({'type':'div','class':'rowDetail','children':[#详情
        {'type':'span','class':'rowPurpose','children':[用途]},#用途
        {'type':'div','class':'rowActions','children':动作钮},#动作
    ]})#详情结束
    if 审批 is None and 下包 is not None and 列 is not None:#版本过渡
        过渡动作=[{#重试
            'type':'button','disabled':忙,'onClick':('action','retry',插件,下包,'run' if 当前包 is None else 'update',
                                                     取字段(取包(列,下包),'hasClientHalf') is True),
            'children':[翻译('action.retry')],
        }]#基
        if 当前包 is not None:#回退
            过渡动作.append({'type':'button','disabled':忙,
                             'onClick':('action','rollback',插件,当前包,'run',取字段(取包(列,当前包),'hasClientHalf') is True),
                             'children':[翻译('action.rollback')]})#回退
        行子.append({'type':'div','class':'transition','children':[#过渡
            {'type':'span','children':[翻译('panel.current',packageId=当前包) if 当前包 is not None else '']},#当前
            {'type':'span','children':[翻译('panel.next',packageId=下包)]},#待切换
            {'type':'div','class':'transitionActions','children':过渡动作},#钮
        ]})#过渡结束
    if 失败 is not None:#页侧失败
        行子.append({'type':'div','class':'rowError','role':'alert',
                     'children':[f"{取字段(失败,'message')} ({取字段(失败,'reason')})"]})#错
    if 失败 is None and 宿主失败 is not None:#宿主失败
        行子.append({'type':'div','class':'rowError','role':'alert',
                     'children':[f"{取字段(宿主失败,'message')} ({取字段(宿主失败,'phase')})"]})#错
    if 动作错 is not None:#动作错
        行子.append({'type':'div','class':'rowError','role':'alert','children':[动作错]})#错
    if 渲染失败 is not None:#渲染崩溃
        键=渲染失败文案键['abdicated' if 取字段(渲染失败,'abdicated') else 'held']#键
        行子.append({'type':'div','class':'rowError','role':'alert',
                     'data-cordis-render-failure':取字段(渲染失败,'slot'),
                     'data-cordis-render-abdicated':取字段(渲染失败,'abdicated') or None,
                     'children':[f"{翻译(键,slot=取字段(渲染失败,'slot'))} {取字段(渲染失败,'message')}"]})#错
    if 活动包 is not None and 取字段(活动包,'packageId')!=选中包:#活动版提示
        行子.append({'type':'span','class':'activeVersion',
                     'children':[f"{翻译('status.running')}: {取字段(活动包,'name')} · {取字段(活动包,'packageId')}"]})#提示
    return {#li
        'type':'li','key':插件,'class':'row','data-cordis-row':插件,
        'data-cordis-status':态,'data-cordis-awaiting':审批 is not None or None,
        'children':行子,
    }#结束

class 面板:#Cordis 侧栏面板
    """组装可见行与触发器嵌套 JSX 树。"""
    def __init__(自身,属性=None):#可选 props
        """记下 props 与开合。"""
        自身.属性=属性 or {}#合成
        自身.打开=False#面板开
        自身.已选={}#插件 → 包
        自身.忙碌=set()#进行中的动作
        自身.动作错误={}#插件 → 消息
        自身.已见表批=set()#见过的审批 id

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 选版本(自身,插件,包):#改选
        """写入已选。"""
        自身.已选={**自身.已选,插件:包}#合并

    def 切换(自身):#开合
        """翻转面板。"""
        自身.打开=not 自身.打开#翻
        刷新=取字段(自身.属性,'onRefresh')#刷新
        if 自身.打开 and callable(刷新):#开时
            刷新()#拉清单

    def 渲染(自身):#结构树
        """产出面板嵌套 JSX 树。"""
        p=自身.属性#props
        def 翻译(键,**参数):#文案
            """带插值。"""
            基=(取字段(p,'t') or (lambda k,**_k:k))(键)#取句
            if not 参数:#无参
                return 基#原
            出=基#模板
            for 名,值 in 参数.items():#逐个
                出=出.replace('{'+名+'}',str(值))#替换
            return 出#句
        宽=bool(取字段(p,'wide',True))#宽
        清单钩=取字段(p,'useInventory')#清单
        活动钩=取字段(p,'useActiveRuns')#活动
        加载钩=取字段(p,'useLoaded')#已加载
        失败钩=取字段(p,'useRunErrors')#失败
        渲钩=取字段(p,'useRenderFailures')#渲染失败
        会话钩=取字段(p,'useSessions')#会话
        if callable(清单钩):#有
            清单=清单钩(lambda s:s)#快照
        else:#直读
            清单=取字段(p,'inventory') or {'rows':[],'read':False}#缺省
        if callable(活动钩):#有
            活动图=活动钩(lambda s:s) or {}#图
        else:#直读
            活动图=取字段(p,'activeRuns') or {}#图
        if callable(加载钩):#有
            已加载=加载钩(lambda s:s) or []#表
        else:#直读
            已加载=取字段(p,'loaded') or []#表
        if callable(失败钩):#有
            失败图=失败钩(lambda s:s) or {}#图
        else:#直读
            失败图=取字段(p,'runErrors') or {}#图
        if callable(渲钩):#有
            渲图=渲钩(lambda s:s) or {}#图
        else:#直读
            渲图=取字段(p,'renderFailures') or {}#图
        if callable(会话钩):#有
            当前=取字段(会话钩(lambda s:s),'current')#当前会话
        else:#直读
            当前=取字段(p,'currentSession')#会话
        if hasattr(活动图,'items'):#映射
            活动项=list(活动图.items())#项
        elif isinstance(活动图,dict):#dict
            活动项=list(活动图.items())#项
        else:#空
            活动项=[]#空
        按插件={}#聚合
        for 列 in 取字段(清单,'rows') or []:#清单行
            标识=取字段(列,'pluginId')#id
            活动=活动图.get(标识) if isinstance(活动图,dict) else None#活动
            按插件[标识]={'pluginId':标识,'agentId':取字段(活动,'agentId') or 取字段(列,'agentId'),'listed':列,**({'activity':活动} if 活动 else {})}#行
        for 标识,活动 in 活动项:#仅活动
            if 标识 in 按插件:#已有
                continue#跳
            按插件[标识]={'pluginId':标识,'agentId':取字段(活动,'agentId'),'activity':活动}#行
        全部=list(按插件.values())#全部
        本组=阻塞优先([r for r in 全部 if 当前 is not None and 取字段(r,'agentId')==当前])#本会话
        他组=阻塞优先([r for r in 全部 if 当前 is None or 取字段(r,'agentId')!=当前])#他会话
        审批数=sum(1 for _,活动 in 活动项 if 取字段(活动,'phase')=='awaiting-approval')#审批数
        运行数=sum(1 for r in 全部 if 面板可见状态(r,选定包标识(r,自身.已选),已加载)=='running')#运行数
        现批=set()#现审批
        for _,活动 in 活动项:#逐个
            if 取字段(活动,'phase')=='awaiting-approval':#审批
                现批.add(取字段(活动,'requestId'))#收入
        if any(批 not in 自身.已见表批 for 批 in 现批):#发现新
            自身.打开=True#打开
        自身.已见表批=现批#更新
        失败映射=失败图 if isinstance(失败图,dict) else dict(失败图) if hasattr(失败图,'items') else {}#图
        渲映射=渲图 if isinstance(渲图,dict) else dict(渲图) if hasattr(渲图,'items') else {}#图
        def 渲组(行们):#组内 li 列表
            """组装行树列表。"""
            return [组装行树(#li
                视,选定包标识(视,自身.已选),已加载,翻译,取字段(视,'pluginId') in 自身.忙碌,
                失败映射,渲映射,自身.动作错误,
            ) for 视 in 行们]#列表
        if len(全部)==0:#空则不渲染（对齐上游 return null）
            return {'type':None,'visible':False,'css':样式表,'note':'无插件时上游 return null'}#隐藏
        体子=滤子([#panel body
            {'type':'p','class':'readError','role':'alert',
             'children':[翻译('panel.readFailed',message=取字段(清单,'error'))]} if 取字段(清单,'error') else None,#读失败
            {'type':'p','class':'note','children':[翻译('panel.loading')]}
            if not 取字段(清单,'read',False) and 取字段(清单,'error') is None else None,#加载中
            {'type':'p','class':'note','children':[翻译('panel.empty')]}
            if 取字段(清单,'read',False) and len(全部)==0 else None,#空
            {'type':'section','children':[#本组
                {'type':'h3','class':'group','children':[翻译('panel.group.current')]},#标题
                {'type':'ul','class':'rows','children':渲组(本组)},#行
            ]} if len(本组)>0 else None,#本组
            {'type':'section','children':[#他组
                {'type':'h3','class':'group','children':[翻译('panel.group.others')]},#标题
                {'type':'ul','class':'rows','children':渲组(他组)},#行
            ]} if len(他组)>0 else None,#他组
        ])#体子结束
        徽子=[{'type':'IconCordisPluginOutline14'}]#徽标子
        if 宽:#宽栏示文案
            徽子.extend([#标签+计数
                {'type':'span','class':'badgeLabel','children':[翻译('panel.trigger')]},#触发
                {'type':'span','class':'badgeCount','children':[翻译('panel.runningCount',count=运行数)]},#计数
            ])#结束
        层子=滤子([#layer 子
            {'type':'section','class':'panel','data-cordis-panel':True,'aria-label':翻译('panel.title'),
             'children':[#开时面板
                {'type':'header','class':'header','children':[
                    {'type':'span','class':'title','children':[翻译('panel.title')]},#标题
                ]},#头
                {'type':'div','class':'body','children':体子},#体
            ]} if 自身.打开 else None,#面板
            {'type':'div','class':'footerButtons','children':[#底钮
                {'type':'button','class':'badge','data-cordis-badge':len(全部),
                 'data-cordis-approval-badge':审批数,'data-active':审批数>0 or None,
                 'aria-label':翻译('panel.plugins.aria'),'aria-expanded':自身.打开,
                 'onClick':'toggle','children':徽子},#徽标钮
            ]},#底
        ])#层子结束
        return {#根 layer
            'type':'div','class':'layer' if 宽 else 'layer rail','visible':True,
            'children':层子,'css':样式表,
            'handlers':{'toggle':自身.切换,'selectPackage':自身.选版本},#动作
            'note':'图标/Tooltip/真实按钮 DOM 需浏览器；无法 Python·vm 执行侧栏像素',#缺口
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷新
        return 自身.渲染()#渲
