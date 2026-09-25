"""语音激活与识别不可用时的共用模态。"""

__all__=['语音输入安装对话框']

class 语音输入安装对话框:
    """把激活或麦克风点击导向既有插件详情；从不启动准备或录音。"""
    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性

    def 渲染(自身):
        """安装引导或不可用说明。"""
        翻译=自身.属性['t']
        需安装=bool(自身.属性.get('needsInstallation'))
        return {
            'type':'voice-setup-dialog',
            'open':bool(自身.属性.get('open')),
            'title':翻译('setupPrompt.title' if 需安装 else 'setupPrompt.unavailableTitle'),
            'closeLabel':翻译('cancel'),
            'body':翻译('setupPrompt.body' if 需安装 else 'setupPrompt.unavailableBody'),
            'later':翻译('setupPrompt.later'),
            'primary':翻译('setupPrompt.open' if 需安装 else 'setupPrompt.details'),
            'onDismiss':自身.属性['onDismiss'],
            'onOpenDetails':自身.属性['onOpenDetails'],
        }

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

VoiceSetupDialog=语音输入安装对话框
