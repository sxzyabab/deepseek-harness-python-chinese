'插件装载页：官方与已安装、详情、安装对话框和卸载确认'
from ...模块.客户端.通告 import 取握手窗口
import base64
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块,挂上
from ...ui_基础界面组件.icons import (
    图标下箭头描边常规,
    图标信息描边常规,
    图标关闭16,
    图标加号16,
    图标勾圈描边常规,
    图标右chevron14,
    图标左chevron14,
    图标垃圾桶16,
    图标下载16,
    图标刷新16,
    图标警告16,
)
from ...ui_基础界面组件.插件画稿 import (
    插件画稿子智能体,
    插件画稿搜索,
    插件画稿循环,
    插件画稿终端,
    插件画稿默认,
)
from ...ui_基础界面组件.分段标签页 import 分段标签页
from ...ui_基础界面组件.开关 import 开关
from ...ui_基础界面组件.吐司 import 吐司
from ...ui_基础界面组件.提示泡 import 提示泡
from ...ui_基础界面组件.按钮 import 按钮
from ...ui_基础界面组件.标签 import 标签
from ...ui_基础界面组件.模态 import 模态
from ...ui_基础界面组件.状态点 import 状态点
from ...ui_基础界面组件.终端块 import 终端块
from ...ui_基础界面组件.点外关闭 import 点外关闭
from ...ui_基础界面组件.输入模态 import 指针模态
from ...ui_基础界面组件.锚定位置 import 使用锚定位置
from .文案 import 中文句,安装示例仓库,安装示例路径
from .呈现 import 包文案,行文案,提示文案,注册表文案对,重启文案,管理文案
from .装载存储 import 已问镜像,是否安装待决,提供的注册表,镜像恢复注册表,行键
from .配置账本 import 行配置键

__all__=['插件装载页']

样式模块='plugin-manager-page'
高亮毫秒=2400
行筛选阈值=10
卡片画稿尺寸=36
行画稿尺寸=30
安装终端行数=12
已安装页='installed'
内置档组合包={
    '@deepseek-ai/dsh-base','@deepseek-ai/dsh-web-app','@deepseek-ai/dsh-headless',
    '@deepseek-ai/dsh-sdk-app','@deepseek-ai/dsh-acp-app','@deepseek-ai/dsh-sdk-minimal',
}
始终展示=(
    '@deepseek-ai/dsh-experimental-agent-team-profile',
    '@deepseek-ai/dsh-experimental-voice-input-bundle',
    '@deepseek-ai/dsh-experimental-auto-review',
    '@deepseek-ai/dsh-experimental-inspector-profile',
)
更多包=(
    '@deepseek-ai/dsh-experimental-tool-worktree',
    '@deepseek-ai/dsh-experimental-cot-translation-bundle',
    '@deepseek-ai/dsh-experimental-terminal-bundle',
    '@deepseek-ai/dsh-experimental-session-search',
    '@deepseek-ai/dsh-experimental-session-titles-bundle',
    '@deepseek-ai/dsh-experimental-badge-skill-bundle',
    '@deepseek-ai/dsh-experimental-ralph-bundle',
    '@deepseek-ai/dsh-experimental-plugin-market-bundle',
    '@deepseek-ai/dsh-subagent-codex',
    '@deepseek-ai/dsh-subagent-claude-code',
)
预览文件={
    '@deepseek-ai/dsh-experimental-badge-skill-bundle':'badge-skill-preview.zh.svg',
    '@deepseek-ai/dsh-experimental-voice-input-bundle':'voice-input-preview.zh.svg',
}
条目画稿类={
    'shell':插件画稿终端,
    'agent-loop':插件画稿循环,
    'subagent':插件画稿子智能体,
    'web-search':插件画稿搜索,
}
阶段键={
    'pending':'rowPhasePending','loading':'rowPhaseLoading','active':'rowPhaseActive',
    'failed':'rowPhaseFailed','unloading':'rowPhaseUnloading',
}
阶段点={'pending':'idle','loading':'ongoing','active':'done','failed':'error','unloading':'ongoing'}
输入问题键={
    'invalid-spec':'installProblemInvalid','already-installed':'installProblemInstalled',
    'shipped':'installProblemShipped','not-found':'installProblemNotFound',
    'not-a-package':'installProblemNotPackage','not-a-bundle':'installProblemNotBundle',
    'network':'installProblemNetwork','unknown':'installProblemUnknown',
}
失败种类键={
    'pnpm-missing':'installFailurePnpmMissing','timeout':'installFailureTimeout',
    'not-found':'installFailureNotFound','no-matching-version':'installFailureNoMatchingVersion',
    'network':'installFailureNetwork','disk-full':'installFailureDiskFull',
    'permission':'installFailurePermission','build-blocked':'installFailureBuildBlocked',
    'integrity':'installFailureIntegrity','unknown':'installFailureGeneric',
}
屏标题键={
    'starting':'installStarting','running':'installingTitle','cancelling':'installCancelling',
    'applying':'installApplying','unconfirmed':'installUnconfirmedTitle','unknown':'installUnknownTitle',
    'done':'installedTitle','failed':'installFailedTitle',
}
主体种类键={'registry':None,'path':'installSubjectPath','git':'installSubjectGit','tarball':'installSubjectTarball'}
引导示例=(
    {'key':'id','titleKey':'installGuideIdTitle','exampleKey':'installGuideIdExample','hintKey':'installGuideIdHint'},
)

def 窗口于(属性):
    '宿主窗口。没有时用当前页'
    if isinstance(属性,dict) and 'window' in 属性:
        return 属性['window']
    return 取握手窗口()

def 确保样式(文档):
    '把本页样式模块插进文档'
    注入模块样式文件(
        文档,
        '插件装载页样式',
        os.path.join(os.path.dirname(__file__),'插件装载页.module.css'),
        样式模块,
    )

def 建(文档,标签,类名=None):
    '造一个挂了官方类名的节点'
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    return 标样式模块(节点,样式模块)

def 挂组件(父,组件):
    '画出组件并挂上'
    if 组件 is None or 父 is None:
        return None
    节点=组件.渲染()
    if 节点 is not None and hasattr(节点,'tagName'):
        标样式模块(节点,样式模块)
        父.appendChild(节点)
    return 节点

def 画图标(窗口,工厂,尺寸=None):
    '按边长画一枚已有图标'
    属性={'window':窗口}
    if 尺寸 is not None:
        属性['size']=尺寸
    return 工厂(属性)

def 预览地址(文件名):
    '把迁移来的中文预览图读成数据地址'
    路径=os.path.join(os.path.dirname(__file__),'静态资产',文件名)
    句柄=open(路径,'rb')
    数据=句柄.read()
    句柄.close()
    return 'data:image/svg+xml;base64,'+base64.b64encode(数据).decode('ascii')

def 包状态(包):
    '卡片状态：异常、运行或关闭'
    if 包.get('error') is not None:
        return 'problem'
    if 包.get('enabled') is True:
        return 'running'
    return 'disabled'

def 可更新(包):
    '已安装且可移除，目录版本或 link 来源和当前不同'
    目标=包.get('installTarget')
    if 包.get('installed') is not True or 包.get('removable') is not True:
        return False
    if 包.get('availability')=='installation' or 目标 is None:
        return False
    if 包.get('version')!=目标.get('version'):
        return True
    来源=包.get('source')
    是链接=目标['spec'].startswith('link:') or (isinstance(来源,str) and 来源.startswith('link:'))
    return 是链接 and 来源!=目标['spec']

def 可选包秩(名称):
    '始终展示的在前，未点名的居中，更多列表垫后'
    始终=始终展示.index(名称) if 名称 in 始终展示 else -1
    if 始终>=0:
        return 始终
    垫后=更多包.index(名称) if 名称 in 更多包 else -1
    if 垫后<0:
        return len(始终展示)
    return len(始终展示)+1+垫后

def 行引用(行):
    '详情槽看到的一行'
    return {'rowId':行['rowId'],'moduleName':行['moduleName'],'enabled':行['enabled']}

def 包引用(包):
    '详情槽看到的一个组合包'
    引用={
        'name':包['name'],
        'installed':包['installed'],
        'availability':包['availability'],
        'official':包['official'],
        'enabled':包['enabled'],
        'rows':[行引用(行) for 行 in 包['rows']],
    }
    if 包.get('version') is not None:
        引用['version']=包['version']
    return 引用

def 注册表名单(注册表列,已解析):
    '按中文名单分隔符拼注册表名'
    名列=[注册表文案对(项,已解析)['name'] for 项 in 注册表列]
    return 中文句('registryListSeparator').join(名列)

def 输入问题句(问题,已解析):
    '检查拒绝时字段下的一句'
    问过=问题['registries'] if 问题.get('registries') is not None else []
    if 问题['problem']=='network' and len(问过)>1:
        return 中文句('installProblemNetworkAll',{'registries':注册表名单(问过,已解析)})
    return 中文句(输入问题键[问题['problem']],{'reason':问题['reason']})

def 失败句(失败,安装):
    '失败屏的一句。兼容性拒绝优先于 pnpm 分类'
    if 失败 is None:
        return 中文句('installFailureGeneric')
    if 失败.get('code')=='incompatible-version':
        错误={'code':失败['code'],'installing':True}
        if 失败.get('incompatible') is not None:
            错误['incompatible']=失败['incompatible']
        return 管理文案(错误)
    待允许=失败.get('pendingBuilds')
    if 失败.get('kind')=='build-blocked' and (待允许 is None or len(待允许)==0):
        return 中文句('installFailureBuildBlockedManual')
    主体=None if 安装 is None else 安装.get('subject')
    主机=None if 主体 is None else 主体.get('host')
    if 失败.get('failedAt')=='spec-host' and 主机 is not None:
        return 中文句('installFailureNetworkHost',{'host':主机})
    问过=[] if 安装 is None or 安装.get('attempts') is None else 安装['attempts']['registries']
    if 失败.get('failedAt')=='registry' and 失败.get('kind') in ('network','timeout') and len(问过)>1:
        已解析=None
        if 安装.get('registries') is not None:
            已解析=安装['registries'].get('resolved')
        return 中文句('installFailureNetworkAll',{'registries':注册表名单(问过,已解析)})
    if 失败.get('kind') is not None:
        return 中文句(失败种类键[失败['kind']])
    if 失败.get('code') is not None:
        return 管理文案({'code':失败['code'],'diagnostic':失败.get('reason')})
    if 失败.get('reason') in (None,''):
        return 中文句('installFailureGeneric')
    return 失败['reason']

def 部件摘要(行表):
    '组件计数：总数，以及出现过的状态'
    异常=0
    关闭=0
    运行=0
    for 行 in 行表:
        if 行.get('phase')=='failed':
            异常=异常+1
        if 行.get('enabled') is not True:
            关闭=关闭+1
        if 行.get('enabled') is True and 行.get('phase')=='active':
            运行=运行+1
    句列=[中文句('partsCountTotal',{'count':str(len(行表))})]
    if 运行>0:
        句列.append(中文句('partsCountRunning',{'count':str(运行)}))
    if 关闭>0:
        句列.append(中文句('partsCountOff',{'count':str(关闭)}))
    if 异常>0:
        句列.append(中文句('partsCountFailed',{'count':str(异常)}))
    return ' · '.join(句列)

def 终端文案():
    '安装终端用的中文标签'
    def 命令行(行号):
        '命令行的无障碍名'
        return 中文句('terminalCommandLine',{'n':str(行号)})
    def 信号(信号名):
        '信号名'
        return 中文句('terminalSignal',{'signal':信号名})
    def 退出码(码):
        '退出码'
        return 中文句('terminalExitCode',{'code':str(码)})
    def 展开名(隐):
        '展开其余行的无障碍名'
        return 中文句('terminalExpandAria',{'n':str(隐)})
    def 展开文(隐):
        '展开其余行'
        return 中文句('terminalExpand',{'n':str(隐)})
    return {
        'commandLine':命令行,
        'signal':信号,
        'exitCode':退出码,
        'noExitCode':中文句('terminalNoExitCode'),
        'running':中文句('terminalRunning'),
        'failed':中文句('terminalFailed'),
        'done':中文句('terminalDone'),
        'copy':中文句('terminalCopy'),
        'copied':中文句('terminalCopied'),
        'noOutput':中文句('terminalNoOutput'),
        'collapseAria':中文句('terminalCollapseAria'),
        'collapse':中文句('terminalCollapse'),
        'expandAria':展开名,
        'expand':展开文,
    }

