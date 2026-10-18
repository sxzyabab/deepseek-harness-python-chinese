import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.icons import 图标检视12,图标提问14
from ...ui_基础界面组件.文字闪烁 import 文字闪烁
from .文案 import 中文文案
from .调用模型 import 格式化工具体
from .询问问题卡片 import 询问问题卡片

__all__=['问题工具表行']

行样式='dsh-tool-row'
问样式='dsh-tool-question-row'

def 确保样式(文档):
    '行样式和提问按钮样式各插一次'
    注入模块样式文件(文档,行样式,os.path.join(os.path.dirname(__file__),'工具行.module.css'),行样式)
    注入模块样式文件(
        文档,
        问样式,
        os.path.join(os.path.dirname(__file__),'问题工具表行.module.css'),
        问样式,
    )

def 元素(文档,标签,类名,模块):
    '挂上对应样式模块'
    节点=文档.createElement(标签)
    节点.className=类名
    标样式模块(节点,模块)
    return 节点

class 问题工具表行:
    '提问摘要，以及回到回答面板的入口'
    def __new__(类,属性):
        '画出提问行'
        自身=object.__new__(类)
        自身.属性=属性 if isinstance(属性,dict) else {}
        return 自身.渲染()

    def 渲染(自身):
        '展开后是问答记录或输入输出'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        确保样式(文档)
        披露=属性['useDisclosure']()
        已展开=披露['expanded'] is True
        切换=披露['toggle']
        状态=属性['state']
        输入原文=属性.get('bodyRaw')
        输出=属性.get('output')
        提问=属性.get('askQuestion')
        可展=输入原文 is not None or 输出 is not None or 提问 is not None
        打开=已展开 and 可展
        根=元素(文档,'div','root',行样式)
        根.setAttribute('data-variant','others')
        根.setAttribute('data-tool','ask_user_question')
        根.setAttribute('data-state',状态)
        if 状态=='running':
            隐藏=元素(文档,'span','visuallyHidden',行样式)
            隐藏.textContent=中文文案('row.running')
            根.appendChild(隐藏)
        行=元素(文档,'div','row',行样式)
        if 可展:
            def 点行(事件,切换=切换):
                '切换展开'
                切换()
            行.addEventListener('click',点行)
        前导=元素(文档,'span','leading',行样式)
        前导.appendChild(图标提问14({'window':窗口}))
        行.appendChild(前导)
        行.appendChild(文字闪烁({
            'window':窗口,
            'active':状态=='running',
            'className':'title',
            'children':中文文案('ask.rowTitle'),
        }).渲染())
        摘要=属性.get('summary') or ''
        if 摘要!='':
            点=元素(文档,'span','sep',行样式)
            点.setAttribute('aria-hidden','true')
            行.appendChild(点)
            摘=元素(文档,'span','summary',行样式)
            摘.appendChild(文字闪烁({
                'window':窗口,
                'active':状态=='running',
                'children':摘要,
            }).渲染())
            行.appendChild(摘)
        面板钮=元素(文档,'button','panelButton',问样式)
        面板钮.type='button'
        面板钮.appendChild(图标提问14({'window':窗口}))
        面板钮.appendChild(文档.createTextNode(属性.get('panelLabel') or ''))
        def 点面板(事件,切换=切换):
            '先打开回答面板。没有面板再展开这一行'
            事件.stopPropagation()
            打开面板=属性.get('openPanel')
            成了=False
            if 打开面板 is not None:
                成了=打开面板() is True
            if not 成了:
                切换()
        def 键面板(事件):
            '回车和空格不冒泡'
            if 事件.key=='Enter' or 事件.key==' ':
                事件.stopPropagation()
        面板钮.addEventListener('click',点面板)
        面板钮.addEventListener('keydown',键面板)
        行.appendChild(面板钮)
        根.appendChild(行)
        if 打开:
            体=元素(文档,'div','bodyWrap',行样式)
            if 提问 is not None:
                体.appendChild(询问问题卡片({'window':窗口,'card':提问}))
            else:
                盒=元素(文档,'div','ioCard',行样式)
                if 输入原文 is not None:
                    段=元素(文档,'div','ioSection',行样式)
                    标=元素(文档,'span','ioLabel',行样式)
                    标.textContent=中文文案('row.input')
                    文=元素(文档,'span','ioText',行样式)
                    体文=格式化工具体('others',输入原文)
                    文.textContent='' if 体文 is None else 体文
                    段.appendChild(标)
                    段.appendChild(文)
                    盒.appendChild(段)
                if 输入原文 is not None and 输出 is not None:
                    盒.appendChild(元素(文档,'span','ioDivider',行样式))
                if 输出 is not None:
                    段=元素(文档,'div','ioSection',行样式)
                    标=元素(文档,'span','ioLabel',行样式)
                    标.textContent=中文文案('row.output')
                    文=元素(文档,'span','ioText',行样式)
                    文.textContent=输出
                    段.appendChild(标)
                    段.appendChild(文)
                    盒.appendChild(段)
                体.appendChild(盒)
            查看=属性.get('inspect')
            if 查看 is not None:
                钮=元素(文档,'button','inspectButton',行样式)
                钮.type='button'
                钮.appendChild(图标检视12({'window':窗口}))
                钮.appendChild(文档.createTextNode(中文文案('row.inspect')))
                def 点查看(事件,查看=查看):
                    '打开轨迹'
                    查看()
                钮.addEventListener('click',点查看)
                体.appendChild(钮)
            根.appendChild(体)
        return 根
