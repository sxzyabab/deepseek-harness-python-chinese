'会话标题栏上的智能体团队面板'
from ....客户端.模块.客户端.通告 import 取握手窗口
import os
from ....客户端.ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点#模块样式
from ....客户端.ui_基础界面组件.状态点 import 状态点#状态点
from ....客户端.ui_基础界面组件.标签 import 标签#当前会话胶囊
from ....客户端.ui_基础界面组件.提示泡 import 提示泡#打开提示
from ....客户端.ui_基础界面组件.锚定位置 import 使用锚定位置#面板定位
from ....客户端.ui_基础界面组件.点外关闭 import 点外关闭#点外关闭
from ....客户端.ui_基础界面组件.icons import 描边图标,图标下箭头描边常规,常规描边#描边图标

连接路径=os.path.join#拼样式路径
所在目录=os.path.dirname#本文件目录

__all__=['团队动作']

样式模块='team-action'#样式隔离名


def 建(文档,标签名,类名):
    '造出带官方类名和样式模块标记的节点'
    return 模块节点(文档,标签名,样式模块,类名)


def 清空子(节点):
    '拆掉这个节点下面的全部子节点'
    while 节点.firstChild is not None:
        节点.firstChild.remove()


class 团队成员行:
    '一名成员的打开按钮'
    def __init__(自身):
        '先空着，等更新后再画'
        自身.属性={}#份额
        自身.根=None#按钮
        自身.泡=None#提示泡

    def 更新(自身,属性):
        '换上这一成员的份额'
        自身.属性=属性#最新

    def 拆除(自身):
        '卸掉提示泡挂在文档上的监听'
        if 自身.泡 is not None and callable(自身.泡.卸):
            自身.泡.卸()#卸监听
        自身.泡=None#清掉

    def 点成员(自身,事件=None):
        '打开这一成员的会话。失败写到面板错误行'
        try:
            打开=自身.属性['打开队友']#打开回调
            打开(自身.属性['会话标识'],自身.属性['成员']['id'])#打开
        except Exception as 原因:
            自身.属性['记下错误'](str(原因))#错误行

    def 渲染(自身):
        '画出成员按钮。未运行用用户图标，其余用状态点'
        自身.拆除()#重画前卸旧提示
        属性=自身.属性#份额
        窗口=属性['窗口']#浏览器窗口
        文档=属性['文档']#文档
        成员=属性['成员']#成员投影
        成员标识=成员['id']#成员会话
        会话标识=属性['会话标识']#当前会话

        def 取模型(状态):
            '这一成员下次要跑的模型名'
            投影表=状态.get('projectionsBySession')#投影表
            if 投影表 is None:
                return None#没有表
            条目=投影表.get(成员标识)#这一会话
            if 条目 is None:
                return None#没有投影
            投影值=条目.get('values')#投影值
            if 投影值 is None:
                return None#没有值
            选择=投影值.get('modelSelection')#模型选择
            if 选择 is None:
                return None#没有选择
            下一=选择.get('next')#下一次
            if 下一 is None:
                return None#没有下一次
            return 下一.get('model')#模型名

        def 取运行(状态):
            '统一状态里这一成员是否在跑'
            状态行=状态.get(成员标识)#这一会话
            if 状态行 is None:
                return None#没有状态
            return 状态行.get('running')#是否在跑

        def 取摘要运行(状态):
            '列表摘要上的 running'
            按标识=状态.get('byId')#摘要表
            if 按标识 is None:
                return None#没有表
            摘要行=按标识.get(成员标识)#这一行
            if 摘要行 is None:
                return None#没有行
            return 摘要行.get('running')#是否在跑

        模型名=属性['用会话表'](取模型)#模型
        运行中=属性['用会话状态'](取运行)#实时回合
        摘要运行=属性['用会话表'](取摘要运行)#列表摘要
        阶段=成员['phase']#耐久阶段
        if 阶段=='active':
            实时=运行中 if 运行中 is not None else 摘要运行#空则用摘要
            if 实时 is True:
                状态='running'#在跑
            else:
                状态='inactive'#没在跑
        else:
            状态=阶段#准备中或失败
        if 状态=='running':
            状态文='运行中'#运行中
        elif 状态=='inactive':
            状态文='未运行'#未运行
        elif 状态=='provisioning':
            状态文='准备中'#准备中
        elif 状态=='failed':
            状态文='失败'#失败
        else:
            状态文=str(状态)#其余原样
        当前=成员标识==会话标识#是不是当前会话
        高亮=当前 and 属性['成员数']>1#多人里标出当前
        惰性=当前 or 状态=='failed' or 状态=='provisioning'#不能打开
        if 高亮:
            按钮类='member memberCurrent'#当前成员
        else:
            按钮类='member'#普通成员
        按钮=建(文档,'button',按钮类)#成员按钮
        按钮.type='button'#按钮
        按钮.disabled=惰性#不能点
        按钮.addEventListener('click',自身.点成员)#打开
        点盒=建(文档,'span','memberDot')#状态点座位
        if 状态=='inactive':
            头路径='M8 8.25C9.51878 8.25 10.75 7.01878 10.75 5.5C10.75 3.98122 9.51878 2.75 8 2.75C6.48122 2.75 5.25 3.98122 5.25 5.5C5.25 7.01878 6.48122 8.25 8 8.25Z'#头
            肩路径='M2.5 14.5C2.5 11.5 5.25 10.25 8 10.25C10.75 10.25 13.5 11.5 13.5 14.5'#肩
            图属性={'window':窗口,'size':14,'className':'inactiveIcon'}#用户图标
            图标节点=描边图标(图属性,'0 0 16 16',[头路径,肩路径],14,常规描边)#画出
            标样式模块(图标节点,样式模块)#接上样式
            点盒.appendChild(图标节点)#放进座位
        else:
            if 状态=='failed':
                点态='error'#失败
            else:
                点态='ongoing'#运行或准备
            点盒.appendChild(状态点({'window':窗口,'state':点态}).渲染())#状态点
        按钮.appendChild(点盒)#状态
        文字盒=建(文档,'span','memberText')#名字和状态
        名行=建(文档,'span','memberName')#名字行
        名字=建(文档,'span','memberNameText')#名字
        名字.textContent=成员['name']#成员名
        名行.appendChild(名字)#放上
        if 当前:
            胶囊=标签({
                'window':窗口,
                'tone':'info',
                'className':'currentTag',
                'children':'当前会话',
            }).渲染()#当前会话
            名行.appendChild(胶囊)#放上
        文字盒.appendChild(名行)#名字
        副文=文档.createElement('small')#状态
        副文.appendChild(文档.createTextNode(状态文))#状态文案
        if 模型名 is not None:
            模型段=建(文档,'span','memberModel')#悬停才看见
            模型段.textContent=' · 模型: '+str(模型名)#模型
            副文.appendChild(模型段)#接上
        文字盒.appendChild(副文)#副文
        if 'error' in 成员 and 成员['error'] is not None:
            诊断=建(文档,'small','diagnostic')#失败原因
            诊断.textContent=str(成员['error'])#原文
            文字盒.appendChild(诊断)#放上
        按钮.appendChild(文字盒)#文字
        自身.泡=提示泡({
            'window':窗口,
            'label':'打开成员会话',
            'side':'bottom',
            'gap':4,
            'disabled':惰性,
            'children':按钮,
        })#提示
        自身.根=自身.泡.渲染()#按钮本身
        return 自身.根#按钮


