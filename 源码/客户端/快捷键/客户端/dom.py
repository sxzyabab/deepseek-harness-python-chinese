"""主文档键盘适配器；局部控件在窗口冒泡前仲裁。"""
import re#平台探测

__all__=['模态选择器','探测环境','安装键盘']#仅中文公开名

模态选择器='[role="dialog"][aria-modal="true"], [role="menu"]'#与 ui-primitives 对齐
苹果设备=re.compile(r'darwin|mac|iphone|ipad',re.IGNORECASE)#苹果
窗口设备=re.compile(r'win',re.IGNORECASE)#Windows

def 探测环境(文档,导航):
    """检测访问设备，而非服务器操作系统。"""
    根=文档.documentElement#html
    桌面标记=None#data-platform
    集=getattr(根,'dataset',None)#dataset
    if 集 is not None:#有
        桌面标记=getattr(集,'platform',None)#平台标记
    设备=桌面标记 if 桌面标记 is not None else 导航.platform#设备串
    运行时='web' if 桌面标记 is None else 'desktop'#壳
    if 苹果设备.search(设备) is not None:#苹果
        平台='macos'#mac
    elif 窗口设备.search(设备) is not None:#Windows
        平台='windows'#win
    else:#其余
        平台='linux'#linux
    return {'runtime':运行时,'platform':平台}#环境

