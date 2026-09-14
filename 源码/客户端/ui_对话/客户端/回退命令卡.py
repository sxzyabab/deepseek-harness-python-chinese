
__all__=['回退命令卡','行状态','前导图标']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

def 行状态(结果):
    """未结算 running；error/ok。"""
    if 结果 is None:#未结
        return 'running'#跑
    种类=结果['kind'] if 'kind' in 结果 else None#种类
    return 'error' if 种类=='error' else 'ok'#结

def 前导图标(状态):
    """error 用 StateDot；否则 api 图标。"""
    return 'error-dot' if 状态=='error' else 'api-icon'#图标

class 回退命令卡:
    """name · outcome；多行正文可展。"""

    def __init__(自身,属性=None):
        """记下 props 与展开。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.展开=False#展

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 切换(自身):
        """翻转。"""
        自身.展开=not 自身.展开#翻

    def 渲染(自身):
        """DisclosureRow 形。"""
        属性=自身.属性#props
        节点=属性['node'] if 'node' in 属性 else None#命令节点
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        跑摘要=属性['runningSummary'] if 'runningSummary' in 属性 else None#专属跑文
        结果=节点['outcome'] if 节点 is not None and 'outcome' in 节点 else None#结果
        正文=结果['text'] if 结果 is not None and 'text' in 结果 else None#文
        if 结果 is None:#跑
            摘要=跑摘要 if 跑摘要 is not None else 翻译('command.running')#摘要
        elif 正文 is not None:#有文
            摘要=正文#用文
        else:#无文
            种类=结果['kind'] if 'kind' in 结果 else None#种类
            摘要=翻译('command.failed') if 种类=='error' else 翻译('command.done')#结
        标题=节点['name'] if 节点 is not None and 'name' in 节点 else None#名
        if 标题 is None:#无
            标题=翻译('command.title')#默认
        状态=行状态(结果)#态
        体=正文 if 正文 is not None and '\n' in 正文 else None#多行体
        开=自身.展开 is True and 体 is not None#开
        return {#卡
            'type':'generic-command-card',#类型
            'className':'root',#根
            'data-variant':'others',#变体
            'data-state':状态,#态
            'runningA11y':翻译('row.running') if 状态=='running' else None,#跑无障碍
            'failedA11y':翻译('row.failed') if 状态=='error' else None,#败无障碍
            'leading':前导图标(状态),#前导
            'title':标题,#标题
            'open':开,#开
            'expandable':体 is not None,#可展
            'summary':摘要,#摘要
            'error':状态=='error',#错
            'body':体,#体
            'onToggle':自身.切换,#切换
            'cssModule':'聊天/通用命令卡.module.css',#样式
            'a11yModule':'聊天/无障碍.module.css',#无障碍
        }#结束

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
