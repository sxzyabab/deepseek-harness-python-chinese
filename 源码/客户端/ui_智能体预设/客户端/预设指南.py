from ...模块.客户端.通告 import 取握手窗口
import os
import re
from ...ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点
from ...ui_基础界面组件.icons import 图标关闭描边常规,图标列表笔16
from ...ui_基础界面组件.分段标签页 import 分段标签页
from ...ui_基础界面组件.标签 import 标签
from ...ui_基础界面组件.模态 import 模态
from ...ui_基础界面组件.markdown.Markdown文本 import Markdown文本
from .文案 import 中文

__all__=['圈定阅读焦点','指南用法','预设指南对话框']

样式模块='preset-guide'#样式隔离

def 圈定阅读焦点(事件):
    'Tab 在这份阅读器里打转，不走到后面的设置页'
    if 事件.key!='Tab':#不是 Tab
        return#不管
    节点列=事件.currentTarget.querySelectorAll('button:not([disabled]):not([tabindex="-1"]), [tabindex="0"]')#可停的控件
    目标=[]#没被 hidden 挡住的
    for 元素 in 节点列:#逐个
        if 元素.closest('[hidden]') is None:#不在隐藏页里
            目标.append(元素)#留下
    if len(目标)==0:#没有
        return#不管
    首=目标[0]#第一个
    尾=目标[len(目标)-1]#最后一个
    文档=事件.currentTarget.ownerDocument#文档
    if 事件.shiftKey and 文档.activeElement is 首:#反向到头
        事件.preventDefault()#不离开
        尾.focus()#回到末尾
    elif 事件.shiftKey is not True and 文档.activeElement is 尾:#正向到尾
        事件.preventDefault()#不离开
        首.focus()#回到开头

def 指南代码文案():
    '复制按钮用本包中文。代码块标题是公共中文表里的原文'
    return {#Markdown 代码栏
        'copyLabel':中文['guideCopy'],#复制
        'copiedLabel':中文['guideCopied'],#已复制
        'toolbarLabels':{#公共表。当前 Markdown 文本不读这三项
            'codeLabel':'代码块',#代码块
            'wrapLabel':'自动换行',#自动换行
            'unwrapLabel':'取消自动换行',#取消自动换行
        },
    }#结束

class 指南用法:
    '用法页按三级标题拆成示例。一块示例一个区'
    def __init__(自身,属性):
        '记下正文和窗口'
        自身.属性=属性#props
        自身.根=None#根

    def 渲染(自身):
        '每个 ### 标题是一条例子'
        属性=自身.属性#props
        窗口=属性['window']#窗口
        文档=窗口.document#文档
        if 自身.根 is not None:#拆旧
            自身.根.remove()#拿掉
        根=文档.createElement('div')#不占额外盒子
        根.style.display='contents'#子级直接进面板
        文本=属性['text']#用法正文
        for 段 in re.split(r'(?=^### )',文本,flags=re.M):#按三级标题切开
            if 段=='':#开头空段
                continue#跳过
            断行=段.find('\n')#标题结束
            标题=段[4:断行]#去掉 ### 
            区=模块节点(文档,'section',样式模块,'guideExample')#一例
            头=模块节点(文档,'div',样式模块,'guideExampleHeader')#标题行
            题=文档.createElement('h3')#标题
            题.textContent=标题#标题
            头.appendChild(题)#放进
            内容=文档.createElement('span')#图标和「示例任务」
            图=图标列表笔16({'window':窗口,'size':12})#笔
            if 图 is not None:#有
                内容.appendChild(图)#放进
            内容.appendChild(文档.createTextNode(中文['guideExampleTask']))#示例任务
            标=标签({'window':窗口,'tone':'neutral','className':'guideExampleTag','children':内容})#胶囊
            标节点=标.渲染()#画出
            if 标节点 is not None:#有
                头.appendChild(标节点)#放进
            区.appendChild(头)#放进
            正文=Markdown文本({#剩下的 markdown
                'window':窗口,
                'text':段[断行+1:],
                'codeLabels':指南代码文案(),
            })
            正文节点=正文.渲染()#画出
            if 正文节点 is not None:#有
                区.appendChild(正文节点)#放进
            根.appendChild(区)#一例
        自身.根=根#记下
        return 自身.根#根

