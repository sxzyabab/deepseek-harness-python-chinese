'侧栏行在成员或顺序变化时滑动、淡入淡出。第一次指针或键盘之后才动'
from ....模块.客户端.通告 import 取握手窗口
import os
from ....ui_对话.异常 import 注入模块样式文件,标样式模块
from ..会话动作.派生 import 换上

__all__=['动画行','动画行组件']

淡入毫秒=100#进入和离开
滑动毫秒=200#换位
样式模块='animated-rows'#样式模块名

def 确保样式(文档):
    '退出层样式只插一次'
    注入模块样式文件(
        文档,
        '工作区动画行样式',
        os.path.join(os.path.dirname(__file__),'动画行.module.css'),
        样式模块,
    )

def 同一组行(先前键,下一键):
    '键的个数和顺序都一样才算没变'
    if len(先前键)!=len(下一键):#个数不同
        return False#变了
    下标=0#位置
    while 下标<len(先前键):#逐个
        if 先前键[下标]!=下一键[下标]:#不同
            return False#变了
        下标=下标+1#下一条
    return True#没变

def 相交(行矩形,视口):
    '行和列表视口有没有重叠'
    return 行矩形.bottom>视口.top and 行矩形.top<视口.bottom and 行矩形.right>视口.left and 行矩形.left<视口.right#重叠

