import os
from ..异常 import 页面失败文案
from .状态 import 可见状态,取包
from .准备行 import 画出根

__all__=['面板','选定包标识','面板可见状态','阻塞优先','样式表','渲染失败文案键','动作图标']#仅中文公开名

_本目录=os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_本目录,'面板.module.css'),'r',encoding='utf-8') as _样式文件:
    样式表=_样式文件.read()

状态文案键={#展示状态 → 词典键
    'idle':'status.idle',
    'awaiting-approval':'status.awaitingApproval',
    'client-pending':'status.clientPending',
    'running':'status.running',
    'failed':'status.failed',
}

渲染失败文案键={#渲染崩溃 → 词典键
    'abdicated':'render.failedAbdicated',
    'held':'render.failedHeld',
}

def 去掉空子节点(子节点列表):
    '保留真值子节点'
    return [子 for 子 in 子节点列表 if 子 is not None]

def 动作图标(种):
    '各动作按钮内图标'
    if 种=='approveOnce':
        return {'type':'IconCheckOutline16','size':14}
    if 种=='approvePlugin':
        return {'type':'span','class':'doubleCheck','aria-hidden':True,'children':[
            {'type':'IconCheckOutline16','size':12},{'type':'IconCheckOutline16','size':12},
        ]}
    if 种=='decline':
        return {'type':'IconCloseOutline16','size':14}
    if 种=='run':
        return {'type':'IconPlayOutline16','size':14}
    if 种=='stop':
        return {'type':'IconStopFill16','size':14}
    if 种=='remove':
        return {'type':'IconTrashOutline16','size':14}
    return None

def 选定包标识(视图,已选):#解析当前选中包
    '已选仍在列表则用已选，否则 next/current/末包/活动包'
    插件=视图['pluginId'] if 'pluginId' in 视图 else None
    列=视图['listed'] if 'listed' in 视图 else None
    活动=视图['activity'] if 'activity' in 视图 else None
    已=已选.get(插件) if isinstance(已选,dict) else None
    if 已 is not None and 列 is not None:
        包列表=列['packages'] if 'packages' in 列 else None
        if any((p['packageId'] if p is not None and 'packageId' in p else None)==已 for p in (包列表 or [])):
            return 已
    if 列 is not None:
        下一=列['nextPackageId'] if 'nextPackageId' in 列 else None
        当前=列['currentPackageId'] if 'currentPackageId' in 列 else None
        包列表=列['packages'] if 'packages' in 列 else None
        末包=None
        if 包列表:
            尾=包列表[-1]
            末包=尾['packageId'] if 尾 is not None and 'packageId' in 尾 else None
        活动包=活动['packageId'] if 活动 is not None and 'packageId' in 活动 else None
        return 下一 or 当前 or 末包 or 活动包
    return 活动['packageId'] if 活动 is not None and 'packageId' in 活动 else None

def 面板可见状态(视图,选中包,已加载):
    '含 awaiting-approval / failed'
    列=视图['listed'] if 'listed' in 视图 else None
    活动=视图['activity'] if 'activity' in 视图 else None
    最近=列['latestRun'] if 列 is not None and 'latestRun' in 列 else None
    活动阶段=活动['phase'] if 活动 is not None and 'phase' in 活动 else None
    最近状态=最近['status'] if 最近 is not None and 'status' in 最近 else None
    if 活动阶段=='awaiting-approval' or 最近状态=='awaiting-approval':
        return 'awaiting-approval'
    最近包=最近['packageId'] if 最近 is not None and 'packageId' in 最近 else None
    if 最近状态=='failed' and 最近包==选中包:
        return 'failed'
    激活=列['activeRun'] if 列 is not None and 'activeRun' in 列 else None
    if 列 is None or 激活 is None:
        return 'idle'
    return 可见状态(列,激活['packageId'] if 'packageId' in 激活 else None,已加载)

def 阻塞优先(行列表):
    'awaiting-approval 在前'
    前=[]
    后=[]
    for 行 in 行列表:
        活动=行['activity'] if 'activity' in 行 else None
        阶段=活动['phase'] if 活动 is not None and 'phase' in 活动 else None
        if 阶段=='awaiting-approval':
            前.append(行)
        else:
            后.append(行)
    return 前+后

