'右对齐的 /goal 输入气泡。开头的命令画成芯片，后面的陈述保持原文'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 挂上,注入模块样式文件,标样式模块
from .命令输入 import 目标命令

__all__=['命令输入视图']

样式模块='goal-command-input'#样式隔离


class 命令输入视图:
    'command-input 节点的文本气泡'

    def __init__(自身,属性):
        '记下节点并画出气泡'
        自身.属性=属性 if isinstance(属性,dict) else {}#份额
        自身.根=None#气泡行
        自身.文本=None#上次画出的原文
        自身.渲染()#第一次画

    def 更新(自身,属性):
        '换一份份额'
        自身.属性=属性 if isinstance(属性,dict) else {}#份额

    def 拆除(自身):
        '拿掉气泡'
        if 自身.根 is not None and getattr(自身.根,'parentNode',None) is not None:#还挂着
            自身.根.remove()#摘掉
        自身.根=None#清空

    def 渲染(自身):
        '原文没变就留下现有节点'
        属性=自身.属性#份额
        数据=属性['node']['data']#节点数据
        文本=数据['text']#可见命令行
        if 自身.根 is not None and 自身.文本==文本:#没变
            return 自身.根#原节点
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        文档=窗口.document#文档
        注入模块样式文件(#样式只插一次
            文档,
            '命令输入视图样式',
            os.path.join(os.path.dirname(__file__),'命令输入视图.module.css'),
            样式模块,
        )#样式结束
        父=None#原来的父
        if 自身.根 is not None:#已有行
            父=getattr(自身.根,'parentNode',None)#记下父
            if 父 is not None:#还挂着
                自身.根.remove()#先摘
        elif 'parent' in 属性:#第一次有父
            父=属性['parent']#用传入的父
        行=文档.createElement('div')#行
        行.className='row'#行类
        标样式模块(行,样式模块)#接上模块
        行.setAttribute('data-command-input','')#命令输入
        行.setAttribute('role','group')#一组
        行.setAttribute('aria-label','指令输入')#无障碍名
        叠=文档.createElement('div')#叠
        叠.className='stack'#叠类
        标样式模块(叠,样式模块)#接上模块
        气泡=文档.createElement('div')#气泡
        气泡.className='bubble'#气泡类
        标样式模块(气泡,样式模块)#接上模块
        挂上(气泡,属性['renderFactorySlot']('conversation.user.text',{#用户原文
            'text':文本,#整行
            'facts':{'commands':[{'start':0,'end':len(目标命令)+1,'name':目标命令}]},#开头的 /goal
            'interactive':False,#只显示
            'window':窗口,#窗口
        }))#挂上结束
        叠.appendChild(气泡)#气泡进叠
        行.appendChild(叠)#叠进行
        自身.根=行#记下
        自身.文本=文本#记下原文
        if 父 is not None:#挂回
            父.appendChild(行)#挂上
        return 行#节点
