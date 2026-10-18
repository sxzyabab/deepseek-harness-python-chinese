from ...模块.客户端.通告 import 取握手窗口
from .区域 import 拖拽标记,召回标记#行标记与召回标记

行选择器='['+拖拽标记+']'#拥有窗口拖拽区域的元素
宽限帧数=2#静止这么多帧之后才停。过渡的第一帧仍是起点
运动事件=('transitionstart','transitionend','animationstart','animationend')#过渡或动画的起止


def 默认排帧(帧):
    '通过浏览器动画帧队列排一帧，返回取消函数'
    窗口=取握手窗口()#当前页
    句柄=窗口.requestAnimationFrame(帧)#下一帧
    def 取消():
        '取消还没跑的那一帧'
        窗口.cancelAnimationFrame(句柄)#取消
    return 取消#取消函数


def 默认看盒(行,变化):
    '文档有 ResizeObserver 时观察这一行的边框盒'
    窗口=行.ownerDocument.defaultView#这一行所在的窗口
    构造=getattr(窗口,'ResizeObserver',None)#页面上的构造器
    if not callable(构造):#没有这个构造器
        def 不看():
            '不观察盒子'
            return None#没有要拆的
        return 不看#空拆除
    观察者=构造(变化)#尺寸变化时调用
    观察者.observe(行)#观察这一行
    def 拆除():
        '停止观察这一行'
        观察者.disconnect()#断开
    return 拆除#拆除函数


