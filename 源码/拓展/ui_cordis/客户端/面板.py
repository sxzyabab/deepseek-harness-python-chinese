from ....客户端.模块.客户端.通告 import 取握手窗口
import os
from ....客户端.ui_对话.异常 import 注入模块样式文件,标样式模块
from ....客户端.ui_基础界面组件.icons import (
    描边图标,
    常规描边,
    图标勾描边常规,
    图标关闭描边常规,
    图标停止填充常规,
)
from ....客户端.ui_基础界面组件.提示泡 import 提示泡
from ....客户端.ui_基础界面组件.状态点 import 状态点
from ....客户端.ui_基础界面组件.点外关闭 import 点外关闭
from .状态 import 取包,可见状态

__all__=['面板','选定包标识','面板可见状态','阻塞优先']

样式模块='ui-cordis-panel'#面板样式
状态文案={#面板状态的中文
    'idle':'待激活',
    'awaiting-approval':'待审批',
    'client-pending':'Client 待激活',
    'running':'运行中',
    'failed':'运行失败',
}
播放路径=[#IconPlayOutlineRegular
    'M8 14.5C11.5899 14.5 14.5 11.5899 14.5 8C14.5 4.41015 11.5899 1.5 8 1.5C4.41015 1.5 1.5 4.41015 1.5 8C1.5 11.5899 4.41015 14.5 8 14.5Z',
    'M10.3329 7.91346C10.3996 7.95195 10.3996 8.04818 10.3329 8.08667L6.78304 10.1362C6.71638 10.1747 6.63304 10.1266 6.63304 10.0496L6.63304 5.95055C6.63304 5.87357 6.71638 5.82546 6.78304 5.86395L10.3329 7.91346Z',
]
垃圾桶路径=[#IconTrashOutlineRegular
    'M1.28149 3.88831H14.7187',
    'M5.41602 3.88833V2.47962C5.41602 2.29282 5.52492 2.11366 5.71876 1.98157C5.9126 1.84948 6.17551 1.77527 6.44964 1.77527H9.55053C9.82466 1.77527 10.0876 1.84948 10.2814 1.98157C10.4753 2.11366 10.5842 2.29282 10.5842 2.47962V3.88833',
    'M2.57349 3.88831L3.19366 13.2943C3.21937 13.5502 3.33952 13.7872 3.53065 13.9593C3.72178 14.1313 3.97016 14.2259 4.22729 14.2246H11.7728C12.0299 14.2259 12.2783 14.1313 12.4694 13.9593C12.6605 13.7872 12.7807 13.5502 12.8064 13.2943L13.4266 3.88831',
    'M6.44946 6.98926V11.1238',
    'M9.55054 6.98926V11.1238',
]
插件路径='M3.16143 6.59068L1.75205 8.00006L3.10619 9.35419L2.39908 10.0613L0.832948 8.49517C0.559581 8.2218 0.559582 7.77831 0.832948 7.50494L2.45432 5.88357L3.16143 6.59068ZM8.49511 15.1671C8.22176 15.4405 7.77826 15.4404 7.50489 15.1671L5.93461 13.5968L6.64172 12.8897L8 14.248L9.40938 12.8386L10.1165 13.5457L8.49511 15.1671ZM15.1671 7.50494C15.4403 7.7782 15.4401 8.22179 15.1671 8.49517L13.652 10.0102L12.9449 9.30309L14.248 8.00006L12.8897 6.64178L13.5968 5.93467L15.1671 7.50494ZM9.35414 3.10624L8 1.7521L6.69696 3.05514L5.98986 2.34803L7.50489 0.833003C7.77828 0.559981 8.22186 0.559752 8.49511 0.833003L10.0612 2.39913L9.35414 3.10624Z'#IconCordisPluginOutlineRegular

def 整份(快照):
    '钩子选择器，返回整份快照'
    return 快照

def 当前主会话(状态):
    '主视图还占着的会话标识。没有则是 None'
    if not isinstance(状态,dict):#不是列表快照
        return None#没有
    按号=状态.get('byId')#按标识
    if not isinstance(按号,dict):#没有表
        return None#没有
    for 会话 in 按号.values():#按出现顺序
        if not isinstance(会话,dict):#跳过坏行
            continue#下一场
        保留=会话.get('retainedBy')#保留计数
        主=0#主视图次数
        if isinstance(保留,dict) and 保留.get('mainView') is not None:#有计数
            主=保留['mainView']#次数
        if 主>0:#还留在主视图
            return 会话.get('id')#这场
    return None#没有