class 安装输入法:
    '记住一次输入法组合，含 Safari 组合结束后 10 毫秒'
    def __init__(自身):
        '组合尚未开始'
        自身.活动=False
        自身.直到=0

    def 复位(自身):
        '对话框阶段变了就清掉组合'
        自身.活动=False
        自身.直到=0

    def 开始(自身,事件=None):
        '组合开始'
        自身.活动=True

    def 结束(自身,事件=None):
        '组合结束，再留 10 毫秒'
        自身.活动=False
        自身.直到=时间毫秒()+10

    def 失焦(自身,事件=None):
        '离开输入框'
        自身.活动=False
        自身.直到=0

    def 正在输入(自身,事件):
        '组合中、229 或刚结束的窗口里，回车不算提交'
        码=getattr(事件,'keyCode',None)
        if getattr(事件,'isComposing',False) is True or 码==229:
            return True
        if 自身.活动 is True:
            return True
        return 时间毫秒()<自身.直到

def 时间毫秒():
    '当前毫秒'
    import time
    return int(time.time()*1000)

class 包画稿:
    '包或行的图。解码失败就换成默认画稿'
    def __init__(自身,属性):
        '记下地址'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.失败源=None

    def 渲染(自身):
        '有地址且没失败就画 img，否则画默认或子智能体稿'
        属性=自身.属性
        窗口=窗口于(属性)
        文档=窗口.document
        是行=属性.get('row') is True
        尺寸=属性['size'] if 'size' in 属性 else (行画稿尺寸 if 是行 else 卡片画稿尺寸)
        地址=属性.get('src')
        if 地址 is None or 地址==自身.失败源:
            类=插件画稿子智能体 if 是行 else 插件画稿默认
            return 类({'window':窗口,'size':尺寸}).渲染()
        图=文档.createElement('img')
        图.className='packageImage'
        标样式模块(图,样式模块)
        图.src=地址
        图.width=尺寸
        图.height=尺寸
        图.alt=''
        def 失败(事件=None):
            '这次地址解码失败'
            自身.失败源=地址
            if 属性.get('重画') is not None:
                属性['重画']()
        图.addEventListener('error',失败)
        return 图

class 包预览:
    '详情页上的功能预览。失败只在原处说明'
    def __init__(自身,属性):
        '记下地址和标题'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.失败源=None

    def 渲染(自身):
        '失败时写出无法显示，否则画图'
        属性=自身.属性
        窗口=窗口于(属性)
        文档=窗口.document
        地址=属性.get('src')
        if 地址==自身.失败源:
            段=建(文档,'p','reason')
            段.setAttribute('role','status')
            段.textContent=中文句('previewUnavailable')
            return 段
        图=文档.createElement('img')
        图.className='packagePreview'
        标样式模块(图,样式模块)
        图.src=地址
        图.alt=中文句('previewAlt',{'name':属性.get('title') or ''})
        def 失败(事件=None):
            '预览解码失败'
            自身.失败源=地址
            if 属性.get('重画') is not None:
                属性['重画']()
        图.addEventListener('error',失败)
        return 图

class 元数据错误:
    'Host 的元信息诊断，不改变管理权限'
    def __init__(自身,属性):
        '记下错误文本'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '没有错误就不画'
        错误=自身.属性.get('error')
        if 错误 is None:
            return None
        文档=窗口于(自身.属性).document
        段=建(文档,'p','reason')
        段.setAttribute('role','status')
        段.setAttribute('data-package-meta-error','')
        段.textContent=中文句('metadataError',{'error':错误})
        return 段

class 启用开关:
    '组合包的启用开关。Host 拒绝或读不了时锁上，并说明原因'
    def __init__(自身,属性):
        '记下包和回调'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '画出开关'
        属性=自身.属性
        包=属性['pkg']
        锁=包.get('readOnlyReason') is not None
        读不了=包.get('enabled') is not True and 包.get('error') is not None
        可装缺文件=包.get('availability')=='missing' and 包.get('installTarget') is not None
        开关属性={
            'window':窗口于(属性),
            'checked':包.get('enabled') is True,
            'label':中文句('enableToggle',{'name':属性.get('title') or ''}),
            'disabled':属性.get('busy') is True or 锁 or (读不了 and not 可装缺文件),
            'onChange':属性.get('onSetEnabled'),
        }
        if 包.get('readOnlyReason') is not None:
            开关属性['title']=管理文案({'code':包['readOnlyReason']})
        return 开关(开关属性).渲染()

class 行开关:
    '一行的开关。没有活入口或 Host 拒绝时锁上'
    def __init__(自身,属性):
        '记下行'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '画出组件开关'
        属性=自身.属性
        行=属性['row']
        锁=行.get('readOnlyReason') is not None or 行.get('entryId') is None
        开关属性={
            'window':窗口于(属性),
            'checked':行.get('enabled') is True,
            'label':中文句('partToggle',{'name':属性.get('title') or ''}),
            'disabled':属性.get('busy') is True or 锁,
            'onChange':属性.get('onChange'),
        }
        if 行.get('readOnlyReason') is not None:
            开关属性['title']=管理文案({'code':行['readOnlyReason']})
        return 开关(开关属性).渲染()

class 卡片头:
    '卡片共有的头：画稿、名称、标签、一行说明和末尾控件'
    def __init__(自身,属性):
        '记下标题和打开动作'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '画出卡片头'
        属性=自身.属性
        文档=窗口于(属性).document
        头=建(文档,'div','cardHead')
        标=建(文档,'span','cardIcon')
        标.setAttribute('aria-hidden','true')
        挂上(标,属性.get('icon'))
        头.appendChild(标)
        主=建(文档,'div','cardMain')
        行=建(文档,'div','titleRow')
        钮=建(文档,'button','cardTitle cardOpen')
        钮.type='button'
        钮.setAttribute('aria-label',中文句('openDetail',{'name':属性.get('title') or ''}))
        钮.textContent=属性.get('title') or ''
        def 打开(事件=None):
            '打开这一张'
            if 属性.get('onOpen') is not None:
                属性['onOpen']()
        钮.addEventListener('click',打开)
        行.appendChild(钮)
        if 属性.get('tags') is not None:
            挂上(行,属性['tags'])
        主.appendChild(行)
        if 属性.get('description') is not None:
            说明=建(文档,'span','cardDesc')
            挂上(说明,属性['description'])
            主.appendChild(说明)
        头.appendChild(主)
        if 属性.get('end') is not None:
            尾=建(文档,'div','cardEnd')
            挂上(尾,属性['end'])
            头.appendChild(尾)
        return 头

class 列表骨架:
    '第一次读取时的占位卡片'
    def __init__(自身,属性):
        '记下无障碍名'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '画出四张空卡片'
        文档=窗口于(自身.属性).document
        区=建(文档,'section','group')
        区.setAttribute('role','status')
        区.setAttribute('aria-label',自身.属性.get('label') or '')
        区.setAttribute('data-plugin-loading','')
        头=建(文档,'div','groupHead')
        头.setAttribute('aria-hidden','true')
        题=建(文档,'span','groupTitle skeletonText skeletonHeading')
        题.appendChild(建(文档,'span','skeletonFill skeletonBar'))
        头.appendChild(题)
        区.appendChild(头)
        列=建(文档,'ul','cards')
        列.setAttribute('aria-hidden','true')
        for 序 in range(4):
            项=建(文档,'li','card')
            卡头=建(文档,'div','cardHead')
            卡头.appendChild(建(文档,'span','cardIcon skeletonFill skeletonIcon'))
            主=建(文档,'div','cardMain')
            行=建(文档,'div','titleRow')
            名=建(文档,'span','cardTitle skeletonText skeletonTitle')
            名.appendChild(建(文档,'span','skeletonFill skeletonBar'))
            行.appendChild(名)
            主.appendChild(行)
            述=建(文档,'span','cardDesc skeletonText skeletonDescription')
            述.appendChild(建(文档,'span','skeletonFill skeletonBar'))
            主.appendChild(述)
            卡头.appendChild(主)
            卡头.appendChild(建(文档,'div','cardEnd skeletonActions'))
            项.appendChild(卡头)
            列.appendChild(项)
        区.appendChild(列)
        return 区

class 详情顶:
    '每页共有的顶：返回屑、图标和动作'
    def __init__(自身,属性):
        '记下返回动作'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '画出返回和动作行'
        属性=自身.属性
        文档=窗口于(属性).document
        顶=建(文档,'div','detailTop')
        顶.setAttribute('data-window-drag','')
        屑=建(文档,'button','crumb')
        屑.type='button'
        屑.setAttribute('aria-label',属性.get('crumbLabel') or '')
        标=画图标(窗口于(属性),图标下箭头描边常规,14)
        if 标 is not None:
            标.className='crumbIcon'
            标.setAttribute('aria-hidden','true')
            标样式模块(标,样式模块)
            屑.appendChild(标)
        字=文档.createElement('span')
        字.textContent=属性.get('crumbText') or ''
        屑.appendChild(字)
        def 返回(事件=None):
            '回到上一层'
            if 属性.get('onBack') is not None:
                属性['onBack']()
        屑.addEventListener('click',返回)
        顶.appendChild(屑)
        头=建(文档,'div','detailHead')
        图=建(文档,'span','cardIcon')
        图.setAttribute('aria-hidden','true')
        挂上(图,属性.get('icon'))
        头.appendChild(图)
        if 属性.get('actions') is not None:
            挂上(头,属性['actions'])
        顶.appendChild(头)
        return 顶

class 来源区:
    '声明的安装来源和版本'
    def __init__(自身,属性):
        '记下包'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '内置且没有来源、未安装、也不是可选包时不画'
        包=自身.属性['pkg']
        if 包.get('source') is None and 包.get('installed') is not True and 包.get('availability')=='installation' and 包.get('optional') is not True:
            return None
        文档=窗口于(自身.属性).document
        区=建(文档,'section','detailSection')
        区.setAttribute('data-plugin-source','')
        题=建(文档,'h4','sectionTitle')
        题.textContent=中文句('sourceTitle')
        区.appendChild(题)
        表=建(文档,'dl','facts')
        def 加行(名,值节点):
            '一行事实'
            行=文档.createElement('div')
            名节=文档.createElement('dt')
            名节.textContent=名
            值节=文档.createElement('dd')
            if isinstance(值节点,str):
                值节.textContent=值节点
            else:
                值节.appendChild(值节点)
            行.appendChild(名节)
            行.appendChild(值节)
            表.appendChild(行)
        if 包.get('source') is not None:
            码=文档.createElement('code')
            码.textContent=包['source']
            加行(中文句('sourceSpec'),码)
        elif 包.get('availability')=='missing':
            键='statusMissingFiles' if 包.get('installed') is True else 'sourceNotInstalled'
            加行(中文句('sourceSpec'),中文句(键))
        else:
            加行(中文句('sourceSpec'),中文句('sourceBuiltIn'))
        if 包.get('version') is not None:
            加行(中文句('sourceVersion'),包['version'])
        目标=包.get('installTarget')
        if 目标 is not None:
            码=文档.createElement('code')
            码.textContent=目标.get('spec') or ''
            加行(中文句('sourceTargetSpec'),码)
            加行(中文句('sourceTargetVersion'),目标.get('version') or '')
        区.appendChild(表)
        return 区

