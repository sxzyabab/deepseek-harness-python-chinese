"""布局插件浏览器半边。

对齐上游 `ui-layout/src/client/index.ts`。公开面仅中文名。
一次 register 把应用帧贡献进 root，并声明四子槽、落座布局 store、接上面板动作。
"""
from .应用帧 import 应用帧#帧组件
from .存储 import 创建布局存储#布局存储工厂
from .服务 import 布局控制器#布局控制器
from .主题呈现 import 主题呈现器#主题呈现

__all__=['注入','应用','应用帧','布局控制器','创建布局存储','主题呈现器']#仅中文公开名

注入=['slots','theme','locale']#槽位、主题、文案

def 应用(上下文):#安装布局界面浏览器半边
    """提供 ctx.layout，登记 root 帧，落座主题呈现器。"""
    def 装服务与根():#提供 layout 并登记 AppFrame
        """挂服务与 root 登记。"""
        句柄=创建布局存储()#布局 store 句柄
        实例={'getSnapshot':句柄['getSnapshot'],'subscribe':句柄['subscribe'],'actions':句柄['actions']}#共享根实例
        def 造实例():#始终交同一实例
            """共享根实例。"""
            return 实例#同一实例
        存储=dict(句柄)#拷贝句柄
        存储['create']=造实例#覆盖工厂
        def 有主面板(标识):#检查主槽登记
            """条目 options.key 是否匹配。"""
            for 条目 in 上下文.slots.entries('main'):#主槽条目
                选项=条目['options'] if isinstance(条目,dict) and 'options' in 条目 else getattr(条目,'options',None)#选项
                键=选项['key'] if isinstance(选项,dict) and 'key' in 选项 else getattr(选项,'key',None) if 选项 is not None else None#键
                if 键==标识:#命中
                    return True#已登记
            return False#未登记
        布局=布局控制器(实例['actions'],有主面板)#控制器
        def 保留主面板():#主槽撤登记时清活动面板
            """收集仍在的键。"""
            键列表=[]#累积
            for 条目 in 上下文.slots.entries('main'):#主槽
                选项=条目['options'] if isinstance(条目,dict) and 'options' in 条目 else getattr(条目,'options',None)#选项
                键=选项['key'] if isinstance(选项,dict) and 'key' in 选项 else getattr(选项,'key',None) if 选项 is not None else None#键
                if 键 is not None:#有键
                    键列表.append(键)#收下
            实例['actions']['retainMainPanels'](键列表)#清理
        def 取面板信息():#读面板信息快照
            """从共享实例取 panelInfo。"""
            return 实例['getSnapshot']()['panelInfo']#面板信息
        面板信息={'getSnapshot':取面板信息,'subscribe':实例['subscribe']}#宿主可观察
        拆面板信息=上下文.slots.provideRoot({'hooks':{'panelInfo':面板信息}})#提供根钩
        拆服务=上下文.反射.提供服务('layout',布局)#挂 layout
        拆登记=上下文.slots.register({#登记 root 帧
            'name':'root',#根槽
            'locale':'common',#共用词表
            'children':{#四子槽
                'sidebar':{'kind':'single','scope':'root'},#侧栏
                'main':{'kind':'keyed','scope':'root'},#主槽
                'rightbar':{'kind':'single','scope':'root'},#右侧栏
                'shell.overlay':{'kind':'list','scope':'root'},#叠层
            },#子槽结束
            'store':存储,#共享布局存储
        },应用帧)#帧组件
        拆面板=上下文.slots.subscribe('main',保留主面板)#主槽变更
        保留主面板()#首次对齐
        def 拆除():#拆除服务与登记
            """先撤导航与订阅再撤登记。"""
            布局.拆除()#作废导航
            拆面板()#取消订阅
            拆登记()#撤登记
            拆面板信息()#撤钩
            拆服务()#撤服务
        return 拆除#拆除器
    上下文.副作用(装服务与根,'ui-layout: service + root registration')#服务与 root
    def 装主题呈现():#落座主题呈现器
        """从已解析快照做纯 DOM 写入。"""
        呈现=主题呈现器()#实例
        呈现.施加(上下文.theme.getTheme())#先投影
        def 变更(快照):#主题变更
            """投影快照。"""
            呈现.施加(快照)#投影
        关=上下文.监听('theme/change',变更)#监听
        def 拆除():#拆除呈现
            """取消监听并收回写入。"""
            关()#取消
            呈现.拆除()#收回
        return 拆除#拆除器
    上下文.副作用(装主题呈现,'ui-layout: theme presenter')#主题呈现
