import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点
from ...ui_基础界面组件.icons import 图标下载16,图标加载描边常规
from ...ui_基础界面组件.提示泡 import 提示泡
from .文案 import 中文,填入

__all__=['桌面更新指示','桌面更新角标']

样式模块='desktopUpdate'
忙阶段=('checking','downloading','verifying','installing')

def 更新文案(状态):
    '按阶段取可见字和提示。显示用中文表原文'
    阶段=状态['phase']
    百分=0 if 状态.get('percent') is None else 状态['percent']
    版本=状态.get('version')
    标签表={
        'idle':'',
        'checking':中文['desktop.update.checking'],
        'available':中文['desktop.update.available'],
        'downloading':填入(中文['desktop.update.progress'],{'percent':百分}),
        'verifying':中文['desktop.update.verifying'],
        'installing':中文['desktop.update.installing'],
        'ready':中文['desktop.update.ready'],
        'error':中文['desktop.update.retry'],
    }
    标签=标签表[阶段]
    if 阶段=='checking' or 阶段=='verifying' or 阶段=='installing':
        详情=标签 if 版本 is None else 版本
        return {'label':标签,'detail':详情}
    if 阶段=='error':
        失败表={
            'check':中文['desktop.update.checkFailed'],
            'check-network':中文['desktop.update.checkNetworkFailed'],
            'download':中文['desktop.update.downloadFailed'],
            'download-network':中文['desktop.update.downloadNetworkFailed'],
            'install':中文['desktop.update.installFailed'],
            'install-network':中文['desktop.update.installNetworkFailed'],
            'stop-failed':中文['desktop.update.stopFailed'],
            'tasks-changed':中文['desktop.update.tasksChanged'],
            'tasks-unavailable':中文['desktop.update.tasksUnavailable'],
        }
        种类=状态.get('failure')
        if 种类 not in 失败表:
            种类='install'
        return {'label':标签,'detail':失败表[种类]}
    if 阶段=='downloading' and 版本 is not None:
        return {
            'label':标签,
            'detail':填入(中文['desktop.update.downloadDetail'],{'percent':百分,'version':版本}),
        }
    if 版本 is None:
        详情=标签
    else:
        详情=填入(中文['desktop.update.versionDetail'],{'label':标签,'version':版本})
    return {'label':标签,'detail':详情}

def 注入更新样式(文档):
    '更新指示样式只插一次'
    注入模块样式文件(
        文档,
        '桌面更新指示器样式',
        os.path.join(os.path.dirname(__file__),'桌面更新指示器.module.css'),
        样式模块,
    )

class 桌面更新指示:
    '宽栏上的更新状态。忙的时候点击并进同一次动作'
    def __init__(自身,属性):
        '记下份额并画出'
        自身.属性=属性
        自身.根=None
        自身.提示=None
        自身.渲染()

    def 更新(自身,属性):
        '换份额'
        自身.属性=属性

    def 拆除(自身):
        '卸掉提示泡挂在文档上的监听'
        if 自身.提示 is not None and callable(自身.提示.卸):
            自身.提示.卸()
        自身.提示=None

    def 渲染(自身):
        '窄栏、被连接状态挡住，或空闲且没失败时不画'
        自身.拆除()
        属性=自身.属性
        视图=属性['view']
        呈现=视图.get('presentation')
        失败=视图['failed'] is True
        空闲=失败 is False and (呈现 is None or 呈现.get('phase')=='idle')
        if 属性['wide'] is not True or 属性['hidden'] is True or 空闲:
            自身.根=None
            return None
        窗口=属性['window']
        文档=窗口.document
        注入更新样式(文档)
        重试=中文['desktop.update.retry']
        if 呈现 is None:
            文案={'label':重试,'detail':重试}
        else:
            文案=更新文案(呈现)
        标签=重试 if 失败 else 文案['label']
        提示文=重试 if 失败 else 文案['detail']
        出错=失败 or (呈现 is not None and 呈现.get('phase')=='error')
        忙=视图['opening'] is True or (呈现 is not None and 呈现.get('phase') in 忙阶段)
        钮=模块节点(文档,'button',样式模块,'indicator')
        钮.type='button'
        钮.setAttribute('aria-label',标签)
        if 忙:
            钮.setAttribute('aria-disabled','true')
        图标盒=模块节点(文档,'span',样式模块,'icon')
        图标盒.setAttribute('aria-hidden','true')
        if 出错:
            点=模块节点(文档,'span',样式模块,'errorDot')
            图标盒.appendChild(点)
        elif 忙:
            转=图标加载描边常规({'window':窗口,'size':14,'className':'spinner'})
            标样式模块(转,样式模块)
            图标盒.appendChild(转)
        else:
            图标盒.appendChild(图标下载16({'window':窗口,'size':14}))
        钮.appendChild(图标盒)
        字=文档.createElement('span')
        字.textContent=标签
        钮.appendChild(字)
        def 点(事件):
            '不忙才打开更新'
            if 忙 is False:
                属性['onOpen']()
        钮.addEventListener('click',点)
        自身.提示=提示泡({
            'window':窗口,
            'label':提示文,
            'side':'top',
            'children':钮,
        })
        自身.根=自身.提示.渲染()
        return 自身.根

