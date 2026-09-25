"""工作区与会话通知的 shell.overlay 席。
同一时刻一条通知；父重渲染不延长停留。
"""

__all__=['行动作提示','长提示停留毫秒','朴素通知文案']#仅中文公开名

长提示停留毫秒=6000#可操作归档通知与创建拒绝的停留

def 朴素通知文案(提示,翻译):
    """一条朴素警告文案，按通知 kind 闭包。"""
    种=提示['kind']#种
    if 种=='pinFailed':#置顶失败
        return 翻译('toast.pinFailed')#文
    if 种=='unpinFailed':#取消置顶失败
        return 翻译('toast.unpinFailed')#文
    if 种=='defaultWorkspaceFailed':#默认工作区失败
        return 翻译('defaultWorkspace.failed')#文
    if 种=='archivedNotOpenable':#已归档不可开
        return 翻译('toast.archivedNotOpenable')#文
    raise ValueError(f'未知通知种:{种}')#闭包兜底

class 行动作提示:#shell.overlay 通知
    """归档成功带撤销；创建拒绝带 Host 原因；其余朴素警告。"""

    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#props

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性 if 属性 is not None else {}#最新

    def 渲染(自身):
        """当前通知，或 None。"""
        属性=自身.属性#props
        提示=属性['useToast'](lambda 当前:当前)#当前
        if 提示 is None:#无
            return None#空
        翻译=属性['t']#文案
        收起=属性['dismissToast']#收起
        种=提示['kind']#种
        if 种=='archived' or 种=='stoppedAndArchived':#归档成功族
            会话标识=提示['sessionId']#会话
            归档行可见=属性['useStore'](lambda 态:(态['archivedFilter'] if 'archivedFilter' in 态 else 'default')!='default')#已显归档
            def 撤销():
                """收起并撤销归档。"""
                收起()#收
                属性['undoArchive'](会话标识)#撤销
            动作表=[{'label':翻译('toast.archivedUndo'),'onClick':撤销}]#动作
            if not 归档行可见:#未显归档行
                def 显示归档():
                    """收起并打开归档过滤。"""
                    收起()#收
                    属性['showArchived']()#显
                动作表.append({'prefix':翻译('toast.archivedOr'),'label':翻译('toast.archivedFilter'),'onClick':显示归档})#过滤
            return {#Toast
                'type':'Toast','key':f"toast-{提示['seq']}",#键
                'text':翻译('toast.archived' if 种=='archived' else 'toast.stoppedAndArchived'),#文
                'tone':'success',#成功调
                'holdMs':长提示停留毫秒,#停留
                'actions':动作表,#动作
                'onDone':收起,#完
            }#Toast 结束
        if 种=='createFailed':#创建拒绝
            return {#Toast
                'type':'Toast','key':f"toast-{提示['seq']}",#键
                'text':翻译('toast.createFailed',{'message':提示['message']}),#带原因
                'icon':'IconWarningOutlineRegular',#图标
                'holdMs':长提示停留毫秒,#停留
                'onDone':收起,#完
            }#Toast 结束
        return {#朴素警告
            'type':'Toast','key':f"toast-{提示['seq']}",#键
            'text':朴素通知文案(提示,翻译),#文
            'icon':'IconWarningOutlineRegular',#图标
            'onDone':收起,#完
        }#Toast 结束

    def __call__(自身,属性=None):
        """刷新后渲染。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
