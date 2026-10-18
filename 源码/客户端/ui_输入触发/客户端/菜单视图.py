'触发候选菜单。打开时画在输入叠层上，关闭时不留节点'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_基础界面组件.icons import 描边图标#描边箭头
from ...ui_基础界面组件.引用图标 import 引用图标常规#file / folder / session
from ...ui_基础界面组件.菜单表面 import 菜单表面#菜单材质
from ...ui_基础界面组件.锚定最大高度 import 锚定最大高度#按底边夹高度
from ...ui_对话.异常 import 注入模块样式文件,标样式模块#样式模块

__all__=['菜单视图']

样式模块='MenuView'#和样式文件对应的模块名
设计高度=400#两行标题加八行内建命令的高度
顶边距=84#对话标题 76 再加 8 的空隙
组标题={#源名到组标题。不认识的源直接显示源名
    'command':'指令',
    'skill':'技能',
    'subagent':'子智能体',
}

def 选项标识(来源,下标):
    '一行的 DOM id，给 aria-activedescendant 用'
    return 'dsh-slash-option-'+来源+'-'+str(下标)#稳定 id

def 造(文档,标签,类名):
    '创建一个挂了菜单样式模块的元素'
    节点=文档.createElement(标签)#元素
    if 类名!='':#有类名
        节点.className=类名#官方类名
    return 标样式模块(节点,样式模块)#接上模块

def 右箭头(窗口,尺寸):
    '右向一像素描边箭头'
    return 描边图标({'window':窗口,'size':尺寸},'0 0 16 16',['M6 12L9.29289 8.70711C9.68342 8.31658 9.68342 7.68342 9.29289 7.29289L6 4'],14)#默认 14，调用方可以改小

def 骨架行(文档,宽):
    '一行等待骨架'
    行=造(文档,'div','skeletonRow')#行
    条=造(文档,'span','skeletonBar')#呼吸条
    条.style.setProperty('width',宽)#宽度
    行.appendChild(条)#条进行
    return 行#行

