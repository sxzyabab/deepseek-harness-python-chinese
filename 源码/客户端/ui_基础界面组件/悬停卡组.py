from ..模块.客户端.通告 import 取握手窗口

__all__=['悬停卡组']

class 悬停卡组:
    '一组悬停卡共用第一次停留。指针在列表或卡片上时保持温热'
    def __init__(自身,属性=None):
        '记下子内容和协调状态'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.指针='outside'
        自身.温热=False
        自身.活动=None
        自身.根=None

    def 是否温热(自身):
        '第一次已经打开过'
        return 自身.温热

    def 进入(自身,在卡片上):
        '指针进入列表或卡片'
        if 在卡片上:
            自身.指针='card'
            自身.温热=True
        else:
            自身.指针='list'

    def 离开(自身):
        '指针离开整组。没有打开的卡片就冷却'
        自身.指针='outside'
        if 自身.活动 is None:
            自身.温热=False

    def 包含卡片(自身,目标):
        '目标是不是当前卡片里的节点'
        if 自身.活动 is None or 目标 is None:
            return False
        return 自身.活动['element'].contains(目标) is True

    def 已显示(自身,业主,收起,元素):
        '记下当前卡片。换了一张就收起上一张'
        if 自身.指针=='card':
            自身.指针='outside'
            自身.温热=False
        if 自身.指针=='list':
            自身.温热=True
        上一张=自身.活动
        自身.活动={'owner':业主,'dismiss':收起,'element':元素}
        if 上一张 is not None and 上一张['owner'] is not 业主:
            上一张['dismiss']()

    def 释放(自身,业主):
        '这张卡片关掉。指针不在列表上就冷却'
        if 自身.活动 is None or 自身.活动['owner'] is not 业主:
            return
        自身.活动=None
        if 自身.指针!='list':
            自身.指针='outside'
            自身.温热=False

    def 渲染(自身):
        '画出包住列表的容器，并听捕获阶段的指针进出'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        根=文档.createElement('div')
        类名=属性.get('className')
        if isinstance(类名,str) and 类名!='':
            根.className=类名
        子=属性.get('children')
        if hasattr(子,'tagName'):
            根.appendChild(子)
        elif isinstance(子,str):
            根.textContent=子
        elif isinstance(子,(list,tuple)):
            for 项 in 子:
                if hasattr(项,'tagName'):
                    根.appendChild(项)
        def 入(事件):
            '指针进组或进当前卡片'
            在卡片=自身.包含卡片(事件.target)
            if 根.contains(事件.target) is True or 在卡片:
                自身.进入(在卡片)
        def 出(事件):
            '指针离开整组才算离开'
            从组=根.contains(事件.target) is True or 自身.包含卡片(事件.target)
            相关=getattr(事件,'relatedTarget',None)
            进组=False
            if 相关 is not None:
                进组=根.contains(相关) is True or 自身.包含卡片(相关)
            if 从组 and not 进组:
                自身.离开()
        根.addEventListener('pointerover',入,True)
        根.addEventListener('pointerout',出,True)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 自身.根