class 行区:
    '按声明顺序列出组件。超过十行才出现筛选'
    def __init__(自身,属性):
        '筛选从空开始'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.筛选=''

    def 渲染(自身):
        '画出标题、计数、筛选和行'
        属性=自身.属性
        窗口=窗口于(属性)
        文档=窗口.document
        行表=属性.get('rows') or []
        解析=属性['resolveText']
        查询=自身.筛选.strip().lower()
        显示=[]
        for 行 in 行表:
            文=行文案(行,解析)
            块=[文['title'],文.get('description'),行['rowId'],行['moduleName']]
            命中=查询=='' or any(isinstance(项,str) and 查询 in 项.lower() for 项 in 块)
            if 命中:
                显示.append((行,文))
        区=建(文档,'section','detailSection')
        区.setAttribute('data-plugin-rows','')
        头=建(文档,'div','sectionHead')
        题=建(文档,'h4','sectionTitle')
        题.textContent=中文句('partsLabel')
        头.appendChild(题)
        if len(行表)>0:
            计数=建(文档,'span','sectionCount')
            计数.textContent=部件摘要(行表)
            头.appendChild(计数)
        区.appendChild(头)
        if len(行表)==0:
            空=建(文档,'p','status')
            空.textContent=中文句('partsEmpty')
            区.appendChild(空)
        if len(行表)>行筛选阈值:
            框=文档.createElement('input')
            框.type='search'
            框.className='partsFilter'
            标样式模块(框,样式模块)
            框.placeholder=中文句('partsFilter')
            框.setAttribute('aria-label',中文句('partsFilter'))
            框.value=自身.筛选
            def 改(事件):
                '更新筛选并重画'
                自身.筛选=事件.target.value
                if 属性.get('重画') is not None:
                    属性['重画']()
            框.addEventListener('input',改)
            区.appendChild(框)
        if len(行表)>0 and len(显示)==0:
            无=建(文档,'p','status')
            无.textContent=中文句('partsFilterEmpty')
            区.appendChild(无)
        if len(显示)>0:
            列=建(文档,'ul','rows')
            for 行,文 in 显示:
                项=建(文档,'li','row')
                项.setAttribute('data-plugin-row',行['entryId'] if 行.get('entryId') is not None else 行['rowId'])
                if 行.get('phase')=='failed':
                    项.setAttribute('data-state','failed')
                elif 行.get('enabled') is not True:
                    项.setAttribute('data-state','off')
                线=建(文档,'div','rowLine')
                图盒=建(文档,'span','rowIcon')
                图盒.setAttribute('aria-hidden','true')
                图=包画稿({'window':窗口,'src':None if 行.get('meta') is None else 行['meta'].get('icon'),'row':True,'重画':属性.get('重画')}).渲染()
                if 图 is not None:
                    图盒.appendChild(图)
                线.appendChild(图盒)
                主=建(文档,'div','rowMain')
                配置=属性.get('configure')
                有页=配置 is not None and 配置['has'](行) is True
                if 有页:
                    开=建(文档,'button','rowOpen')
                    开.type='button'
                    开.setAttribute('aria-label',中文句('configureRow',{'name':文['title']}))
                    名=建(文档,'span','rowId')
                    名.textContent=文['title']
                    开.appendChild(名)
                    箭=画图标(窗口,图标右chevron14,14)
                    if 箭 is not None:
                        箭.className='rowOpenIcon'
                        箭.setAttribute('aria-hidden','true')
                        开.appendChild(箭)
                    def 点开(事件=None,当前行=行):
                        '打开这一行的配置'
                        配置['open'](当前行)
                    开.addEventListener('click',点开)
                    主.appendChild(开)
                else:
                    名=建(文档,'span','rowId')
                    名.textContent=文['title']
                    主.appendChild(名)
                if 文.get('description') is not None:
                    述=建(文档,'span','rowModule')
                    述.textContent=文['description']
                    主.appendChild(述)
                if 文['title']!=行['rowId']:
                    码=建(文档,'code','rowModule')
                    码.textContent=行['rowId']
                    主.appendChild(码)
                if 文['title']!=行['moduleName']:
                    码=建(文档,'code','rowModule')
                    码.textContent=行['moduleName']
                    主.appendChild(码)
                线.appendChild(主)
                态=建(文档,'span','rowState')
                点态='idle'
                if 行.get('enabled') is True and 行.get('phase') is not None:
                    点态=阶段点[行['phase']]
                点=状态点({'window':窗口,'state':点态}).渲染()
                if 点 is not None:
                    态.appendChild(点)
                if 行.get('enabled') is not True:
                    态文=中文句('partOff')
                elif 行.get('phase') is None:
                    态文=中文句('rowStateIdle')
                else:
                    态文=中文句(阶段键[行['phase']])
                态.appendChild(文档.createTextNode(态文))
                线.appendChild(态)
                切换=属性.get('toggle')
                if 切换 is not None:
                    def 改开关(启用,当前行=行):
                        '启停这一行'
                        切换['onSetEnabled'](当前行,启用)
                    开关节点=行开关({
                        'window':窗口,'row':行,'title':文['title'],
                        'busy':切换['busy'](行),
                        'onChange':改开关,
                    }).渲染()
                    if 开关节点 is not None:
                        线.appendChild(开关节点)
                项.appendChild(线)
                错=None if 行.get('meta') is None else 行['meta'].get('error')
                错节点=元数据错误({'window':窗口,'error':错}).渲染()
                if 错节点 is not None:
                    项.appendChild(错节点)
                列.appendChild(项)
            区.appendChild(列)
        return 区

class 包卡片:
    '一张打开详情的组合包卡片'
    def __init__(自身,属性):
        '记下包'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '画出名称、说明、标签和开关'
        属性=自身.属性
        窗口=窗口于(属性)
        文档=窗口.document
        包=属性['pkg']
        文=包文案(包,属性['resolveText'])
        状态=包状态(包)
        项=建(文档,'li','card cardLink')
        项.setAttribute('data-plugin-package',包['name'])
        项.setAttribute('data-plugin-status',状态)
        if 属性.get('highlighted') is True:
            项.setAttribute('data-plugin-highlight','')
        标签盒=文档.createElement('span')
        if 文['beta'] is True:
            挂组件(标签盒,标签({'window':窗口,'className':'statusTag','tone':'info','children':中文句('statusBeta')}))
        if 状态=='problem':
            挂组件(标签盒,标签({'window':窗口,'className':'statusTag','tone':'danger','children':中文句('statusProblem')}))
        if 包.get('availability')=='missing':
            键='statusMissingFiles' if 包.get('installed') is True else 'statusNotInstalled'
            挂组件(标签盒,标签({'window':窗口,'className':'statusTag','children':中文句(键)}))
        if 可更新(包):
            挂组件(标签盒,标签({'window':窗口,'className':'statusTag','tone':'info','children':中文句('statusUpdateAvailable')}))
        开关节点=启用开关({
            'window':窗口,'pkg':包,'title':文['title'],'busy':属性.get('busy'),
            'onSetEnabled':属性.get('onSetEnabled'),
        }).渲染()
        头=卡片头({
            'window':窗口,'title':文['title'],'onOpen':属性.get('onOpen'),
            'icon':包画稿({'window':窗口,'src':None if 包.get('meta') is None else 包['meta'].get('icon'),'重画':属性.get('重画')}).渲染(),
            'tags':标签盒,'description':文.get('description'),'end':开关节点,
        }).渲染()
        项.appendChild(头)
        错=None if 包.get('meta') is None else 包['meta'].get('error')
        错节点=元数据错误({'window':窗口,'error':错}).渲染()
        if 错节点 is not None:
            项.appendChild(错节点)
        return 项

class 条目卡片:
    '一张打开官方插件页的卡片'
    def __init__(自身,属性):
        '记下条目'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '标题来自登记，一行说明来自 summary'
        属性=自身.属性
        窗口=窗口于(属性)
        文档=窗口.document
        条目=属性['item']
        项=建(文档,'li','card cardLink')
        项.setAttribute('data-plugin-item',条目['id'])
        类=条目画稿类.get(条目['id'],插件画稿默认)
        头=卡片头({
            'window':窗口,'title':条目['label'],'onOpen':属性.get('onOpen'),
            'icon':类({'window':窗口,'size':卡片画稿尺寸}).渲染(),
            'description':属性['renderSlot']('plugins.item',{'view':'summary'},{'only':条目['id']}),
        }).渲染()
        项.appendChild(头)
        return 项

class 条目详情:
    '官方插件自己的页'
    def __init__(自身,属性):
        '记下条目和表单'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '屑、动作、说明、表单和贡献分区'
        属性=自身.属性
        窗口=窗口于(属性)
        文档=窗口.document
        条目=属性['item']
        主体={'kind':'item','id':条目['id']}
        根=建(文档,'div','detail')
        根.setAttribute('data-plugin-item-detail',条目['id'])
        动作=建(文档,'div','detailActions')
        挂上(动作,属性['renderSlot']('plugins.detail.actions',{'subject':主体}))
        类=条目画稿类.get(条目['id'],插件画稿默认)
        根.appendChild(详情顶({
            'window':窗口,
            'crumbLabel':中文句('backToList'),
            'crumbText':中文句('crumbRoot'),
            'onBack':属性.get('onBack'),
            'icon':类({'window':窗口,'size':卡片画稿尺寸}).渲染(),
            'actions':动作,
        }).渲染())
        主=建(文档,'div','detailMain')
        行=建(文档,'div','titleRow')
        题=建(文档,'h3','detailTitle')
        题.textContent=条目['label']
        行.appendChild(题)
        挂上(行,属性['renderSlot']('plugins.detail.badge',{'subject':主体}))
        主.appendChild(行)
        述=建(文档,'p','detailDesc')
        挂上(述,属性['renderSlot']('plugins.item',{'view':'summary'},{'only':条目['id']}))
        主.appendChild(述)
        根.appendChild(主)
        区=建(文档,'div','detailSections')
        配置=建(文档,'section','detailSection')
        配置.setAttribute('data-plugin-config','')
        挂上(配置,属性['renderSlot']('plugins.item',{'view':'page','form':属性.get('form')},{'only':条目['id']}))
        区.appendChild(配置)
        挂上(区,属性['renderSlot']('plugins.detail.section',{'subject':主体}))
        根.appendChild(区)
        return 根

class 行详情:
    '一行自己的配置页'
    def __init__(自身,属性):
        '记下行和表单'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '技术名留在标题旁边，表单来自这一行的登记'
        属性=自身.属性
        窗口=窗口于(属性)
        文档=窗口.document
        包=属性['pkg']
        行=属性['row']
        包文=包文案(包,属性['resolveText'])
        行文=行文案(行,属性['resolveText'])
        键=行配置键(包['name'],行['rowId'])
        主体={'kind':'row','pkg':包引用(包),'row':行引用(行)}
        根=建(文档,'div','detail')
        根.setAttribute('data-plugin-row-detail',键)
        动作=建(文档,'div','detailActions')
        挂上(动作,属性['renderSlot']('plugins.detail.actions',{'subject':主体}))
        根.appendChild(详情顶({
            'window':窗口,
            'crumbLabel':中文句('backToPackage',{'name':包文['title']}),
            'crumbText':包文['title'],
            'onBack':属性.get('onBack'),
            'icon':包画稿({
                'window':窗口,
                'src':None if 行.get('meta') is None else 行['meta'].get('icon'),
                'row':True,'size':卡片画稿尺寸,'重画':属性.get('重画'),
            }).渲染(),
            'actions':动作,
        }).渲染())
        主=建(文档,'div','detailMain')
        题行=建(文档,'div','titleRow')
        题=建(文档,'h3','detailTitle')
        题.textContent=行文['title']
        题行.appendChild(题)
        挂上(题行,属性['renderSlot']('plugins.detail.badge',{'subject':主体}))
        主.appendChild(题行)
        if 行文['title']!=行['rowId']:
            名=建(文档,'p','detailName')
            码=文档.createElement('code')
            码.textContent=行['rowId']
            名.appendChild(码)
            主.appendChild(名)
        模块=建(文档,'p','detailName')
        码=文档.createElement('code')
        码.textContent=行['moduleName']
        模块.appendChild(码)
        主.appendChild(模块)
        述=建(文档,'p','detailDesc')
        if 行文.get('description') is not None:
            述.textContent=行文['description']
        else:
            挂上(述,属性['renderSlot']('plugins.row.config',{'view':'summary'},{'entryKey':键}))
        主.appendChild(述)
        根.appendChild(主)
        错=None if 行.get('meta') is None else 行['meta'].get('error')
        错节点=元数据错误({'window':窗口,'error':错}).渲染()
        if 错节点 is not None:
            根.appendChild(错节点)
        区=建(文档,'div','detailSections')
        区.setAttribute('data-plugin-config','')
        挂上(区,属性['renderSlot']('plugins.row.config',{'view':'page','form':属性.get('form')},{'entryKey':键}))
        挂上(区,属性['renderSlot']('plugins.detail.section',{'subject':主体}))
        根.appendChild(区)
        return 根

