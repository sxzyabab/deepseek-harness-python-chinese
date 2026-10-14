from nicegui import ui as 界面
from ..ui_基础界面组件.icons import 图标智能体预设16
from .异常 import 页面失败文案

__all__=['创建插件菜单项']#仅中文公开名

class 创建插件菜单项:
    '添加插件菜单里的创造模式入口。槽位只调用构造'
    def __init__(自身,属性):
        '记下属性、拉名册并画出'
        自身.属性=属性 if isinstance(属性,dict) else {}#合并后的属性
        自身.画面=None#可反复清空的容器
        自身.画面失败=None
        加载=自身.属性['load'] if 'load' in 自身.属性 else None#加载
        if 加载 is not None:
            加载()#拉名册
        if 't' in 自身.属性 and 'useAgentPresets' in 自身.属性:
            自身.渲染()#槽位只调用构造

    def 更新(自身,属性):
        '刷新并按需再拉'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新
        加载=自身.属性['load'] if 'load' in 自身.属性 else None#加载
        if 加载 is not None:
            加载()#拉

    def 名册(自身):
        '经 useAgentPresets 读整表'
        用=自身.属性['useAgentPresets']#钩子
        def 原样(快照):
            '整表'
            return 快照#快照
        return 用(原样)#快照

    def 渲染(自身):
        '画出图标、标题、说明；名册没有创造模式时禁用'
        if 't' not in 自身.属性 or 'useAgentPresets' not in 自身.属性:#未齐
            return None#不画
        翻译=自身.属性['t']#翻译
        态=自身.名册()#名册
        选项=态['options'] if 'options' in 态 and 态['options'] is not None else []#选项
        状态码=态['status'] if 'status' in 态 else None#状态
        启用=False#默认可不用
        if 状态码=='ready':#就绪才找
            for 项 in 选项:#扫
                if 项['id']=='cordis':#创造模式
                    启用=True#可用
                    break
        if 状态码=='idle' or 状态码=='loading':#还在查
            说明=翻译('createPluginChecking')#检查中
        elif 状态码=='error' or 状态码=='unavailable':#失败
            说明=翻译('createPluginUnavailable')#不可用
        elif 启用 is not True:#没有创造模式
            说明=翻译('createPluginMissing')#缺失
        else:#可用
            说明=翻译('createPluginDescription')#说明
        旧=getattr(自身,'画面',None)#已有容器
        if 旧 is not None:
            try:
                旧.clear()
            except Exception as 错误:#父级清掉容器后，把失败留在页面上
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column()#根
        自身.画面.clear()#再清一次
        def 点():
            '先关菜单再进入创造模式'
            if 启用 is not True:#不可用
                return
            关=自身.属性['onDismiss'] if 'onDismiss' in 自身.属性 else None#关闭菜单
            if 关 is not None:
                关()#关
            启=自身.属性['startCreatorDraft'] if 'startCreatorDraft' in 自身.属性 else None#启动
            if 启 is not None:
                启()#启动
        with 自身.画面:#根
            if isinstance(自身.画面失败,str) and 自身.画面失败!='':
                界面.label(自身.画面失败)
            图标智能体预设16()#预设图标
            界面.label(翻译('createPlugin'))#标题
            界面.label(说明)#说明
            钮=界面.button(翻译('createPlugin'), on_click=点)#入口
            if 启用 is not True:#不可用
                钮.disable()#禁

    def __call__(自身,属性=None):
        '只接收一个属性字典'
        if 属性 is not None:
            自身.更新(属性)#刷
        return 自身.渲染()