def 组装行树(视,选中包,已加载,翻译,忙碌,失败图,渲染失败图,动作错误图):
    '各行嵌套结构'
    列=视['listed'] if 'listed' in 视 else None
    活动=视['activity'] if 'activity' in 视 else None
    插件=视['pluginId'] if 'pluginId' in 视 else None
    选中包元=取包(列,选中包) if 列 is not None and 选中包 is not None else None
    激活运行=列['activeRun'] if 列 is not None and 'activeRun' in 列 else None
    活动包=取包(列,激活运行['packageId'] if 激活运行 is not None and 'packageId' in 激活运行 else None) if 列 is not None and 激活运行 else None
    选中名=选中包元['name'] if 选中包元 is not None and 'name' in 选中包元 else None
    活动阶段=活动['phase'] if 活动 is not None and 'phase' in 活动 else None
    活动名=活动['name'] if 活动 is not None and 'name' in 活动 else None
    名=选中名 or (活动名 if 活动阶段=='awaiting-approval' else 插件)
    选中用途=选中包元['purpose'] if 选中包元 is not None and 'purpose' in 选中包元 else None
    活动用途=活动['purpose'] if 活动 is not None and 'purpose' in 活动 else None
    用途=选中用途 or (活动用途 if 活动阶段=='awaiting-approval' else '')
    最近=列['latestRun'] if 列 is not None and 'latestRun' in 列 else None
    最近状态=最近['status'] if 最近 is not None and 'status' in 最近 else None
    if 活动阶段=='awaiting-approval':
        审批=活动['requestId'] if 活动 is not None and 'requestId' in 活动 else None
    elif 最近状态=='awaiting-approval':
        审批=最近['approvalRequestId'] if 最近 is not None and 'approvalRequestId' in 最近 else None
    else:
        审批=None
    态=面板可见状态(视,选中包,已加载)
    忙=忙碌 or 活动阶段=='orchestrating'
    失败=失败图.get(插件) if isinstance(失败图,dict) else None
    宿主失败=最近['error'] if 最近状态=='failed' and 最近 is not None and 'error' in 最近 else None
    渲染失败=渲染失败图.get(插件) if isinstance(渲染失败图,dict) else None
    动作错=动作错误图.get(插件) if isinstance(动作错误图,dict) else None
    下一包=列['nextPackageId'] if 列 is not None and 'nextPackageId' in 列 else None
    当前包=列['currentPackageId'] if 列 is not None and 'currentPackageId' in 列 else None
    下包=下一包 if 列 is not None and 下一包!=当前包 else None
    模式='update' if 列 and 当前包 is not None and 选中包!=当前包 else 'run'
    动作钮=[]
    if 审批 is not None:
        for 种,标,属 in (#种/文案键/data 属性
            ('approveOnce','action.approveOnce',{'data-cordis-approve':审批}),
            ('approvePlugin','action.approvePlugin',{'data-cordis-approve-plugin':审批}),
            ('decline','action.decline',{'data-cordis-decline':审批}),
        ):
            钮={#RowAction → button
                'type':'button','class':'actionButton','aria-label':翻译(标),'disabled':忙,
                'onClick':('action',种,插件,审批),'children':[动作图标(种)],
            }
            钮.update(属)
            动作钮.append({'type':'Tooltip','label':翻译(标),'side':'bottom','delayMs':500,'children':[钮]})
    elif 列 is not None:
        有客户端=选中包元['hasClientHalf'] is True if 选中包元 is not None and 'hasClientHalf' in 选中包元 else False
        激活包=激活运行['packageId'] if 激活运行 is not None and 'packageId' in 激活运行 else None
        if 选中包 is not None and 激活运行 is None:
            钮={'type':'button','class':'actionButton','aria-label':翻译('action.run'),'disabled':忙,
                'data-cordis-switch':'run','onClick':('action','run',插件,选中包,模式,有客户端),
                'children':[动作图标('run')]}
            动作钮.append({'type':'Tooltip','label':翻译('action.run'),'side':'bottom','delayMs':500,'children':[钮]})
        if 激活运行 is not None and 选中包!=激活包 and 选中包元 is not None:
            钮={'type':'button','class':'actionButton','aria-label':翻译('action.run'),'disabled':忙,
                'data-cordis-switch':'run','onClick':('action','run',插件,选中包元['packageId'] if 'packageId' in 选中包元 else None,模式,选中包元['hasClientHalf'] if 'hasClientHalf' in 选中包元 else None),
                'children':[动作图标('run')]}
            动作钮.append({'type':'Tooltip','label':翻译('action.run'),'side':'bottom','delayMs':500,'children':[钮]})
        if (激活运行 is not None and 态=='client-pending' and 活动包 is not None
            and 选中包==激活包):
            钮={'type':'button','class':'actionButton','aria-label':翻译('action.run'),'disabled':忙,
                'data-cordis-switch':'run','onClick':('action','run',插件,活动包['packageId'] if 'packageId' in 活动包 else None,'run',True),
                'children':[动作图标('run')]}
            动作钮.append({'type':'Tooltip','label':翻译('action.run'),'side':'bottom','delayMs':500,'children':[钮]})
        if 激活运行 is not None:
            钮={'type':'button','class':'actionButton','aria-label':翻译('action.stop'),'disabled':忙,
                'data-cordis-switch':'stop','onClick':('action','stop',插件),
                'children':[动作图标('stop')]}
            动作钮.append({'type':'Tooltip','label':翻译('action.stop'),'side':'bottom','delayMs':500,'children':[钮]})
        钮={'type':'button','class':'actionButton','aria-label':翻译('action.remove'),'disabled':忙,
            'data-cordis-remove':插件,'onClick':('action','remove',插件),
            'children':[动作图标('remove')]}
        动作钮.append({'type':'Tooltip','label':翻译('action.remove'),'side':'bottom','delayMs':500,'children':[钮]})
    行子=[{
        'type':'div','class':'rowHead','children':[
            {'type':'span','class':'rowId','children':[插件]},
            {'type':'span','class':'rowName','children':[名]},
            {'type':'span','class':'rowStatus','children':[翻译(状态文案键.get(态,态))]},
        ],
    }]
    包列表=列['packages'] if 列 is not None and 'packages' in 列 else None
    if 列 is not None and len(包列表 or [])>1 and 选中包 is not None:
        选项列表=[]
        for p in (包列表 or []):
            包标识=p['packageId'] if 'packageId' in p else None
            包名=p['name'] if 'name' in p else None
            选项列表.append({'type':'option','value':包标识,'children':[str(包名)+' · '+str(包标识)]})
        行子.append({'type':'label','class':'versionPicker','children':[
            {'type':'span','children':[翻译('panel.version')]},
            {'type':'select','value':选中包,'disabled':忙,'onChange':('selectPackage',插件),
             'children':选项列表},
        ]})
    行子.append({'type':'div','class':'rowDetail','children':[
        {'type':'span','class':'rowPurpose','children':[用途]},
        {'type':'div','class':'rowActions','children':动作钮},
    ]})
    if 审批 is None and 下包 is not None and 列 is not None:
        下包元=取包(列,下包)
        下包有客户端=下包元['hasClientHalf'] is True if 下包元 is not None and 'hasClientHalf' in 下包元 else False
        过渡动作=[{
            'type':'button','disabled':忙,'onClick':('action','retry',插件,下包,'run' if 当前包 is None else 'update',
                                                     下包有客户端),
            'children':[翻译('action.retry')],
        }]
        if 当前包 is not None:
            当前包元=取包(列,当前包)
            当前有客户端=当前包元['hasClientHalf'] is True if 当前包元 is not None and 'hasClientHalf' in 当前包元 else False
            过渡动作.append({'type':'button','disabled':忙,
                             'onClick':('action','rollback',插件,当前包,'run',当前有客户端),
                             'children':[翻译('action.rollback')]})
        行子.append({'type':'div','class':'transition','children':[
            {'type':'span','children':[翻译('panel.current',packageId=当前包) if 当前包 is not None else '']},
            {'type':'span','children':[翻译('panel.next',packageId=下包)]},
            {'type':'div','class':'transitionActions','children':过渡动作},
        ]})
    if 失败 is not None:
        失败消息=失败['message'] if 'message' in 失败 else None
        失败原因=失败['reason'] if 'reason' in 失败 else None
        行子.append({'type':'div','class':'rowError','role':'alert',
                     'children':[页面失败文案(失败消息)+' ('+页面失败文案(失败原因)+')']})
    if 失败 is None and 宿主失败 is not None:
        宿主消息=宿主失败['message'] if 'message' in 宿主失败 else None
        宿主阶段=宿主失败['phase'] if 'phase' in 宿主失败 else None
        行子.append({'type':'div','class':'rowError','role':'alert',
                     'children':[页面失败文案(宿主消息)+' ('+页面失败文案(宿主阶段)+')']})
    if 动作错 is not None:
        行子.append({'type':'div','class':'rowError','role':'alert','children':[页面失败文案(动作错)]})
    if 渲染失败 is not None:
        已弃=渲染失败['abdicated'] if 'abdicated' in 渲染失败 else None
        槽=渲染失败['slot'] if 'slot' in 渲染失败 else None
        渲消息=渲染失败['message'] if 'message' in 渲染失败 else None
        键=渲染失败文案键['abdicated' if 已弃 else 'held']
        行子.append({'type':'div','class':'rowError','role':'alert',
                     'data-cordis-render-failure':槽,
                     'data-cordis-render-abdicated':已弃 or None,
                     'children':[翻译(键,slot=槽)+' '+页面失败文案(渲消息)]})
    if 活动包 is not None and (活动包['packageId'] if 'packageId' in 活动包 else None)!=选中包:
        行子.append({'type':'span','class':'activeVersion',
                     'children':[翻译('status.running')+': '+(活动包['name'] if 'name' in 活动包 else None)+' · '+(活动包['packageId'] if 'packageId' in 活动包 else None)]})
    return {
        'type':'li','key':插件,'class':'row','data-cordis-row':插件,
        'data-cordis-status':态,'data-cordis-awaiting':审批 is not None or None,
        'children':行子,
    }

