"""布局插件浏览器半边。

对齐上游 `ui-layout/src/client/index.ts`。公开面仅中文名。
一次 register 把应用帧贡献进 root，并声明四子槽、落座布局 store、接上面板动作。
"""
from .应用帧 import 应用帧#帧组件
from .仓库 import 创建布局仓库#布局 store 工厂
from .服务 import 布局控制器#布局控制器
from .主题呈现 import 主题呈现器#主题呈现

__all__=['注入','应用','应用帧','布局控制器','创建布局仓库','主题呈现器']#仅中文公开名

注入=['slots','theme']#槽位与主题

def 应用(上下文):#安装布局界面浏览器半边
    """提供 ctx.layout，登记 root 帧，落座主题呈现器。"""
    布局=布局控制器()#本插件布局控制器
    def 装服务与根():#提供 layout 并登记 AppFrame
        """挂服务与 root 登记。"""
        拆服务=上下文.reflect.provide('layout',布局)#挂 layout
        def 注入面(动作):#把根 store 绑定动作交给服务
            """接线面板动作。"""
            布局.接入面板(动作)#接入
            return {}#无额外注入
        拆登记=上下文.slots.register({#登记 root 帧
            'name':'root',#根槽
            'children':{#四子槽
                'sidebar':{'kind':'single','scope':'root'},#侧栏
                'conversation':{'kind':'single','scope':'session-maybe'},#会话
                'details':{'kind':'single','scope':'session'},#详情
                'shell.overlay':{'kind':'list','scope':'root'},#叠层
            },#子槽结束
            'store':创建布局仓库,#布局 store 工厂
            'inject':注入面,#接线钩
        },应用帧)#帧组件
        def 拆除():#拆除服务与登记
            """先撤登记再撤服务。"""
            拆登记()#撤登记
            拆服务()#撤服务
        return 拆除#拆除器
    上下文.effect(装服务与根,'ui-layout: service + root registration')#服务与 root
    def 装主题呈现():#落座主题呈现器
        """从已解析快照做纯 DOM 写入。"""
        呈现=主题呈现器()#实例
        呈现.施加(上下文.theme.getTheme())#先投影
        def 变更(快照):#主题变更
            """投影快照。"""
            呈现.施加(快照)#投影
        关=上下文.on('theme/change',变更)#监听
        def 拆除():#拆除呈现
            """取消监听并收回写入。"""
            关()#取消
            呈现.拆除()#收回
        return 拆除#拆除器
    上下文.effect(装主题呈现,'ui-layout: theme presenter')#主题呈现