class 桌面更新角标:
    '折叠侧栏展开钮上的更新点。连接异常时让位，安装中除外'
    def __init__(自身,属性):
        '记下份额并画出'
        自身.属性=属性
        自身.根=None
        自身.提示=None
        自身.已订=False
        自身.退订=[]
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 更新(自身,属性):
        '换份额'
        自身.属性=属性

    def 拆订阅(自身):
        '退掉更新和连接'
        for 退 in 自身.退订:
            退()
        自身.退订=[]
        自身.已订=False

    def 拆提示(自身):
        '卸掉提示泡'
        if 自身.提示 is not None and callable(自身.提示.卸):
            自身.提示.卸()
        自身.提示=None

    def 渲染(自身):
        '断开或连接中且不是安装阶段时不画。空闲且没失败也不画'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            自身.拆提示()
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            注入更新样式(文档)
            def 全量(值):
                '整份快照'
                return 值
            视图=属性['useDesktopUpdate'](全量)
            连接=属性['useConnectionState'](全量)
            呈现=视图.get('presentation')
            失败=视图['failed'] is True
            阶段=None if 呈现 is None else 呈现.get('phase')
            连接让位=(连接=='disconnected' or 连接=='connecting') and 阶段!='installing'
            空闲=失败 is False and (呈现 is None or 阶段=='idle')
            if 自身.根 is None:
                自身.根=文档.createElement('div')
                自身.根.style.display='contents'
            else:
                while 自身.根.firstChild is not None:
                    自身.根.firstChild.remove()
            if 连接让位 is False and 空闲 is False:
                重试=中文['desktop.update.retry']
                if 呈现 is None:
                    文案={'label':重试,'detail':重试}
                else:
                    文案=更新文案(呈现)
                标签=重试 if 失败 else 文案['label']
                提示文=标签 if 失败 else 文案['detail']
                点=模块节点(文档,'span',样式模块,'badge')
                点.setAttribute('role','img')
                点.setAttribute('aria-label',标签)
                自身.提示=提示泡({
                    'window':窗口,
                    'label':提示文,
                    'side':'right',
                    'children':点,
                })
                自身.根.appendChild(自身.提示.渲染())
            if 自身.已订 is False:
                自身.已订=True
                def 变更():
                    '更新或连接变了就重画。已经不在页面上就退订'
                    if 自身.绘制中:
                        自身.待重画=True
                        return
                    if 自身.根 is None or 自身.根.parentNode is None:
                        自身.拆订阅()
                        return
                    自身.渲染()
                for 名 in ('useDesktopUpdate','useConnectionState'):
                    钩=属性.get(名)
                    if 钩 is not None and hasattr(钩,'_subscribe') and callable(钩._subscribe):
                        退=钩._subscribe(变更)
                        if callable(退):
                            自身.退订.append(退)
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

    def 拆除(自身):
        '退订并卸提示泡'
        自身.拆提示()
        自身.拆订阅()