def 选定包标识(视图,已选):
    '已选的包还在列表里就用它，否则用待切换、当前、最后一份或活动包'
    插件=视图['pluginId']#插件
    列出=视图.get('listed')#清单行
    活动=视图.get('activity')#活动
    选中=已选.get(插件)#这页选过的包
    if 选中 is not None and 列出 is not None:#选过而且有清单
        for 包 in 列出['packages']:#还在不在
            if 包['packageId']==选中:#还在
                return 选中#用选中的
    if 列出 is not None and 列出.get('nextPackageId') is not None:#有待切换
        return 列出['nextPackageId']#待切换
    if 列出 is not None and 列出.get('currentPackageId') is not None:#有当前
        return 列出['currentPackageId']#当前
    if 列出 is not None and len(列出['packages'])>0:#有包
        return 列出['packages'][-1]['packageId']#最后一份
    if 活动 is not None:#只有活动
        return 活动.get('packageId')#活动包
    return None#没有

def 面板可见状态(视图,选中包,已加载):
    '待审批和失败优先，其余跟可见状态走'
    列出=视图.get('listed')#清单行
    活动=视图.get('activity')#活动
    最近=None if 列出 is None else 列出.get('latestRun')#最近一次
    if (活动 is not None and 活动.get('phase')=='awaiting-approval') or (最近 is not None and 最近.get('status')=='awaiting-approval'):#有人在等
        return 'awaiting-approval'#待审批
    if 最近 is not None and 最近.get('status')=='failed' and 最近.get('packageId')==选中包:#选中的这份失败了
        return 'failed'#失败
    if 列出 is None or 列出.get('activeRun') is None:#没在跑
        return 'idle'#待激活
    return 可见状态(列出,列出['activeRun']['packageId'],已加载)#正在跑的那份

def 阻塞优先(行列表):
    '等审批的行放在前面'
    前面=[]#等审批
    后面=[]#其余
    for 行 in 行列表:#逐行
        活动=行.get('activity')#活动
        if 活动 is not None and 活动.get('phase')=='awaiting-approval':#等审批
            前面.append(行)#放前
        else:#其余
            后面.append(行)#放后
    return 前面+后面#拼起来

def 确保样式(文档):
    '面板样式只插一次'
    注入模块样式文件(
        文档,
        'ui-cordis-panel-style',
        os.path.join(os.path.dirname(__file__),'面板.module.css'),
        样式模块,
    )

def 节点(文档,标签,类名):
    '带面板样式模块的节点'
    元素=文档.createElement(标签)#元素
    if 类名:#有类
        元素.className=类名#官方类名
    标样式模块(元素,样式模块)#接上样式
    return 元素#节点

def 写可选(元素,名,值):
    '真写成 true，空和假拿掉，其余写成字符串'
    if 值 is True:#布尔真
        元素.setAttribute(名,'true')#出现
        return
    if 值 is None or 值 is False:#不出现
        元素.removeAttribute(名)#拿掉
        return
    元素.setAttribute(名,str(值))#原值

def 画描边(窗口,路径,尺寸):
    '按上游路径画常规描边图标'
    return 描边图标({'window':窗口,'size':尺寸},'0 0 16 16',路径,尺寸,常规描边)

def 画插件(窗口,尺寸):
    'Cordis 插件图标。中间的圆描边图标画不了'
    文档=窗口.document#文档
    图=文档.createElement('svg')#图
    图.setAttribute('width',str(尺寸))#宽
    图.setAttribute('height',str(尺寸))#高
    图.setAttribute('viewBox','0 0 16 16')#视框
    图.setAttribute('fill','none')#不填
    图.setAttribute('xmlns','http://www.w3.org/2000/svg')#命名空间
    图.setAttribute('aria-hidden','true')#装饰
    图.setAttribute('stroke-width',str(常规描边))#常规描边
    路=文档.createElement('path')#四向
    路.setAttribute('d',插件路径)#路径
    路.setAttribute('fill','currentColor')#填充
    图.appendChild(路)#放上
    圆=文档.createElement('circle')#中心圆
    圆.setAttribute('cx','8')#横
    圆.setAttribute('cy','8')#纵
    圆.setAttribute('r','1.76221')#半径
    圆.setAttribute('stroke','currentColor')#描边
    图.appendChild(圆)#放上
    return 图#图标

def 行按钮(窗口,标签,图标节点,禁用,点击,数据):
    '底边提示包住圆形动作按钮'
    文档=窗口.document#文档
    钮=节点(文档,'button','actionButton')#按钮
    钮.type='button'#按钮
    钮.setAttribute('aria-label',标签)#无障碍名
    钮.disabled=禁用 is True#忙时禁用
    for 键,值 in 数据.items():#数据属性
        if 值 is not None:#有值
            钮.setAttribute(键,str(值))#写上
    钮.appendChild(图标节点)#图标
    钮.addEventListener('click',点击)#点击
    泡=提示泡({'window':窗口,'label':标签,'side':'bottom','delayMs':500,'children':钮})#提示
    泡.渲染()#挂上监听
    return 泡#留给拆除