class 包详情:
    '一个组合包的页：开关、卸载、行和来源'
    def __init__(自身,属性):
        '记下包。行筛选由行区自己留'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.行区=None

    def 渲染(自身):
        '画出详情'
        属性=自身.属性
        窗口=窗口于(属性)
        文档=窗口.document
        包=属性['pkg']
        文=包文案(包,属性['resolveText'])
        状态=包状态(包)
        主体={'kind':'bundle','pkg':包引用(包)}
        根=建(文档,'div','detail')
        根.setAttribute('data-plugin-detail',包['name'])
        动作=建(文档,'div','detailActions')
        挂上(动作,属性['renderSlot']('plugins.detail.actions',{'subject':主体}))
        if 可更新(包):
            挂组件(动作,按钮({
                'window':窗口,'variant':'outline','size':'sm',
                'icon':画图标(窗口,图标刷新16,13),
                'disabled':属性.get('busy') is True,
                'aria-label':中文句('updateLabel',{'name':文['title']}),
                'onClick':属性.get('onUpdate'),
                'children':中文句('update'),
            }))
        if 包.get('installed') is True or 包.get('removable') is True:
            挂组件(动作,按钮({
                'window':窗口,'variant':'outline','size':'sm','className':'danger',
                'icon':画图标(窗口,图标垃圾桶16,13),
                'aria-label':中文句('uninstallLabel',{'name':文['title']}),
                'disabled':属性.get('busy') is True or 包.get('removable') is not True or 包.get('readOnlyReason') is not None,
                'onClick':属性.get('onUninstall'),
                'children':中文句('uninstall'),
            }))
        挂组件(动作,启用开关({
            'window':窗口,'pkg':包,'title':文['title'],'busy':属性.get('busy'),
            'onSetEnabled':属性.get('onSetEnabled'),
        }))
        屑键='backToPackage' if 属性.get('inMore') is True else 'backToList'
        屑文='moreTitle' if 属性.get('inMore') is True else 'crumbRoot'
        根.appendChild(详情顶({
            'window':窗口,
            'crumbLabel':中文句(屑键,{'name':中文句('moreTitle')}) if 属性.get('inMore') is True else 中文句('backToList'),
            'crumbText':中文句(屑文),
            'onBack':属性.get('onBack'),
            'icon':包画稿({'window':窗口,'src':None if 包.get('meta') is None else 包['meta'].get('icon'),'重画':属性.get('重画')}).渲染(),
            'actions':动作,
        }).渲染())
        主=建(文档,'div','detailMain')
        题行=建(文档,'div','titleRow')
        题=建(文档,'h3','detailTitle')
        题.textContent=文['title']
        题行.appendChild(题)
        if 包.get('version') is not None:
            挂组件(题行,标签({'window':窗口,'className':'versionTag','tone':'neutral','children':中文句('versionTag',{'version':包['version']})}))
        if 文['beta'] is True:
            挂组件(题行,标签({'window':窗口,'className':'statusTag','tone':'info','children':中文句('statusBeta')}))
        if 状态=='problem':
            挂组件(题行,标签({'window':窗口,'className':'statusTag','tone':'danger','children':中文句('statusProblem')}))
        if 包.get('availability')=='missing':
            键='statusMissingFiles' if 包.get('installed') is True else 'statusNotInstalled'
            挂组件(题行,标签({'window':窗口,'className':'statusTag','children':中文句(键)}))
        if 可更新(包):
            挂组件(题行,标签({'window':窗口,'className':'statusTag','tone':'info','children':中文句('statusUpdateAvailable')}))
        挂上(题行,属性['renderSlot']('plugins.detail.badge',{'subject':主体}))
        主.appendChild(题行)
        名=建(文档,'p','detailName')
        码=文档.createElement('code')
        码.setAttribute('data-plugin-name','')
        码.textContent=包['name']
        名.appendChild(码)
        主.appendChild(名)
        if 文.get('description') is not None:
            述=建(文档,'p','detailDesc')
            述.textContent=文['description']
            主.appendChild(述)
        根.appendChild(主)
        错=None if 包.get('meta') is None else 包['meta'].get('error')
        错节点=元数据错误({'window':窗口,'error':错}).渲染()
        if 错节点 is not None:
            根.appendChild(错节点)
        if 包.get('error') is not None:
            因=建(文档,'p','reason')
            因.setAttribute('role','status')
            因.textContent=中文句('reasonLabel')+'：'+管理文案(包['error'])
            根.appendChild(因)
        if 包.get('readOnlyReason') is not None:
            因=建(文档,'p','reason')
            因.setAttribute('role','status')
            因.textContent=管理文案({'code':包['readOnlyReason']})
            根.appendChild(因)
        文件=预览文件.get(包['name'])
        if 文件 is not None:
            预览=包预览({'window':窗口,'src':预览地址(文件),'title':文['title'],'重画':属性.get('重画')}).渲染()
            if 预览 is not None:
                根.appendChild(预览)
        区=建(文档,'div','detailSections')
        if 属性.get('configured') is True:
            配置=建(文档,'section','detailSection')
            配置.setAttribute('data-plugin-config','')
            挂上(配置,属性['renderSlot']('plugins.bundle.config',{'view':'page'},{'entryKey':包['name']}))
            区.appendChild(配置)
        if 包.get('availability')!='missing':
            if 自身.行区 is None or 自身.行区.属性.get('rows') is not 包['rows']:
                自身.行区=行区({
                    'window':窗口,'rows':包['rows'],'resolveText':属性['resolveText'],
                    'toggle':属性.get('toggle'),'configure':属性.get('configure'),'重画':属性.get('重画'),
                })
            else:
                自身.行区.属性= {
                    'window':窗口,'rows':包['rows'],'resolveText':属性['resolveText'],
                    'toggle':属性.get('toggle'),'configure':属性.get('configure'),'重画':属性.get('重画'),
                }
            区.appendChild(自身.行区.渲染())
        来源=来源区({'window':窗口,'pkg':包}).渲染()
        if 来源 is not None:
            区.appendChild(来源)
        挂上(区,属性['renderSlot']('plugins.detail.section',{'subject':主体}))
        根.appendChild(区)
        return 根

class 主体块:
    '安装对话框里的名称、说明、版本和规格'
    def __init__(自身,属性):
        '记下行'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '按有没有说明和版本画'
        属性=自身.属性
        文档=窗口于(属性).document
        行=属性['lines']
        根=建(文档,'div','subject')
        根.setAttribute('data-install-subject',行['spec'])
        名=建(文档,'p','subjectName')
        名.textContent=行['title']
        根.appendChild(名)
        if 行.get('description') is not None:
            述=建(文档,'p','subjectDesc')
            述.textContent=行['description']
            根.appendChild(述)
        if 行.get('version') is not None:
            版=建(文档,'p','subjectMeta')
            版.textContent=中文句('installVersion',{'version':行['version']})
            根.appendChild(版)
        if 行.get('showSpec') is True:
            规格=建(文档,'p','subjectSpec')
            规格.textContent=行['spec']
            根.appendChild(规格)
        return 根

class 添加插件菜单:
    '主按钮安装，旁边的菜单列出其余添加方式'
    def __init__(自身,属性):
        '菜单开始是关的'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.开=False

    def 渲染(自身):
        '画出一组按钮。菜单用页面样式，因为共享菜单不收任意子节点'
        属性=自身.属性
        窗口=窗口于(属性)
        文档=窗口.document
        根=建(文档,'span','addGroup')
        根.setAttribute('role','group')
        根.setAttribute('aria-label',中文句('addPlugin'))
        挂组件(根,按钮({
            'window':窗口,'variant':'primary','size':'sm','className':'addPrimary',
            'icon':画图标(窗口,图标加号16,13),
            'disabled':属性.get('disabled') is True,
            'onClick':自身.主安装,
            'children':中文句('addPlugin'),
        }))
        更多=按钮({
            'window':窗口,'variant':'primary','size':'sm','className':'addMore',
            'disabled':属性.get('disabled') is True,
            'children':画图标(窗口,图标下箭头描边常规,12),
        }).渲染()
        if 更多 is not None:
            更多.setAttribute('aria-label',中文句('chooseAddMethod'))
            更多.setAttribute('aria-haspopup','menu')
            更多.setAttribute('aria-expanded','true' if 自身.开 else 'false')
            def 点更多(事件=None):
                '翻转菜单'
                自身.开=自身.开 is not True
                if 属性.get('重画') is not None:
                    属性['重画']()
            更多.addEventListener('click',点更多)
            def 按下(事件):
                '关闭时按下方向键打开'
                if 自身.开 is not True and 事件.key=='ArrowDown':
                    事件.preventDefault()
                    自身.开=True
                    if 属性.get('重画') is not None:
                        属性['重画']()
            更多.addEventListener('keydown',按下)
            根.appendChild(更多)
        if 自身.开:
            单=建(文档,'div','addMenu')
            单.setAttribute('role','menu')
            项=文档.createElement('button')
            项.type='button'
            项.setAttribute('role','menuitem')
            项.className='菜单项'
            图=画图标(窗口,图标下载16,14)
            if 图 is not None:
                项.appendChild(图)
            文=建(文档,'span','addMenuItem')
            题=文档.createElement('span')
            题.textContent=中文句('installExisting')
            述=建(文档,'span','addMenuDescription')
            述.textContent=中文句('installExistingDescription')
            文.appendChild(题)
            文.appendChild(述)
            项.appendChild(文)
            def 选现成(事件=None):
                '关掉菜单并打开安装'
                自身.开=False
                if 属性.get('openInstall') is not None:
                    属性['openInstall']()
            项.addEventListener('click',选现成)
            单.appendChild(项)
            def 关掉():
                '贡献动作开始前先关菜单'
                自身.开=False
                if 属性.get('重画') is not None:
                    属性['重画']()
            挂上(单,属性['renderSlot']('plugins.add.actions',{'onDismiss':关掉}))
            文档.body.appendChild(单)
            自身.拆外=点外关闭(根,True,自身.点外,单)
        return 根

    def 主安装(自身):
        '关掉菜单并打开安装'
        自身.开=False
        if 自身.属性.get('openInstall') is not None:
            自身.属性['openInstall']()

    def 点外(自身,开着):
        '点到外面就关'
        if 开着:
            return
        自身.开=False
        if 自身.属性.get('重画') is not None:
            自身.属性['重画']()

class 确认对话框:
    '卸载前的确认'
    def __init__(自身,属性):
        '记下名字'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '画出确认和取消'
        属性=自身.属性
        窗口=窗口于(属性)
        取消=按钮({'window':窗口,'variant':'outline','onClick':属性.get('onCancel'),'children':中文句('cancel')}).渲染()
        确认=按钮({
            'window':窗口,'variant':'primary','className':'dangerButton',
            'onClick':属性.get('onConfirm'),'children':中文句('confirmUninstall'),
        }).渲染()
        脚=窗口.document.createElement('span')
        if 取消 is not None:
            脚.appendChild(取消)
        if 确认 is not None:
            标样式模块(确认,样式模块)
            脚.appendChild(确认)
        return 模态({
            'window':窗口,'open':True,'onClose':属性.get('onCancel'),
            'title':中文句('confirmUninstallTitle',{'name':属性.get('name') or ''}),
            'closeLabel':中文句('close'),
            'description':中文句('confirmUninstallDescription'),
            'footer':脚,
        }).渲染()

class 安装对话框:
    '规格、检查、安装中、已安装和失败。失败留下的脚本在这里允许'
    def __init__(自身,属性):
        '引导默认收起'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.引导开=False
        自身.自定义草稿=''
        自身.规格输入=安装输入法()
        自身.源输入=安装输入法()

    def 渲染(自身):
        '按阶段画。GitHub 连不上时先给镜像恢复'
        if getattr(自身,'拆锚定',None) is not None:
            自身.拆锚定()
            自身.拆锚定=None
        if getattr(自身,'拆外',None) is not None:
            自身.拆外()
            自身.拆外=None
        if getattr(自身,'拆键',None) is not None:
            自身.拆键()
            自身.拆键=None
        属性=自身.属性
        安装=属性['install']
        窗口=窗口于(属性)
        文档=窗口.document
        确保样式(文档)
        阶段=安装['phase']
        镜像=镜像恢复注册表(安装)
        if 镜像!='缺席':
            return self_镜像(自身,窗口,安装,镜像)
        if 阶段 in ('idle','checking') and 安装.get('confirmed') is not None:
            return self_已确认(自身,窗口,安装)
        if 阶段 in ('idle','checking'):
            return self_规格(自身,窗口,安装)
        return self_结果(自身,窗口,安装)

