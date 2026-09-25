from .语音输入安装对话框 import 语音输入安装对话框

__all__=['语音输入安装提示']

def 读就绪(属性):
    """注入面 hooks.speechReadiness。"""
    钩=属性.get('hooks') or {}
    存储=钩.get('speechReadiness')
    if 存储 is not None:
        return 存储.getSnapshot()
    取=属性.get('useSpeechReadiness')
    if 取 is not None:
        def 全量(快照):
            """整份就绪快照。"""
            return 快照
        return 取(全量)
    return {'catalog':None,'connected':False,'error':None}

class 语音输入安装提示:
    """首次启用后、缓存检查完成时，只引导去安装、不开始下载。"""
    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性
        自身.对话框=语音输入安装对话框({
            'open':False,
            'needsInstallation':True,
            'onDismiss':属性['onDismiss'],
            'onOpenDetails':属性['onOpenDetails'],
            't':属性['t'],
        })

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性

    def 渲染(自身):
        """仅所选本地提供方仍需准备时显示。"""
        翻译=自身.属性['t']
        就绪=读就绪(自身.属性)
        目录=就绪.get('catalog')
        提供方=None
        if 目录 is not None:
            选=目录.get('selection') or {}
            for 项 in 目录.get('providers') or []:
                if 项.get('id')==选.get('providerId'):
                    提供方=项
                    break
        阶段=None
        if 就绪.get('connected') and 提供方 is not None:
            阶段=(提供方.get('preparation') or {}).get('phase')
        需安装=阶段=='unprepared' and 提供方 is not None and 提供方.get('location')=='host-local'
        if 阶段 is not None and 阶段!='checking' and not 需安装:
            自身.属性['onDismiss']()
            return None
        return 自身.对话框({
            'open':需安装,
            'needsInstallation':True,
            'onDismiss':自身.属性['onDismiss'],
            'onOpenDetails':自身.属性['onOpenDetails'],
            't':翻译,
        })

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
