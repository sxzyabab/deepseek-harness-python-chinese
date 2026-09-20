from .配置账本 import 行配置键#行配置键
from .装载存储 import 是否安装待决,行键#装载工具
from .呈现 import 装载文案,提示文案,包文案#呈现

__all__=['插件装载页','高亮毫秒','行筛选阈值']#仅中文公开名

高亮毫秒=2400#安装启用后列表高亮时长
行筛选阈值=10#超过此数显示筛选框

内置档组合包={#页面排除的内置 profile 组合包
    '@deepseek-ai/dsh-base',
    '@deepseek-ai/dsh-web-app',
    '@deepseek-ai/dsh-headless',
    '@deepseek-ai/dsh-sdk-app',
    '@deepseek-ai/dsh-acp-app',
    '@deepseek-ai/dsh-sdk-minimal',
}#内置结束

阶段键={#fiber 阶段 → 文案键
    'pending':'rowPhasePending',
    'loading':'rowPhaseLoading',
    'active':'rowPhaseActive',
    'failed':'rowPhaseFailed',
    'unloading':'rowPhaseUnloading',
}#阶段结束

阶段点={#阶段 → 状态点
    'pending':'idle',
    'loading':'ongoing',
    'active':'done',
    'failed':'error',
    'unloading':'idle',
}#点结束

输入问题键={#检查拒因 → 文案键
    'invalid-spec':'installProblemInvalid',
    'already-installed':'installProblemInstalled',
    'not-found':'installProblemNotFound',
    'not-a-package':'installProblemNotPackage',
    'not-a-bundle':'installProblemNotBundle',
    'network':'installProblemNetwork',
    'unknown':'installProblemUnknown',
}#输入结束

失败种类键={#pnpm 失败种类 → 文案键
    'pnpm-missing':'installFailurePnpmMissing',
    'timeout':'installFailureTimeout',
    'not-found':'installFailureNotFound',
    'no-matching-version':'installFailureNoMatchingVersion',
    'network':'installFailureNetwork',
    'disk-full':'installFailureDiskFull',
    'permission':'installFailurePermission',
    'build-blocked':'installFailureBuildBlocked',
    'integrity':'installFailureIntegrity',
    'unknown':'installFailureGeneric',
}#失败种类结束

屏标题键={#安装阶段 → 标题
    'starting':'installStarting',
    'running':'installingTitle',
    'cancelling':'installCancelling',
    'applying':'installApplying',
    'done':'installedTitle',
    'failed':'installFailedTitle',
}#屏标题结束

主体种类键={#主体种类 → 文案键
    'registry':None,
    'path':'installSubjectPath',
    'git':'installSubjectGit',
    'tarball':'installSubjectTarball',
}#主体结束

引导示例=(#安装引导三例
    {'key':'id','titleKey':'installGuideIdTitle','exampleKey':'installGuideIdExample','hintKey':'installGuideIdHint'},
    {'key':'git','titleKey':'installGuideGitTitle','exampleKey':'installGuideGitExample','hintKey':'installGuideGitHint'},
    {'key':'path','titleKey':'installGuidePathTitle','exampleKey':'installGuidePathExample','hintKey':'installGuidePathHint'},
)#引导结束

def 轻提示毫秒(文本):
    """toast 停留时长。"""
    return min(8000,max(3000,len(文本.encode('utf-8'))*80))#按字节预算

def 部件摘要(行表,翻译):
    """组件计数行。"""
    失败=len([行 for 行 in 行表 if 行.get('phase')=='failed'])#失败数
    关闭=len([行 for 行 in 行表 if not 行['enabled']])#关闭数
    运行=len([行 for 行 in 行表 if 行['enabled'] and 行.get('phase')=='active'])#运行数
    段=[翻译('partsCountTotal',{'count':str(len(行表))})]#段
    if 运行>0:段.append(翻译('partsCountRunning',{'count':str(运行)}))#运行
    if 关闭>0:段.append(翻译('partsCountOff',{'count':str(关闭)}))#关闭
    if 失败>0:段.append(翻译('partsCountFailed',{'count':str(失败)}))#失败
    return ' · '.join(段)#连接

def 包状态(包):
    """卡片状态：运行/关闭/异常。"""
    if 'error' in 包 and 包['error'] is not None:return 'problem'#异常
    return 'running' if 包['enabled'] else 'disabled'#启停

def 行状态文案(行,翻译):
    """行状态句。"""
    if not 行['enabled']:return 翻译('partOff')#关闭
    阶段=行.get('phase')#阶段
    return 翻译('rowStateIdle') if 阶段 is None else 翻译(阶段键[阶段])#阶段