def 安装键盘(窗口,快捷键,固定=None,原生=False):
    """安装文档输入法组合跟踪，并在局部处理器之后做应用分发。"""
    文档=窗口.document#文档
    #组合态：对齐 observeComposition
    组合中=False#compositionstart
    刚结束=False#compositionend 至 keyup
    def 组合开始():
        """进入组合。"""
        nonlocal 组合中#写
        组合中=True#开
    def 组合结束():
        """结束组合，记刚结束。"""
        nonlocal 组合中,刚结束#写
        组合中=False#关
        刚结束=True#刚结束
    def 组合释放():
        """keyup 清刚结束。"""
        nonlocal 刚结束#写
        刚结束=False#清
    def 组合失焦():
        """失焦清组合。"""
        nonlocal 组合中,刚结束#写
        组合中=False#关
        刚结束=False#清
    def 组合守卫(事件):
        """是否应视为组合中。"""
        nonlocal 刚结束#写
        键码=getattr(事件,'keyCode',None)#旧键码
        守卫=组合中 or 刚结束 or getattr(事件,'isComposing',False) or 键码==229#IME
        刚结束=False#消费刚结束
        return 守卫#是否守卫
    文档.addEventListener('compositionstart',组合开始,True)#开始
    文档.addEventListener('compositionend',组合结束,True)#结束
    文档.addEventListener('keyup',组合释放,True)#释放
    视口=getattr(文档,'defaultView',None)#窗口
    if 视口 is not None:#有
        视口.addEventListener('blur',组合失焦)#失焦
    待定=False#捕获后待定重置
    待定时器=None#setTimeout 句柄
    def 重置():
        """使固定序列失效。"""
        if 固定 is not None:#有消费者
            固定({'type':'reset'})#重置
    死键=False#Dead 键残留
    def 失焦():
        """窗口失焦清死键并重置。"""
        nonlocal 死键#写
        死键=False#清
        重置()#重置
    def 含模态(节点):
        """节点自身或子孙是否模态。"""
        匹配=getattr(节点,'matches',None)#matches
        查询=getattr(节点,'querySelector',None)#querySelector
        if not callable(匹配):#非元素
            return False#否
        if 匹配(模态选择器):#自身
            return True#是
        if callable(查询) and 查询(模态选择器) is not None:#子孙
            return True#是
        return False#否
    def 模态变更(记录表):
        """模态增删或属性变则重置。"""
        for 记录 in 记录表:#逐记录
            if 记录.type=='attributes':#属性
                if 记录.oldValue in ('dialog','true') or 含模态(记录.target):#相关
                    重置()#重置
                    return#止
            else:#子树
                for 节点 in list(记录.addedNodes)+list(记录.removedNodes):#增减
                    if 含模态(节点):#含模态
                        重置()#重置
                        return#止
    观察者=None#MutationObserver
    if 固定 is not None:#需要观察
        观察者=窗口.MutationObserver(模态变更) if hasattr(窗口,'MutationObserver') else None#构造
        if 观察者 is None:#挂在全局
            import builtins#全局
            观察构造=getattr(builtins,'MutationObserver',None)#构造
            if 观察构造 is not None:#有
                观察者=观察构造(模态变更)#建
        if 观察者 is not None:#观察根
            观察者.observe(文档.documentElement,{#选项
                'childList':True,
                'subtree':True,
                'attributes':True,
                'attributeFilter':['role','aria-modal'],
                'attributeOldValue':True,
            })#观察结束
    def 捕获(_事件=None):
        """捕获阶段：安排微任务式重置。"""
        nonlocal 待定,待定时器#写
        if 待定:#已有待定
            重置()#立即重置
        窗口.clearTimeout(待定时器)#清旧
        if 观察者 is not None:#冲刷突变
            模态变更(观察者.takeRecords())#冲刷
        待定=True#待定
        def 到期():
            """零延迟后重置。"""
            nonlocal 待定,待定时器#写
            待定=False#清
            待定时器=None#清
            重置()#重置
        待定时器=窗口.setTimeout(到期,0)#排队
    def 按下(事件):
        """冒泡阶段分发。"""
        nonlocal 待定,待定时器,死键#写
        窗口.clearTimeout(待定时器)#清待定
        待定时器=None#清
        待定=False#清
        #解析目标
        目标=None#元素
        路径=事件.composedPath() if callable(getattr(事件,'composedPath',None)) else []#路径
        for 值 in 路径:#找元素
            if callable(getattr(值,'matches',None)):#元素
                目标=值#记下
                break#止
        元素=目标 if 目标 is not None else 文档.activeElement#焦点回落
        if 元素 is not None and callable(getattr(元素,'closest',None)) and 元素.closest('.xterm'):#终端
            区域='terminal'#终端
        elif 元素 is not None and callable(getattr(元素,'closest',None)) and 元素.closest(
            'input, textarea, select, [contenteditable="true"], [contenteditable=""]'
        ):#可编辑
            区域='editable'#可编辑
        else:#页面
            区域='page'#页面
        对话框=文档.querySelectorAll(模态选择器)#模态列
        顶=对话框[len(对话框)-1] if len(对话框)>0 else None#最前
        if 顶 is None:#无模态
            模态=None#空
        else:#有
            数据=getattr(顶,'dataset',None)#dataset
            模态=getattr(数据,'shortcutModal',None) if 数据 is not None else None#声明
            if 模态 is None:#未声明
                模态='other'#其他
        上下文={'region':区域,'modal':模态,'target':元素}#上下文
        守卫=组合守卫(事件) or 死键 or 事件.getModifierState('AltGraph')#守卫
        是死=事件.key=='Dead'#Dead
        #macOS 可能在输入法组合外把 Option+Command+N 报告为 Dead
        命令死键=(是死 and 快捷键.runtime=='web' and 快捷键.platform=='macos'
            and 事件.code=='KeyN' and 事件.metaKey and 事件.altKey
            and not 事件.ctrlKey and not 事件.shiftKey)#特例
        死键=是死#记下
        手势={#手势
            'code':事件.code,
            'control':事件.ctrlKey,
            'alt':事件.altKey,
            'shift':事件.shiftKey,
            'meta':事件.metaKey,
            'repeat':事件.repeat,
            'composing':守卫 or 是死,
            'defaultPrevented':事件.defaultPrevented,
        }#手势结束
        def 消费():
            """preventDefault；特例清死键。"""
            nonlocal 死键#写
            事件.preventDefault()#消费
            if 命令死键:#特例
                死键=False#清
        if 固定 is not None:#固定消费者
            固定({'type':'keydown','gesture':手势,'context':上下文,'consume':消费})#投递
        if 原生:#原生拥有可配置绑定
            return#DOM 只喂固定
        分发手势={#分发用
            **手势,
            'composing':守卫 or (是死 and not 命令死键),
            'defaultPrevented':事件.defaultPrevented,
        }#手势
        快捷键.dispatch(分发手势,上下文,消费)#分发
    文档.addEventListener('compositionstart',重置,True)#重置
    文档.addEventListener('compositionend',重置,True)#重置
    文档.addEventListener('focusin',重置,True)#重置
    文档.addEventListener('pointerdown',重置,True)#重置
    窗口.addEventListener('keydown',捕获,True)#捕获
    窗口.addEventListener('keydown',按下)#冒泡
    窗口.addEventListener('blur',失焦)#失焦
    def 拆除():
        """释放全部监听。"""
        nonlocal 待定,待定时器#写
        待定=False#清
        窗口.clearTimeout(待定时器)#清时器
        if 观察者 is not None:#卸观察
            观察者.disconnect()#断
        文档.removeEventListener('compositionstart',组合开始,True)#卸
        文档.removeEventListener('compositionend',组合结束,True)#卸
        文档.removeEventListener('keyup',组合释放,True)#卸
        if 视口 is not None:#卸失焦
            视口.removeEventListener('blur',组合失焦)#卸
        文档.removeEventListener('compositionstart',重置,True)#卸
        文档.removeEventListener('compositionend',重置,True)#卸
        文档.removeEventListener('focusin',重置,True)#卸
        文档.removeEventListener('pointerdown',重置,True)#卸
        窗口.removeEventListener('keydown',捕获,True)#卸
        窗口.removeEventListener('keydown',按下)#卸
        窗口.removeEventListener('blur',失焦)#卸
    return 拆除#拆除器
