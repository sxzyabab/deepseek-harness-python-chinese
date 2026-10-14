from nicegui import ui as 界面
from .异常 import 叠页面失败

__all__=['拖放覆盖']#仅中文公开名

class 拖放覆盖:#全视口拖放邀请
    '文件拖到页面上方时的邀请层'
    def __init__(自身,属性):#构造
        '记下 props'
        自身.属性=属性#合成 props
        自身.画面失败=None

    def 更新(自身,属性):#props 变更
        '刷新'
        自身.属性=属性#最新

    def 卸载(自身):#卸载
        '无状态'
        return#空

    def 视图(自身):#读视图模型
        '投影标题与说明'
        文案=自身.属性['labels'] if 'labels' in 自身.属性 and 自身.属性['labels'] is not None else {}#文案
        禁用=bool(自身.属性['disabled']) if 'disabled' in 自身.属性 else False#禁用
        return {#视图
            'disabled':禁用,#禁用
            'title':文案['title'] if 'title' in 文案 else None,#标题
            'desc':None if 禁用 else (文案['desc'] if 'desc' in 文案 else None),#说明
            'illustration':'disabled' if 禁用 else 'upload',#插图键
        }#视图结束

    def 渲染(自身):
        '标题；未禁用时再画说明'
        视=自身.视图()
        旧=getattr(自身,'根',None)
        if 旧 is not None:
            try:
                旧.clear()
            except Exception as 错误:
                自身.根=None
                自身.画面失败=叠页面失败(自身.画面失败,错误)
        if getattr(自身,'根',None) is None:
            自身.根=界面.column().classes('drop-overlay')
        with 自身.根:
            if isinstance(自身.画面失败,str) and 自身.画面失败!='':
                界面.label(自身.画面失败)
            图名='block' if 视['illustration']=='disabled' else 'cloud_upload'
            界面.icon(图名, size='48px')
            if isinstance(视['title'],str) and 视['title']!='':
                界面.label(视['title'])
            if isinstance(视['desc'],str) and 视['desc']!='':
                界面.label(视['desc'])

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 组件调用'
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.渲染()