def self_镜像(自身,窗口,安装,镜像):
    'GitHub 失败后的镜像或换一种方式'
    另一=已问镜像(安装)
    def 采用(事件=None):
        '已经在问镜像时先打开包名引导'
        if 另一:
            自身.引导开=True
        自身.属性['onUseGithubMirror']()
    取消=按钮({'window':窗口,'variant':'outline','onClick':自身.属性['onClose'],'children':中文句('cancel')}).渲染()
    主=按钮({
        'window':窗口,'variant':'primary','onClick':采用,
        'children':中文句('installTryAnotherWay' if 另一 else 'installUseGithubMirror'),
    }).渲染()
    脚=窗口.document.createElement('span')
    if 取消 is not None:
        脚.appendChild(取消)
    if 主 is not None:
        脚.appendChild(主)
    键='installGithubTimeoutTitle' if 安装.get('failure') is not None and 安装['failure'].get('kind')=='timeout' else 'installGithubFailedTitle'
    return 模态({
        'window':窗口,'open':安装['open'],'onClose':自身.属性['onClose'],
        'title':中文句(键),'closeLabel':中文句('close'),
        'description':中文句('installGithubFailedDescription'),'footer':脚,
    }).渲染()

def self_已确认(自身,窗口,安装):
    '没有规格表。检查、拒绝后重试，或取消后安装'
    检查中=安装['phase']=='checking'
    问题=安装.get('inputError')
    体=建(窗口.document,'div','installBody')
    体.setAttribute('data-install-phase',安装['phase'])
    确认=安装['confirmed']
    体.appendChild(主体块({'window':窗口,'lines':{
        'spec':安装['spec'],'title':确认['title'],'version':确认['version'],'showSpec':True,
    }}).渲染())
    if 检查中:
        段=建(窗口.document,'p','status statusWithDot')
        段.setAttribute('role','status')
        点=状态点({'window':窗口,'state':'ongoing'}).渲染()
        if 点 is not None:
            段.appendChild(点)
        段.appendChild(窗口.document.createTextNode(中文句('installChecking')))
        体.appendChild(段)
    elif 问题 is not None:
        警=建(窗口.document,'p','inputError')
        警.setAttribute('role','alert')
        已解析=None if 安装.get('registries') is None else 安装['registries'].get('resolved')
        警.textContent=输入问题句(问题,已解析)
        体.appendChild(警)
    脚=None
    if not 检查中:
        关=按钮({'window':窗口,'variant':'outline','onClick':自身.属性['onClose'],'children':中文句('close')}).渲染()
        跑=按钮({
            'window':窗口,'variant':'primary','onClick':自身.属性['onRun'],
            'children':中文句('installRun' if 问题 is None else 'retry'),
        }).渲染()
        脚=窗口.document.createElement('span')
        if 关 is not None:
            脚.appendChild(关)
        if 跑 is not None:
            脚.appendChild(跑)
    return 模态({
        'window':窗口,'open':安装['open'],'onClose':自身.属性['onClose'],
        'title':中文句('installConfirmedTitle' if 问题 is None else 'installConfirmedRefused'),
        'closeLabel':中文句('close'),'className':'installDialog','children':体,'footer':脚,
    }).渲染()

def self_规格(自身,窗口,安装):
    '规格、引导和注册表'
    文档=窗口.document
    检查中=安装['phase']=='checking'
    空=安装['spec'].strip()==''
    选择=安装['registry']
    已解析=None if 安装.get('registries') is None else 安装['registries'].get('resolved')
    选中名=中文句('registryCustom') if 选择['kind']=='custom' else 注册表文案对(选择['registry'],已解析)['name']
    句=None if 安装.get('inputError') is None else 输入问题句(安装['inputError'],已解析)
    if 安装['spec']==安装示例仓库:
        模板提示=中文句('installGitTemplateHint')
    elif 安装['spec']==安装示例路径:
        模板提示=中文句('installPathTemplateHint')
    else:
        模板提示=None
    体=建(文档,'div','installBody')
    字段=建(文档,'div','installField')
    框=文档.createElement('input')
    框.type='text'
    if 安装.get('mirrorRecovery') is True:
        框.autofocus=True
    框.setAttribute('data-modal-autofocus','')
    框.value=安装['spec']
    框.placeholder=中文句('installSpecPlaceholder')
    框.disabled=检查中
    框.setAttribute('aria-label',中文句('installPackageLabel' if 安装.get('mirrorRecovery') else 'installSpecLabel'))
    框.setAttribute('aria-invalid','true' if 安装.get('inputError') is not None else 'false')
    def 改规格(事件):
        '把输入交回控制器'
        自身.属性['onEditSpec'](事件.target.value)
    def 规格键(事件):
        '非组合中的回车开始安装'
        if 自身.规格输入.正在输入(事件):
            return
        if 事件.key=='Enter' and not 空 and not 检查中:
            自身.属性['onRun']()
    框.addEventListener('input',改规格)
    框.addEventListener('compositionstart',自身.规格输入.开始)
    框.addEventListener('compositionend',自身.规格输入.结束)
    框.addEventListener('blur',自身.规格输入.失焦)
    框.addEventListener('keydown',规格键)
    字段.appendChild(框)
    体.appendChild(字段)
    if 句 is not None:
        警=建(文档,'p','inputError')
        警.setAttribute('role','alert')
        警.textContent=句
        体.appendChild(警)
    elif 模板提示 is not None:
        提=建(文档,'p','templateHint')
        提.setAttribute('role','status')
        提.textContent=模板提示
        体.appendChild(提)
    行=建(文档,'div','optionsRow')
    引导=建(文档,'button','guideToggle')
    引导.type='button'
    引导.setAttribute('aria-expanded','true' if 自身.引导开 else 'false')
    箭=画图标(窗口,图标下箭头描边常规,12)
    if 箭 is not None:
        箭.className='guideChevron'
        箭.setAttribute('aria-hidden','true')
        引导.appendChild(箭)
    引导字=文档.createElement('span')
    引导字.textContent=中文句('installGuideHide' if 自身.引导开 else 'installGuideToggle')
    引导.appendChild(引导字)
    def 翻引导(事件=None):
        '展开或收起引导'
        自身.引导开=自身.引导开 is not True
        if 自身.属性.get('重画') is not None:
            自身.属性['重画']()
    引导.addEventListener('click',翻引导)
    行.appendChild(引导)
    源钮=建(文档,'button','registryToggle')
    源钮.type='button'
    源钮.setAttribute('aria-expanded','true' if 安装.get('registryOpen') else 'false')
    源钮.setAttribute('aria-haspopup','dialog')
    源钮.disabled=检查中
    源字=文档.createElement('span')
    源字.textContent=中文句('registryToggle')
    源选=建(文档,'span','registryChosen')
    源选.textContent=选中名
    源钮.appendChild(源字)
    源钮.appendChild(文档.createTextNode(' '))
    源钮.appendChild(源选)
    源箭=画图标(窗口,图标下箭头描边常规,12)
    if 源箭 is not None:
        源箭.className='guideChevron'
        源箭.setAttribute('aria-hidden','true')
        源钮.appendChild(源箭)
    def 点源(事件=None):
        '展开或收起注册表'
        自身.属性['onToggleRegistry']()
    源钮.addEventListener('click',点源)
    行.appendChild(源钮)
    体.appendChild(行)
    if 自身.引导开:
        导=建(文档,'div','guide')
        导.setAttribute('data-install-guide','')
        单=建(文档,'ol','guideList')
        for 例 in 引导示例:
            项=建(文档,'li','guideItem')
            主=建(文档,'div','guideMain')
            题=建(文档,'span','guideTitle')
            题.textContent=中文句(例['titleKey'])
            主.appendChild(题)
            示=建(文档,'span','guideHint')
            示.textContent=中文句(例['hintKey'])
            主.appendChild(示)
            样=建(文档,'span','guideExample')
            样标=建(文档,'span','guideExampleLabel')
            样标.textContent=中文句('installGuideExampleLabel')
            样码=文档.createElement('code')
            样码.textContent=中文句(例['exampleKey'])
            样.appendChild(样标)
            样.appendChild(样码)
            主.appendChild(样)
            项.appendChild(主)
            def 填入(事件=None,键=例['exampleKey']):
                '把示例填进规格'
                自身.属性['onEditSpec'](中文句(键))
            挂组件(项,按钮({
                'window':窗口,'variant':'outline','size':'sm','disabled':检查中,'onClick':填入,
                'children':中文句('installGuideFill'),
            }))
            单.appendChild(项)
        导.appendChild(单)
        体.appendChild(导)
    if 安装.get('registryOpen') is True and 安装['phase']=='idle':
        面板=建(文档,'fieldset','registry')
        面板.setAttribute('data-install-registry','')
        面板.setAttribute('aria-label',中文句('registryLegend'))
        for 注册表 in 提供的注册表(安装.get('registries')):
            选中=选择['kind']=='offered' and 选择.get('registry') is 注册表
            标签=建(文档,'label','registryOption')
            标签.setAttribute('data-checked','true' if 选中 else 'false')
            单选=文档.createElement('input')
            单选.type='radio'
            单选.name='plugin-registry'
            单选.checked=选中
            def 选这项(事件=None,项=注册表):
                '选一个提供的源'
                if 选择['kind']=='custom':
                    自身.自定义草稿=选择.get('url') or ''
                自身.属性['onChooseRegistry']({'kind':'offered','registry':项})
            单选.addEventListener('change',选这项)
            标签.appendChild(单选)
            题=建(文档,'span','registryTitle')
            对=注册表文案对(注册表,已解析)
            if 对['name']==对['host']:
                题.textContent=对['name']
            else:
                题.appendChild(文档.createTextNode(对['name']+' '))
                辅=建(文档,'span','registryHint')
                辅.textContent=对['host']
                题.appendChild(辅)
            标签.appendChild(题)
            面板.appendChild(标签)
        自定义行=建(文档,'div','registryOption')
        自定义行.setAttribute('data-checked','true' if 选择['kind']=='custom' else 'false')
        自定义选=建(文档,'label','registryCustomPick')
        自定义单选=文档.createElement('input')
        自定义单选.type='radio'
        自定义单选.name='plugin-registry'
        自定义单选.checked=选择['kind']=='custom'
        def 选自定义(事件=None):
            '改用自己填的地址'
            自身.属性['onChooseRegistry']({'kind':'custom','url':自身.自定义草稿})
        自定义单选.addEventListener('change',选自定义)
        自定义选.appendChild(自定义单选)
        自定义题=建(文档,'span','registryTitle')
        自定义题字=文档.createElement('span')
        自定义题字.textContent=中文句('registryCustom')
        自定义题.appendChild(自定义题字)
        自定义选.appendChild(自定义题)
        自定义行.appendChild(自定义选)
        自定义框=文档.createElement('input')
        自定义框.type='text'
        自定义框.className='registryCustomField'
        标样式模块(自定义框,样式模块)
        自定义框.setAttribute('aria-label',中文句('registryCustom'))
        自定义框.placeholder=中文句('registryCustomPlaceholder')
        自定义框.value=选择['url'] if 选择['kind']=='custom' else 自身.自定义草稿
        自定义框.setAttribute('aria-invalid','true' if 安装.get('registryError') else 'false')
        def 改自定义(事件):
            '把自填地址交给控制器'
            自身.属性['onChooseRegistry']({'kind':'custom','url':事件.target.value})
        def 自定义键(事件):
            '非组合中的回车开始安装'
            if 自身.源输入.正在输入(事件):
                return
            if 事件.key=='Enter' and not 空:
                自身.属性['onRun']()
        def 聚焦自定义(事件=None):
            '指针点进输入框时改成自定义源'
            if 指针模态() and 选择['kind']!='custom':
                自身.属性['onChooseRegistry']({'kind':'custom','url':自身.自定义草稿})
        自定义框.addEventListener('input',改自定义)
        自定义框.addEventListener('focus',聚焦自定义)
        自定义框.addEventListener('compositionstart',自身.源输入.开始)
        自定义框.addEventListener('compositionend',自身.源输入.结束)
        自定义框.addEventListener('blur',自身.源输入.失焦)
        自定义框.addEventListener('keydown',自定义键)
        自定义行.appendChild(自定义框)
        if 安装.get('registryError') is True:
            错=建(文档,'p','inputError')
            错.setAttribute('role','alert')
            错.textContent=中文句('registryCustomInvalid')
            自定义行.appendChild(错)
        提示=建(文档,'span','registryHint')
        提示.textContent=中文句('registryCustomHint')
        自定义行.appendChild(提示)
        面板.appendChild(自定义行)
        文档.body.appendChild(面板)
        自身.拆锚定=使用锚定位置({
            'open':True,'anchor':源钮,'panel':面板,'window':窗口,
            'align':'end','gap':6,'margin':12,
        })
        def 点外关(开着):
            '点到面板外就收起'
            if 开着:
                return
            自身.属性['onToggleRegistry']()
        自身.拆外=点外关闭(源钮,True,点外关,面板)
        def 按逃(事件):
            'Escape 只收起注册表'
            if 事件.key!='Escape':
                return
            事件.stopPropagation()
            自身.属性['onToggleRegistry']()
        文档.addEventListener('keydown',按逃,True)
        def 拆键():
            '卸掉 Escape'
            文档.removeEventListener('keydown',按逃,True)
        自身.拆键=拆键
    安全=建(文档,'p','installSafety')
    安全.setAttribute('role','note')
    警图=画图标(窗口,图标警告16,14)
    if 警图 is not None:
        警图.setAttribute('aria-hidden','true')
        安全.appendChild(警图)
    安全文=建(文档,'span','installSafetyText')
    甲=文档.createElement('span')
    甲.textContent=中文句('installGuideSafety')
    乙=文档.createElement('span')
    乙.textContent=中文句('installUpgradeNotice')
    安全文.appendChild(甲)
    安全文.appendChild(乙)
    安全.appendChild(安全文)
    装钮=按钮({
        'window':窗口,'variant':'primary','className':'wide',
        'disabled':检查中 or 空,'onClick':自身.属性['onRun'],
        'children':中文句('installChecking' if 检查中 else 'installRun'),
    }).渲染()
    脚=建(文档,'div','installFooter')
    脚.appendChild(安全)
    if 装钮 is not None:
        if 检查中:
            装钮.setAttribute('aria-busy','true')
        脚.appendChild(装钮)
    模态属性={
        'window':窗口,'open':安装['open'],'onClose':自身.属性['onClose'],
        'title':中文句('installTitle'),'closeLabel':中文句('close'),
        'className':'installDialog','contentClassName':'installContent',
        'children':体,'footer':脚,
    }
    if 安装.get('mirrorRecovery') is not True:
        模态属性['description']=中文句('installDescription')
    return 模态(模态属性).渲染()

