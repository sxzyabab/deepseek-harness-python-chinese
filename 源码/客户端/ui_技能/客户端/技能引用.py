'技能引用芯片。能不能点由这一条会话注入的预览动作决定'
from ...ui_基础界面组件.用户文本 import 引用芯片#行内芯片

__all__=['技能引用']

class 技能引用:
    '画出 /名字。预览不保证一定打开'
    def __new__(类,属性):
        '槽位把组件当函数调用，直接返回芯片节点'
        自身=object.__new__(类)#实例
        自身.属性=属性#props
        return 自身.渲染()#节点

    def 渲染(自身):
        '可交互时点芯片去预览。否则只是文字'
        属性=自身.属性#当前 props
        窗口=属性['window']#宿主窗口
        节点=属性['node']#文本节点
        原文=属性['raw']#原文拼写
        芯片属性={#交给引用芯片
            'window':窗口,#窗口
            'appearance':'skill',#技能外观
            'label':'/'+节点['data']['name'],#带斜杠的标签
            'title':'' if 原文 is None else str(原文),#原文作标题
        }
        if 属性['interactive'] is True:#允许预览
            def 激活():
                '预览这个已确认的名字'
                属性['openSkill'](节点['data']['name'])#不含斜杠
            芯片属性['onActivate']=激活#点芯片
        return 引用芯片(芯片属性).渲染()#芯片节点
