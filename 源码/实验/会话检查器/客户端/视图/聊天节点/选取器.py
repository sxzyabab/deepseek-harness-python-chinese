'用一块真正接住点击的罩子，在主对话上选取一次'

from ......客户端.模块.客户端.通告 import 取握手窗口
import os#样式文件
from ......客户端.ui_对话.异常 import 注入模块样式文件,标样式模块#检查器样式
from .文档对象 import 已显示,在聊天内#可见和所属列
from .高亮 import 放置聊天高亮#罩子和预览的位置
from .选取匹配 import 匹配聊天元素#指针下的身份

样式模块='session-inspector'#与表格共用的样式模块
指针动作=('pointerdown','pointerup','mousedown','mouseup','auxclick','dblclick','contextmenu')#罩子要吞掉的指针

class 检查器聊天选取器:
    '一次选取手势的罩子、预览和几何观察'
    def __init__(自身,取根,所有者,已选取,已取消,已释放):
        '取根返回当前会话的主对话。所有者藏起来或拆掉就取消'
        自身.取根=取根#当前主对话
        自身.所有者=所有者#选取按钮
        自身.已选取=已选取#选中回调，真表示完成
        自身.已取消=已取消#取消时清面板状态
        自身.已释放=已释放#资源拆掉后忘掉这次手势
        自身.罩=None#点击罩
        自身.覆盖=None#悬停预览
        自身.根=None#开始时的对话列
        自身.观察=None#属性变化
        自身.缩放=None#列尺寸

    def 确保样式(自身,文档):
        '罩子和预览用检查器样式'
        注入模块样式文件(文档,'dsh-session-inspector',os.path.join(os.path.dirname(__file__),'..','检查器.module.css'),样式模块)#只插一次

    def 开始(自身):
        '在可见的主对话上装罩子。没有可见对话就不动'
        根=自身.取根()#当前列
        if 根 is None or not 已显示(根) or not 已显示(自身.所有者):#对话或按钮不可见
            return False#不开始
        窗口=取握手窗口()#页面
        文档=窗口.document#文档
        自身.确保样式(文档)#样式
        罩=文档.createElement('div')#罩子
        if not 放置聊天高亮(罩,根):#列不在视口里
            return False#不装
        罩.className='chatPickMask'#罩子类名
        标样式模块(罩,样式模块)#接上模块
        罩.setAttribute('data-session-inspector-picker','')#选取罩标记
        罩.setAttribute('aria-hidden','true')#不进无障碍树
        自身.根=根#记住列
        自身.罩=罩#记住罩
        罩.addEventListener('pointermove',自身.移动)#预览
        罩.addEventListener('pointerleave',自身.隐藏)#离开就收预览
        罩.addEventListener('click',自身.点击)#选定
        罩.addEventListener('wheel',自身.滚轮,{'passive':False})#转给下面的滚动口
        for 类型 in 指针动作:#其余指针
            罩.addEventListener(类型,自身.压下)#吞掉
        文档.body.append(罩)#挂到页面
        窗口.addEventListener('keydown',自身.按键,True)#Esc
        窗口.addEventListener('blur',自身.取消)#失焦取消
        窗口.addEventListener('scroll',自身.定位,True)#滚动后重测
        窗口.addEventListener('resize',自身.定位)#缩放后重测
        自身.观察=窗口.MutationObserver(自身.核对)#属性变化
        for 起点 in (自身.所有者,根):#按钮和列
            元素=起点#从自己往上
            while 元素 is not None:#每个祖先
                自身.观察.observe(元素,{'attributes':True,'attributeFilter':['hidden','style','class'],'childList':True})#看隐藏和结构
                元素=元素.parentElement#上一层
        if hasattr(窗口,'ResizeObserver'):#有尺寸观察
            自身.缩放=窗口.ResizeObserver(自身.定位)#尺寸变化
            自身.缩放.observe(根)#看对话列
        return True#罩子已装上

    def 拆除(自身):
        '拆罩子和观察，不在卸载时调用面板回调'
        罩=自身.罩#当前罩
        窗口=取握手窗口()#页面
        if 罩 is not None:#还在
            罩.removeEventListener('pointermove',自身.移动)#预览
            罩.removeEventListener('pointerleave',自身.隐藏)#离开
            罩.removeEventListener('click',自身.点击)#点击
            罩.removeEventListener('wheel',自身.滚轮)#滚轮
            for 类型 in 指针动作:#其余指针
                罩.removeEventListener(类型,自身.压下)#卸掉
            罩.remove()#从页面拿掉
        自身.罩=None#清空
        自身.根=None#清空列
        窗口.removeEventListener('keydown',自身.按键,True)#按键
        窗口.removeEventListener('blur',自身.取消)#失焦
        窗口.removeEventListener('scroll',自身.定位,True)#滚动
        窗口.removeEventListener('resize',自身.定位)#缩放
        if 自身.观察 is not None:#有观察
            自身.观察.disconnect()#停
        自身.观察=None#清空
        if 自身.缩放 is not None:#有尺寸观察
            自身.缩放.disconnect()#停
        自身.缩放=None#清空
        自身.隐藏()#收预览
        自身.已释放()#告诉登记方忘掉

    def 当前根(自身):
        '开始时的列必须仍是当前主对话，并且列和按钮都可见'
        根=自身.根#开始时的列
        if 根 is None or 自身.取根() is not 根 or not 已显示(根) or not 已显示(自身.所有者):#已经换了或藏了
            return None#不能继续
        return 根#还是这一列

    def 定位(自身,事件=None):
        '滚动或缩放后先收预览，再核对罩子还在不在'
        自身.隐藏()#预览作废
        自身.核对()#罩子可能也该取消

    def 核对(自身,记录=None):
        '列没了或罩子放不上就取消'
        if 自身.罩 is None:#已经拆了
            return#不用
        根=自身.当前根()#还有效的列
        if 根 is None or not 放置聊天高亮(自身.罩,根):#放不上
            自身.取消()#结束选取

    def 命中(自身,事件):
        '罩子下面、仍属于这列的元素'
        if 自身.罩 is None:#没有罩
            return None#没有
        根=自身.当前根()#当前列
        if 根 is None:#列失效
            自身.取消()#结束
            return None#没有
        窗口=取握手窗口()#页面
        元素=None#第一个不是罩也不是预览的元素
        for 候选 in 窗口.document.elementsFromPoint(事件.clientX,事件.clientY):#从上到下
            if 候选 is not 自身.罩 and 候选 is not 自身.覆盖:#真正的对话元素
                元素=候选#用它
                break#停
        if 元素 is None or not 在聊天内(元素,根):#不在这列
            return None#没有
        return {'element':元素,'root':根}#元素和列

    def 隐藏(自身,事件=None):
        '拿掉预览'
        if 自身.覆盖 is not None:#有预览
            自身.覆盖.remove()#拿掉
        自身.覆盖=None#清空

    def 取消(自身,事件=None):
        '结束手势并清掉面板上的选取状态'
        if 自身.罩 is None:#已经结束
            return#不重复
        自身.拆除()#先拆资源
        自身.已取消()#再通知面板

    def 移动(自身,事件):
        '在命中的盒子上放预览'
        命中=自身.命中(事件)#罩子下的元素
        匹配=None if 命中 is None else 匹配聊天元素(命中['element'],命中['root'])#身份
        if 匹配 is None:#没有可预览的盒子
            自身.隐藏()#收起
            return#停
        窗口=取握手窗口()#页面
        覆盖=自身.覆盖#已有预览
        if 覆盖 is None:#还没有
            覆盖=窗口.document.createElement('div')#新建
        覆盖.className='chatPick'#预览类名
        标样式模块(覆盖,样式模块)#接上模块
        覆盖.setAttribute('data-session-inspector-highlight','pick')#选取预览
        覆盖.setAttribute('aria-hidden','true')#不进无障碍树
        if not 放置聊天高亮(覆盖,匹配['element']):#盒子不在视口里
            自身.隐藏()#收起
            return#停
        if 自身.覆盖 is None:#第一次放上
            窗口.document.body.append(覆盖)#挂到页面
            自身.覆盖=覆盖#记住

    def 压下(自身,事件):
        '不让指针落到对话上'
        事件.preventDefault()#取消默认
        事件.stopImmediatePropagation()#不再往下传

    def 点击(自身,事件):
        '主键选中。选中回调返回真才拆掉罩子'
        自身.压下(事件)#先吞掉
        if 事件.button!=0:#不是主键
            return#不选
        命中=自身.命中(事件)#罩子下的元素
        匹配=None if 命中 is None else 匹配聊天元素(命中['element'],命中['root'])#身份
        if 匹配 is not None and 自身.已选取(匹配['target']):#面板接受了
            自身.拆除()#结束，不再调用取消

    def 滚轮(自身,事件):
        '把滚动转给对话或过程体里第一个还能滚的祖先'
        自身.压下(事件)#罩子自己不滚
        命中=自身.命中(事件)#下面的元素
        元素=None if 命中 is None else 命中['element']#起点
        窗口=取握手窗口()#页面
        while 元素 is not None:#往上找滚动口
            if 元素.matches('[data-conversation-scroll], [data-step-process-body]'):#滚动容器
                垂直=事件.deltaY<0 and 元素.scrollTop>0 or 事件.deltaY>0 and 元素.scrollTop+元素.clientHeight<元素.scrollHeight#垂直还能滚
                水平=事件.deltaX<0 and 元素.scrollLeft>0 or 事件.deltaX>0 and 元素.scrollLeft+元素.clientWidth<元素.scrollWidth#水平还能滚
                if (事件.deltaY!=0 and 垂直) or (事件.deltaX!=0 and 水平):#这一层吃得下
                    样式=窗口.getComputedStyle(元素)#行高
                    if 事件.deltaMode==窗口.WheelEvent.DOM_DELTA_PAGE:#按页
                        比例=元素.clientHeight#一页的像素
                    elif 事件.deltaMode==窗口.WheelEvent.DOM_DELTA_LINE:#按行
                        行高文=str(样式.lineHeight).replace('px','').strip()#去掉单位
                        字号文=str(样式.fontSize).replace('px','').strip()#去掉单位
                        行高=float(行高文) if 行高文.replace('.','').isdigit() else 0#行高像素
                        字号=float(字号文) if 字号文.replace('.','').isdigit() else 0#字号
                        比例=行高 or 字号 or 1#退到 1
                    else:#像素
                        比例=1#不缩放
                    元素.scrollBy({'top':事件.deltaY*比例,'left':事件.deltaX*比例,'behavior':'instant'})#滚动
                    break#只滚一层
            元素=元素.parentElement#上一层

    def 按键(自身,事件):
        'Esc 取消选取'
        if 事件.key!='Escape':#不是取消
            return#不管
        自身.压下(事件)#吞掉
        自身.取消()#结束