class 面板:
    '组装可见行与触发器嵌套 JSX 树'
    def __init__(自身,属性=None):
        '记下 props 与开合'
        自身.属性=属性 or {}
        自身.打开=False
        自身.已选={}
        自身.忙碌=set()
        自身.动作错误={}
        自身.已见表批=set()
        if 自身.属性:#槽位只调用构造
            自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 or {}

    def 选版本(自身,插件,包):
        '写入已选'
        自身.已选={**自身.已选,插件:包}

    def 切换(自身):
        '翻转面板'
        自身.打开=not 自身.打开
        刷新=自身.属性['onRefresh'] if 'onRefresh' in 自身.属性 else None
        if 自身.打开 and callable(刷新):
            刷新()

    def 渲染(自身):
        '产出面板嵌套 JSX 树'
        p=自身.属性
        def 原样(键,**_参数):
            '缺翻译器时原样返回键'
            return 键
        def 翻译(键,**参数):
            '带插值'
            译=p['t'] if 't' in p else None
            if 译 is None:
                基=原样(键)
            else:
                基=译(键)
            if not 参数:
                return 基
            出=基
            for 名,值 in 参数.items():
                出=出.replace('{'+名+'}',str(值))
            return 出
        def 原样快照(快照):
            '钩子选择器：整份快照'
            return 快照
        宽=bool(p['wide'] if 'wide' in p else True)
        清单钩=p['useInventory'] if 'useInventory' in p else None
        活动钩=p['useActiveRuns'] if 'useActiveRuns' in p else None
        加载钩=p['useLoaded'] if 'useLoaded' in p else None
        失败钩=p['useRunErrors'] if 'useRunErrors' in p else None
        渲钩=p['useRenderFailures'] if 'useRenderFailures' in p else None
        会话钩=p['useSessions'] if 'useSessions' in p else None
        if callable(清单钩):
            清单=清单钩(原样快照)
        else:
            清单=p['inventory'] if 'inventory' in p else {'rows':[],'read':False}
        if callable(活动钩):
            活动图=活动钩(原样快照) or {}
        else:
            活动图=p['activeRuns'] if 'activeRuns' in p else {}
        if callable(加载钩):
            已加载=加载钩(原样快照) or []
        else:
            已加载=p['loaded'] if 'loaded' in p else []
        if callable(失败钩):
            失败图=失败钩(原样快照) or {}
        else:
            失败图=p['runErrors'] if 'runErrors' in p else {}
        if callable(渲钩):
            渲图=渲钩(原样快照) or {}
        else:
            渲图=p['renderFailures'] if 'renderFailures' in p else {}
        if callable(会话钩):
            会话快照=会话钩(原样快照)
            当前=会话快照['current'] if 会话快照 is not None and 'current' in 会话快照 else None
        else:
            当前=p['currentSession'] if 'currentSession' in p else None
        if hasattr(活动图,'items'):
            活动项=list(活动图.items())
        elif isinstance(活动图,dict):
            活动项=list(活动图.items())
        else:
            活动项=[]
        按插件={}
        行列表=清单['rows'] if 清单 is not None and 'rows' in 清单 else None
        for 列 in (行列表 or []):
            标识=列['pluginId'] if 'pluginId' in 列 else None
            活动=活动图.get(标识) if isinstance(活动图,dict) else None
            活动智能体=活动['agentId'] if 活动 is not None and 'agentId' in 活动 else None
            列智能体=列['agentId'] if 'agentId' in 列 else None
            按插件[标识]={'pluginId':标识,'agentId':活动智能体 or 列智能体,'listed':列,**({'activity':活动} if 活动 else {})}
        for 标识,活动 in 活动项:
            if 标识 in 按插件:
                continue
            按插件[标识]={'pluginId':标识,'agentId':活动['agentId'] if 活动 is not None and 'agentId' in 活动 else None,'activity':活动}
        全部=list(按插件.values())
        本组=阻塞优先([r for r in 全部 if 当前 is not None and (r['agentId'] if 'agentId' in r else None)==当前])
        他组=阻塞优先([r for r in 全部 if 当前 is None or (r['agentId'] if 'agentId' in r else None)!=当前])
        审批数=0
        for _,活动 in 活动项:
            if 活动 is not None and 'phase' in 活动 and 活动['phase']=='awaiting-approval':
                审批数+=1
        运行数=sum(1 for r in 全部 if 面板可见状态(r,选定包标识(r,自身.已选),已加载)=='running')
        现批=set()
        for _,活动 in 活动项:
            if 活动 is not None and 'phase' in 活动 and 活动['phase']=='awaiting-approval':
                if 'requestId' in 活动:
                    现批.add(活动['requestId'])
        if any(批 not in 自身.已见表批 for 批 in 现批):
            自身.打开=True
        自身.已见表批=现批
        失败映射=失败图 if isinstance(失败图,dict) else dict(失败图) if hasattr(失败图,'items') else {}
        渲映射=渲图 if isinstance(渲图,dict) else dict(渲图) if hasattr(渲图,'items') else {}
        def 渲组(行列表):
            '组装行树列表'
            树列表=[]
            for 视 in 行列表:
                树列表.append(组装行树(
                    视,选定包标识(视,自身.已选),已加载,翻译,('pluginId' in 视 and 视['pluginId'] in 自身.忙碌),
                    失败映射,渲映射,自身.动作错误,
                ))
            return 树列表
        if len(全部)==0:
            return 画出根({'type':None,'visible':False,'css':样式表,'note':'无插件时不渲染'})
        清单错=清单['error'] if 清单 is not None and 'error' in 清单 else None
        已读=清单['read'] if 清单 is not None and 'read' in 清单 else False
        体子=去掉空子节点([
            {'type':'p','class':'readError','role':'alert',
             'children':[翻译('panel.readFailed',message=页面失败文案(清单错))]} if 清单错 else None,
            {'type':'p','class':'note','children':[翻译('panel.loading')]}
            if not 已读 and 清单错 is None else None,
            {'type':'p','class':'note','children':[翻译('panel.empty')]}
            if 已读 and len(全部)==0 else None,
            {'type':'section','children':[
                {'type':'h3','class':'group','children':[翻译('panel.group.current')]},
                {'type':'ul','class':'rows','children':渲组(本组)},
            ]} if len(本组)>0 else None,
            {'type':'section','children':[
                {'type':'h3','class':'group','children':[翻译('panel.group.others')]},
                {'type':'ul','class':'rows','children':渲组(他组)},
            ]} if len(他组)>0 else None,
        ])
        徽子=[{'type':'IconCordisPluginOutline14'}]
        if 宽:
            徽子.extend([
                {'type':'span','class':'badgeLabel','children':[翻译('panel.trigger')]},
                {'type':'span','class':'badgeCount','children':[翻译('panel.runningCount',count=运行数)]},
            ])
        层子=去掉空子节点([
            {'type':'section','class':'panel','data-cordis-panel':True,'aria-label':翻译('panel.title'),
             'children':[
                {'type':'header','class':'header','children':[
                    {'type':'span','class':'title','children':[翻译('panel.title')]},
                ]},
                {'type':'div','class':'body','children':体子},
            ]} if 自身.打开 else None,
            {'type':'div','class':'footerButtons','children':[
                {'type':'button','class':'badge','data-cordis-badge':len(全部),
                 'data-cordis-approval-badge':审批数,'data-active':审批数>0 or None,
                 'aria-label':翻译('panel.plugins.aria'),'aria-expanded':自身.打开,
                 'onClick':'toggle','children':徽子},
            ]},
        ])
        树={
            'type':'div','class':'layer' if 宽 else 'layer rail','visible':True,
            'children':层子,'css':样式表,
            'handlers':{'toggle':自身.切换,'selectPackage':自身.选版本},
            'note':'图标/Tooltip/真实按钮 DOM 需浏览器；无法 Python·vm 执行侧栏像素',
        }
        return 画出根(树)

    def __call__(自身,属性=None):
        '结构树面'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