class 面板:
    '侧栏底部的插件清单、审批和运行控制'
    def __init__(自身,属性):
        '记下属性并画出'
        自身.属性=属性#宿主交来的属性
        自身.根=None#还没画
        自身.打开=False#默认收起
        自身.已选={}#插件到选中的包
        自身.待定=set()#正在做动作的插件
        自身.动作错误={}#插件到这次动作的错误
        自身.已见审批=set()#已经见过的审批号
        自身.锚=None#面板的 left 和 bottom
        自身.已订=False#还没订阅
        自身.退订=[]#订阅拆除
        自身.泡列表=[]#这一轮的提示
        自身.外拆=None#点外面关闭的拆除
        自身.跟随=None#窗口尺寸监听
        自身.已听尺寸=False#是否已听尺寸
        自身.已排量=False#是否已排再量
        自身.上次刷新=object()#让第一次刷新算变化
        自身.上次打开=False#上一轮是否打开
        自身.绘制中=False#防止订阅重入
        自身.待重画=False#画的时候又脏了
        自身.窗口=None#当前窗口
        自身.渲染()#首画

    def 更新(自身,属性):
        '换成新属性'
        自身.属性=属性#新属性

    def 拆除(自身):
        '退掉订阅、提示、点外面和尺寸监听'
        for 退 in 自身.退订:#逐个
            if callable(退):#是拆除器
                退()#退订
        自身.退订=[]#清空
        if 自身.外拆 is not None:#有点外面
            自身.外拆()#拆掉
            自身.外拆=None#清空
        for 泡 in 自身.泡列表:#提示
            卸=getattr(泡,'卸',None)#拆除
            if callable(卸):#有
                卸()#拆掉
        自身.泡列表=[]#清空
        if 自身.已听尺寸 and 自身.跟随 is not None and 自身.窗口 is not None:#还在听尺寸
            自身.窗口.removeEventListener('resize',自身.跟随)#卸掉
            自身.已听尺寸=False#已卸

    def 跑动作(自身,插件,动作):
        '同一插件同时只做一件。失败留在这一行'
        if 插件 in 自身.待定:#已经在做
            return#不重复
        自身.待定.add(插件)#标忙
        if 插件 in 自身.动作错误:#清掉上次的错
            del 自身.动作错误[插件]#拿掉
        try:#动作本身的失败留在行上
            结果=动作()#同步做完
            if 结果 is not None and 结果.get('ok') is not True:#带消息的失败
                消息=结果.get('message')#消息
                if 消息 is None:#没有消息
                    消息='operation failed'#上游的缺省句
                自身.动作错误[插件]=消息#留下
        except Exception as 错误:#抛出来的失败
            自身.动作错误[插件]=str(错误)#消息
        finally:#无论成败都收尾
            自身.待定.discard(插件)#不再忙
            刷新=自身.属性.get('onRefresh')#重读
            if callable(刷新):#有
                刷新()#重读清单
        自身.渲染()#按新状态重画

    def 渲染(自身):
        '有插件才画出徽章。打开时按触发器量出固定面板'
        if 自身.绘制中:#重入
            自身.待重画=True#等这一轮结束
            return 自身.根#当前根
        自身.绘制中=True#占用
        try:#结束时放开
            新根=自身.画出()#这一轮
        finally:#一定放开
            自身.绘制中=False#放开
        if 自身.待重画:#画的时候又脏了
            自身.待重画=False#清标记
            return 自身.渲染()#再画
        return 新根#节点

    def 画出(自身):
        '读钩子、分组、画行，并在打开时刷新'
        属性=自身.属性#当前属性
        if 'window' in 属性 and 属性['window'] is not None:#调用方窗口
            窗口=属性['window']#用它
        else:#没有单独窗口
            窗口=取握手窗口()#当前页
        自身.窗口=窗口#拆除时用来卸监听
        文档=窗口.document#文档
        确保样式(文档)#样式
        if 自身.已订 is not True:#只订一次
            def 重画():
                '快照变了就重画'
                自身.渲染()#重画
            for 名 in ('useInventory','useActiveRuns','useRunErrors','useLoaded','useRenderFailures','useSessions'):#六份钩子
                钩=属性.get(名)#钩子
                订=getattr(钩,'_subscribe',None) if callable(钩) else None#订阅
                if callable(订):#有订阅
                    自身.退订.append(订(重画))#记下
            自身.已订=True#已订
        for 泡 in 自身.泡列表:#上一轮提示
            卸=getattr(泡,'卸',None)#拆除
            if callable(卸):#有
                卸()#先拆监听
        自身.泡列表=[]#清空
        清单快照=属性['useInventory'](整份)#清单
        活动表=属性['useActiveRuns'](整份)#活动
        失败表=属性['useRunErrors'](整份)#运行失败
        已加载=属性['useLoaded'](整份)#本页已加载
        渲染失败表=属性['useRenderFailures'](整份)#渲染失败
        当前=属性['useSessions'](当前主会话)#主视图会话
        现在=set()#这一轮看见的审批
        for 活动 in 活动表.values():#逐个活动
            if 活动.get('phase')=='awaiting-approval':#等审批
                现在.add(活动.get('requestId'))#记下号
        发现=False#有没有新的
        for 请求号 in 现在:#逐个
            if 请求号 not in 自身.已见审批:#没见过
                发现=True#新的
                break#不用再看
        自身.已见审批=现在#换成这一轮
        if 发现:#新审批自动打开
            自身.打开=True#打开
        按插件={}#插件到行
        for 列出 in 清单快照['rows']:#清单行
            活动=活动表.get(列出['pluginId'])#活动
            视={'pluginId':列出['pluginId'],'agentId':列出['agentId'],'listed':列出}#一行
            if 活动 is not None:#有活动
                if 活动.get('agentId') is not None:#活动带了会话
                    视['agentId']=活动['agentId']#用活动的
                视['activity']=活动#带上
            按插件[列出['pluginId']]=视#写入
        for 插件,活动 in 活动表.items():#只有活动、清单还没有的
            if 插件 in 按插件:#已经有了
                continue#跳过
            按插件[插件]={'pluginId':插件,'agentId':活动.get('agentId'),'activity':活动}#只有活动
        全部=list(按插件.values())#全部行
        我的=[]#当前会话
        别人的=[]#其他会话
        for 视 in 全部:#分组
            if 当前 is not None and 视.get('agentId')==当前:#这场
                我的.append(视)#我的
            else:#别的或没有当前会话
                别人的.append(视)#别人的
        我的=阻塞优先(我的)#审批在前
        别人的=阻塞优先(别人的)#审批在前
        审批数=0#等审批的个数
        for 活动 in 活动表.values():#再数一次
            if 活动.get('phase')=='awaiting-approval':#等审批
                审批数=审批数+1#加一
        在跑=0#正在跑的个数
        for 视 in 全部:#逐行
            选=选定包标识(视,自身.已选)#选中的包
            if 面板可见状态(视,选,已加载)=='running':#在跑
                在跑=在跑+1#加一
        新根=None#没有插件就不画
        量到=False#这一轮有没有量到位置
        if len(全部)>0:#有插件
            if 自身.打开 and 自身.根 is not None and getattr(自身.根,'isConnected',None) is True:#已经在页面上
                矩形=自身.根.getBoundingClientRect()#触发器矩形
                if isinstance(矩形,dict) and 矩形.get('left') is not None and 矩形.get('top') is not None:#量到了
                    自身.锚={'left':矩形['left'],'bottom':窗口.innerHeight-矩形['top']+8}#固定坐标
                    量到=True#这一轮量到
            宽=属性.get('wide') is True#宽侧栏
            新根=节点(文档,'div','layer' if 宽 else 'layer rail')#外层
            if 自身.打开 and 量到 and 自身.锚 is not None:#打开而且量到了
                节=节点(文档,'section','panel')#面板
                节.style.left=str(自身.锚['left'])+'px'#左边
                节.style.bottom=str(自身.锚['bottom'])+'px'#底边
                节.setAttribute('data-cordis-panel','')#面板标记
                节.setAttribute('aria-label','Cordis 插件')#标题
                头=节点(文档,'header','header')#头
                题=节点(文档,'span','title')#标题
                题.textContent='Cordis 插件'#中文
                头.appendChild(题)#标题
                节.appendChild(头)#头
                身=节点(文档,'div','body')#正文
                if 清单快照.get('error') is not None:#读取失败
                    误=节点(文档,'p','readError')#失败句
                    误.setAttribute('role','alert')#提示
                    误.textContent='读取插件清单失败：'+str(清单快照['error'])#中文模板
                    身.appendChild(误)#放上
                if 清单快照.get('read') is not True and 清单快照.get('error') is None:#还没读完
                    注=节点(文档,'p','note')#读取中
                    注.textContent='读取中…'#中文
                    身.appendChild(注)#放上
                if 清单快照.get('read') is True and len(全部)==0:#读完了还是空
                    注=节点(文档,'p','note')#空
                    注.textContent='还没有定义任何插件'#中文
                    身.appendChild(注)#放上
                if len(我的)>0:#当前会话有行
                    组=文档.createElement('section')#一组
                    标样式模块(组,样式模块)#样式
                    题组=节点(文档,'h3','group')#组名
                    题组.textContent='当前会话'#中文
                    组.appendChild(题组)#组名
                    表=节点(文档,'ul','rows')#行
                    for 视 in 我的:#逐行
                        表.appendChild(自身.画行(文档,窗口,视,已加载,失败表,渲染失败表))#一行
                    组.appendChild(表)#行
                    身.appendChild(组)#组
                if len(别人的)>0:#其他会话有行
                    组=文档.createElement('section')#一组
                    标样式模块(组,样式模块)#样式
                    题组=节点(文档,'h3','group')#组名
                    题组.textContent='其他会话'#中文
                    组.appendChild(题组)#组名
                    表=节点(文档,'ul','rows')#行
                    for 视 in 别人的:#逐行
                        表.appendChild(自身.画行(文档,窗口,视,已加载,失败表,渲染失败表))#一行
                    组.appendChild(表)#行
                    身.appendChild(组)#组
                节.appendChild(身)#正文
                新根.appendChild(节)#面板
            脚=节点(文档,'div','footerButtons')#徽章座
            徽=节点(文档,'button','badge')#徽章
            徽.type='button'#按钮
            徽.setAttribute('data-cordis-badge',str(len(全部)))#行数
            徽.setAttribute('data-cordis-approval-badge',str(审批数))#审批数
            写可选(徽,'data-active',审批数>0)#有审批就高亮
            徽.setAttribute('aria-label','Cordis 插件')#无障碍名
            徽.setAttribute('aria-expanded','true' if 自身.打开 else 'false')#是否展开
            徽.appendChild(画插件(窗口,16 if 宽 else 18))#图标
            if 宽:#宽侧栏才写字
                字=节点(文档,'span','badgeLabel')#触发器文案
                字.textContent='Cordis Plugin'#中文表原文
                徽.appendChild(字)#文案
                数=节点(文档,'span','badgeCount')#运行数
                数.textContent=str(在跑)+' running'#中文表模板
                徽.appendChild(数)#计数
            def 点徽章(事件):
                '打开或收起面板'
                自身.打开=not 自身.打开#翻
                自身.渲染()#重画
            徽.addEventListener('click',点徽章)#点击
            脚.appendChild(徽)#徽章
            新根.appendChild(脚)#座
        旧=自身.根#上一棵
        父=None#挂载点
        if 旧 is not None:#换掉
            父=旧.parentNode#记住位置
            旧.remove()#拆掉
        自身.根=新根#新根
        if 父 is None and 'parent' in 属性:#宿主指定的父节点
            父=属性['parent']#用它
        if 父 is not None and 新根 is not None and 新根.parentNode is not 父:#还没挂上
            父.appendChild(新根)#挂上
        if 自身.外拆 is not None:#上一轮的点外面
            自身.外拆()#拆掉
            自身.外拆=None#清空
        if 自身.打开 and 新根 is not None:#开着才听外面
            def 置关(开着):
                '点在面板外面就收起'
                if 开着 is False:#要关
                    自身.打开=False#收起
                    自身.渲染()#重画
            自身.外拆=点外关闭(新根,True,置关)#听 pointerdown
        if 自身.跟随 is None:#尺寸监听只建一次
            def 跟随(事件=None):
                '窗口变了就重量'
                自身.渲染()#重画
            自身.跟随=跟随#留下
        if 自身.打开:#开着才听
            if 自身.已听尺寸 is not True:#还没听
                窗口.addEventListener('resize',自身.跟随)#听
                自身.已听尺寸=True#已听
        elif 自身.已听尺寸:#关上了
            窗口.removeEventListener('resize',自身.跟随)#卸
            自身.已听尺寸=False#已卸
        if 自身.打开 and 量到 is not True and 自身.已排量 is not True:#还没挂上页面，量不到
            自身.已排量=True#只排一次
            def 再量():
                '挂上之后再量一次'
                自身.已排量=False#允许下次
                if 自身.根 is None or getattr(自身.根,'isConnected',None) is not True:#还没进页面
                    return#等下一次绘制
                自身.渲染()#重画
            窗口.queueMicrotask(再量)#当前这一轮挂上之后
        刷新=属性.get('onRefresh')#重读
        刷新变了=刷新 is not 自身.上次刷新#回调换了，含第一次
        打开变了=自身.打开 is not 自身.上次打开#开合变了
        自身.上次刷新=刷新#记下
        自身.上次打开=自身.打开#记下
        if callable(刷新) and 刷新变了:#挂上或回调换了就读一次
            刷新()#重读
        if callable(刷新) and 自身.打开 and (刷新变了 or 打开变了):#打开时再读一次
            刷新()#重读
        return 新根#节点

    def 画行(自身,文档,窗口,视图,已加载,失败表,渲染失败表):
        '一行插件：版本、动作、过渡和错误'
        属性=自身.属性#当前属性
        插件=视图['pluginId']#插件
        列出=视图.get('listed')#清单行
        活动=视图.get('activity')#活动
        选中包=选定包标识(视图,自身.已选)#选中的包
        选中元=取包(列出,选中包) if 列出 is not None and 选中包 is not None else None#选中包的元数据
        活动运行=None if 列出 is None else 列出.get('activeRun')#正在跑的
        活动元=None#正在跑的包
        if 活动运行 is not None:#在跑
            活动元=取包(列出,活动运行['packageId'])#那一份
        if 选中元 is not None and 选中元.get('name') is not None:#选中的有名字
            名称=选中元['name']#名字
        elif 活动 is not None and 活动.get('phase')=='awaiting-approval':#审批里的名字
            名称=活动.get('name')#名字
        else:#没有名字
            名称=插件#用插件号
        if 选中元 is not None and 选中元.get('purpose') is not None:#选中的有用途
            用途=选中元['purpose']#用途
        elif 活动 is not None and 活动.get('phase')=='awaiting-approval':#审批里的用途
            用途=活动.get('purpose')#用途
        else:#没有
            用途=''#空
        最近=None if 列出 is None else 列出.get('latestRun')#最近一次
        if 活动 is not None and 活动.get('phase')=='awaiting-approval':#活动在等
            等待=活动.get('requestId')#审批号
        elif 最近 is not None and 最近.get('status')=='awaiting-approval':#清单在等
            等待=最近.get('approvalRequestId')#审批号
        else:#没在等
            等待=None#没有
        状态=面板可见状态(视图,选中包,已加载)#展示状态
        忙碌=插件 in 自身.待定 or (活动 is not None and 活动.get('phase')=='orchestrating')#忙
        if 忙碌:#动作进行中
            点态='ongoing'#转圈
        elif 状态=='idle':#待激活
            点态='idle'#空闲点
        elif 状态=='client-pending':#客户端还没接上
            点态='ongoing'#转圈
        elif 状态=='running':#在跑
            点态='done'#完成点
        elif 状态=='awaiting-approval':#等审批
            点态='warning'#警告点
        else:#失败
            点态='error'#错误点
        失败=失败表.get(插件)#运行失败
        宿主失败=最近.get('error') if 最近 is not None and 最近.get('status')=='failed' else None#宿主失败
        渲染失败=渲染失败表.get(插件)#渲染失败
        动作错=自身.动作错误.get(插件)#这一次动作的错
        下一包=None#待切换
        if 列出 is not None and 列出.get('nextPackageId') is not None and 列出.get('nextPackageId')!=列出.get('currentPackageId'):#和当前不是同一份
            下一包=列出['nextPackageId']#待切换
        当前包=None if 列出 is None else 列出.get('currentPackageId')#当前包
        if 列出 is not None and 当前包 is not None and 选中包!=当前包:#选的不是当前
            运行模式='update'#更新
        else:#否则当运行
            运行模式='run'#运行
        项=节点(文档,'li','row')#一行
        项.setAttribute('data-cordis-row',str(插件))#插件
        项.setAttribute('data-cordis-status',状态)#状态
        写可选(项,'data-cordis-awaiting',等待 is not None)#等审批描边
        头=节点(文档,'div','rowHead')#头
        号=节点(文档,'span','rowId')#插件号
        号.textContent=str(插件)#号
        头.appendChild(号)#号
        名=节点(文档,'span','rowName')#名字
        名.textContent='' if 名称 is None else str(名称)#名字
        头.appendChild(名)#名字
        态=节点(文档,'span','rowStatus')#状态
        点=状态点({'window':窗口,'state':点态})#状态点
        点根=点.渲染()#点
        if 点根 is not None:#画出来了
            态.appendChild(点根)#点
        字=文档.createElement('span')#状态字
        字.textContent=状态文案[状态]#中文
        态.appendChild(字)#字
        头.appendChild(态)#状态
        项.appendChild(头)#头
        if 列出 is not None and len(列出['packages'])>1 and 选中包 is not None:#多版本
            拣=节点(文档,'label','versionPicker')#版本
            版字=文档.createElement('span')#标签
            版字.textContent='版本'#中文
            拣.appendChild(版字)#标签
            选=文档.createElement('select')#下拉
            选.disabled=忙碌 is True#忙时不能改
            for 包 in 列出['packages']:#每个版本
                选项目=文档.createElement('option')#一项
                选项目.value=str(包['packageId'])#包号
                选项目.textContent=str(包.get('name'))+' · '+str(包['packageId'])#名字和号
                选.appendChild(选项目)#放上
            选.value=str(选中包)#选项放完再写当前值
            def 改版本(事件,这一插件=插件):
                '记住这一插件选中的包'
                自身.已选[这一插件]=事件.target.value#包号
                自身.渲染()#重画
            选.addEventListener('change',改版本)#变更
            拣.appendChild(选)#下拉
            项.appendChild(拣)#版本
        细=节点(文档,'div','rowDetail')#用途和动作
        途=节点(文档,'span','rowPurpose')#用途
        途.textContent='' if 用途 is None else str(用途)#用途
        细.appendChild(途)#用途
        动作条=节点(文档,'div','rowActions')#动作
        def 绑定(动作体):
            '点击后走这一插件的动作'
            def 点击(事件):
                '做这一件'
                自身.跑动作(插件,动作体)#串起来
            return 点击#监听
        if 等待 is not None:#等审批
            def 允许一次():
                '只允许这一版'
                属性['onApprove'](等待,False)#不允许后续
                自身.打开=False#收起
            def 允许后续():
                '允许这个插件以后的版本'
                属性['onApprove'](等待,True)#允许后续
                自身.打开=False#收起
            def 拒绝():
                '拒绝这一次'
                属性['onDecline'](等待)#拒绝
                自身.打开=False#收起
            自身.泡列表.append(行按钮(窗口,'仅允许此版本',图标勾描边常规({'window':窗口,'size':14}),忙碌,绑定(允许一次),{'data-cordis-approve':等待}))#允许这一版
            双=节点(文档,'span','doubleCheck')#双勾
            双.setAttribute('aria-hidden','true')#装饰
            双.appendChild(图标勾描边常规({'window':窗口,'size':12}))#后一个
            双.appendChild(图标勾描边常规({'window':窗口,'size':12}))#前一个
            自身.泡列表.append(行按钮(窗口,'允许此插件的后续版本',双,忙碌,绑定(允许后续),{'data-cordis-approve-plugin':等待}))#允许后续
            自身.泡列表.append(行按钮(窗口,'拒绝',图标关闭描边常规({'window':窗口,'size':14}),忙碌,绑定(拒绝),{'data-cordis-decline':等待}))#拒绝
        if 等待 is None and 列出 is not None and 选中包 is not None and 活动运行 is None:#没在跑，可以启动选中的
            def 启动选中():
                '按选中的包运行或更新'
                属性['onRun']({
                    'agentId':列出['agentId'],
                    'pluginId':插件,
                    'packageId':选中包,
                    'mode':运行模式,
                    'hasClientHalf':选中元 is not None and 选中元.get('hasClientHalf') is True,
                })#运行
            自身.泡列表.append(行按钮(窗口,'运行',画描边(窗口,播放路径,14),忙碌,绑定(启动选中),{'data-cordis-switch':'run'}))#运行
        if 等待 is None and 列出 is not None and 活动运行 is not None and 选中包!=活动运行.get('packageId') and 选中元 is not None:#换到另一份
            def 换包():
                '切到选中的另一份'
                属性['onRun']({
                    'agentId':列出['agentId'],
                    'pluginId':插件,
                    'packageId':选中元['packageId'],
                    'mode':运行模式,
                    'hasClientHalf':选中元.get('hasClientHalf'),
                })#运行
            自身.泡列表.append(行按钮(窗口,'运行',画描边(窗口,播放路径,14),忙碌,绑定(换包),{'data-cordis-switch':'run'}))#运行
        if 等待 is None and 列出 is not None and 活动运行 is not None and 状态=='client-pending' and 活动元 is not None and 选中包==活动运行.get('packageId'):#客户端半还没接上
            def 再接():
                '把已经起来的宿主半再交给客户端'
                属性['onRun']({
                    'agentId':列出['agentId'],
                    'pluginId':插件,
                    'packageId':活动元['packageId'],
                    'mode':'run',
                    'hasClientHalf':True,
                })#运行
            自身.泡列表.append(行按钮(窗口,'运行',画描边(窗口,播放路径,14),忙碌,绑定(再接),{'data-cordis-switch':'run'}))#运行
        if 等待 is None and 列出 is not None and 活动运行 is not None:#在跑就可以停
            def 停止():
                '停止这个插件'
                return 属性['onStop'](列出['agentId'],插件)#结果
            自身.泡列表.append(行按钮(窗口,'停止',图标停止填充常规({'window':窗口,'size':14}),忙碌,绑定(停止),{'data-cordis-switch':'stop'}))#停止
        if 等待 is None and 列出 is not None:#有清单就可以移除
            def 移除():
                '移除这个插件'
                return 属性['onRemove'](列出['agentId'],插件)#结果
            自身.泡列表.append(行按钮(窗口,'移除',画描边(窗口,垃圾桶路径,14),忙碌,绑定(移除),{'data-cordis-remove':插件}))#移除
        细.appendChild(动作条)#动作
        项.appendChild(细)#明细
        if 等待 is None and 下一包 is not None and 列出 is not None:#有待切换
            渡=节点(文档,'div','transition')#过渡
            现=文档.createElement('span')#当前
            现.textContent='' if 当前包 is None else '当前：'+str(当前包)#中文模板
            渡.appendChild(现)#当前
            下=文档.createElement('span')#待切换
            下.textContent='待切换：'+str(下一包)#中文模板
            渡.appendChild(下)#待切换
            渡钮=节点(文档,'div','transitionActions')#按钮
            重试=文档.createElement('button')#重试
            重试.type='button'#按钮
            重试.disabled=忙碌 is True#忙
            重试.textContent='重试'#中文
            def 点重试(事件):
                '再跑待切换的那一份'
                def 动作():
                    '重试'
                    属性['onRun']({
                        'agentId':列出['agentId'],
                        'pluginId':插件,
                        'packageId':下一包,
                        'mode':'run' if 当前包 is None else 'update',
                        'hasClientHalf':取包(列出,下一包) is not None and 取包(列出,下一包).get('hasClientHalf') is True,
                    })#运行
                自身.跑动作(插件,动作)#做
            重试.addEventListener('click',点重试)#点击
            渡钮.appendChild(重试)#重试
            if 当前包 is not None:#可以回到当前
                回=文档.createElement('button')#回退
                回.type='button'#按钮
                回.disabled=忙碌 is True#忙
                回.textContent='回退'#中文
                def 点回退(事件):
                    '回到当前这份'
                    def 动作():
                        '回退'
                        当前元=取包(列出,当前包)#当前包
                        属性['onRun']({
                            'agentId':列出['agentId'],
                            'pluginId':插件,
                            'packageId':当前包,
                            'mode':'run',
                            'hasClientHalf':当前元 is not None and 当前元.get('hasClientHalf') is True,
                        })#运行
                    自身.跑动作(插件,动作)#做
                回.addEventListener('click',点回退)#点击
                渡钮.appendChild(回)#回退
            渡.appendChild(渡钮)#按钮
            项.appendChild(渡)#过渡
        if 失败 is not None:#运行失败
            误=节点(文档,'div','rowError')#错误
            误.setAttribute('role','alert')#提示
            误.textContent=str(失败.get('message'))+' ('+str(失败.get('reason'))+')'#消息和原因
            项.appendChild(误)#错误
        if 失败 is None and 宿主失败 is not None:#没有运行失败才写宿主失败
            误=节点(文档,'div','rowError')#错误
            误.setAttribute('role','alert')#提示
            误.textContent=str(宿主失败.get('message'))+' ('+str(宿主失败.get('phase'))+')'#消息和阶段
            项.appendChild(误)#错误
        if 动作错 is not None:#这一次动作的错
            误=节点(文档,'div','rowError')#错误
            误.setAttribute('role','alert')#提示
            误.textContent=str(动作错)#原文
            项.appendChild(误)#错误
        if 渲染失败 is not None:#渲染失败
            误=节点(文档,'div','rowError')#错误
            误.setAttribute('role','alert')#提示
            误.setAttribute('data-cordis-render-failure',str(渲染失败.get('slot')))#槽
            写可选(误,'data-cordis-render-abdicated',渲染失败.get('abdicated') is True)#是否已恢复默认
            if 渲染失败.get('abdicated') is True:#摘掉了入口
                前='{slot} 渲染失败，已恢复默认界面：'.replace('{slot}',str(渲染失败.get('slot')))#中文模板
            else:#还占着
                前='{slot} 渲染失败：'.replace('{slot}',str(渲染失败.get('slot')))#中文模板
            误.textContent=前+' '+str(渲染失败.get('message'))#模板加消息
            项.appendChild(误)#错误
        if 活动元 is not None and 活动元.get('packageId')!=选中包:#正在跑的不是选中的
            活=节点(文档,'span','activeVersion')#正在跑的版本
            活.textContent='运行中: '+str(活动元.get('name'))+' · '+str(活动元.get('packageId'))#中文状态加名字
            项.appendChild(活)#版本
        for 泡 in 自身.泡列表:#把这一行新做的按钮挂进动作条
            锚=getattr(泡,'锚',None)#按钮
            if 锚 is not None and 锚.parentNode is None:#还没挂
                动作条.appendChild(锚)#挂上
        return 项#一行
