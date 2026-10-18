'通用设置里的上传行，以及关掉设置后仍在的提示'
import os
from ...ui_对话.异常 import 注入模块样式文件,模块节点
from ...ui_基础界面组件.开关 import 开关
from ...ui_基础界面组件.吐司 import 吐司
from .文案 import 中文

__all__=['上传行','上传提示']

样式模块='upload-row'
样式路径=os.path.join(os.path.dirname(__file__),'上传行.module.css')

def 整份(值):
    '选择整份快照'
    return 值

def 订上(钩子,重画):
    '快照变了调用重画'
    订=getattr(钩子,'_subscribe',None)
    if callable(订):
        return 订(重画)
    return None

class 上传行:
    '画出已接受的 API 上传状态'
    def __init__(自身,属性):
        '记下 props。键齐了就画。'
        自身.属性=属性
        自身.根=None
        自身.已订=False
        if isinstance(属性,dict) and 'window' in 属性 and 'useUpload' in 属性 and 'useMutation' in 属性 and 'setEnabled' in 属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性

    def 渲染(自身):
        '拆掉旧行，再按当前快照画一次'
        if 自身.已订 is False:
            自身.已订=True
            def 重画():
                '上传值或写入状态变了再画'
                自身.渲染()
            订上(自身.属性['useUpload'],重画)
            订上(自身.属性['useMutation'],重画)
        窗口=自身.属性['window']
        文档=窗口.document
        注入模块样式文件(文档,'上传行样式',样式路径,样式模块)
        上传=自身.属性['useUpload'](整份)
        def 是否忙(值):
            '选择是否正在写入'
            return 值['busy']
        忙=自身.属性['useMutation'](是否忙)
        已接受值=上传['value']
        选中=False
        if 已接受值 is not None:
            选中=已接受值['enabled'] is True
        禁用=忙 or 上传['status']!='ready' or not 上传['writable']
        def 改开关(启用):
            '把请求的开关交给偏好写入'
            自身.属性['setEnabled'](启用)
        行=模块节点(文档,'div',样式模块,'row')
        文=文档.createElement('div')
        题=模块节点(文档,'div',样式模块,'title')
        题.textContent=中文['title']
        说明=模块节点(文档,'div',样式模块,'description')
        说明.textContent=中文['description']
        文.appendChild(题)
        文.appendChild(说明)
        行.appendChild(文)
        控件=开关({
            'window':窗口,
            'checked':选中,
            'label':中文['title'],
            'disabled':禁用,
            'onChange':改开关,
        }).渲染()
        行.appendChild(控件)
        if 自身.根 is not None:
            自身.根.remove()
        if 'parent' in 自身.属性:
            自身.属性['parent'].appendChild(行)
        自身.根=行
        return 行

    def __call__(自身,属性=None):
        '对齐槽位再次调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

class 上传提示:
    '设置关掉后仍显示保存结果'
    def __init__(自身,属性):
        '记下 props。键齐了就画。'
        自身.属性=属性
        自身.根=None
        自身.序号=None
        自身.已订=False
        if isinstance(属性,dict) and 'window' in 属性 and 'useMutation' in 属性 and 'dismiss' in 属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性

    def 渲染(自身):
        '没有提示时卸掉。序号没变就留着原来那条。'
        if 自身.已订 is False:
            自身.已订=True
            def 重画():
                '写入结果变了再画提示'
                自身.渲染()
            订上(自身.属性['useMutation'],重画)
        状态=自身.属性['useMutation'](整份)
        提示=状态['notice']
        if 提示 is not None and 自身.根 is not None and 自身.序号==状态['sequence']:
            return 自身.根
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        自身.序号=None
        if 提示 is None:
            return None
        窗口=自身.属性['window']
        道具={
            'window':窗口,
            'text':中文[提示],
            'onDone':自身.属性['dismiss'],
            'key':状态['sequence'],
        }
        if 提示=='saved':
            道具['tone']='success'
        if 'parent' in 自身.属性:
            道具['parent']=自身.属性['parent']
        自身.序号=状态['sequence']
        自身.根=吐司(道具).渲染()
        return 自身.根

    def __call__(自身,属性=None):
        '对齐槽位再次调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