def 安装窗口拖拽召回(选项):
    '观察带标记的拖拽行。几何可能变了就打一帧召回标记。不是 darwin 时什么都不装'
    文档=选项['document']#要观察的文档
    if 文档.documentElement.getAttribute('data-platform')!='darwin':#没有 app-region
        def 不装():
            '这个平台不观察'
            return None#没有要拆的
        return 不装#空拆除
    排一帧=选项['scheduleFrame'] if 'scheduleFrame' in 选项 else 默认排帧#帧调度
    看盒=选项['watchBox'] if 'watchBox' in 选项 else 默认看盒#盒子观察
    几何={}#上一帧每个行的盒子
    盒子={}#当前还在的行到它的拆除函数
    已排=False#已经有一帧在等
    已拆除=False#观察已停
    取消待定=None#取消在等的那一帧
    宽限=0#还要再看几帧静止
    窗口=文档.defaultView#文档所在窗口

    def 测量():
        '测量每个带标记的行。和上一帧不同就打上召回标记'
        nonlocal 几何,宽限#要改外层的几何和宽限
        文档.body.removeAttribute(召回标记)#先清掉，样式过一遍 Electron 才看得见变回来
        行表=list(文档.querySelectorAll(行选择器))#当前带标记的行
        for 行,拆除观察 in list(盒子.items()):#已经不在的行
            还在=False#是否还在这一帧
            for 现存 in 行表:#逐个现存行
                if 现存 is 行:#还是这一行
                    还在=True#还在
                    break#不用再找
            if 还在:#继续观察
                continue#下一行
            拆除观察()#拆掉盒子观察
            del 盒子[行]#忘掉这一行
        for 行 in 行表:#新出现的行
            if 行 in 盒子:#已经在看
                continue#下一行
            盒子[行]=看盒(行,武装)#尺寸一变就再武装
        下一={}#这一帧的盒子
        for 行 in 行表:#读盒子
            矩形=行.getBoundingClientRect()#视口像素
            下一[行]=str(矩形['x'])+','+str(矩形['y'])+','+str(矩形['width'])+','+str(矩形['height'])#这一帧的文本
        移动了=len(行表)!=len(几何)#行数变了就算移动
        if not 移动了:#行数没变
            for 行 in 行表:#再比每一行的盒子
                if 几何.get(行)!=下一.get(行):#盒子变了
                    移动了=True#移动了
                    break#不用再比
        几何=下一#这一帧成为基线
        if 移动了:#这一帧动过
            文档.body.setAttribute(召回标记,'')#打上召回标记
            宽限=0#重新数静止帧
            排帧()#下一帧再量
            return#本帧结束
        if 宽限==0:#已经静止够了
            return#停下
        宽限=宽限-1#再给一帧
        排帧()#下一帧再量

    def 武装(*位置参数):
        '表面可能在动，重新打开宽限。尺寸观察传来的记录放在位置参数里，这里不用'
        nonlocal 宽限#要改外层宽限
        宽限=宽限帧数#重新数
        排帧()#排一帧

    def 排帧():
        '最多只留一帧在等'
        nonlocal 已排,取消待定#要改外层的排队状态
        if 已排:#已经有一帧
            return#不再排
        已排=True#记下
        def 到帧(*位置参数):
            '这一帧到了就测量。动画帧传来的时间戳放在位置参数里。已经拆除的观察不再量'
            nonlocal 已排,取消待定#清掉排队状态
            已排=False#这帧已经到了
            取消待定=None#没有待取消的了
            if 已拆除:#观察已经停
                return#不再测量
            测量()#量这一帧
        取消待定=排一帧(到帧)#交给调度

    def 运动时(事件):
        '过渡或动画可能在滑动带标记的行时，重新武装'
        目标=事件.target#事件目标
        if 目标 is None or getattr(目标,'nodeType',None)!=1:#不是元素
            return#不武装
        if 目标.closest(行选择器) is not None or 目标.querySelector(行选择器) is not None:#自己是、包着、或在里面
            武装()#重新量

    def 变更(记录表,观察者=None):
        '有一处改动碰到拖拽表面时重新武装。观察者是 MutationObserver 交回来的自己'
        for 记录 in 记录表:#逐条记录
            if 记录.attributeName==召回标记:#自己打的标记
                continue#不是移动
            碰到=False#这条记录会不会动到表面
            for 节点 in list(记录.addedNodes)+list(记录.removedNodes):#加上或去掉的节点
                if getattr(节点,'nodeType',None)!=1:#不是元素
                    continue#下一个节点
                if 节点.matches(行选择器) or 节点.querySelector(行选择器) is not None:#自己是行或里面有行
                    碰到=True#要重测
                    break#不用再看节点
            if not 碰到:#加减节点没有碰到
                目标=记录.target#改动落点
                if getattr(目标,'nodeType',None)!=1:#文本落点
                    目标=目标.parentElement#升到元素
                if 目标 is None:#没有元素
                    continue#下一条记录
                if 记录.type=='childList':#子节点列表变了
                    for 行 in 几何:#上一帧量过的行
                        if 目标.contains(行):#行住在这个容器里
                            碰到=True#容器一变，行可能挪了
                            break#不用再看行
                elif 目标.closest(行选择器) is not None or 目标.querySelector(行选择器) is not None:#属性或文本落在行上、行里、或包着行
                    碰到=True#要重测
            if 碰到:#这条记录碰到了
                武装()#重新量
                return#一条就够

    观察者=窗口.MutationObserver(变更)#监听文档变化
    观察者.observe(文档.body,{'subtree':True,'childList':True,'attributes':True,'characterData':True})#整棵 body
    for 类型 in 运动事件:#过渡和动画
        文档.addEventListener(类型,运动时,True)#捕获
    武装()#第一帧先量当前表面

    def 停止():
        '停止观察，丢掉还没跑的帧，并清掉召回标记'
        nonlocal 已拆除#记下已停
        已拆除=True#帧回调里不再测量
        观察者.disconnect()#不再收变化
        for 类型 in 运动事件:#过渡和动画
            文档.removeEventListener(类型,运动时,True)#摘掉捕获监听
        if 取消待定 is not None:#还有一帧在等
            取消待定()#取消
        for 拆除观察 in 盒子.values():#每个盒子观察
            拆除观察()#拆掉
        盒子.clear()#忘掉行
        几何.clear()#忘掉基线
        文档.body.removeAttribute(召回标记)#清掉标记
    return 停止#交给壳在拆除时调用
