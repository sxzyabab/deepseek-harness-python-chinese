"""默认命令行：精简 GenericToolCard，作 commandview 回退。

对齐上游 `ui-conversation/src/client/chat/GenericCommandCard.tsx`。公开面仅中文名。
"""

__all__=['通用命令卡','行状态','前导种']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 行状态(结果):#outcome → 行态
    """未结算 running；error/ok。"""
    if 结果 is None:#未结
        return 'running'#跑
    return 'error' if 取字段(结果,'kind')=='error' else 'ok'#结

def 前导种(状态):#前导图标语义
    """error 用 StateDot；否则 api 图标。"""
    return 'error-dot' if 状态=='error' else 'api-icon'#种

class 通用命令卡:#命令行回退
    """name · outcome；多行正文可展。"""

    def __init__(自身,属性=None):#构造
        """记下 props 与展开。"""
        自身.属性=属性 or {}#合成
        自身.展开=False#展

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 切换(自身):#开合
        """翻转。"""
        自身.展开=not 自身.展开#翻

    def 渲染(自身):#结构树
        """DisclosureRow 形。"""
        属性=自身.属性#props
        节点=取字段(属性,'node')#命令节点
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        跑摘要=取字段(属性,'runningSummary')#专属跑文
        结果=取字段(节点,'outcome')#结果
        正文=取字段(结果,'text') if 结果 is not None else None#文
        if 结果 is None:#跑
            摘要=跑摘要 if 跑摘要 is not None else 翻译('command.running')#摘要
        elif 正文 is not None:#有文
            摘要=正文#用文
        else:#无文
            摘要=翻译('command.failed') if 取字段(结果,'kind')=='error' else 翻译('command.done')#结
        标题=取字段(节点,'name')#名
        if 标题 is None:#无
            标题=翻译('command.title')#默认
        状态=行状态(结果)#态
        体=正文 if 正文 is not None and '\n' in 正文 else None#多行体
        开=自身.展开 and 体 is not None#开
        return {#卡
            'type':'generic-command-card',#类型
            'className':'root',#根
            'data-variant':'others',#变体
            'data-state':状态,#态
            'runningA11y':翻译('row.running') if 状态=='running' else None,#跑无障碍
            'failedA11y':翻译('row.failed') if 状态=='error' else None,#败无障碍
            'leading':前导种(状态),#前导
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

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