def self_结果(自身,窗口,安装):
    '安装中、完成和失败'
    文档=窗口.document
    阶段=安装['phase']
    标题=中文句(屏标题键[阶段])
    待决=是否安装待决(阶段)
    可取消=阶段 in ('starting','running','unconfirmed')
    可停=可取消 or 阶段 in ('failed','unknown')
    失败=安装.get('failure')
    不确定=None if 失败 is None else 失败.get('uncertainty')
    不确定文=None
    if 不确定=='result':
        不确定文=中文句('installResultUnconfirmed',{'reason':失败.get('reason') or ''})
    elif 不确定=='cancellation':
        键='installApplyingCancellationError' if 阶段=='applying' else 'installCancelUnconfirmed'
        不确定文=中文句(键,{'reason':失败.get('reason') or ''})
    elif 不确定=='acceptance':
        不确定文=中文句('installAwaitingAcceptance',{'reason':失败.get('reason') or ''})
    待允许=失败.get('pendingBuilds') if 阶段=='failed' and 失败 is not None and 失败.get('pendingBuilds') is not None else []
    可允许=len(待允许)>0
    问过=安装['attempts'] if 安装.get('attempts') is not None and len(安装['attempts']['registries'])>1 else None
    已解析=None if 安装.get('registries') is None else 安装['registries'].get('resolved')
    尝试句=None
    if 待决 and 问过 is not None and len(问过['registries'])>=2:
        当前源=问过['registries'][-1]
        上一源=问过['registries'][-2]
        尝试句=中文句('installAttempt',{
            'previous':注册表文案对(上一源,已解析)['name'],
            'registry':注册表文案对(当前源,已解析)['name'],
            'index':str(len(问过['registries'])),
            'total':str(问过['total']),
        })
    可换源=阶段=='failed' and not 可允许 and 失败 is not None and 失败.get('failedAt')=='registry' and 安装.get('confirmed') is None
    向导=建(文档,'div','wizard')
    向导.setAttribute('data-install-phase',阶段)
    头=建(文档,'div','wizardHead')
    if 阶段=='done' or (安装.get('confirmed') is not None and not 待决):
        头.appendChild(文档.createElement('span'))
    else:
        if 安装.get('confirmed') is not None:
            返回名='cancel'
        elif 待决:
            返回名='installCancelAndEdit'
        else:
            返回名='installEdit'
        回=建(文档,'button','wizardBack')
        回.type='button'
        回.setAttribute('aria-label',中文句('cancel' if 安装.get('confirmed') is not None else ('installCancelAndEdit' if 待决 else 'installEditAria')))
        回.disabled=not 可停
        左=画图标(窗口,图标左chevron14,16)
        if 左 is not None:
            左.setAttribute('aria-hidden','true')
            回.appendChild(左)
        回字=文档.createElement('span')
        回字.textContent=中文句(返回名)
        回.appendChild(回字)
        def 点回(事件=None):
            '取消或回到编辑'
            自身.属性['onCancel']()
        回.addEventListener('click',点回)
        头.appendChild(回)
    关=建(文档,'button','wizardClose')
    关.type='button'
    关.setAttribute('aria-label',中文句('installCloseCancels' if 可取消 else 'close'))
    关图=画图标(窗口,图标关闭16,14)
    if 关图 is not None:
        关.appendChild(关图)
    def 点关(事件=None):
        '关闭对话框'
        自身.属性['onClose']()
    关.addEventListener('click',点关)
    头.appendChild(关)
    向导.appendChild(头)
    滚=建(文档,'div','wizardScroll')
    英雄=建(文档,'div','wizardHero')
    图标盒=建(文档,'span','wizardIcon')
    图标盒.setAttribute('aria-hidden','true')
    if 待决:
        图标盒.setAttribute('data-state','ongoing')
        点=状态点({'window':窗口,'state':'ongoing','size':28}).渲染()
        if 点 is not None:
            图标盒.appendChild(点)
    elif 阶段=='done':
        图标盒.setAttribute('data-state','done')
        勾=画图标(窗口,图标勾圈描边常规,28)
        if 勾 is not None:
            图标盒.appendChild(勾)
    else:
        图标盒.setAttribute('data-state','error')
        警=画图标(窗口,图标警告16,28)
        if 警 is not None:
            图标盒.appendChild(警)
    英雄.appendChild(图标盒)
    题=建(文档,'h2','wizardTitle')
    题.setAttribute('role','alert' if 阶段=='failed' else 'status')
    题.textContent=标题
    英雄.appendChild(题)
    if 阶段=='failed':
        副=建(文档,'p','wizardSub')
        副.textContent=失败句(失败,安装)
        英雄.appendChild(副)
    if 尝试句 is not None:
        副=建(文档,'p','wizardSub')
        副.textContent=尝试句
        英雄.appendChild(副)
    if 不确定文 is not None:
        副=建(文档,'p','wizardSub')
        副.setAttribute('role','alert')
        副.textContent=不确定文
        英雄.appendChild(副)
    if 阶段=='unknown':
        副=建(文档,'p','wizardSub')
        副.textContent=中文句('installUnknownDescription')
        英雄.appendChild(副)
    滚.appendChild(英雄)
    主体=安装.get('subject')
    if 主体 is not None:
        展示=dict(主体)
        if 阶段=='done' and 安装.get('installedVersion') is not None:
            展示['version']=安装['installedVersion']
        种类键=主体种类键.get(主体.get('kind'))
        说明=主体.get('description')
        if 说明 is None and 种类键 is not None:
            说明=中文句(种类键)
        滚.appendChild(主体块({'window':窗口,'lines':{
            'spec':主体.get('spec') or 安装['spec'],
            'title':安装['confirmed']['title'] if 安装.get('confirmed') is not None else (主体.get('name') or 主体.get('spec') or ''),
            'description':说明,
            'version':展示.get('version') if 展示.get('version') is not None else (None if 安装.get('confirmed') is None else 安装['confirmed'].get('version')),
            'showSpec':安装.get('confirmed') is not None,
        }}).渲染())
    if 可允许:
        批=建(文档,'section','approval')
        批.setAttribute('role','group')
        批.setAttribute('data-install-approval','')
        批题=建(文档,'h3','approvalTitle')
        批题.textContent=中文句('installApprovalTitle')
        批.appendChild(批题)
        批文=建(文档,'p','approvalText')
        批文.textContent=中文句('installApprovalDescription')
        批.appendChild(批文)
        名单=建(文档,'ul','approvalList')
        for 名 in 待允许:
            项=文档.createElement('li')
            码=文档.createElement('code')
            码.textContent=名
            项.appendChild(码)
            名单.appendChild(项)
        批.appendChild(名单)
        果=建(文档,'p','approvalText')
        果.textContent=中文句('installApprovalConsequence')
        批.appendChild(果)
        慎=建(文档,'p','approvalCaution')
        慎.textContent=中文句('installApprovalCaution')
        批.appendChild(慎)
        挂组件(批,按钮({'window':窗口,'variant':'primary','className':'wide','onClick':自身.属性['onApproveBuilds'],'children':中文句('installApproveAndRetry')}))
        滚.appendChild(批)
    if 阶段=='done' and 安装.get('installed') is None:
        果=建(文档,'p','result')
        果.setAttribute('role','status')
        果.textContent=中文句('installDoneNothing')
        滚.appendChild(果)
    if 阶段=='done' and 安装.get('restartRequired') is True:
        果=建(文档,'p','resultWarn')
        果.setAttribute('role','status')
        果.textContent=重启文案('installDoneRestart',安装.get('restartReason'))
        滚.appendChild(果)
    if 阶段=='done' and 主体 is not None and 主体.get('kind')=='registry' and 主体.get('name') is not None and 主体.get('version') is not None and 安装.get('installedVersion') is not None and 安装['installedVersion']!=主体['version'] and (1 if 安装.get('attempts') is None else len(安装['attempts']['registries']))==1:
        果=建(文档,'p','resultWarn')
        果.setAttribute('role','status')
        果.textContent=中文句('installDoneOtherVersion',{
            'installed':安装['installedVersion'],'version':主体['version'],
            'exact':主体['name']+'@'+主体['version'],
        })
        滚.appendChild(果)
    if 阶段=='done' and 安装.get('approvedBuilds') is not None and len(安装['approvedBuilds'])>0:
        果=建(文档,'p','result')
        果.setAttribute('role','status')
        果.textContent=中文句('installDoneApproved',{'names':', '.join(安装['approvedBuilds'])})
        滚.appendChild(果)
    脚=建(文档,'div','wizardFoot')
    详=建(文档,'button','detailsToggle')
    详.type='button'
    详.setAttribute('aria-expanded','true' if 安装.get('detailsOpen') else 'false')
    详字=文档.createElement('span')
    详字.textContent=中文句('installDetailsHide' if 安装.get('detailsOpen') else 'installDetailsShow')
    详.appendChild(详字)
    详箭=画图标(窗口,图标下箭头描边常规,12)
    if 详箭 is not None:
        详箭.className='detailsChevron'
        详箭.setAttribute('aria-hidden','true')
        详.appendChild(详箭)
    def 点详情(事件=None):
        '展开或收起安装详情'
        自身.属性['onToggleDetails']()
    详.addEventListener('click',点详情)
    脚.appendChild(详)
    if 不确定=='result':
        挂组件(脚,按钮({'window':窗口,'variant':'outline','size':'sm','className':'footAction','onClick':自身.属性['onReconcile'],'children':中文句('installReconcile')}))
    if 待决:
        挂组件(脚,按钮({
            'window':窗口,'variant':'outline','size':'sm','className':'footAction',
            'disabled':not 可取消,'onClick':自身.属性['onCancel'],
            'children':中文句('installCancelling' if 阶段=='cancelling' else 'installCancel'),
        }))
    if 阶段=='failed' and not 可允许:
        组=建(文档,'span','wizardActions')
        if 可换源:
            挂组件(组,按钮({'window':窗口,'variant':'outline','size':'sm','className':'footAction','onClick':自身.属性['onChangeRegistry'],'children':中文句('installChangeRegistry')}))
        挂组件(组,按钮({'window':窗口,'variant':'primary','size':'sm','className':'footAction','onClick':自身.属性['onRun'],'children':中文句('installRetry')}))
        脚.appendChild(组)
    滚.appendChild(脚)
    if 安装.get('detailsOpen') is True:
        身=建(文档,'div','detailsBody')
        第一=安装['runs'][0] if len(安装['runs'])>0 else None
        位置=建(文档,'p','installLocation')
        位置.textContent=中文句('terminalNoOutput') if 第一 is None else 中文句('installLocation',{'dir':第一['cwd']})
        身.appendChild(位置)
        序=0
        标签=终端文案()
        if 阶段=='cancelling':
            标签={**标签,'failed':中文句('installCancelledShort')}
        for 运行 in 安装['runs']:
            块=建(文档,'div','run')
            if 问过 is not None and 序<len(问过['registries']):
                徽=建(文档,'p','attemptBadge')
                徽.textContent=中文句('installAttemptBadge',{
                    'index':str(序+1),
                    'registry':注册表文案对(问过['registries'][序],已解析)['name'],
                })
                块.appendChild(徽)
            挂组件(块,终端块({
                'window':窗口,'command':运行['command'],'output':运行['output'],
                'running':'exitCode' not in 运行,'exitCode':运行.get('exitCode'),
                'maxLines':安装终端行数,'labels':标签,'className':'terminal',
            }))
            身.appendChild(块)
            序=序+1
        滚.appendChild(身)
    if 阶段=='done':
        if 安装.get('installed') is not None and (安装.get('subject') is None or 'selection' not in 安装['subject']):
            挂组件(滚,按钮({
                'window':窗口,'variant':'primary','className':'wide',
                'disabled':安装.get('enabling') is True,'onClick':自身.属性['onEnableNow'],
                'children':中文句('installEnableNow'),
            }))
        else:
            挂组件(滚,按钮({'window':窗口,'variant':'primary','className':'wide','onClick':自身.属性['onClose'],'children':中文句('installClose')}))
    向导.appendChild(滚)
    return 模态({
        'window':窗口,'open':安装['open'],'onClose':自身.属性['onClose'],
        'title':标题,'headless':True,'className':'installDialog','children':向导,
    }).渲染()

