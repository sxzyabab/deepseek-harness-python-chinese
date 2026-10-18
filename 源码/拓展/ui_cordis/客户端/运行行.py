from ....客户端.模块.客户端.通告 import 取握手窗口
import os
from ....客户端.ui_对话.异常 import 注入模块样式文件,标样式模块
from ....客户端.ui_基础界面组件.icons import 描边图标,常规描边
from ....客户端.ui_基础界面组件.icons.共享画稿 import 代码括号画稿
from .卡片模型 import 运行卡片
from .状态 import 可见状态
from .准备行 import 准备行
from .槽位 import 业务视图槽

__all__=['运行行']

样式模块='ui-cordis-run'#运行卡片样式
代码路径=[#IconCodeOutlineRegular
    'M6.27612 1.5L4.52612 14.5',
    'M11.4739 1.5L9.72388 14.5',
    'M2.39868 5.5H14.0681',
    'M1.93188 10.5H13.6013',
]
读数文={#RunReading 的中文
    'idle':'待激活',
    'awaiting-approval':'待审批',
    'failed':'运行失败',
    'client-pending':'Client 待激活',
    'running':'运行中',
    'removed':'已移除',
    'superseded':'已有更新',
}

def 确保样式(文档):
    '运行行样式只插一次'
    注入模块样式文件(
        文档,
        'ui-cordis-run-style',
        os.path.join(os.path.dirname(__file__),'运行行.module.css'),
        样式模块,
    )

def 节点(文档,标签,类名):
    '带运行行样式模块的节点'
    元素=文档.createElement(标签)#元素
    if 类名:#有类
        元素.className=类名#官方类名
    标样式模块(元素,样式模块)#接上样式
    return 元素#节点

def 画代码(窗口):
    '常规描边代码图标'
    return 描边图标({'window':窗口,'size':14},'0 0 16 16',代码路径,14,常规描边)

def 整份(快照):
    '钩子选择器，返回整份快照'
    return 快照

def 写可选(元素,名,值):
    '真写成 true，空和假拿掉，其余写成字符串'
    if 值 is True:#布尔真
        元素.setAttribute(名,'true')#出现
        return
    if 值 is None or 值 is False:#不出现
        元素.removeAttribute(名)#拿掉
        return
    元素.setAttribute(名,str(值))#原值