class 任务卡片:
    '一条共享任务。描述默认夹两行，元数据行里的按钮可以展开'
    def __init__(自身):
        '展开状态留在这一张卡片上'
        自身.属性={}#份额
        自身.展开=False#是否展开
        自身.夹住=False#两行放不下
        自身.根=None#文章
        自身.正文=None#描述段落
        自身.元数据=None#元数据行
        自身.观察=None#尺寸观察
        自身.窗口=None#浏览器窗口
        自身.文档=None#文档

    def 更新(自身,属性):
        '换上这一条任务'
        自身.属性=属性#最新
        自身.窗口=属性['窗口']#窗口
        自身.文档=属性['文档']#文档

    def 拆观察(自身):
        '卸掉段落尺寸观察'
        if 自身.观察 is not None:
            自身.观察.disconnect()#停止
            自身.观察=None#清掉

    def 拆除(自身):
        '卸掉尺寸观察'
        自身.拆观察()#卸观察

    def 点展开(自身,事件=None):
        '展开或收起描述'
        自身.展开=not 自身.展开#切换
        if 自身.展开:
            自身.正文.className=''#不再夹
            自身.正文.removeAttribute('data-dsh-css')#没有类
        else:
            自身.正文.className='clampedDescription'#夹两行
            标样式模块(自身.正文,样式模块)#接上样式
        自身.填元数据()#按钮文案
        自身.装测量()#展开后不再观察

    def 填元数据(自身):
        '重画展开按钮和任务元数据'
        文档=自身.文档#文档
        任务=自身.属性['任务']#任务
        清空子(自身.元数据)#旧的
        if 自身.夹住 or 自身.展开:
            按钮=建(文档,'button','expandToggle')#展开按钮
            按钮.type='button'#按钮
            if 自身.展开:
                按钮.setAttribute('aria-expanded','true')#已展开
                按钮文字='收起'#收起
            else:
                按钮.setAttribute('aria-expanded','false')#已收起
                按钮文字='展开'#展开
            按钮.addEventListener('click',自身.点展开)#切换
            按钮.appendChild(文档.createTextNode(按钮文字))#文案
            箭头=图标下箭头描边常规({'window':自身.窗口,'size':12})#箭头
            if 自身.展开:
                箭头.setAttribute('class','expandToggleOpen')#翻上来
                标样式模块(箭头,样式模块)#接上样式
            按钮.appendChild(箭头)#放上
            自身.元数据.appendChild(按钮)#浮在右边

        def 加一段(文字,类名=None):
            '元数据里的一段'
            if 类名 is None:
                一段=文档.createElement('span')#普通段
            else:
                一段=建(文档,'span',类名)#带类
            一段.textContent=文字#文字
            自身.元数据.appendChild(一段)#放上

        加一段(str(任务['id']))#任务标识
        if 'ownerName' in 任务 and 任务['ownerName'] is not None:
            所有者=str(任务['ownerName'])#所有者
        else:
            所有者='未分配'#没有所有者
        加一段('Owner: '+所有者)#所有者
        if 任务['status']=='pending':
            if 任务['ready']:
                加一段('可开始')#依赖已完成
            else:
                加一段('被依赖阻塞')#还被挡住
        if len(任务['blockedBy'])>0:
            加一段('依赖: '+', '.join(任务['blockedBy']))#依赖
        if len(任务['writeScopes'])>0:
            加一段('写入范围: '+', '.join(任务['writeScopes']))#写入范围
        for 警告 in 任务['writeScopeWarnings']:
            加一段(str(警告),'warning')#重叠警告

    def 装测量(自身):
        '没展开时按行高判断要不要展开按钮'
        if 自身.展开:
            自身.拆观察()#展开后不测
            return
        段落=自身.正文#描述
        if 段落 is None:
            return#还没画
        夹住=段落.scrollHeight>段落.clientHeight+1#超出两行
        if 夹住!=自身.夹住:
            自身.夹住=夹住#记下
            自身.填元数据()#补上或拿掉按钮
        if 自身.观察 is not None:
            return#已经在看
        构造=getattr(自身.窗口,'ResizeObserver',None)#尺寸观察
        if 构造 is None:
            return#没有这个构造
        def 变化(记录=None):
            '段落尺寸变了就重测'
            自身.装测量()#重测
        自身.观察=构造(变化)#创建
        自身.观察.observe(段落)#盯着段落

    def 渲染(自身):
        '画出任务卡片'
        自身.拆观察()#旧段落作废
        文档=自身.文档#文档
        窗口=自身.窗口#窗口
        任务=自身.属性['任务']#任务
        状况=任务['status']#状态
        点态='idle'#删除时闲置
        状态文='已完成'#删除当已完成
        if 状况=='pending':
            if 任务['ready']:
                点态='idle'#可以开始
            else:
                点态='warning'#被挡住
            状态文='待处理'#待处理
        elif 状况=='in_progress':
            点态='ongoing'#进行中
            状态文='进行中'#进行中
        elif 状况=='completed':
            点态='done'#已完成
            状态文='已完成'#已完成
        elif 状况=='deleted':
            点态='idle'#删除
            状态文='已完成'#当已完成
        文章=建(文档,'article','task')#卡片
        题行=建(文档,'div','taskTitle')#标题行
        标题节点=文档.createElement('strong')#标题
        标题节点.textContent=str(任务['subject'])#标题
        题行.appendChild(标题节点)#放上
        状态盒=建(文档,'span','taskState')#状态
        状态盒.appendChild(状态点({'window':窗口,'state':点态}).渲染())#点
        态文=文档.createElement('span')#状态文
        态文.textContent=状态文#文案
        状态盒.appendChild(态文)#放上
        题行.appendChild(状态盒)#放上
        文章.appendChild(题行)#标题
        段落=文档.createElement('p')#描述
        if 自身.展开:
            段落.className=''#全文
        else:
            段落.className='clampedDescription'#夹两行
            标样式模块(段落,样式模块)#接上样式
        段落.textContent=str(任务['description'])#描述
        文章.appendChild(段落)#描述
        元数据=建(文档,'div','meta')#元数据
        文章.appendChild(元数据)#放上
        自身.根=文章#文章
        自身.正文=段落#段落
        自身.元数据=元数据#元数据行
        自身.填元数据()#元数据
        return 文章#文章