class 预设指南对话框:
    '只读帮助。不改当前选中的预设。两页各自滚动'
    def __init__(自身,属性):
        '从打开时的那一页开始'
        自身.属性=属性#props
        自身.页=属性['initialPage']#当前页
        自身.根=None#对话框根
        自身.已聚焦=False#只在打开时聚焦当前页签
        自身.标识='preset-guide-'+str(id(自身))#页签和面板的 id 前缀
        自身.渲染()#首画

    def 渲染(自身):
        '无头对话框里放标题、两页和对应正文'
        属性=自身.属性#props
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        文档=窗口.document#文档
        注入模块样式文件(#样式
            文档,
            '预设指南样式',
            os.path.join(os.path.dirname(__file__),'预设指南.module.css'),
            样式模块,
        )
        指南=属性['guide']#这份预设的帮助键
        页=自身.页#当前页
        if 自身.根 is not None:#拆旧
            自身.根.remove()#拿掉
            自身.根=None#空
        布局=模块节点(文档,'div',样式模块,'guideLayout')#整页
        布局.setAttribute('role','presentation')#只是布局

        def 按键(事件):
            'Escape 只关这一层。Tab 留在阅读器里'
            if 事件.key=='Escape':#关闭
                事件.preventDefault()#不交给后面的设置
                事件.stopPropagation()#停
                属性['onClose']()#关
            else:#其它键
                圈定阅读焦点(事件)#圈住 Tab
        布局.addEventListener('keydown',按键,True)#捕获
        头=模块节点(文档,'div',样式模块,'guideHeader')#头
        行=模块节点(文档,'div',样式模块,'guideTitleRow')#标题行
        题=模块节点(文档,'h2',样式模块,'guideTitle')#标题
        题.textContent=中文[指南['name']]#模式名
        行.appendChild(题)#放进
        关=文档.createElement('button')#关闭。按钮组件把节点子内容画成 div
        关.type='button'#按钮
        关.className='guideClose'#本页样式
        标样式模块(关,样式模块)#接上
        关.setAttribute('aria-label',中文['close'])#关闭
        def 点关(事件):
            '关闭阅读器'
            属性['onClose']()#关
        关.addEventListener('click',点关)#点
        叉=图标关闭描边常规({'window':窗口,'size':18})#叉
        if 叉 is not None:#有
            关.appendChild(叉)#放进
        行.appendChild(关)#放进
        头.appendChild(行)#放进
        导=模块节点(文档,'p',样式模块,'guideIntro')#导语
        导.textContent=中文[指南['intro']]#导语
        头.appendChild(导)#放进
        布局.appendChild(头)#放进

        def 换页(值):
            '换到模式说明或如何使用'
            自身.页=值#记下
            自身.渲染()#重画
        页签=分段标签页({#两页
            'window':窗口,
            'className':'guideTabs',
            'label':中文['guideSections'],
            'value':页,
            'onChange':换页,
            'items':[
                {'value':'explanation','label':中文['modeExplanation'],'id':自身.标识+'-explanation-tab','panelId':自身.标识+'-explanation-panel'},
                {'value':'usage','label':中文['howToUse'],'id':自身.标识+'-usage-tab','panelId':自身.标识+'-usage-panel'},
            ],
        })
        页签节点=页签.渲染()#画出
        if 页签节点 is not None:#有
            布局.appendChild(页签节点)#放进
        for 段名 in ('explanation','usage'):#两块正文都留着
            面板=模块节点(文档,'div',样式模块,'guidePanel')#面板
            面板.id=自身.标识+'-'+段名+'-panel'#id
            面板.setAttribute('role','tabpanel')#面板
            面板.setAttribute('aria-labelledby',自身.标识+'-'+段名+'-tab')#对应页签
            面板.setAttribute('data-guide-page',段名)#用法页的样式
            面板.tabIndex=0#键盘能停
            if 页!=段名:#不是当前页
                面板.setAttribute('hidden','')#藏起，滚动位置还在
            if 段名=='usage':#用法
                用法=指南用法({'window':窗口,'text':中文[指南['usage']]})#示例
                用法节点=用法.渲染()#画出
                if 用法节点 is not None:#有
                    面板.appendChild(用法节点)#放进
            else:#说明
                说明=Markdown文本({#说明正文
                    'window':窗口,
                    'text':中文[指南['explanation']],
                    'codeLabels':指南代码文案(),
                })
                说明节点=说明.渲染()#画出
                if 说明节点 is not None:#有
                    面板.appendChild(说明节点)#放进
            布局.appendChild(面板)#放进
        对话框=模态({#无头，标题在布局里
            'window':窗口,
            'open':True,
            'headless':True,
            'onClose':属性['onClose'],
            'title':中文[指南['name']],
            'className':'guideDialog',
            'children':布局,
        })
        自身.根=对话框.渲染()#画出
        if 自身.根 is not None:#给对话框卡片接上本页宽度
            卡=自身.根.querySelector('.guideDialog')#卡片
            if 卡 is not None:#有
                标样式模块(卡,样式模块)#宽度
        if 自身.已聚焦 is not True and 自身.根 is not None:#打开时聚焦当前页签
            自身.已聚焦=True#只一次

            def 聚焦():
                '等挂上页面后再聚焦'
                if 自身.根 is None:#已经拆了
                    return#停
                当前=自身.根.querySelector('[role="tab"][aria-selected="true"]')#当前页签
                if 当前 is not None:#有
                    当前.focus()#聚焦
            窗口.setTimeout(聚焦,0)#下一拍
        return 自身.根#根