class 运行行:
    '一次激活结果。还在跑时给包的业务视图留座位'
    def __init__(自身,属性):
        '记下属性并画出'
        自身.属性=属性#宿主交来的属性
        自身.根=None#还没画
        自身.已订=False#还没订阅
        自身.退订=[]#订阅拆除
        自身.已观察=None#上次交给索引的指针
        自身.绘制中=False#防止订阅重入
        自身.待重画=False#画的时候又脏了
        自身.渲染()#首画

    def 更新(自身,属性):
        '换成新属性'
        自身.属性=属性#新属性

    def 拆除(自身):
        '退掉快照订阅'
        for 退 in 自身.退订:#逐个
            if callable(退):#是拆除器
                退()#退订
        自身.退订=[]#清空

    def 渲染(自身):
        '准备中走前缀。落定后画出读数，符合条件时挂上业务视图'
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
        '按当前阶段组装节点'
        属性=自身.属性#当前属性
        if 'window' in 属性 and 属性['window'] is not None:#调用方窗口
            窗口=属性['window']#用它
        else:#没有单独窗口
            窗口=取握手窗口()#当前页
        文档=窗口.document#文档
        确保样式(文档)#样式
        if 自身.已订 is not True:#只订一次
            def 重画():
                '快照变了就重画'
                自身.渲染()#重画
            for 名 in ('useInventory','useLoaded','useRunCards','useActiveRuns'):#四份钩子
                钩=属性.get(名)#钩子
                订=getattr(钩,'_subscribe',None) if callable(钩) else None#订阅
                if callable(订):#有订阅
                    自身.退订.append(订(重画))#记下
            自身.已订=True#已订
        if 属性.get('phase')=='preparing':#参数还没到
            准备=准备行({
                'window':窗口,
                'toolName':属性.get('toolName'),
                'icon':画代码(窗口),
                'title':'运行 Cordis 插件',
                'className':'card',
                'rowClassName':'row',
                'titleClassName':'title',
                '样式模块':样式模块,
            })#前缀
            新根=准备.根#前缀根
        else:#已开始
            卡片=运行卡片(属性['block'])#卡片数据
            清单快照=属性['useInventory'](整份)#清单
            已加载=属性['useLoaded'](整份)#本页已加载
            最新=属性['useRunCards'](整份)#会话里最新的运行卡
            活动表=属性['useActiveRuns'](整份)#活动
            调用标识=属性['callId']#这次调用
            键=None#业务视图键
            if 卡片['state']=='ok' and 卡片['pluginId'] is not None and 卡片['packageId'] is not None and 卡片['pluginRunId'] is not None and 卡片['seq'] is not None:#成功且身份齐全
                键=卡片['pluginId']+'.'+卡片['packageId']#pluginId.packageId
            观察=属性.get('onObserveRunCard')#交给索引
            标记=(键,调用标识,卡片['seq'],卡片['pluginRunId'],观察)#这次要观察的内容
            if 键 is not None and 卡片['seq'] is not None and 卡片['pluginRunId'] is not None and callable(观察):#可以发布
                if 标记!=自身.已观察:#内容变了才再交
                    自身.已观察=标记#记下
                    观察({
                        'key':键,
                        'callId':调用标识,
                        'seq':卡片['seq'],
                        'pluginRunId':卡片['pluginRunId'],
                    })#发布指针
            else:#这张卡不参与索引
                自身.已观察=None#清掉
            行数据=None#清单行
            if 卡片['pluginId'] is not None:#有插件
                for 候选 in 清单快照['rows']:#找行
                    if 候选['pluginId']==卡片['pluginId']:#同一插件
                        行数据=候选#命中
                        break#停
            指针=None if 键 is None else 最新.get(键)#这把键的最新卡
            序号=卡片['seq'] if 卡片['seq'] is not None else -1#没有序号时比不过正序号
            被取代=指针 is not None and 指针.get('callId')!=调用标识 and 指针.get('seq',-1)>=序号#有更新的卡
            活动=None if 卡片['pluginId'] is None else 活动表.get(卡片['pluginId'])#这个插件的活动
            尝试=None#同一次激活的最近运行
            if 卡片['pluginRunId'] is not None and 行数据 is not None:#能对上
                最近=行数据.get('latestRun')#最近一次
                if isinstance(最近,dict) and 最近.get('pluginRunId')==卡片['pluginRunId']:#同一次
                    尝试=最近#用它
            等审批=False#是否在等审批
            if 尝试 is not None and 尝试.get('status')=='awaiting-approval':#这次还在等
                等审批=True#等审批
            elif 卡片['packageId'] is not None and 活动 is not None and 活动.get('phase')=='awaiting-approval' and 活动.get('packageId')==卡片['packageId'] and (卡片['mode'] is None or 活动.get('mode')==卡片['mode']):#活动对得上这张卡
                等审批=True#等审批
            已移除=卡片['pluginId'] is not None and 卡片['pluginId'] in 清单快照['removed']#这页移除过
            if 已移除:#已移除
                读数='removed'#包没了
            elif 被取代:#有更新
                读数='superseded'#看下方
            elif 等审批:#等审批
                读数='awaiting-approval'#待审批
            elif 尝试 is not None and 尝试.get('status')=='failed':#这次失败
                读数='failed'#失败
            elif 行数据 is not None and 卡片['packageId'] is not None:#能读可见状态
                读数=可见状态(行数据,卡片['packageId'],已加载)#idle / pending / running
            else:#对不上
                读数='idle'#待激活
            if 卡片['errorSummary'] is not None:#错误摘要
                摘要=卡片['errorSummary']#用它
            elif 卡片['pluginId'] is None:#没有插件
                摘要=调用标识#调用号
            else:#插件和包
                摘要=卡片['pluginId']#插件
                if 卡片['packageId'] is not None:#有包
                    摘要=摘要+' · '+卡片['packageId']#插件 · 包
            新根=节点(文档,'div','card')#卡片
            新根.setAttribute('data-tool','cordis_run')#工具
            新根.setAttribute('data-state',卡片['state'])#调用状态
            写可选(新根,'data-cordis-plugin-id',卡片['pluginId'])#插件
            写可选(新根,'data-cordis-package-id',卡片['packageId'])#包
            写可选(新根,'data-cordis-run-id',卡片['pluginRunId'])#激活
            新根.setAttribute('data-cordis-status',读数)#读数
            行=节点(文档,'div','row')#一行
            图标座=节点(文档,'span','icon')#图标
            图标座.appendChild(画代码(窗口))#代码图标
            行.appendChild(图标座)#图标
            题=节点(文档,'span','title')#标题
            题.textContent='更新 Cordis 插件' if 卡片['mode']=='update' else '运行 Cordis 插件'#中文标题
            行.appendChild(题)#标题
            隔=节点(文档,'span','separator')#分隔点
            隔.setAttribute('aria-hidden','true')#装饰
            行.appendChild(隔)#点
            要=节点(文档,'span','error' if 卡片['errorSummary'] is not None else 'summary')#摘要
            要.textContent=摘要#文字
            行.appendChild(要)#摘要
            态=节点(文档,'span','status')#状态
            态.textContent=读数文[读数]#中文状态
            行.appendChild(态)#状态
            检视=属性.get('inspect')#检查回调
            if 检视 is not None:#有检查
                钮=节点(文档,'button','inspect')#检查按钮
                钮.type='button'#按钮
                钮.setAttribute('aria-label','查看')#无障碍名
                钮.appendChild(代码括号画稿({'window':窗口,'size':12},常规描边))#检视图标
                def 点查看(事件):
                    '打开这一次调用的检查'
                    检视()#回调
                钮.addEventListener('click',点查看)#点击
                行.appendChild(钮)#按钮
            新根.appendChild(行)#行
            if 读数=='removed':#包没了
                讯=节点(文档,'div','message')#说明
                讯.textContent='包已不存在'#中文
                新根.appendChild(讯)#说明
            if 读数=='superseded':#有更新的卡
                讯=节点(文档,'div','message')#说明
                讯.textContent='已有更新的运行卡片，请查看下方'#中文
                新根.appendChild(讯)#说明
            if 读数=='failed' and 尝试 is not None and 尝试.get('error') is not None:#失败说明
                讯=节点(文档,'div','message')#说明
                讯.textContent=尝试['error']['message']#宿主错误
                新根.appendChild(讯)#说明
            展示业务=读数=='running' and 键 is not None#还在跑才给业务视图
            if 展示业务 and 卡片['pluginId'] is not None and 卡片['packageId'] is not None and 卡片['pluginRunId'] is not None:#身份齐全
                座=节点(文档,'div','business')#座位
                座.setAttribute('data-cordis-business-view',键)#这把键
                回退=None#没有结果就不回退
                if 卡片['output'] is not None:#有结果
                    回退=节点(文档,'pre','output')#回退结果
                    回退.textContent=卡片['output']#原文
                子槽=属性['renderSlot'](业务视图槽,{
                    'pluginId':卡片['pluginId'],
                    'packageId':卡片['packageId'],
                    'pluginRunId':卡片['pluginRunId'],
                    'window':窗口,
                },{
                    'entryKey':键,
                    'fallback':回退,
                })#子槽包裹
                if 子槽 is not None and hasattr(子槽,'tagName'):#是节点
                    座.appendChild(子槽)#放进座位
                新根.appendChild(座)#座位
            if 展示业务 is not True and 读数!='removed' and 读数!='superseded' and 卡片['output'] is not None:#结果直接放在卡上
                预=节点(文档,'pre','output')#结果
                预.textContent=卡片['output']#原文
                新根.appendChild(预)#结果
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
        return 新根#节点
