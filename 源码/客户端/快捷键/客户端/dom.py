'主文档键盘适配器。局部控件在窗口冒泡前仲裁'
import re#访问设备
import pywebbridge#页面上的未定义
from ...ui_基础界面组件.模态层 import 模态选择器#对话框与菜单
from ...ui_基础界面组件.键盘合成 import 观察合成#输入法组合守卫

__all__=['探测环境','安装键盘']

未定义=pywebbridge.undefined#属性缺失

def 探测环境(文档,导航):
    '检测访问设备，而不是服务器操作系统'
    桌面标记=文档.documentElement.dataset.platform#data-platform，没有就是未定义
    if 桌面标记 is 未定义 or 桌面标记 is None:#未定义或 null 才改用导航平台
        设备=导航.platform#浏览器报告的平台
    else:#预加载写了标记，空串也算
        设备=桌面标记#标记原文
    if re.search(r'darwin|mac|iphone|ipad',设备,re.IGNORECASE) is not None:#苹果
        平台='macos'#mac
    elif re.search(r'win',设备,re.IGNORECASE) is not None:#Windows
        平台='windows'#win
    else:#其余
        平台='linux'#linux
    return {'runtime':'web' if 桌面标记 is 未定义 else 'desktop','platform':平台}#环境

def 安装键盘(窗口,快捷键,固定=None,原生=False):
    '安装输入法组合跟踪，并在局部处理器之后做应用分发'
    文档=窗口.document#文档
    组合=观察合成(文档)#组合守卫
    待定=False#捕获后等待冒泡
    待定时器=None#零延迟句柄
    死键=False#Dead 键残留
    对话框表=未定义#模态节点缓存，有变更才重查

    def 重置():
        '使固定序列失效'
        if 固定 is not None:#有消费者
            固定({'type':'reset'})#重置

    def 含模态(节点):
        '节点自身或子孙是否模态'
        if 节点 is None or 节点 is 未定义:#空
            return False#否
        匹配=getattr(节点,'matches',None)#元素才有。没有时是 undefined
        if 匹配 is 未定义 or not callable(匹配):#文本节点
            return False#否
        if 匹配(模态选择器):#自身
            return True#是
        查询=节点.querySelector(模态选择器)#子孙
        return 查询 is not None and 查询 is not 未定义#有则是

    def 列表含模态(清单):
        '节点列表里是否有模态'
        if 清单 is None or 清单 is 未定义:#空
            return False#否
        数量=清单.length#长度
        下标=0#下标
        while 下标<数量:#逐个
            if 含模态(清单[下标]):#含模态
                return True#是
            下标+=1#下一个
        return False#否

    def 模态变更(记录表):
        '有记录就丢掉模态缓存。碰到模态增删或角色变化就重置固定序列'
        nonlocal 对话框表#写缓存
        数量=记录表.length#页面数组不能用 len，越界下标是 undefined
        if 数量>0:#有变更
            对话框表=未定义#下次重查
        下标=0#下标
        while 下标<数量:#逐条
            记录=记录表[下标]#这一条
            下标+=1#下一个
            if 记录.type=='attributes':#属性
                if 记录.oldValue=='dialog' or 记录.oldValue=='true' or 含模态(记录.target):#相关
                    重置()#重置
                    return#一条就够
            elif 列表含模态(记录.addedNodes) or 列表含模态(记录.removedNodes):#子树增减
                重置()#重置
                return#一条就够

    观察者=pywebbridge.new(窗口.MutationObserver,模态变更)#模态缓存与固定序列
    观察者.observe(文档.documentElement,{
        'childList':True,
        'subtree':True,
        'attributes':True,
        'attributeFilter':['role','aria-modal'],
        'attributeOldValue':True,
    })

    def 失焦():
        '窗口失焦时清掉死键并重置固定序列'
        nonlocal 死键#写
        死键=False#清
        重置()#重置

    def 捕获(事件=None):
        '捕获阶段安排一次零延迟重置'
        nonlocal 待定,待定时器#写
        if 待定:#上一记还没冒泡
            重置()#先重置
        窗口.clearTimeout(待定时器)#清旧
        模态变更(观察者.takeRecords())#冲刷
        待定=True#等冒泡
        def 到期():
            '零延迟后仍没有冒泡键就重置'
            nonlocal 待定,待定时器#写
            待定=False#结束等待
            待定时器=None#句柄作废
            重置()#重置
        待定时器=窗口.setTimeout(到期,0)#排队

    def 按下(事件):
        '冒泡阶段把键交给固定序列，再按需分发可编辑命令'
        nonlocal 待定,待定时器,死键,对话框表#写
        窗口.clearTimeout(待定时器)#取消零延迟重置
        待定时器=None#句柄作废
        待定=False#冒泡已到
        目标=None#路径上的元素
        for 值 in 事件.composedPath():#从目标向外
            if callable(getattr(值,'matches',None)):#元素
                目标=值#最近的元素
                break#止
        元素=目标 if 目标 is not None else 文档.activeElement#没有路径元素就用焦点
        if 元素 is not None and 元素.closest('.xterm'):#终端
            区域='terminal'#终端
        elif 元素 is not None and 元素.closest('input, textarea, select, [contenteditable="true"], [contenteditable=""]'):#可编辑
            区域='editable'#可编辑
        else:#页面
            区域='page'#页面
        模态变更(观察者.takeRecords())#局部处理器可能已经改了模态
        if 对话框表 is 未定义:#缓存失效
            对话框表=文档.querySelectorAll(模态选择器)#重查
        长度=对话框表.length#模态数
        顶=None if 长度==0 else 对话框表[长度-1]#最前一层
        if 顶 is None:#无模态
            模态=None#空
        else:#有模态
            声明=顶.dataset.shortcutModal#声明的模态名
            模态='other' if 声明 is 未定义 or 声明 is None else 声明#未声明归其他
        上下文={'region':区域,'modal':模态,'target':元素}#分发上下文
        守卫=组合['guards'](事件) or 死键 or 事件.getModifierState('AltGraph')#组合或死键
        是死=事件.key=='Dead'#这一记是 Dead
        命令死键=是死 and 快捷键.runtime=='web' and 快捷键.platform=='macos' and 事件.code=='KeyN' and 事件.metaKey and 事件.altKey and not 事件.ctrlKey and not 事件.shiftKey#Option+Command+N
        死键=是死#留给下一记
        手势={
            'code':事件.code,
            'control':事件.ctrlKey,
            'alt':事件.altKey,
            'shift':事件.shiftKey,
            'meta':事件.metaKey,
            'repeat':事件.repeat,
            'composing':守卫 or 是死,
            'defaultPrevented':事件.defaultPrevented,
        }

        def 消费():
            '阻止浏览器默认，并清掉命令死键特例'
            nonlocal 死键#写
            事件.preventDefault()#消费
            if 命令死键:#特例
                死键=False#下一记不再当成死键

        if 固定 is not None:#固定序列在可编辑命令之前
            固定({'type':'keydown','gesture':手势,'context':上下文,'consume':消费})#投递
        if 原生:#原生键盘拥有可配置绑定
            return#DOM 只喂固定序列
        快捷键.dispatch({
            **手势,
            'composing':守卫 or (是死 and not 命令死键),
            'defaultPrevented':事件.defaultPrevented,
        },上下文,消费)#分发

    文档.addEventListener('compositionstart',重置,True)#组合开始即重置
    文档.addEventListener('compositionend',重置,True)#组合结束即重置
    文档.addEventListener('focusin',重置,True)#焦点进入即重置
    文档.addEventListener('pointerdown',重置,True)#指针按下即重置
    窗口.addEventListener('keydown',捕获,True)#捕获
    窗口.addEventListener('keydown',按下)#冒泡
    窗口.addEventListener('blur',失焦)#失焦

    def 拆除():
        '释放监听、模态观察、组合守卫和缓存'
        nonlocal 待定,对话框表#写
        待定=False#不再等冒泡
        窗口.clearTimeout(待定时器)#清时器
        观察者.disconnect()#停止观察
        对话框表=未定义#丢掉节点
        组合['dispose']()#卸组合守卫
        文档.removeEventListener('compositionstart',重置,True)#卸
        文档.removeEventListener('compositionend',重置,True)#卸
        文档.removeEventListener('focusin',重置,True)#卸
        文档.removeEventListener('pointerdown',重置,True)#卸
        窗口.removeEventListener('keydown',捕获,True)#卸捕获
        窗口.removeEventListener('keydown',按下)#卸冒泡
        窗口.removeEventListener('blur',失焦)#卸失焦

    return 拆除#拆除器
