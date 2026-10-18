from ....客户端.模块.客户端.通告 import 取握手窗口
import os
from ....客户端.ui_对话.异常 import 注入模块样式文件,标样式模块
from ....客户端.ui_基础界面组件.icons import 描边图标,常规描边
from ....客户端.ui_基础界面组件.icons.共享画稿 import 代码括号画稿
from ....客户端.ui_基础界面组件.markdown.代码块 import 代码块
from .卡片模型 import 定义卡片
from .状态 import 可见状态
from .准备行 import 准备行

__all__=['定义行']

样式模块='ui-cordis-define'#定义卡样式
代码路径=[#IconCodeOutlineRegular
    'M6.27612 1.5L4.52612 14.5',
    'M11.4739 1.5L9.72388 14.5',
    'M2.39868 5.5H14.0681',
    'M1.93188 10.5H13.6013',
]
上箭头路径=['M12 10L8.70711 6.70711C8.31658 6.31658 7.68342 6.31658 7.29289 6.70711L4 10']#IconChevronUpOutlineRegular
读数文={#定义卡读数的中文
    'idle':'待激活',
    'client-pending':'Client 待激活',
    'running':'运行中',
    'removed':'已移除',
}

def 确保样式(文档):
    '定义卡样式只插一次'
    注入模块样式文件(
        文档,
        'ui-cordis-define-style',
        os.path.join(os.path.dirname(__file__),'定义行.module.css'),
        样式模块,
    )

def 节点(文档,标签,类名):
    '带定义卡样式模块的节点'
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

