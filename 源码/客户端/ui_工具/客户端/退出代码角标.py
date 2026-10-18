import os
import pywebbridge
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.标签 import 标签

__all__=['退出代码角标']

样式模块='dsh-tool-exit-badge'

def 确保样式(文档):
    '退出码角标样式只插一次'
    注入模块样式文件(
        文档,
        'dsh-tool-exit-badge',
        os.path.join(os.path.dirname(__file__),'退出代码角标.module.css'),
        样式模块,
    )

class 退出代码角标:
    '中性胶囊，带失败点和退出状态文案'
    def __new__(类,属性):
        '画出胶囊并返回节点'
        自身=object.__new__(类)
        自身.属性=属性 if isinstance(属性,dict) else {}
        return 自身.渲染()

    def 渲染(自身):
        '标签里放失败点和文案'
        窗口=自身.属性['window']
        文档=窗口.document
        确保样式(文档)
        文=自身.属性.get('label')
        if 文 is None:
            文=''
        胶囊=标签({'window':窗口,'tone':'neutral','className':'badge','children':str(文)}).渲染()
        点=文档.createElement('span')
        点.className='dot'
        点.setAttribute('aria-hidden','true')
        标样式模块(点,样式模块)
        if 胶囊.firstChild is not None:
            胶囊.insertBefore(点,胶囊.firstChild)
        else:
            胶囊.appendChild(点)
        return 胶囊
