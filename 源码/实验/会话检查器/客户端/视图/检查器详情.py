'可拖高的原始数据面板。指针捕获管住这一次拖动'

import os#样式
import pywebbridge#窗口
from .....客户端.ui_对话.异常 import 注入模块样式文件,模块节点,标样式模块#样式模块

样式模块='session-inspector'#检查器样式
序号=0#详情面板编号

def 夹百分比(值):
    '高度停在 15% 到 80% 之间'
    if 值<15:#太小
        return 15#下限
    if 值>80:#太大
        return 80#上限
    return 值#原值

class 检查器详情:
    '从面板上沿拖高度，表格始终留在上面'
    def __init__(自身,属性):
        '记下原文、失败和关闭，并画出面板'
        自身.属性=属性#渲染器或表格交来的属性
        自身.根=None#面板
        自身.拖=None#进行中的拖动
        自身.百分比=40#初始高度
        global 序号
        序号=序号+1#下一份
        自身.编号='session-inspector-details-'+str(序号)#给分隔条控制
        自身.渲染()#构造时画出

    def 更新(自身,属性):
        '换成新的原文或关闭回调'
        自身.属性=属性#新属性

    def 拆除(自身):
        '卸掉面板'
        if 自身.根 is not None:#还在
            自身.根.remove()#拿掉
        自身.根=None#清空
        自身.拖=None#结束拖动

    def 渲染(自身):
        '画出分隔条、标题和原文或子树'
        属性=自身.属性#当前属性
        窗口=属性['window']#宿主窗口
        文档=窗口.document#文档
        注入模块样式文件(文档,'dsh-session-inspector',os.path.join(os.path.dirname(__file__),'检查器.module.css'),样式模块)#样式
        旧=自身.根#上一份
        父=旧.parentNode if 旧 is not None else 属性.get('parent')#挂点
        if 旧 is not None:#拆旧的
            旧.remove()#拿掉
        根=模块节点(文档,'div',样式模块,'details')#面板
        根.id=自身.编号#供分隔条指向
        根.style.flexBasis=str(自身.百分比)+'%'#当前高度
        分隔=模块节点(文档,'div',样式模块,'detailsResize')#上沿
        分隔.setAttribute('role','separator')#分隔
        分隔.setAttribute('tabindex','0')#键盘可调
        分隔.setAttribute('aria-orientation','horizontal')#横向
        分隔.setAttribute('aria-controls',自身.编号)#控制面板
        分隔.setAttribute('aria-label','调整原始数据面板高度')#中文标签
        分隔.setAttribute('aria-valuemin','15')#下限
        分隔.setAttribute('aria-valuemax','80')#上限
        分隔.setAttribute('aria-valuenow',str(round(自身.百分比)))#当前
        def 按下(事件):
            '主键开始拖。记下指针、起点和可用高度'
            if 事件.button!=0 or 自身.拖 is not None:#不是主键或已经在拖
                return#不开始
            可用=0#父级高度
            if 根.parentElement is not None:#有父
                可用=根.parentElement.getBoundingClientRect().height#可用高度
            if 可用==0:#没有高度
                return#不能拖
            事件.preventDefault()#不选中文字
            自身.拖={'pointerId':事件.pointerId,'y':事件.clientY,'height':根.getBoundingClientRect().height,'available':可用}#这次拖动
            事件.currentTarget.setPointerCapture(事件.pointerId)#捕获指针
        def 移动(事件):
            '按指针移动改高度'
            当前=自身.拖#这次拖动
            if 当前 is None or 当前['pointerId']!=事件.pointerId:#不是这一支
                return#忽略
            自身.百分比=夹百分比((当前['height']+当前['y']-事件.clientY)/当前['available']*100)#新百分比
            根.style.flexBasis=str(自身.百分比)+'%'#写上
            分隔.setAttribute('aria-valuenow',str(round(自身.百分比)))#同步读数
        def 停止(事件):
            '松开或取消时释放捕获'
            if 自身.拖 is None or 自身.拖['pointerId']!=事件.pointerId:#不是这一支
                return#忽略
            自身.拖=None#结束
            if 事件.currentTarget.hasPointerCapture(事件.pointerId):#还捕获着
                事件.currentTarget.releasePointerCapture(事件.pointerId)#放开
        def 丢失(事件):
            '捕获被系统拿走'
            自身.拖=None#结束
        def 按键(事件):
            '上下方向键微调，Home 和 End 到两端'
            if 事件.key=='ArrowUp':#增高
                自身.百分比=夹百分比(自身.百分比+5)#加五
            elif 事件.key=='ArrowDown':#变矮
                自身.百分比=夹百分比(自身.百分比-5)#减五
            elif 事件.key=='Home':#最矮
                自身.百分比=15#下限
            elif 事件.key=='End':#最高
                自身.百分比=80#上限
            else:#其他键
                return#不拦
            事件.preventDefault()#不滚动页面
            根.style.flexBasis=str(自身.百分比)+'%'#写上
            分隔.setAttribute('aria-valuenow',str(round(自身.百分比)))#读数
        分隔.addEventListener('pointerdown',按下)#开始
        分隔.addEventListener('pointermove',移动)#拖
        def 抬起(事件):
            '先应用到抬起的位置，再结束'
            移动(事件)#最后一档
            停止(事件)#释放
        分隔.addEventListener('pointerup',抬起)#结束
        分隔.addEventListener('pointercancel',停止)#取消
        分隔.addEventListener('lostpointercapture',丢失)#丢失捕获
        分隔.addEventListener('keydown',按键)#键盘
        根.appendChild(分隔)#上沿
        栏=模块节点(文档,'div',样式模块,'toolbar')#标题栏
        标题=文档.createElement('span')#标题
        标题.textContent='原始数据'#中文标题
        栏.appendChild(标题)#放入
        关闭=文档.createElement('button')#关闭
        关闭.setAttribute('type','button')#按钮
        关闭.textContent='关闭'#中文
        def 点关闭(事件):
            '关掉详情'
            属性['close']()#表格清掉选中
        关闭.addEventListener('click',点关闭)#点击
        栏.appendChild(关闭)#放入
        根.appendChild(栏)#标题栏
        子=属性.get('children')#对象树或空
        if 子 is None:#纯文本
            预=文档.createElement('pre')#原文
            if 属性.get('failed') is True:#序列化失败
                预.setAttribute('role','alert')#警告
            预.textContent=属性.get('text') or ''#原文
            根.appendChild(预)#放入
        else:#对象树
            盒=模块节点(文档,'div',样式模块,'objectDetails')#可滚动的树
            if hasattr(子,'parentNode') or hasattr(子,'tagName'):#已经是节点
                盒.appendChild(子)#挂上
            根.appendChild(盒)#放入
        自身.根=根#记住
        if 父 is not None and 根.parentNode is not 父:#还没挂上
            父.appendChild(根)#挂回原处
        return 根#面板