class 菜单视图:
    '候选菜单。关闭时没有节点，打开时按名册画组和行'
    def __init__(自身,属性=None,**关键字参数):
        '记下份额并画一次'
        自身.属性={}#份额
        if isinstance(属性,dict):#字典份额
            自身.属性.update(属性)#抄入
        if len(关键字参数)>0:#还有关键字
            自身.属性.update(关键字参数)#盖上
        自身.根=None#菜单根
        自身.表面=None#菜单材质
        自身.视口=None#可滚动的列表
        自身.高亮行=None#当前高亮的按钮
        自身.退订=[]#菜单仓和页眉仓的退订
        自身.已订菜单=None#已经订上的菜单仓
        自身.已订页眉=None#已经订上的页眉仓
        自身.听窗口=None#尺寸和滚动听在这个窗口上
        自身.拆指针=None#卸掉点外监听
        自身.绘制中=False#正在画，避免订阅重入
        自身.待重画=False#画的过程中又脏了
        自身.渲染()#第一次

    def 更新(自身,属性):
        '换成这一轮的份额。渲染器随后会再调渲染'
        if isinstance(属性,dict):#有新份额
            自身.属性=dict(属性)#换掉

    def 窗口(自身):
        '份额里有窗口就用它，否则用桥上的窗口'
        if 'window' in 自身.属性 and 自身.属性['window'] is not None:#调用方给了
            return 自身.属性['window']#那一个
        return 取握手窗口()#当前页

    def 渲染(自身):
        '打开就重画菜单，关闭就摘掉'
        if 自身.绘制中:#正在画
            自身.待重画=True#等这一轮完再画
            return 自身.根#先交出现在的根
        自身.绘制中=True#占住
        try:#画完一定放开
            自身.订存储()#菜单或页眉一变就重画
            菜单=自身.属性.get('menu')#菜单仓
            if 菜单 is None:#还没有
                自身.收起()#不留节点
            else:#有仓
                态=菜单.getSnapshot()#当前菜单
                if 态['open'] is not True:#关着
                    自身.收起()#不留节点
                else:#开着
                    自身.画开(态)#重画
        finally:#放开
            自身.绘制中=False#可以再画
        if 自身.待重画:#画的时候又脏了
            自身.待重画=False#清掉
            return 自身.渲染()#再画一次
        return 自身.根#根或 None

    def 订存储(自身):
        '菜单仓和页眉仓没换就继续用原来的订阅'
        菜单=自身.属性.get('menu')#菜单仓
        页眉=自身.属性.get('headers')#页眉仓
        if 菜单 is None or 页眉 is None:#还不全
            return#先不订
        if 自身.已订菜单 is 菜单 and 自身.已订页眉 is 页眉:#还是这两份
            return#不用重订

        def 变了():
            '仓变了就重画'
            自身.渲染()#重画

        自身.退订存储()#先卸旧的
        自身.退订.append(菜单.subscribe(变了))#菜单
        自身.退订.append(页眉.subscribe(变了))#页眉
        自身.已订菜单=菜单#记下
        自身.已订页眉=页眉#记下

    def 退订存储(自身):
        '卸掉菜单仓和页眉仓的订阅'
        for 退 in 自身.退订:#每一个退订
            if callable(退):#真是函数
                退()#卸掉
        自身.退订=[]#清空
        自身.已订菜单=None#忘掉
        自身.已订页眉=None#忘掉

    def 收起(自身):
        '关闭时摘掉菜单和背板'
        自身.拆监听()#尺寸、滚动、点外
        if 自身.表面 is not None:#有材质
            if 自身.表面.背板 is not None:#背板还在
                自身.表面.背板.remove()#摘掉
                自身.表面.背板=None#忘掉
            if 自身.表面.根 is not None:#表面还在
                自身.表面.根.remove()#摘掉
                自身.表面.根=None#忘掉
        自身.根=None#没有根
        自身.视口=None#没有列表
        自身.高亮行=None#没有高亮行

    def 拆监听(自身):
        '卸掉窗口和文档上的监听'
        窗口=自身.听窗口#听过的窗口
        if 窗口 is not None:#有
            窗口.removeEventListener('resize',自身.适配高度)#尺寸
            窗口.removeEventListener('scroll',自身.适配高度,True)#捕获阶段的滚动
            自身.听窗口=None#忘掉
        if 自身.拆指针 is not None:#有点外监听
            自身.拆指针()#卸掉
            自身.拆指针=None#忘掉

    def 画开(自身,态):
        '按当前菜单把组和行画进菜单表面'
        窗口=自身.窗口()#窗口
        文档=窗口.document#文档
        注入模块样式文件(文档,'菜单视图样式',os.path.join(os.path.dirname(__file__),'菜单视图.module.css'),样式模块)#样式只插一次
        自身.拆监听()#旧监听对着旧节点
        父=None#原来挂在谁下面
        if 自身.根 is not None:#旧根还在
            父=getattr(自身.根,'parentNode',None)#记下父节点
        if 自身.表面 is None:#第一次
            自身.表面=菜单表面({'window':窗口,'className':'menu'})#带上 menu 类
        else:#以后换窗口
            自身.表面.更新({'window':窗口,'className':'menu'})#换份额
        根=自身.表面.渲染()#新的表面。旧的会被它摘掉
        标样式模块(根,样式模块)#菜单样式盖在同一层上
        根.setAttribute('data-trigger-menu','')#触发菜单
        根.style.setProperty('border-radius','var(--dsw-radius-lg)')#表面圆角。属性被菜单模块占住
        根.style.setProperty('isolation','isolate')#材质隔离
        根.style.setProperty('anchor-name','var(--dsh-menu-anchor)')#背板锚
        自身.根=根#这就是根
        自身.视口=None#等列表造出来
        自身.高亮行=None#等行造出来
        屑表=自身.属性['headers'].getSnapshot()#各源面包屑
        高亮=态['highlight']#当前高亮
        for 组 in 态['groups']:#页眉按组
            轨迹=屑表.get(组['source'])#这一源的面包屑
            if 轨迹 is None:#没有页眉
                continue#下一组
            导航=造(文档,'nav','crumbs')#面包屑
            导航.setAttribute('aria-label','目录导航')#导航名
            序=0#节号
            while 序<len(轨迹):#每一节
                屑=轨迹[序]#这一节
                if 序>0:#节与节之间
                    隔=造(文档,'span','crumbSeparator')#分隔
                    隔.setAttribute('aria-hidden','true')#不进无障碍树
                    隔.appendChild(右箭头(窗口,14))#箭头
                    导航.appendChild(隔)#放上
                当前节=屑.get('current') is True#已经是当前这一节
                钮=造(文档,'button','crumb crumbCurrent' if 当前节 else 'crumb')#这一节
                钮.setAttribute('type','button')#不要提交表单
                if 当前节:#当前节不可点
                    钮.setAttribute('aria-current','location')#当前位置
                    钮.setAttribute('disabled','')#禁用
                钮.setAttribute('data-source',组['source'])#源名
                钮.setAttribute('data-index',str(序))#节号
                钮.textContent=屑['label']#文字
                钮.addEventListener('mousedown',自身.按下屑)#按下就走下钻
                导航.appendChild(钮)#放上
                序+=1#下一节
            根.appendChild(导航)#页眉钉在列表外面
        视口=造(文档,'div','viewport')#可滚动列表
        视口.setAttribute('role','listbox')#列表框在视口上，不在外壳上
        视口.setAttribute('aria-label','触发候选建议')#列表名
        if 高亮 is not None:#有高亮
            视口.setAttribute('aria-activedescendant',选项标识(高亮['source'],高亮['index']))#指向那一行
        视口.addEventListener('scroll',自身.更新溢出)#滚动时更新底部提示
        根.appendChild(视口)#列表进菜单
        自身.视口=视口#记下
        for 组 in 态['groups']:#候选按组
            if 组['status']=='ready' and len(组['items'])==0:#就绪而且空
                continue#整组不画
            有分段=False#有没有行自己的分段标题
            for 候 in 组['items']:#看行
                if 候.get('section') is not None:#有分段
                    有分段=True#记下
                    break#不用再看
            if 组.get('showGroupTitle') is not False and 有分段 is not True:#还要组标题
                标题=造(文档,'div','groupTitle')#组标题
                标题.setAttribute('role','presentation')#不是选项
                标题.setAttribute('data-source',组['source'])#源名
                源名=组['source']#源名
                标题.textContent=组标题[源名] if 源名 in 组标题 else 源名#中文标题，不认识就显示源名
                视口.appendChild(标题)#放上
            if 组['status']=='pending' and len(组['items'])==0:#还没有行
                状态=文档.createElement('div')#等待
                状态.setAttribute('role','status')#状态
                状态.setAttribute('aria-label','正在加载…')#正在加载
                状态.setAttribute('data-source',组['source'])#源名
                状态.appendChild(骨架行(文档,'32%'))#短条
                状态.appendChild(骨架行(文档,'48%'))#长一点
                视口.appendChild(状态)#放上
                continue#这一组完了
            序号=0#行号
            while 序号<len(组['items']):#每一行
                项=组['items'][序号]#这一行
                上一=None#上一行的分段
                if 序号>0:#有上一行
                    上一=组['items'][序号-1].get('section')#它的分段
                if 项.get('section') is not None and 项['section']!=上一:#新分段
                    节=造(文档,'div','sectionTitle')#分段标题
                    节.setAttribute('role','presentation')#不是选项
                    节.textContent=项['section']#分段文字
                    视口.appendChild(节)#放上
                活动=高亮 is not None and 高亮['source']==组['source'] and 高亮['index']==序号#是不是高亮行
                按钮=造(文档,'button','item active' if 活动 else 'item')#一行
                按钮.setAttribute('id',选项标识(组['source'],序号))#给 aria 指
                按钮.setAttribute('type','button')#不要提交表单
                按钮.setAttribute('role','option')#选项
                按钮.setAttribute('aria-selected','true' if 活动 else 'false')#是否选中
                按钮.setAttribute('data-source',组['source'])#源名
                按钮.setAttribute('data-index',str(序号))#行号
                按钮.addEventListener('mousedown',自身.按下选项)#按下就点选
                if 活动 is not True:#高亮行不再抢指针
                    按钮.addEventListener('mousemove',自身.移到选项)#指针移动才改高亮
                if 活动:#记下这一行
                    自身.高亮行=按钮#等下滚进视口
                if 项.get('icon') is not None:#有图标
                    盒=造(文档,'span','itemIcon')#图标座
                    盒.setAttribute('aria-hidden','true')#不进无障碍树
                    图标=项['icon']#字形或组件
                    图=None#画出来的节点
                    if isinstance(图标,str):#file / folder / session
                        图=引用图标常规({'window':窗口,'kind':图标,'size':14})#共享引用图标
                    elif callable(图标):#调用方自己的图标
                        图=图标({'window':窗口,'size':14})#交给它画
                    if 图 is not None:#画出来了
                        盒.appendChild(图)#放进座
                        按钮.appendChild(盒)#座进行
                名字=项['name']#命令名
                标签=项['label'] if 项.get('label') is not None else None#显示标题
                名盒=造(文档,'span','itemName')#标题
                名盒.textContent=名字 if 标签 is None else 标签#没有标题就用名字
                按钮.appendChild(名盒)#放上
                if 标签 is not None and 标签.lower()!=名字.lower():#标题不是名字的另一种大小写
                    别名=造(文档,'span','itemAlias')#名字跟在标题后面
                    别名.textContent=名字#命令名
                    按钮.appendChild(别名)#放上
                if 项.get('description') is not None:#有说明
                    说明=造(文档,'span','itemDescription')#右对齐说明
                    说明.textContent=项['description']#说明
                    按钮.appendChild(说明)#放上
                if 项.get('drill') is True:#可以下钻
                    尾=造(文档,'span','trailing')#行尾
                    提示=造(文档,'span','drillHintText')#文字提示
                    提示.setAttribute('aria-hidden','true')#箭头自己有名字
                    提示.textContent='进入目录'#提示
                    键帽=造(文档,'kbd','drillHint')#Tab
                    键帽.setAttribute('aria-hidden','true')#不重复读
                    键帽.textContent='Tab'#键名
                    钻=造(文档,'span','drill')#箭头按钮
                    钻.setAttribute('role','button')#按钮
                    钻.setAttribute('aria-label','进入目录')#名字
                    钻.setAttribute('data-source',组['source'])#源名
                    钻.setAttribute('data-index',str(序号))#行号
                    钻.addEventListener('mousedown',自身.按下下钻)#按下只下钻
                    钻.appendChild(右箭头(窗口,12))#小箭头
                    尾.appendChild(提示)#文字
                    尾.appendChild(键帽)#键帽
                    尾.appendChild(钻)#箭头
                    按钮.appendChild(尾)#行尾
                视口.appendChild(按钮)#行进列表
                序号+=1#下一行
        if 父 is not None and getattr(根,'parentNode',None) is not 父:#原来有父节点
            父.appendChild(根)#挂回去
        自身.听窗口=窗口#记下
        窗口.addEventListener('resize',自身.适配高度)#窗口尺寸
        窗口.addEventListener('scroll',自身.适配高度,True)#页面滚动用捕获

        def 点外(事件):
            '点在菜单和编写卡片外面才驳回'
            目标=getattr(事件,'target',None)#点中的节点
            if 目标 is None:#没有目标
                return#不理
            if 自身.根 is not None and 自身.根.contains(目标):#点在菜单里
                return#不关
            卡片=None#编写卡片
            if 自身.根 is not None:#有根
                卡片=自身.根.closest('[data-composer-card]')#编写区
            if 卡片 is not None and 卡片.contains(目标):#点在编写区
                return#不关
            自身.属性['onDismiss']()#驳回

        文档.addEventListener('pointerdown',点外,True)#捕获阶段，先于编写区

        def 拆指针():
            '卸掉点外监听'
            文档.removeEventListener('pointerdown',点外,True)#同一捕获标志

        自身.拆指针=拆指针#交给收起

        def 布局后():
            '挂上之后夹高度、标溢出，并把高亮行滚进视口'
            自身.适配高度()#夹高度
            if 自身.高亮行 is not None:#有高亮行
                自身.高亮行.scrollIntoView({'block':'nearest'})#滚进视口

        窗口.queueMicrotask(布局后)#等节点挂上再量

    def 按下选项(自身,事件):
        '按下候选项。焦点留在编写器'
        事件.preventDefault()#不要把焦点偷走
        目标=事件.currentTarget#这一行
        自身.属性['onPick'](目标.getAttribute('data-source'),int(目标.getAttribute('data-index')))#落定

    def 移到选项(自身,事件):
        '指针移动时把高亮停到这一行。高亮行不挂这个监听'
        目标=事件.currentTarget#这一行
        自身.属性['onHover'](目标.getAttribute('data-source'),int(目标.getAttribute('data-index')))#停高亮

    def 按下下钻(自身,事件):
        '按下箭头只下钻，不落定这一行'
        事件.preventDefault()#焦点留在编写器
        事件.stopPropagation()#不要再冒泡成行上的点选
        目标=事件.currentTarget#箭头
        自身.属性['onPick'](目标.getAttribute('data-source'),int(目标.getAttribute('data-index')),'drill')#下钻

    def 按下屑(自身,事件):
        '按下面包屑，走下钻'
        事件.preventDefault()#焦点留在编写器
        目标=事件.currentTarget#这一节
        自身.属性['onCrumb'](目标.getAttribute('data-source'),int(目标.getAttribute('data-index')))#下钻

    def 适配高度(自身,事件=None):
        '按菜单底边把设计高度夹进视口，并更新底部溢出'
        if 自身.根 is None:#已经收起
            return#不量
        矩形=自身.根.getBoundingClientRect()#底边
        if isinstance(矩形,dict):#桥交回字典
            底=矩形['bottom']#底
        else:#对象
            底=矩形.bottom#底
        自身.根.style.setProperty('max-height',str(锚定最大高度(底,设计高度,顶边距))+'px')#夹高度
        自身.更新溢出()#高度变了，溢出也变

    def 更新溢出(自身,事件=None):
        '视口下面还有行时标上 data-overflow-below'
        if 自身.根 is None or 自身.视口 is None:#没有列表
            return#不标
        视口=自身.视口#列表
        溢出=视口.scrollTop+视口.clientHeight<视口.scrollHeight-1#下面还有内容
        if 溢出:#还有
            自身.根.setAttribute('data-overflow-below','')#显示渐变
        elif 自身.根.hasAttribute('data-overflow-below'):#已经到底
            自身.根.removeAttribute('data-overflow-below')#去掉渐变

    def 拆除(自身):
        '槽位卸下时摘掉节点和订阅'
        自身.收起()#节点和监听
        自身.退订存储()#仓的订阅