class 定义行:
    '只读的定义卡。展开后有宿主和客户端源码'
    def __init__(自身,属性):
        '记下属性并画出'
        自身.属性=属性#宿主交来的属性
        自身.根=None#还没画
        自身.已订=False#还没订阅
        自身.退订=[]#订阅拆除
        自身.已展开=False#默认收起
        自身.选中源='host'#源码页
        自身.已初选=False#还没按第一张卡选页
        自身.绘制中=False#防止订阅重入
        自身.待重画=False#画的时候又脏了
        自身.源面板标识='cordis-src-'+str(id(自身))#页签和面板的 id
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
        '准备中走前缀。落定后画出名字、用途、源码和结果'
        if 自身.绘制中:#重入
            自身.待重画=True#等这一轮结束
            return 自身.根#当前根
        自身.绘制中=True#占用
        try:#结束时放开
            新根=自身.画出()#这一轮的树
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
            for 名 in ('useInventory','useLoaded'):#两份钩子
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
                'title':'注册 Cordis 插件',
                'className':'card',
                'rowClassName':'row',
                'titleClassName':'title',
                '样式模块':样式模块,
            })#前缀
            新根=准备.根#前缀根
        else:#已开始
            新根=自身.画开始(文档,窗口,属性)#定义卡
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

    def 画开始(自身,文档,窗口,属性):
        '已开始的定义卡'
        卡片=定义卡片(属性['block'])#卡片数据
        清单快照=属性['useInventory'](整份)#清单
        已加载=属性['useLoaded'](整份)#本页已加载
        if 自身.已初选 is not True:#只按第一张卡选默认页
            自身.选中源='client' if 卡片['clientCode'] is not None else 'host'#有客户端源就先看它
            自身.已初选=True#已选
        行数据=None#清单行
        if 卡片['pluginId'] is not None:#有插件
            for 候选 in 清单快照['rows']:#找行
                if 候选['pluginId']==卡片['pluginId']:#同一插件
                    行数据=候选#命中
                    break#停
        if 卡片['pluginId'] is not None and 卡片['pluginId'] in 清单快照['removed']:#这页移除过
            读数='removed'#已移除
        elif 行数据 is not None and 卡片['packageId'] is not None:#能读可见状态
            读数=可见状态(行数据,卡片['packageId'],已加载)#idle / pending / running
        else:#对不上
            读数='idle'#待激活
        名称=卡片['name'] if 卡片['name'] is not None else 属性['callId']#名字或调用号
        可展=卡片['hostCode'] is not None or 卡片['clientCode'] is not None or 卡片['output'] is not None#有东西可展开
        打开=自身.已展开 is True and 可展 is True#收起或没内容都不展开
        if 卡片['state']=='running':#进行中
            无障碍='正在定义插件'#中文
        elif 卡片['state']=='error':#失败
            无障碍='定义失败'#中文
        elif 卡片['state']=='stopped':#中断
            无障碍='定义已中断'#中文
        else:#成功不另说
            无障碍=None#不插隐藏句
        if 自身.选中源=='client' and 卡片['clientCode'] is not None:#选中的客户端源还在
            当前源='client'#客户端
        elif 自身.选中源=='host' and 卡片['hostCode'] is not None:#选中的宿主源还在
            当前源='host'#宿主
        elif 卡片['clientCode'] is not None:#优先客户端
            当前源='client'#客户端
        else:#只剩宿主
            当前源='host'#宿主
        当前代码=卡片['clientCode'] if 当前源=='client' else 卡片['hostCode']#当前源码
        有源=卡片['clientCode'] is not None or 卡片['hostCode'] is not None#至少一份源码
        外=节点(文档,'div','card')#卡片
        外.setAttribute('data-tool','cordis_define')#工具
        外.setAttribute('data-state',卡片['state'])#调用状态
        写可选(外,'data-terminal',读数=='removed')#已移除变灰
        写可选(外,'data-cordis-plugin-id',卡片['pluginId'])#插件
        写可选(外,'data-cordis-package-id',卡片['packageId'])#包
        外.setAttribute('data-cordis-status',读数)#读数
        if 无障碍 is not None:#有隐藏句
            藏=节点(文档,'span','visuallyHidden')#只给读屏
            藏.textContent=无障碍#中文
            外.appendChild(藏)#放上
        行=节点(文档,'div','row')#标题行
        行.style.display='flex'#披露行的横排
        行.style.alignItems='center'#垂直居中
        行.style.minWidth='0'#允许收缩
        行.style.overflow='hidden'#单行
        行.style.height='24px'#披露行高度
        if 可展:#整行可点
            行.setAttribute('data-expandable','true')#可展开
            行.setAttribute('role','button')#按钮
            行.setAttribute('tabindex','0')#可聚焦
            行.setAttribute('aria-expanded','true' if 打开 else 'false')#是否展开
            行.style.cursor='pointer'#手型
            def 切换(事件=None):
                '展开或收起'
                自身.已展开=not 自身.已展开#翻
                自身.渲染()#重画
            def 键盘(事件):
                '回车和空格也切换'
                键=getattr(事件,'key',None)#键
                if 键!='Enter' and 键!=' ':#不是这两个
                    return#不动
                if hasattr(事件,'preventDefault'):#能取消
                    事件.preventDefault()#不滚动
                切换(事件)#切换
            行.addEventListener('click',切换)#点击
            行.addEventListener('keydown',键盘)#键盘
        前导=文档.createElement('span')#图标座
        前导.style.display='inline-flex'#居中
        前导.style.flex='none'#不缩
        前导.style.width='16px'#披露前导宽
        前导.style.height='16px'#披露前导高
        前导.style.alignItems='center'#垂直居中
        前导.style.justifyContent='center'#水平居中
        前导.style.marginRight='6px'#与标题的间距
        if 打开:#展开时换成上箭头
            箭头=描边图标({'window':窗口,'size':14,'className':'chevron'},'0 0 16 16',上箭头路径,14,常规描边)#上箭头
            标样式模块(箭头,样式模块)#箭头颜色
            前导.appendChild(箭头)#放上
        else:#收起时是代码图标
            前导.appendChild(画代码(窗口))#代码图标
        行.appendChild(前导)#前导
        题=节点(文档,'span','title')#标题
        题.textContent='注册 Cordis 插件'#中文
        行.appendChild(题)#标题
        隔=节点(文档,'span','separator')#分隔点
        隔.setAttribute('aria-hidden','true')#装饰
        行.appendChild(隔)#点
        if 卡片['errorSummary'] is None:#没有错误
            名类='name'#名字
            名文=名称#名字
        else:#错误摘要占住名字的位置
            名类='errorSummary'#错误
            名文=卡片['errorSummary']#首行
        名点=节点(文档,'span',名类)#名字或错误
        名点.textContent=名文#文字
        行.appendChild(名点)#放上
        if 卡片['errorSummary'] is None:#没有错误才写用途
            用途=节点(文档,'span','purpose')#用途
            用途.textContent=卡片['purpose'] if 卡片['purpose'] is not None else '(未填写用途)'#中文
            行.appendChild(用途)#用途
        if 卡片['pluginId'] is not None:#有插件才写读数
            读出=节点(文档,'span','readout')#读数座
            标=节点(文档,'span','statusLabel')#读数
            标.textContent=读数文[读数]#中文
            读出.appendChild(标)#文字
            行.appendChild(读出)#读数
        外.appendChild(行)#标题行
        if 打开:#展开体
            体=节点(文档,'div','bodyWrap')#正文
            if 有源 and 当前代码 is not None:#源码
                源区=节点(文档,'section','sourceCard')#源码卡
                页签=节点(文档,'div','sourceTabs')#页签条
                页签.setAttribute('role','tablist')#页签列表
                页签.setAttribute('aria-label','插件代码')#中文
                for 源 in ('client','host'):#两页
                    可用=卡片['clientCode'] is not None if 源=='client' else 卡片['hostCode'] is not None#这页有没有源
                    钮=节点(文档,'button','sourceTab sourceTabActive' if 当前源==源 else 'sourceTab')#页签
                    钮.type='button'#按钮
                    钮.id=自身.源面板标识+'-'+源#给面板指向
                    钮.setAttribute('role','tab')#页签
                    钮.setAttribute('aria-controls',自身.源面板标识)#控制面板
                    钮.setAttribute('aria-selected','true' if 当前源==源 else 'false')#是否选中
                    钮.disabled=可用 is not True#没有源就禁用
                    钮.textContent='Client' if 源=='client' else 'Host'#中文表里的原文
                    def 点源(事件,这一源=源):
                        '切换源码页'
                        自身.选中源=这一源#记下
                        自身.渲染()#重画
                    钮.addEventListener('click',点源)#点击
                    页签.appendChild(钮)#页签
                源区.appendChild(页签)#页签条
                面板=节点(文档,'div','sourcePanel')#源码面板
                面板.id=自身.源面板标识#id
                面板.setAttribute('role','tabpanel')#面板
                面板.setAttribute('aria-labelledby',自身.源面板标识+'-'+当前源)#指向当前页签
                块=代码块({
                    'window':窗口,
                    'code':当前代码,
                    'lang':'javascript',
                    'copyLabel':'复制',
                    'copiedLabel':'已复制',
                    'className':'sourceCode',
                    'toolbarLabels':{
                        'codeLabel':'代码块',
                        'wrapLabel':'自动换行',
                        'unwrapLabel':'取消自动换行',
                    },
                })#代码块
                块根=块.渲染()#节点
                if 块根 is not None:#画出来了
                    块根.style.margin='0'#sourceCode 只把外边距清掉
                    面板.appendChild(块根)#放上
                源区.appendChild(面板)#面板
                体.appendChild(源区)#源码
            if 卡片['output'] is not None:#结果
                段=节点(文档,'section','codeSection')#结果区
                签=节点(文档,'div','sectionLabel')#小标题
                签.textContent='结果'#中文
                段.appendChild(签)#标题
                预=节点(文档,'pre','output')#结果
                写可选(预,'data-error',卡片['state']=='error')#错误着色
                预.textContent=卡片['output']#原文
                段.appendChild(预)#结果
                体.appendChild(段)#结果区
            if 卡片['pluginId'] is not None:#有插件才提示去面板
                提示=节点(文档,'div','panelHint')#提示
                提示.textContent='运行控制在左下角设置上方的 Cordis 面板'#中文
                体.appendChild(提示)#提示
            检视=属性.get('inspect')#检查回调
            if 检视 is not None:#有检查
                看=节点(文档,'button','inspectButton')#检查按钮
                看.type='button'#按钮
                看.appendChild(代码括号画稿({'window':窗口,'size':12},常规描边))#图标
                看.appendChild(文档.createTextNode('查看'))#中文
                def 点查看(事件):
                    '打开这一次调用的检查'
                    检视()#回调
                看.addEventListener('click',点查看)#点击
                体.appendChild(看)#按钮
            外.appendChild(体)#正文
        return 外#卡片