def 行点状态(行):
    """行旁状态点。"""
    if not 行['enabled'] or 'phase' not in 行:return 'idle'#空闲
    return 阶段点[行['phase']]#点

def 失败文案(失败,翻译):
    """失败屏一句。"""
    if 失败 is None:return 翻译('installFailureGeneric')#通用
    待=失败['pendingBuilds'] if 'pendingBuilds' in 失败 else None#待允许
    if 失败.get('kind')=='build-blocked' and (待 is None or len(待)==0):
        return 翻译('installFailureBuildBlockedManual')#手动
    if 'kind' in 失败 and 失败['kind'] is not None:
        return 翻译(失败种类键[失败['kind']])#种类
    if 'code' in 失败 and 失败['code'] is not None:
        return 装载文案({'code':失败['code'],'diagnostic':失败.get('reason')},翻译)#码
    原因=失败.get('reason') or ''#原因
    return 翻译('installFailureGeneric') if 原因=='' else 原因#原样

class 插件装载页:#插件装载页视图模型
    """官方与已安装组合包、详情、安装对话框与卸载确认。"""
    def __init__(自身,属性):
        """记下合成 props。"""
        自身.属性=属性#props
        自身.页态={'kind':'list'}#当前页
        自身.行筛选=''#行筛选
        自身.引导开=False#安装引导
        自身.已确保=False#已首读

    def 更新(自身,属性):
        """刷新合成 props。"""
        自身.属性=属性#最新

    def 开包(自身,名):
        """打开组合包页。"""
        自身.页态={'kind':'package','name':名}#包页

    def 开条目(自身,身份):
        """打开官方插件页。"""
        自身.页态={'kind':'item','id':身份}#条目页

    def 开行(自身,名,行标识):
        """打开行配置页。"""
        自身.页态={'kind':'row','name':名,'rowId':行标识}#行页

    def 回列表(自身):
        """回卡片列表。"""
        自身.页态={'kind':'list'}#列表

    def 回包(自身,名):
        """回组合包页。"""
        自身.页态={'kind':'package','name':名}#包页

    def 设行筛选(自身,文本):
        """改行筛选。"""
        自身.行筛选=文本#筛选

    def 切换引导(自身):
        """翻转安装引导。"""
        自身.引导开=not 自身.引导开#翻转

    def 视图(自身):
        """投影整页视图模型。"""
        属性=自身.属性#props
        翻译=属性['t']#文案
        if not 自身.已确保:#首读
            属性['ensure']()#确保
            自身.已确保=True#已
        钩=属性['hooks']#钩
        状态=钩['pluginManager'].getSnapshot()#装载态
        账本=钩['configLedger'].getSnapshot()#账本
        提示行=None if 状态['notice'] is None else 提示文案(状态['notice'],翻译)#提示
        列出=[包 for 包 in 状态['packages'] if 包['name'] not in 内置档组合包 and (包['installed'] or 包['optional'] or 包.get('error') is not None)]#列出
        我的=[包 for 包 in 列出 if 包['installed'] or not 包['optional']]#已装
        官方=[包 for 包 in 列出 if 包['optional'] and not 包['installed']]#官方
        已载=状态['status'] in ('ready','error')#已载
        视=自身.页态#当前页态
        开包=None#开的包
        开条目=None#开的条目
        开行=None#开的行
        if 视['kind'] in ('package','row'):#包或行
            for 包 in 列出:#查找
                if 包['name']==视['name']:#命中
                    开包=包#记下
                    break#停
        if 视['kind']=='item':#条目
            for 项 in 账本['items']:#查找
                if 项['id']==视['id']:#命中
                    开条目=项#记下
                    break#停
        if 视['kind']=='row' and 开包 is not None:#行
            for 行 in 开包['rows']:#查找
                if 行['rowId']==视['rowId']:#命中
                    开行=行#记下
                    break#停
        显示卡片=开包 is None and 开条目 is None#卡片态
        结果={#基础
            'kind':'plugin-manager-page',#种类
            'cssModule':'插件装载页.module.css',#样式
            'status':状态['status'],#状态
            'busy':状态['busy'],#忙碌
            'notice':状态['notice'],#提示
            'noticeLine':提示行,#提示句
            'noticeHoldMs':轻提示毫秒(提示行) if 提示行 is not None else 0,#停留
            'install':自身._安装视图(状态['install'],翻译),#安装
            'confirm':自身._确认视图(状态['confirm'],翻译),#确认
            'highlight':状态['highlight'],#高亮
            'highlightMs':高亮毫秒,#高亮时长
            'showsCards':显示卡片,#卡片
            'loaded':已载,#已载
            'labels':{#页文案
                'title':翻译('title'),
                'intro':翻译('intro'),
                'refresh':翻译('refresh'),
                'addPlugin':翻译('addPlugin'),
                'loading':翻译('loading'),
                'unavailable':翻译('unavailable'),
                'error':翻译('error'),
                'retry':翻译('retry'),
                'empty':翻译('empty'),
                'officialTitle':翻译('officialTitle'),
                'bundlesTitle':翻译('bundlesTitle'),
            },#文案结束
            'actions':{#动作
                'refresh':属性['refresh'],
                'openInstall':属性['openInstall'],
                'dismissNotice':属性['dismissNotice'],
                'clearHighlight':属性['clearHighlight'],
                'backToList':自身.回列表,
            },#动作结束
        }#基础结束
        if 显示卡片 and 已载:#卡片列表
            官方卡=[自身._包卡(包,翻译,状态) for 包 in 官方]#官方包卡
            for 项 in 账本['items']:#官方条目
                官方卡.append(自身._条目卡(项,翻译,属性))#条目卡
            结果['officialCards']=官方卡#官方
            结果['bundleCards']=[自身._包卡(包,翻译,状态) for 包 in 我的]#已装
        if 已载 and 开包 is not None and 开行 is not None:#行详情
            结果['rowDetail']=自身._行详情(开包,开行,翻译,属性)#行
        elif 已载 and 开包 is not None:#包详情
            结果['packageDetail']=自身._包详情(开包,翻译,状态,账本,属性)#包
        elif 已载 and 开条目 is not None:#条目详情
            结果['itemDetail']=自身._条目详情(开条目,翻译,属性)#条目
        return 结果#视图

    def _包卡(自身,包,翻译,状态):
        """组合包卡片。"""
        文=包文案(包,翻译)#文案
        return {#卡
            'kind':'package-card',#种类
            'name':包['name'],#名
            'title':文['title'],#标题
            'description':文['description'],#描述
            'beta':文['beta'],#beta
            'status':包状态(包),#状态
            'enabled':包['enabled'],#启用
            'busy':包['name'] in 状态['busy'],#忙碌
            'highlighted':状态['highlight']==包['name'],#高亮
            'readOnlyReason':包.get('readOnlyReason'),#只读
            'error':包.get('error'),#错误
            'actions':{#动作
                'open':lambda 名=包['name']:自身.开包(名),#开
                'setEnabled':lambda 启,名=包['name']:自身.属性['setEnabled'](名,启),#启停
            },#动作结束
        }#卡结束

    def _条目卡(自身,项,翻译,属性):
        """官方插件卡片。"""
        return {#卡
            'kind':'item-card',#种类
            'id':项['id'],#id
            'label':项['label'],#标签
            'summarySlot':{'name':'plugins.item','view':'summary','only':项['id']},#摘要槽
            'actions':{'open':lambda 身份=项['id']:自身.开条目(身份)},#开
        }#卡结束

    def _包详情(自身,包,翻译,状态,账本,属性):
        """组合包详情页。"""
        文=包文案(包,翻译)#文案
        查询=自身.行筛选.strip().lower()#筛选
        行表=包['rows'] if 查询=='' else [行 for 行 in 包['rows'] if 查询 in 行['rowId'].lower()]#过滤
        行视图=[]#行
        for 行 in 行表:#每行
            键=行配置键(包['name'],行['rowId'])#配置键
            有配置=键 in 账本['rows']#有配置
            行视图.append({#行
                'rowId':行['rowId'],#id
                'moduleName':行['moduleName'],#模块
                'entryId':行.get('entryId'),#入口
                'enabled':行['enabled'],#启用
                'phase':行.get('phase'),#阶段
                'stateText':行状态文案(行,翻译),#状态句
                'dotState':行点状态(行),#点
                'busy':行.get('entryId') is not None and 行键(行['entryId']) in 状态['busy'],#忙碌
                'locked':'readOnlyReason' in 行 or 'entryId' not in 行,#锁定
                'readOnlyReason':行.get('readOnlyReason'),#只读
                'hasConfig':有配置,#配置
                'actions':{#动作
                    'setEnabled':lambda 启,入口=行.get('entryId'):属性['setRowEnabled'](入口,启) if 入口 is not None else None,
                    'openConfig':lambda 名=包['name'],行标识=行['rowId']:自身.开行(名,行标识) if 有配置 else None,
                },#动作结束
            })#行结束
        return {#详情
            'kind':'package-detail',#种类
            'name':包['name'],#名
            'title':文['title'],#标题
            'description':文['description'] if 文['description'] is not None else 翻译('noDescription'),#描述
            'beta':文['beta'],#beta
            'version':包.get('version'),#版本
            'status':包状态(包),#状态
            'installed':包['installed'],#已装
            'enabled':包['enabled'],#启用
            'busy':包['name'] in 状态['busy'],#忙碌
            'readOnlyReason':包.get('readOnlyReason'),#只读
            'error':包.get('error'),#错误
            'errorText':装载文案(包['error'],翻译) if 包.get('error') is not None else None,#错误句
            'readOnlyText':装载文案({'code':包['readOnlyReason']},翻译) if 包.get('readOnlyReason') is not None else None,#只读句
            'configured':包['name'] in 账本['bundles'],#自有配置
            'bundleConfigSlot':{'name':'plugins.bundle.config','view':'page','entryKey':包['name']},#配置槽
            'partsSummary':部件摘要(包['rows'],翻译) if len(包['rows'])>0 else None,#摘要
            'showFilter':len(包['rows'])>行筛选阈值,#筛选
            'filter':自身.行筛选,#筛选值
            'rows':行视图,#行
            'filterEmpty':len(包['rows'])>0 and len(行视图)==0,#无匹配
            'labels':{#文案
                'backToList':翻译('backToList'),
                'crumbRoot':翻译('crumbRoot'),
                'uninstall':翻译('uninstall'),
                'uninstallLabel':翻译('uninstallLabel',{'name':文['title']}),
                'enableToggle':翻译('enableToggle',{'name':文['title']}),
                'partsLabel':翻译('partsLabel'),
                'partsEmpty':翻译('partsEmpty'),
                'partsFilter':翻译('partsFilter'),
                'partsFilterEmpty':翻译('partsFilterEmpty'),
                'reasonLabel':翻译('reasonLabel'),
                'versionTag':翻译('versionTag',{'version':包['version']}) if 包.get('version') is not None else None,
                'statusBeta':翻译('statusBeta'),
                'statusProblem':翻译('statusProblem'),
                'configureRow':翻译('configureRow'),
            },#文案结束
            'actions':{#动作
                'back':自身.回列表,#回
                'setEnabled':lambda 启:属性['setEnabled'](包['name'],启),#启停
                'uninstall':lambda:属性['uninstall'](包['name']),#卸载
                'setFilter':自身.设行筛选,#筛选
            },#动作结束
        }#详情结束

    def _行详情(自身,包,行,翻译,属性):
        """行配置详情。"""
        文=包文案(包,翻译)#文案
        键=行配置键(包['name'],行['rowId'])#键
        return {#详情
            'kind':'row-detail',#种类
            'key':键,#键
            'rowId':行['rowId'],#行 id
            'moduleName':行['moduleName'],#模块
            'summarySlot':{'name':'plugins.row.config','view':'summary','entryKey':键},#摘要
            'pageSlot':{'name':'plugins.row.config','view':'page','entryKey':键},#页面
            'labels':{#文案
                'back':翻译('backToPackage',{'name':文['title']}),
                'crumb':文['title'],
            },#文案结束
            'actions':{'back':lambda 名=包['name']:自身.回包(名)},#回
        }#详情结束

    def _条目详情(自身,项,翻译,属性):
        """官方插件详情。"""
        return {#详情
            'kind':'item-detail',#种类
            'id':项['id'],#id
            'label':项['label'],#标签
            'summarySlot':{'name':'plugins.item','view':'summary','only':项['id']},#摘要
            'pageSlot':{'name':'plugins.item','view':'page','only':项['id']},#页面
            'labels':{'backToList':翻译('backToList'),'crumbRoot':翻译('crumbRoot')},#文案
            'actions':{'back':自身.回列表},#回
        }#详情结束

    def _安装视图(自身,安装,翻译):
        """安装对话框视图。"""
        阶段=安装['phase']#阶段
        结果={#基础
            'open':安装['open'],#开
            'phase':阶段,#阶段
            'spec':安装['spec'],#规格
            'guideOpen':自身.引导开,#引导
            'detailsOpen':安装['detailsOpen'],#详情
            'runs':安装['runs'],#运行
            'subject':安装['subject'],#主体
            'enabling':安装['enabling'],#启用中
            'installed':安装['installed'],#已装名
            'restartRequired':安装['restartRequired'],#需重启
            'approvedBuilds':安装['approvedBuilds'],#已允许
            'failure':安装['failure'],#失败
            'inputError':安装['inputError'],#输入错
            'pending':是否安装待决(阶段),#待决
            'guideExamples':[{#引导例
                'key':例['key'],
                'title':翻译(例['titleKey']),
                'example':翻译(例['exampleKey']),
                'hint':翻译(例['hintKey']),
            } for 例 in 引导示例],
        }#基础结束
        if 安装['inputError'] is not None:#输入错
            错=安装['inputError']#错
            结果['inputErrorText']=翻译(输入问题键[错['problem']],{'reason':错['reason']})#句
        if 阶段 not in ('idle','checking'):#后续屏
            结果['heading']=翻译(屏标题键[阶段])#标题
            结果['failureText']=失败文案(安装['failure'],翻译) if 阶段=='failed' else None#失败句
            if 安装['subject'] is not None:#主体卡
                主体=安装['subject']#主体
                种键=主体种类键.get(主体['kind'])#种类键
                结果['subjectCard']={#卡
                    'title':主体['name'] if 'name' in 主体 and 主体['name'] is not None else 主体['spec'],#标题
                    'description':主体['description'] if 'description' in 主体 and 主体['description'] is not None else (翻译(种键) if 种键 is not None else None),#描述
                    'version':翻译('installVersion',{'version':主体['version']}) if 'version' in 主体 and 主体['version'] is not None else None,#版本
                }#卡结束
            待=安装['failure']['pendingBuilds'] if 阶段=='failed' and 安装['failure'] is not None and 'pendingBuilds' in 安装['failure'] else []#待允许
            结果['pendingBuilds']=待 if 待 is not None else []#待
            结果['approvable']=len(结果['pendingBuilds'])>0#可批准
        属性=自身.属性#props
        结果['actions']={#动作
            'close':属性['closeInstall'],
            'editSpec':属性['editInstallSpec'],
            'run':属性['runInstall'],
            'cancel':属性['cancelInstall'],
            'cancelAndClose':属性['cancelInstallAndClose'],
            'toggleDetails':属性['toggleInstallDetails'],
            'enableNow':属性['enableInstalled'],
            'approveBuilds':属性['approveBuildsAndRetry'],
            'toggleGuide':自身.切换引导,
        }#动作结束
        结果['labels']={#文案键投影（常用）
            'installTitle':翻译('installTitle'),
            'installDescription':翻译('installDescription'),
            'installSpecLabel':翻译('installSpecLabel'),
            'installSpecPlaceholder':翻译('installSpecPlaceholder'),
            'installRun':翻译('installRun'),
            'installChecking':翻译('installChecking'),
            'installGuideToggle':翻译('installGuideToggle'),
            'installGuideHide':翻译('installGuideHide'),
            'installGuideIntro':翻译('installGuideIntro'),
            'installGuideIdNote':翻译('installGuideIdNote'),
            'installGuideExampleLabel':翻译('installGuideExampleLabel'),
            'installGuideFill':翻译('installGuideFill'),
            'installGuideSafety':翻译('installGuideSafety'),
            'close':翻译('close'),
            'installEdit':翻译('installEdit'),
            'installCancel':翻译('installCancel'),
            'installCancelling':翻译('installCancelling'),
            'installCloseCancels':翻译('installCloseCancels'),
            'installDetailsShow':翻译('installDetailsShow'),
            'installDetailsHide':翻译('installDetailsHide'),
            'installRetry':翻译('installRetry'),
            'installEnableNow':翻译('installEnableNow'),
            'installClose':翻译('installClose'),
            'installApprovalTitle':翻译('installApprovalTitle'),
            'installApprovalDescription':翻译('installApprovalDescription'),
            'installApprovalConsequence':翻译('installApprovalConsequence'),
            'installApprovalCaution':翻译('installApprovalCaution'),
            'installApproveAndRetry':翻译('installApproveAndRetry'),
            'installDoneNothing':翻译('installDoneNothing'),
            'installDoneRestart':翻译('installDoneRestart'),
            'installLocation':翻译('installLocation'),
            'terminalNoOutput':翻译('terminalNoOutput'),
        }#文案结束
        return 结果#安装视图

    def _确认视图(自身,确认,翻译):
        """卸载确认视图。"""
        if 确认 is None:return None#无
        文=包文案({'name':确认['packageName']},翻译)#文案
        return {#确认
            'action':确认['action'],#动作
            'packageName':确认['packageName'],#包名
            'title':翻译('confirmUninstallTitle',{'name':文['title']}),#标题
            'description':翻译('confirmUninstallDescription'),#说明
            'confirmLabel':翻译('confirmUninstall'),#确认
            'cancelLabel':翻译('cancel'),#取消
            'closeLabel':翻译('close'),#关闭
            'actions':{#动作
                'confirm':自身.属性['confirm'],
                'cancel':自身.属性['cancelConfirm'],
            },#动作结束
        }#确认结束