class 插件装载页:
    '官方插件、已安装组合包、它们的页、安装对话框和卸载确认'
    def __init__(自身,属性):
        '记下合成属性并画出'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.已订=False
        自身.绘制中=False
        自身.已确保=False
        自身.激活=None
        自身.高亮定时=None
        自身.菜单=添加插件菜单({})
        自身.安装框=安装对话框({})
        自身.包详情=None
        自身.渲染()

    def __call__(自身,属性=None):
        '宿主再次渲染'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '按快照重画整页'
        if 自身.绘制中:
            return 自身.根
        自身.绘制中=True
        try:
            return 自身.画出()
        finally:
            自身.绘制中=False

    def 画出(自身):
        '读取钩子并摆上列表、详情和对话框'
        属性=自身.属性
        窗口=窗口于(属性)
        文档=窗口.document
        确保样式(文档)
        def 取整(快照):
            '整份装载快照'
            return 快照
        def 取视图(状态):
            '当前导航'
            return 状态['view']
        def 取标签(状态):
            '当前页'
            return 状态['tab']
        def 取命名空间(快照):
            '配置镜像里的命名空间'
            视图=快照.get('view') if isinstance(快照,dict) else None
            if isinstance(视图,dict):
                return 视图.get('namespaces')
            return None
        状态=属性['usePluginManager'](取整)
        账本=属性['useConfigLedger'](取整)
        视图=属性['useStore'](取视图)
        选中标签=属性['useStore'](取标签)
        标签表=属性['usePluginTabs'](取整)
        配置空间=属性['useConfigurations'](取命名空间)
        if 自身.已订 is not True:
            def 重画():
                '状态变了就重画'
                自身.渲染()
            属性['usePluginManager']._subscribe(重画)
            属性['useConfigLedger']._subscribe(重画)
            属性['useStore']._subscribe(重画)
            属性['usePluginTabs']._subscribe(重画)
            属性['useConfigurations']._subscribe(重画)
            自身.已订=True
        if 自身.已确保 is not True:
            属性['ensure']()
            自身.已确保=True
        标签=选中标签 if any(项['id']==选中标签 for 项 in 标签表) else 已安装页
        if 标签!=选中标签:
            属性['actions']['setTab'](标签)
        if 状态.get('highlight') is not None and 标签!=已安装页:
            属性['actions']['setTab'](已安装页)
            标签=已安装页
        列出=[包 for 包 in 状态['packages'] if 包['name'] not in 内置档组合包 and (包.get('installed') is True or 包.get('official') is True or 包.get('error') is not None)]
        我的=[包 for 包 in 列出 if 包.get('official') is not True]
        官方=[包 for 包 in 列出 if 包.get('official') is True]
        def 按秩(包):
            '官方可选包的显示顺序'
            return 可选包秩(包['name'])
        官方.sort(key=按秩)
        钉=set()
        for 包 in 官方:
            if 包['name'] not in 更多包 or 包.get('enabled') is True:
                钉.add(包['name'])
        扩展=[包 for 包 in 官方 if 包['name'] in 钉]
        更多=list(官方)
        已载=状态['status'] in ('ready','error')
        刷新中=状态['refreshStatus']=='refreshing'
        打开包=None
        if 视图['kind'] in ('package','row'):
            for 包 in 列出:
                if 包['name']==视图['name']:
                    打开包=包
                    break
        打开条目=None
        if 视图['kind']=='item':
            for 项 in 账本['items']:
                if 项['id']==视图['id']:
                    打开条目=项
                    break
        打开行=None
        if 视图['kind']=='row' and 打开包 is not None:
            for 行 in 打开包['rows']:
                if 行['rowId']==视图['rowId']:
                    打开行=行
                    break
        在已安装=标签==已安装页
        显示卡片=(not 在已安装) or (打开包 is None and 打开条目 is None)
        来自更多=(视图['kind'] in ('package','row')) and (视图.get('from')=='more' or (视图.get('name') in 更多包 and 视图.get('name') not in 钉))
        显示更多=在已安装 and 显示卡片 and (视图['kind']=='more' or 来自更多)
        显示主列表=显示卡片 and not 显示更多
        已安装卡片=在已安装 and 显示卡片
        打开包在更多=打开包 is not None and 打开包.get('official') is True and 来自更多
        旧=自身.根
        父=None
        if 旧 is not None:
            父=旧.parentNode
            旧.remove()
        根=建(文档,'section','page')
        根.setAttribute('data-plugin-panel','')
        if 状态['status']=='loading' or 刷新中:
            根.setAttribute('aria-busy','true')
        if 显示主列表:
            头=建(文档,'header','pageHead')
            头.setAttribute('data-window-drag','')
            标题区=建(文档,'div','pageHeading')
            题=建(文档,'h1','pageTitle')
            题.textContent=中文句('title')
            标题区.appendChild(题)
            引=建(文档,'div','pageIntro')
            引字=文档.createElement('span')
            引字.textContent=中文句('intro')
            引.appendChild(引字)
            说明钮=按钮({
                'window':窗口,'variant':'ghost','size':'sm','className':'infoButton',
                'children':画图标(窗口,图标信息描边常规,11),
            }).渲染()
            if 说明钮 is not None:
                说明钮.setAttribute('aria-label',中文句('infoLabel'))
                标样式模块(说明钮,样式模块)
            挂组件(引,提示泡({
                'window':窗口,'label':中文句('infoDescription'),'side':'bottom',
                'delayMs':300,'maxWidth':300,'portal':True,'openOnClick':True,
                'children':说明钮,
            }))
            标题区.appendChild(引)
            头.appendChild(标题区)
            具=建(文档,'div','toolbar')
            if not 在已安装:
                具.setAttribute('hidden','')
            刷新钮=文档.createElement('button')
            刷新钮.type='button'
            刷新钮.className='iconButton'
            标样式模块(刷新钮,样式模块)
            刷新钮.setAttribute('aria-label',中文句('refresh'))
            刷新钮.setAttribute('aria-busy','true' if 刷新中 else 'false')
            刷新钮.disabled=not 已载 or 刷新中
            包图=建(文档,'span','iconWrap')
            包图.setAttribute('aria-hidden','true')
            if 刷新中:
                点=状态点({'window':窗口,'state':'ongoing','size':18}).渲染()
                if 点 is not None:
                    包图.appendChild(点)
            else:
                图=画图标(窗口,图标刷新16)
                if 图 is not None:
                    包图.appendChild(图)
            刷新钮.appendChild(包图)
            def 点刷新(事件=None):
                '再读插件'
                属性['refresh']()
            刷新钮.addEventListener('click',点刷新)
            挂组件(具,提示泡({
                'window':窗口,'label':中文句('refresh'),'delayMs':500,'focusDelayMs':500,
                'side':'bottom','portal':True,'disabled':not 已载 or 刷新中,'children':刷新钮,
            }))
            if 状态['install'].get('requestId') is None:
                自身.菜单.属性={
                    'window':窗口,'disabled':not 已载,'openInstall':属性['openInstall'],
                    'renderSlot':属性['renderSlot'],'重画':自身.渲染,
                }
                菜单节点=自身.菜单.渲染()
                if 菜单节点 is not None:
                    具.appendChild(菜单节点)
            else:
                挂组件(具,按钮({
                    'window':窗口,'variant':'primary','size':'sm','className':'addButton',
                    'icon':画图标(窗口,图标加号16,13),'disabled':not 已载,
                    'onClick':属性['openInstall'],'children':中文句('installViewTask'),
                }))
            头.appendChild(具)
            根.appendChild(头)
        if 显示主列表 and len(标签表)>0:
            页签=建(文档,'div','pageTabs')
            项列=[{
                'value':已安装页,'label':中文句('installedTab'),
                'id':'plugins-tab-installed','panelId':'plugins-panel-installed',
            }]
            for 项 in 标签表:
                项列.append({
                    'value':项['id'],'label':项['label'],
                    'id':'plugins-tab-'+项['id'],'panelId':'plugins-panel-'+项['id'],
                })
            def 换页(下一):
                '切到选中的页'
                属性['actions']['setTab'](下一)
            挂组件(页签,分段标签页({
                'window':窗口,'className':'pageTabList','label':中文句('tabsLabel'),
                'value':标签,'onChange':换页,'items':项列,
            }))
            根.appendChild(页签)
        if not 在已安装:
            面板=建(文档,'div','tabPanel')
            面板.setAttribute('role','tabpanel')
            面板.id='plugins-panel-'+标签
            def 打开包名(名):
                '切到已安装并打开组合包'
                属性['actions']['setTab'](已安装页)
                属性['actions']['setView']({'kind':'package','name':名})
            挂上(面板,属性['renderSlot']('plugins.tab',{
                'install':属性['installFrom'],'openPackage':打开包名,
            },{'only':标签}))
            根.appendChild(面板)
        if 显示更多:
            更多头=建(文档,'header','moreHead')
            更多头.setAttribute('data-window-drag','')
            def 回列表(事件=None):
                '回到主列表'
                属性['actions']['setView']({'kind':'list'})
            挂组件(更多头,按钮({
                'window':窗口,'size':'sm','className':'moreBack',
                'children':画图标(窗口,图标左chevron14,20),'onClick':回列表,
            }))
            更多题=建(文档,'h1','pageTitle')
            更多题.textContent=中文句('moreTitle')
            更多头.appendChild(更多题)
            根.appendChild(更多头)
        if 已安装卡片 and not 已载:
            面板=建(文档,'div','installedPanel')
            if 状态['status']=='loading':
                面板.appendChild(列表骨架({'window':窗口,'label':中文句('loading')}).渲染())
            if 状态['status']=='unavailable':
                段=建(文档,'p','status statusWithDot')
                段.setAttribute('role','status')
                点=状态点({'window':窗口,'state':'idle'}).渲染()
                if 点 is not None:
                    段.appendChild(点)
                段.appendChild(文档.createTextNode(中文句('unavailable')))
                面板.appendChild(段)
            根.appendChild(面板)
        提示=状态.get('notice')
        if 提示 is not None and 提示.get('kind')!='refresh-failed':
            句=提示文案(提示)
            停留=min(8000,max(3000,len(句)*80))
            挂组件(根,吐司({
                'window':窗口,'text':句,'icon':画图标(窗口,图标警告16),
                'holdMs':停留,'onDone':属性['dismissNotice'],
            }))
        if not 显示卡片 and 状态['status']=='error' and not 刷新中:
            失败盒=建(文档,'div','failure')
            段=建(文档,'p','statusWithDot')
            段.setAttribute('role','alert')
            点=状态点({'window':窗口,'state':'error'}).渲染()
            if 点 is not None:
                段.appendChild(点)
            段.appendChild(文档.createTextNode(中文句('refreshError' if 状态['refreshStatus']=='failed' else 'error')))
            失败盒.appendChild(段)
            挂组件(失败盒,按钮({'window':窗口,'variant':'outline','size':'sm','onClick':属性['refresh'],'children':中文句('retry')}))
            根.appendChild(失败盒)
        def 表单于(身份):
            '这一页的配置表单。镜像里没有这个命名空间就不给'
            if not isinstance(配置空间,list) or not any(isinstance(项,dict) and 项.get('ns')==身份 for 项 in 配置空间):
                return None
            表单=属性['configForm'](身份)
            def 提交(操作,修订):
                '按读到的修订提交'
                return 表单.mutate(操作,修订)
            return {'state':表单.getSnapshot(),'mutate':提交}
        def 设行(行,启用):
            '有活入口才启停'
            if 行.get('entryId') is not None:
                属性['setRowEnabled'](行['entryId'],启用)
        if 在已安装 and 已载 and 打开包 is not None and 打开行 is not None:
            def 回包():
                '回到这个组合包'
                视图值={'kind':'package','name':打开包['name']}
                if 打开包在更多:
                    视图值['from']='more'
                属性['actions']['setView'](视图值)
            根.appendChild(行详情({
                'window':窗口,'pkg':打开包,'row':打开行,'form':表单于(打开行['rowId']),
                'resolveText':属性['resolveText'],'renderSlot':属性['renderSlot'],'重画':自身.渲染,
                'onBack':回包,
            }).渲染())
        if 在已安装 and 已载 and 打开包 is not None and 打开行 is None:
            if 自身.包详情 is None:
                自身.包详情=包详情({})
            def 行忙(行):
                '这一行是否正在写'
                return 行.get('entryId') is not None and 行键(行['entryId']) in 状态['busy']
            def 包忙(包):
                '包本身忙，或它的安装还在飞'
                if 包['name'] in 状态['busy']:
                    return True
                主体=状态['install'].get('subject')
                return 主体 is not None and 主体.get('name')==包['name'] and (是否安装待决(状态['install']['phase']) or 状态['install']['phase']=='checking')
            def 行是否忙(行):
                '包或这一行正在写'
                return 包忙(打开包) or 行忙(行)
            def 行有配置(行,名=打开包['name']):
                '这一行是否登记了自己的页'
                return 行配置键(名,行['rowId']) in 账本['rows']
            def 开行(行,名=打开包['name']):
                '打开这一行'
                视图值={'kind':'row','name':名,'rowId':行['rowId']}
                if 打开包在更多:
                    视图值['from']='more'
                属性['actions']['setView'](视图值)
            def 回层():
                '回到更多或主列表'
                属性['actions']['setView']({'kind':'more' if 打开包在更多 else 'list'})
            def 改启用(启用,名=打开包['name']):
                '启停这个包'
                属性['setEnabled'](名,启用)
            def 去卸载(名=打开包['name']):
                '请求卸载'
                属性['uninstall'](名)
            def 去更新(名=打开包['name']):
                '请求更新'
                属性['update'](名)
            自身.包详情.属性={
                'window':窗口,'pkg':打开包,'resolveText':属性['resolveText'],
                'busy':包忙(打开包),'renderSlot':属性['renderSlot'],'inMore':打开包在更多,
                'configured':打开包['name'] in 账本['bundles'],'重画':自身.渲染,
                'toggle':{'busy':行是否忙,'onSetEnabled':设行} if 打开包.get('enabled') is True else None,
                'configure':{'has':行有配置,'open':开行},
                'onBack':回层,
                'onSetEnabled':改启用,
                'onUninstall':去卸载,
                'onUpdate':去更新,
            }
            根.appendChild(自身.包详情.渲染())
        if 在已安装 and 已载 and 打开条目 is not None:
            def 回列表():
                '回到卡片列表'
                属性['actions']['setView']({'kind':'list'})
            根.appendChild(条目详情({
                'window':窗口,'item':打开条目,'form':表单于(打开条目['id']),
                'renderSlot':属性['renderSlot'],
                'onBack':回列表,
            }).渲染())
        if 已载 and 已安装卡片:
            if len(账本['items'])==0 and len(官方)==0 and len(我的)==0 and 状态['status']!='error':
                面板=建(文档,'div','installedPanel')
                空=建(文档,'p','empty')
                空.textContent=中文句('empty')
                面板.appendChild(空)
                根.appendChild(面板)
            else:
                面板=建(文档,'div','installedPanel')
                def 画包卡(包,来自更多列表):
                    '一张组合包卡片'
                    def 打开():
                        '打开详情'
                        自身.激活=None
                        视图值={'kind':'package','name':包['name']}
                        if 来自更多列表:
                            视图值['from']='more'
                        属性['actions']['setView'](视图值)
                    def 开关改(启用):
                        '启停，启用时记下引导'
                        自身.激活=包['name'] if 启用 else None
                        属性['setEnabled'](包['name'],启用)
                    def 忙():
                        '这张卡是否忙'
                        if 包['name'] in 状态['busy']:
                            return True
                        主体=状态['install'].get('subject')
                        return 主体 is not None and 主体.get('name')==包['name'] and (是否安装待决(状态['install']['phase']) or 状态['install']['phase']=='checking')
                    return 包卡片({
                        'window':窗口,'pkg':包,'resolveText':属性['resolveText'],
                        'busy':忙(),'highlighted':状态.get('highlight')==包['name'],
                        'onOpen':打开,'onSetEnabled':开关改,'重画':自身.渲染,
                    }).渲染()
                if 显示更多:
                    组=建(文档,'section','group')
                    组.setAttribute('data-plugin-scope','global')
                    组.setAttribute('data-plugin-group','more')
                    列=建(文档,'ul','cards')
                    for 包 in 更多:
                        卡=画包卡(包,True)
                        if 卡 is not None:
                            列.appendChild(卡)
                    组.appendChild(列)
                    面板.appendChild(组)
                else:
                    def 画组(身份,标题,卡片):
                        '一组卡片。实验组还可以去更多'
                        有更多=身份=='extensions' and len(更多)>0
                        if len(卡片)==0 and not 有更多:
                            return
                        组=建(文档,'section','group')
                        组.setAttribute('data-plugin-scope','global')
                        组.setAttribute('data-plugin-group',身份)
                        组头=建(文档,'div','groupHead')
                        题=建(文档,'h3','groupTitle')
                        题.textContent=标题
                        组头.appendChild(题)
                        if 有更多:
                            def 去更多(事件=None):
                                '打开更多列表'
                                属性['actions']['setView']({'kind':'more'})
                            挂组件(组头,按钮({
                                'window':窗口,'size':'sm','className':'groupMore','onClick':去更多,
                                'children':中文句('moreAction'),
                            }))
                        组.appendChild(组头)
                        if len(卡片)>0:
                            列=建(文档,'ul','cards')
                            for 卡 in 卡片:
                                if 卡 is not None:
                                    列.appendChild(卡)
                            组.appendChild(列)
                        面板.appendChild(组)
                    基本卡=[]
                    for 项 in 账本['items']:
                        def 开条目(身份=项['id']):
                            '打开官方插件'
                            属性['actions']['setView']({'kind':'item','id':身份})
                        基本卡.append(条目卡片({
                            'window':窗口,'item':项,'renderSlot':属性['renderSlot'],'onOpen':开条目,
                        }).渲染())
                    画组('basic',中文句('basicTitle'),基本卡)
                    画组('extensions',中文句('extensionsTitle'),[画包卡(包,False) for 包 in 扩展])
                    画组('bundles',中文句('bundlesTitle'),[画包卡(包,False) for 包 in 我的])
                if 状态['status']=='error' and not 刷新中:
                    失败盒=建(文档,'div','failure')
                    段=建(文档,'p','statusWithDot')
                    段.setAttribute('role','alert')
                    点=状态点({'window':窗口,'state':'error'}).渲染()
                    if 点 is not None:
                        段.appendChild(点)
                    段.appendChild(文档.createTextNode(中文句('refreshError' if 状态['refreshStatus']=='failed' else 'error')))
                    失败盒.appendChild(段)
                    挂组件(失败盒,按钮({'window':窗口,'variant':'outline','size':'sm','onClick':属性['refresh'],'children':中文句('retry')}))
                    面板.appendChild(失败盒)
                根.appendChild(面板)
        激活包=None
        for 包 in 列出:
            if 包['name']==自身.激活 and 包.get('enabled') is True and 包['name'] not in 状态['busy']:
                激活包=包
                break
        if 显示卡片 and 激活包 is not None and 状态['install']['open'] is not True:
            def 关掉引导():
                '丢掉这次启用引导'
                自身.激活=None
                自身.渲染()
            def 打开详情():
                '关掉引导并打开这个包'
                自身.激活=None
                视图值={'kind':'package','name':激活包['name']}
                if 显示更多:
                    视图值['from']='more'
                属性['actions']['setView'](视图值)
            挂上(根,属性['renderSlot']('plugins.bundle.activation',{
                'packageName':激活包['name'],'onDismiss':关掉引导,'onOpenDetails':打开详情,
            },{'entryKey':激活包['name']}))
        def 启用刚装():
            '记下引导并启用刚装上的包'
            自身.激活=状态['install'].get('installed')
            属性['enableInstalled']()
        自身.安装框.属性={
            'window':窗口,'install':状态['install'],'重画':自身.渲染,
            'onClose':属性['closeInstall'],'onEditSpec':属性['editInstallSpec'],
            'onRun':属性['runInstall'],'onCancel':属性['cancelInstall'],
            'onReconcile':属性['reconcileInstall'],'onToggleDetails':属性['toggleInstallDetails'],
            'onEnableNow':启用刚装,'onApproveBuilds':属性['approveBuildsAndRetry'],
            'onToggleRegistry':属性['toggleRegistryOptions'],'onChooseRegistry':属性['chooseRegistry'],
            'onChangeRegistry':属性['changeRegistry'],'onUseGithubMirror':属性['useGithubMirror'],
        }
        对话=自身.安装框.渲染()
        if 对话 is not None:
            根.appendChild(对话)
        if 状态.get('confirm') is not None:
            确认包=None
            for 包 in 状态['packages']:
                if 包['name']==状态['confirm']['packageName']:
                    确认包=包
                    break
            if 确认包 is None:
                名=状态['confirm']['packageName']
            else:
                名=包文案(确认包,属性['resolveText'])['title']
            确认=确认对话框({
                'window':窗口,'name':名,'onConfirm':属性['confirm'],'onCancel':属性['cancelConfirm'],
            }).渲染()
            if 确认 is not None:
                根.appendChild(确认)
        自身.根=根
        if 父 is None and 'parent' in 属性:
            父=属性['parent']
        if 父 is not None and 根.parentNode is not 父:
            父.appendChild(根)
        if 状态.get('highlight') is not None:
            卡=文档.querySelector('[data-plugin-package="'+状态['highlight']+'"]')
            if 卡 is not None and hasattr(卡,'scrollIntoView'):
                卡.scrollIntoView({'block':'center','behavior':'smooth'})
            if 自身.高亮定时 is not None:
                窗口.clearTimeout(自身.高亮定时)
            自身.高亮定时=窗口.setTimeout(属性['clearHighlight'],高亮毫秒)
        return 根
