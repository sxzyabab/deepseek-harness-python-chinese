import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点
from ...ui_基础界面组件.开关 import 开关
from .文案 import 中文

__all__=['开发者工具行']

样式模块='developerTools'

class 开发者工具行:
    '通用设置里的代码工作视图开关'
    def __init__(自身,属性):
        '记下份额并画出'
        自身.属性=属性
        自身.根=None
        自身.忙=False
        自身.失败=False
        自身.已订=False
        自身.退订=[]
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 更新(自身,属性):
        '换份额'
        自身.属性=属性

    def 拆订阅(自身):
        '退掉已接受值'
        for 退 in 自身.退订:
            退()
        自身.退订=[]
        自身.已订=False

    def 渲染(自身):
        '标题、说明、失败提示和开关。写入是同步的，拒绝则标保存失败'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            注入模块样式文件(
                文档,
                '开发者工具行样式',
                os.path.join(os.path.dirname(__file__),'开发者工具行.module.css'),
                样式模块,
            )
            def 全量(值):
                '已接受的开关'
                return 值
            启用=属性['useDeveloperTools'](全量)
            if 自身.根 is None:
                自身.根=文档.createElement('div')
            else:
                while 自身.根.firstChild is not None:
                    自身.根.firstChild.remove()
            自身.根.className='row'
            标样式模块(自身.根,样式模块)
            左=文档.createElement('div')
            题=模块节点(文档,'div',样式模块,'title')
            题.textContent=中文['developerTools.title']
            说明=模块节点(文档,'div',样式模块,'description')
            说明.textContent=中文['developerTools.description']
            左.appendChild(题)
            左.appendChild(说明)
            if 自身.失败:
                警=文档.createElement('div')
                警.setAttribute('role','alert')
                警.textContent=中文['developerTools.error']
                左.appendChild(警)
            自身.根.appendChild(左)
            def 改(下一):
                '清掉上一次失败再写。宿主拒绝则留下保存失败'
                自身.失败=False
                自身.忙=True
                try:
                    属性['setEnabled'](下一)
                except Exception:
                    自身.失败=True
                finally:
                    自身.忙=False
                if 自身.绘制中:
                    自身.待重画=True
                    return
                自身.渲染()
            自身.根.appendChild(开关({
                'window':窗口,
                'checked':启用 is True,
                'disabled':自身.忙,
                'label':中文['developerTools.title'],
                'onChange':改,
            }).渲染())
            if 自身.已订 is False:
                自身.已订=True
                钩=属性['useDeveloperTools']
                if hasattr(钩,'_subscribe') and callable(钩._subscribe):
                    def 变更():
                        '已接受值变了就重画。行已经不在页面上就退订'
                        if 自身.绘制中:
                            自身.待重画=True
                            return
                        if 自身.根 is None or 自身.根.parentNode is None:
                            自身.拆订阅()
                            return
                        自身.渲染()
                    退=钩._subscribe(变更)
                    if callable(退):
                        自身.退订.append(退)
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

    def 拆除(自身):
        '退掉已接受值订阅'
        自身.拆订阅()