class 动画行:
    '列表和退出层。父级给出定位容器'
    def __init__(自身,属性):
        '记下属性。武装之前只换内容'
        自身.属性=属性#属性
        自身.已武装=False#还没交互
        自身.移动={}#元素到动画
        自身.退出={}#键到退出副本
        自身.列表=None#列表节点
        自身.覆盖=None#退出层
        自身.根=None#包裹
        自身.先前键=list(属性.get('rowKeys') or [])#上一组键
        自身.先前复位=属性.get('resetKey')#上一复位键
        自身.先前就绪=属性.get('ready') is True#上一就绪

    def 读位置(自身):
        '当前带 data-row-key 的行'
        结果={}#键到位置
        if 自身.列表 is None:#还没画
            return 结果#空
        行列=自身.列表.querySelectorAll('[data-row-key]')#行
        下标=0#下标
        长度=行列.length if hasattr(行列,'length') else len(行列)#条数
        while 下标<长度:#逐行
            元素=行列[下标]#元素
            键=元素.dataset.rowKey if hasattr(元素,'dataset') else 元素.getAttribute('data-row-key')#键
            透明度=1#默认不透明
            if 元素 in 自身.移动:#正在动
                透明度=float(自身.列表.ownerDocument.defaultView.getComputedStyle(元素).opacity)#当前透明度
            结果[键]={'element':元素,'rect':元素.getBoundingClientRect(),'opacity':透明度}#记下
            下标=下标+1#下一条
        return 结果#位置

    def 取消移动(自身):
        '停掉还在滑的动画'
        for 动画 in list(自身.移动.values()):#逐个
            动画.onfinish=None#不再收尾
            动画.cancel()#取消
        自身.移动.clear()#清空

    def 去掉退出(自身,键):
        '拆掉一条正在淡出的副本'
        退出=自身.退出.get(键)#这条
        if 退出 is None:#没有
            return#停
        退出['animation'].onfinish=None#不再收尾
        退出['animation'].cancel()#取消
        退出['element'].remove()#拆节点
        del 自身.退出[键]#忘掉

    def 清空(自身):
        '停移动并拆掉全部退出副本'
        自身.取消移动()#停移动
        for 键 in list(自身.退出.keys()):#全部退出
            自身.去掉退出(键)#拆

    def 移动元素(自身,元素,帧,时长):
        '播放一段，结束就取消以便样式回到终点'
        动画=元素.animate(帧,{'duration':时长,'easing':'ease-out'})#播放
        自身.移动[元素]=动画#记下
        def 结束():
            '播完就从移动表拿掉'
            if 自身.移动.get(元素) is 动画:#仍是这一段
                del 自身.移动[元素]#拿掉
            动画.cancel()#取消填充
        动画.onfinish=结束#结束

    def 拍快照(自身,先前属性):
        '成员或顺序变了、并且已经武装，才记位置'
        列表=自身.列表#列表
        先前键=先前属性.get('rowKeys') or []#旧键
        下一键=自身.属性.get('rowKeys') or []#新键
        if not 自身.已武装 or 同一组行(先前键,下一键):#不用动
            return None#不记
        if 先前属性.get('resetKey')!=自身.属性.get('resetKey'):#视图被换掉
            return None#不记
        if 先前属性.get('ready') is not True or 自身.属性.get('ready') is not True:#还没就绪
            return None#不记
        if 列表 is None or not hasattr(列表,'animate'):#不能动画
            return None#不记
        窗口=列表.ownerDocument.defaultView#窗口
        if 窗口.matchMedia('(prefers-reduced-motion: reduce)').matches:#减少动效
            return None#不记
        视口=列表.getBoundingClientRect()#视口
        位置=自身.读位置()#现在的位置
        下一=set(下一键)#还在的键
        移除={}#要淡出的
        for 键,行 in 位置.items():#逐行
            if 键 in 下一 or not 相交(行['rect'],视口):#还在或看不见
                continue#不克隆
            副本=行['element'].cloneNode(True)#克隆
            副本.removeAttribute('data-row-key')#不再算行
            副本.inert=True#不交互
            缩进=窗口.getComputedStyle(行['element']).getPropertyValue('--dsh-workspace-indent')#缩进
            副本.style.setProperty('--dsh-workspace-indent',缩进)#带上
            移除[键]={'element':副本,'rect':行['rect'],'opacity':行['opacity']}#记下
        return {'positions':位置,'removed':移除}#快照

    def 播放(自身,快照):
        '新行淡入，旧位置滑到新位置，离开视口的淡出'
        if 快照 is None:#没有快照
            return#不播
        自身.取消移动()#停旧的
        列表=自身.列表#列表
        覆盖=自身.覆盖#退出层
        窗口=列表.ownerDocument.defaultView#窗口
        视口=列表.getBoundingClientRect()#视口
        原点=覆盖.getBoundingClientRect()#退出层原点
        位置=自身.读位置()#新位置
        for 键,行 in 位置.items():#还在的行
            自身.去掉退出(键)#若正在淡出就拆掉
            先前=快照['positions'].get(键)#旧位置
            现在可见=相交(行['rect'],视口)#现在看得到
            先前可见=先前 is not None and 相交(先前['rect'],视口)#先前看得到
            if not 现在可见 and not 先前可见:#两边都看不见
                continue#不动
            if 先前 is None:#新来的
                自身.移动元素(行['element'],[{'opacity':0},{'opacity':1}],淡入毫秒)#淡入
                continue#下一条
            横=先前['rect'].left-行['rect'].left#横向差
            纵=先前['rect'].top-行['rect'].top#纵向差
            if 横==0 and 纵==0 and 先前['opacity']==1:#没动
                continue#不动
            自身.移动元素(行['element'],[
                {'transform':'translate('+str(横)+'px, '+str(纵)+'px)','opacity':先前['opacity']},
                {'transform':'translate(0, 0)','opacity':1},
            ],滑动毫秒)#滑过去
        for 键,行 in 快照['removed'].items():#离开的
            元素=行['element']#副本
            自身.去掉退出(键)#旧副本
            元素.style.position='absolute'#绝对
            元素.style.margin='0'#无边距
            元素.style.transform='none'#不变换
            元素.style.boxSizing='border-box'#含边
            元素.style.left=str(行['rect'].left-原点.left)+'px'#左
            元素.style.top=str(行['rect'].top-原点.top)+'px'#上
            元素.style.width=str(行['rect'].width)+'px'#宽
            元素.style.height=str(行['rect'].height)+'px'#高
            覆盖.append(元素)#放进退出层
            动画=元素.animate(
                [{'opacity':行['opacity']},{'opacity':0}],
                {'duration':淡入毫秒,'easing':'ease-out','fill':'forwards'},
            )#淡出
            自身.退出[键]={'element':元素,'animation':动画}#记下
            def 结束(键=键):
                '淡完就拆'
                自身.去掉退出(键)#拆
            动画.onfinish=结束#结束

    def 渲染(自身,子节点=None):
        '画出列表和退出层。子节点由调用方放进列表'
        属性=自身.属性#属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        文档=窗口.document#文档
        确保样式(文档)#样式
        先前={'rowKeys':自身.先前键,'resetKey':自身.先前复位,'ready':自身.先前就绪}#上一份
        快照=None#更新前的位置
        if 自身.列表 is not None:#已经有列表
            快照=自身.拍快照(先前)#先记位置
            if 快照 is None:#这次不动画
                键变了=not 同一组行(自身.先前键,属性.get('rowKeys') or [])#键变了
                复位变了=自身.先前复位!=属性.get('resetKey')#复位变了
                就绪变了=自身.先前就绪!=(属性.get('ready') is True)#就绪变了
                if 键变了 or 复位变了 or 就绪变了:#内容换了
                    自身.清空()#停掉旧动画
        包裹=文档.createElement('div')#不额外占位的包裹由调用方决定，这里用片段式的两层父
        列表=文档.createElement('div')#列表
        列表.className=属性.get('className') or ''#类
        列表.setAttribute('role','tree')#树
        列表.setAttribute('aria-label',属性.get('label') or '')#名称
        def 武装指针(事件):
            '指针进过列表之后才动画'
            自身.已武装=True#武装
        def 武装键(事件):
            '键盘进过列表之后才动画'
            自身.已武装=True#武装
        列表.addEventListener('pointerdown',武装指针,True)#捕获
        列表.addEventListener('keydown',武装键,True)#捕获
        覆盖=文档.createElement('div')#退出层
        覆盖.className='exits'#上游类名
        标样式模块(覆盖,样式模块)#模块
        覆盖.setAttribute('aria-hidden','true')#不读
        包裹.appendChild(列表)#列表
        包裹.appendChild(覆盖)#退出层
        自身.列表=列表#记下
        自身.覆盖=覆盖#记下
        if 子节点 is not None:#有子
            for 子 in 子节点:#逐个
                if 子 is not None and hasattr(子,'tagName'):#节点
                    列表.appendChild(子)#放入
        换上(自身,包裹)#换根
        自身.播放(快照)#播放
        自身.先前键=list(属性.get('rowKeys') or [])#记下键
        自身.先前复位=属性.get('resetKey')#记下复位
        自身.先前就绪=属性.get('ready') is True#记下就绪
        return 自身.根#节点

    def 拆除(自身):
        '卸下时停动画'
        自身.清空()#停

def 动画行组件(属性):
    '渲染器按函数调用'
    return 动画行(属性).渲染(属性.get('children'))#节点