class 团队动作:
    '会话标题栏上的团队入口。打开后是只读的成员名单和共享任务'
    def __init__(自身,属性=None):
        '记下份额。有窗口就画出触发按钮'
        自身.属性=属性 if isinstance(属性,dict) else {}#份额
        自身.打开=False#面板是否打开
        自身.错误=None#打开失败的一行
        自身.钉住=False#点击打开后不随移出关闭
        自身.悬停定时=None#悬停开关
        自身.根=None#根
        自身.触发=None#触发按钮
        自身.触发文案=None#按钮里的字
        自身.面板=None#传送到 body 的面板
        自身.面板体=None#可滚动正文
        自身.刚挂面板=False#这一轮才挂上
        自身.拆位置=None#定位拆除
        自身.拆外面=None#点外拆除
        自身.拆按键=None#Escape 拆除
        自身.成员行={}#成员按钮
        自身.任务卡={}#任务卡片
        自身.已订=False#是否已订快照
        自身.退订=[]#快照退订
        自身.绘制中=False#防止订阅重入
        自身.待重画=False#画的过程中又脏了
        自身.窗口=None#浏览器窗口
        自身.文档=None#文档
        自身.会话标识=自身.属性.get('sessionId')#当前会话
        if 'window' in 自身.属性:
            自身.渲染()#有窗口就画

    def 更新(自身,属性):
        '换上新份额。会话变了就收起并清错误'
        新标识=None#新会话
        if isinstance(属性,dict):
            新标识=属性.get('sessionId')#新会话
        if 新标识!=自身.会话标识:
            自身.取消悬停()#停掉悬停
            自身.钉住=False#取消钉住
            自身.打开=False#收起
            自身.错误=None#清错误
            自身.会话标识=新标识#记下
        if isinstance(属性,dict):
            自身.属性=属性#最新
        else:
            自身.属性={}#空份额

    def 取消悬停(自身,事件=None):
        '清掉还没到点的悬停开关'
        if 自身.悬停定时 is None:
            return#没有定时
        if 自身.窗口 is not None:
            自身.窗口.clearTimeout(自身.悬停定时)#取消
        自身.悬停定时=None#清掉

    def 改打开(自身,下一):
        '按下一态打开或收起。收起时取消钉住'
        自身.取消悬停()#停掉悬停
        if 下一 is not True:
            自身.钉住=False#收起不再钉住
        自身.打开=下一 is True#下一态
        自身.渲染()#重画

    def 安排悬停打开(自身,事件=None):
        '标签还看得见时，150 毫秒后打开。收成图标后只响应点击'
        自身.取消悬停()#重计时
        if 自身.打开:
            return#已经开着
        标签=自身.触发文案#按钮文字
        if 标签 is None:
            return#还没画
        if 自身.窗口.getComputedStyle(标签).display=='none':
            return#只剩图标
        def 到点():
            '悬停时间到了就打开'
            自身.悬停定时=None#定时结束
            自身.改打开(True)#打开
        自身.悬停定时=自身.窗口.setTimeout(到点,150)#150 毫秒

    def 安排悬停关闭(自身,事件=None):
        '没钉住时，120 毫秒后关闭'
        自身.取消悬停()#重计时
        if 自身.钉住:
            return#点击钉住的不关
        def 到点():
            '离开时间到了就关闭'
            自身.悬停定时=None#定时结束
            自身.改打开(False)#关闭
        自身.悬停定时=自身.窗口.setTimeout(到点,120)#120 毫秒

    def 点触发(自身,事件=None):
        '点击钉住。没开就打开，已开就把焦点交给面板'
        自身.取消悬停()#停掉悬停
        自身.钉住=True#钉住
        if 自身.打开 is not True:
            自身.改打开(True)#打开
            return
        if 自身.面板 is not None:
            自身.面板.focus()#焦点交回面板

    def 按逃(自身,事件):
        'Escape 收起面板。焦点在面板里时回到触发按钮'
        if 事件.key!='Escape':
            return#不是退出
        事件.preventDefault()#不要再往上冒
        自身.取消悬停()#停掉悬停
        自身.钉住=False#取消钉住
        应回焦=False#先不回焦
        if 自身.面板 is not None and 自身.文档 is not None:
            应回焦=自身.面板.contains(自身.文档.activeElement) is True#焦点在面板里
        自身.打开=False#收起
        自身.渲染()#拿掉面板
        if 应回焦 and 自身.触发 is not None:
            自身.触发.focus()#回到按钮

    def 记下错误(自身,消息):
        '成员打开失败时写到面板错误行'
        自身.错误=消息#错误行
        自身.渲染()#重画

    def 清成员(自身):
        '卸掉成员提示泡'
        for 一行 in list(自身.成员行.values()):
            一行.拆除()#卸提示
        自身.成员行={}#清空

    def 清卡片(自身):
        '卸掉任务卡片的尺寸观察'
        for 卡片 in list(自身.任务卡.values()):
            卡片.拆除()#卸观察
        自身.任务卡={}#清空

    def 收起面板(自身):
        '卸掉定位、点外和 Escape，并拿掉传送面板'
        if callable(自身.拆位置):
            自身.拆位置()#卸定位
            自身.拆位置=None#清掉
        if callable(自身.拆外面):
            自身.拆外面()#卸点外
            自身.拆外面=None#清掉
        if callable(自身.拆按键):
            自身.拆按键()#卸按键
            自身.拆按键=None#清掉
        if 自身.面板 is not None and 自身.面板.parentNode is not None:
            自身.面板.parentNode.removeChild(自身.面板)#拿掉
        自身.面板=None#没有面板
        自身.面板体=None#没有正文
        自身.刚挂面板=False#不再算刚挂
        自身.清成员()#卸成员
        自身.清卡片()#卸任务

    def 装触发(自身,文档,窗口):
        '画出标题栏按钮。只建一次'
        if 自身.根 is not None:
            return#已经有了
        根=建(文档,'div','root')#根
        根.setAttribute('data-team-action','true')#团队动作
        根.addEventListener('mouseleave',自身.安排悬停关闭)#移出关闭
        触发=建(文档,'button','trigger')#触发
        触发.type='button'#按钮
        触发.setAttribute('aria-label','智能体团队')#名字
        触发.setAttribute('aria-haspopup','dialog')#会弹出对话框
        触发.setAttribute('aria-expanded','false')#先收起
        触发.addEventListener('mouseenter',自身.安排悬停打开)#悬停打开
        触发.addEventListener('click',自身.点触发)#点击钉住
        前路径='M6 8.25C7.51878 8.25 8.75 7.01878 8.75 5.5C8.75 3.98122 7.51878 2.75 6 2.75C4.48122 2.75 3.25 3.98122 3.25 5.5C3.25 7.01878 4.48122 8.25 6 8.25Z'#前面的人
        前肩='M1 14.5C1 11.5 3.5 10.25 6 10.25C8.5 10.25 11 11.5 11 14.5'#前面的肩
        后头='M10.5 2.9C11.65 3.35 12.45 4.35 12.45 5.5C12.45 6.65 11.65 7.65 10.5 8.1'#后面的头
        后肩='M12.4 10.6C13.9 11.3 15 12.6 15 14.5'#后面的肩
        图属性={'window':窗口,'size':14}#多人图标
        图标节点=描边图标(图属性,'0 0 16 16',[前路径,前肩,后头,后肩],14,常规描边)#画出
        触发.appendChild(图标节点)#图标
        文案=建(文档,'span','triggerLabel')#窄了会藏起
        文案.textContent='智能体团队'#按钮文字
        触发.appendChild(文案)#文字
        根.appendChild(触发)#放上
        自身.根=根#根
        自身.触发=触发#按钮
        自身.触发文案=文案#文字节点

    def 挂面板(自身,文档,窗口):
        '把对话框传送到 body，并跟上按钮'
        if 自身.面板 is not None:
            return#已经挂着
        面板=建(文档,'div','panel')#面板
        面板.setAttribute('role','dialog')#对话框
        面板.setAttribute('tabindex','-1')#可编程聚焦
        面板.setAttribute('aria-label','智能体团队')#名字
        面板.setAttribute('data-team-panel','true')#团队面板
        面板.style.visibility='hidden'#还没量完先藏
        面板.style.left='0px'#先放原点
        面板.style.top='0px'#先放原点
        面板.addEventListener('mouseenter',自身.取消悬停)#进面板不停
        面板.addEventListener('mouseleave',自身.安排悬停关闭)#离开再关
        滚动正文=建(文档,'div','body')#滚动正文
        面板.appendChild(滚动正文)#放上
        文档.body.appendChild(面板)#传送
        自身.面板=面板#面板
        自身.面板体=滚动正文#正文
        自身.拆位置=使用锚定位置({
            'open':True,
            'anchor':自身.触发,
            'panel':面板,
            'window':窗口,
            'side':'bottom',
            'align':'start',
            'gap':5,
            'margin':16,
        })#跟着按钮
        面板.style.visibility='visible'#量完就显示
        自身.拆外面=点外关闭(自身.根,True,自身.改打开,面板)#点外面关闭
        def 卸键():
            '卸掉 Escape'
            文档.removeEventListener('keydown',自身.按逃)#卸掉
        文档.addEventListener('keydown',自身.按逃)#退出键
        自身.拆按键=卸键#记下
        自身.刚挂面板=True#这一轮才挂上

    def 填面板(自身,文档,窗口):
        '按 Lead 的 agentTeam 投影重画面板正文'
        属性=自身.属性#份额

        def 取父(快照):
            '子会话映射到 Lead'
            子智能体=快照.get('subagent')#子智能体
            if 子智能体 is None:
                return None#没有父
            地址=子智能体.get('address')#地址
            if 地址 is None:
                return None#没有地址
            return 地址.get('parentSessionId')#父会话

        def 取打开中(快照):
            '会话是否还在加载'
            return 快照.get('openState')=='loading'#加载中

        父标识=属性['useSession'](取父)#父会话
        if 父标识 is None:
            领导=属性['sessionId']#当前就是 Lead
        else:
            领导=父标识#用 Lead

        def 取团队(状态):
            'Lead 上的 agentTeam 投影'
            投影表=状态.get('projectionsBySession')#投影表
            if 投影表 is None:
                return None#没有表
            条目=投影表.get(领导)#Lead
            if 条目 is None:
                return None#没有投影
            投影值=条目.get('values')#投影值
            if 投影值 is None:
                return None#没有值
            return 投影值.get('agentTeam')#团队

        def 取列表中(状态):
            '会话列表是否还在等待'
            return 状态.get('phase')=='pending'#还在等

        团队=属性['useSessions'](取团队)#团队投影
        正在打开=属性['useSession'](取打开中) is True#会话加载
        正在列表=属性['useSessions'](取列表中) is True#列表等待
        if 团队 is not None and len(团队['members'])==1 and len(团队['tasks'])==0:
            自身.面板.className='panel panelCompact'#一个人且没有任务
        else:
            自身.面板.className='panel'#普通宽度
        标样式模块(自身.面板,样式模块)#接上样式
        正文=自身.面板体#正文
        清空子(正文)#重画
        if 自身.错误 is not None:
            错误行=建(文档,'div','error')#错误
            错误行.setAttribute('role','alert')#提示
            错误行.appendChild(状态点({'window':窗口,'state':'error'}).渲染())#红点
            错误行.appendChild(文档.createTextNode(自身.错误))#错误原文
            正文.appendChild(错误行)#放上
        if 团队 is None:
            提示=建(文档,'div','notice')#还没有团队
            提示.setAttribute('role','status')#状态
            if 正在打开 or 正在列表:
                点态='ongoing'#还在加载
                提示文='正在加载团队…'#加载文案
            else:
                点态='warning'#不可用
                提示文='Team 暂不可用'#不可用
            提示.appendChild(状态点({'window':窗口,'state':点态}).渲染())#点
            提示.appendChild(文档.createTextNode(提示文))#文案
            正文.appendChild(提示)#放上
            自身.清成员()#没有成员
            自身.清卡片()#没有任务
            return#停
        if 'failure' in 团队:
            失败行=建(文档,'div','error')#持久记录无效
            失败行.setAttribute('role','alert')#提示
            失败行.appendChild(状态点({'window':窗口,'state':'error'}).渲染())#红点
            失败文='团队持久记录无效：'+str(团队['failure'])#带上原因
            失败行.appendChild(文档.createTextNode(失败文))#文案
            正文.appendChild(失败行)#放上
        成员分区=文档.createElement('section')#成员区
        成员题=文档.createElement('h3')#成员标题
        成员题.appendChild(文档.createTextNode('成员'))#成员
        成员表=团队['members']#成员
        if len(成员表)>1:
            成员数=建(文档,'span','count')#人数
            成员数.textContent=str(len(成员表))#人数
            成员题.appendChild(成员数)#放上
        成员分区.appendChild(成员题)#标题
        花名册=建(文档,'div','roster')#名单
        自身.清成员()#旧按钮作废
        for 成员 in 成员表:
            一行=团队成员行()#新的一行
            自身.成员行[成员['id']]=一行#记下
            一行.更新({
                '窗口':窗口,
                '文档':文档,
                '成员':成员,
                '成员数':len(成员表),
                '会话标识':属性['sessionId'],
                '用会话表':属性['useSessions'],
                '用会话状态':属性['useSessionStatus'],
                '打开队友':属性['openTeammate'],
                '记下错误':自身.记下错误,
            })#份额
            花名册.appendChild(一行.渲染())#放上
        成员分区.appendChild(花名册)#名单
        正文.appendChild(成员分区)#成员区
        任务分区=文档.createElement('section')#任务区
        任务表=团队['tasks']#任务
        if len(任务表)==0:
            空提示=建(文档,'p','emptyNotice')#没有任务
            空提示.textContent='暂无共享任务，可以通过对话创建'#空文案
            任务分区.appendChild(空提示)#放上
            自身.清卡片()#没有卡片
        else:
            任务题=文档.createElement('h3')#任务标题
            任务题.appendChild(文档.createTextNode('共享任务'))#共享任务
            任务数=建(文档,'span','count')#条数
            任务数.textContent=str(len(任务表))#条数
            任务题.appendChild(任务数)#放上
            任务分区.appendChild(任务题)#标题
            任务盒=建(文档,'div','tasks')#任务列表
            仍在={}#这一轮还在的任务
            for 任务 in 任务表:
                标识=任务['id']#任务标识
                卡片=自身.任务卡.get(标识)#已有卡片
                if 卡片 is None:
                    卡片=任务卡片()#新建
                    自身.任务卡[标识]=卡片#记下
                卡片.更新({'窗口':窗口,'文档':文档,'任务':任务})#换任务
                任务盒.appendChild(卡片.渲染())#先放进文档
                卡片.装测量()#再量两行
                仍在[标识]=卡片#还在
            for 标识 in list(自身.任务卡.keys()):
                if 标识 not in 仍在:
                    自身.任务卡[标识].拆除()#卸观察
                    del 自身.任务卡[标识]#拿掉
            任务分区.appendChild(任务盒)#列表
        正文.appendChild(任务分区)#任务区

    def 确保订阅(自身):
        '会话、列表或统一状态变了就重画'
        if 自身.已订:
            return#已经订过
        自身.已订=True#记下
        def 变更():
            '快照变了'
            if 自身.绘制中:
                自身.待重画=True#等这一轮结束
                return
            自身.渲染()#重画
        for 钩子名 in ('useSession','useSessions','useSessionStatus'):
            钩子=自身.属性.get(钩子名)#钩子
            订阅=getattr(钩子,'_subscribe',None) if 钩子 is not None else None#订阅口
            if callable(订阅):
                自身.退订.append(订阅(变更))#退订函数

    def 渲染(自身):
        '画出标题栏动作。打开时把面板挂到 body'
        if 自身.绘制中:
            自身.待重画=True#等这一轮结束
            return 自身.根#先交出现在的根
        自身.绘制中=True#开始
        try:
            属性=自身.属性#份额
            窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
            文档=窗口.document#文档
            自身.窗口=窗口#留给悬停和按键
            自身.文档=文档#留给焦点判断
            样式路径=连接路径(所在目录(__file__),'团队动作.module.css')#样式文件
            注入模块样式文件(文档,'团队动作样式',样式路径,样式模块)#只插一次
            自身.确保订阅()#订快照
            自身.装触发(文档,窗口)#按钮
            if 自身.打开:
                自身.触发.setAttribute('aria-expanded','true')#已展开
            else:
                自身.触发.setAttribute('aria-expanded','false')#已收起
            if 自身.打开 is not True:
                自身.收起面板()#拿掉面板
            else:
                自身.挂面板(文档,窗口)#传送
                自身.填面板(文档,窗口)#正文
                if 自身.刚挂面板 and 自身.钉住 and 自身.面板 is not None:
                    自身.面板.focus()#点击打开后聚焦
                自身.刚挂面板=False#只聚焦这一次
        finally:
            自身.绘制中=False#结束
        if 自身.待重画:
            自身.待重画=False#清标记
            return 自身.渲染()#再画
        return 自身.根#根

    def 拆除(自身):
        '卸掉悬停、面板和快照订阅'
        自身.取消悬停()#停掉悬停
        自身.收起面板()#拿掉面板
        退订=自身.退订#抄出来
        自身.退订=[]#清空
        自身.已订=False#可以再订
        for 退订函数 in 退订:
            退订函数()#退订
