'确认过的命令只显示成芯片，不负责执行'
from ...模块.客户端.通告 import 取握手窗口
from ...ui_基础界面组件.用户文本 import 引用芯片

__all__=['命令引用']


class 命令引用:
    '一条确认过的命令原文'

    def __init__(自身,属性):
        '记下节点并画出芯片'
        自身.属性=属性 if isinstance(属性,dict) else {}#份额
        自身.根=None#芯片节点
        自身.渲染()#第一次画

    def 更新(自身,属性):
        '换一份份额'
        自身.属性=属性 if isinstance(属性,dict) else {}#份额

    def 拆除(自身):
        '拿掉芯片'
        if 自身.根 is not None and getattr(自身.根,'parentNode',None) is not None:#还挂着
            自身.根.remove()#摘掉
        自身.根=None#清空

    def 渲染(自身):
        '标签是斜杠加命令名，title 用原文'
        属性=自身.属性#份额
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        节点=属性['node']#命令节点
        父=None#原来的父
        if 自身.根 is not None:#已有芯片
            父=getattr(自身.根,'parentNode',None)#记下父
            if 父 is not None:#还挂着
                自身.根.remove()#先摘
        elif 'parent' in 属性:#第一次有父
            父=属性['parent']#用传入的父
        份额={#交给引用芯片
            'window':窗口,#窗口
            'appearance':'command',#命令外观
            'label':'/'+节点['data']['name'],#斜杠加名字
        }#份额结束
        if 属性.get('raw') is not None:#有原文
            份额['title']=属性['raw']#悬停原文
        芯片=引用芯片(份额)#芯片
        根=芯片.渲染()#节点
        自身.根=根#记下
        if 父 is not None and 根 is not None and getattr(根,'parentNode',None) is None:#还没挂
            父.appendChild(根)#挂回
        return 根#节点
