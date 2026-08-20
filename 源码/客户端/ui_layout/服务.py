"""LayoutController：ctx.layout 背后的跨插件面板动作面。

对齐上游 `ui-layout/src/client/service.ts`。公开面仅中文名。
"""

__all__=['布局控制器']#仅中文公开名

class 布局控制器:#跨插件面板动作面
    """其它插件可触发的面板过渡。"""
    def __init__(自身):#构造
        """未接线时动作表为空。"""
        自身.面板=None#根入口绑定动作

    def 接入面板(自身,动作):#接入根入口绑定的 store 动作
        """登记时 inject 钩调用。"""
        自身.面板=动作#记下

    def 要求面板(自身):#取出已接线动作
        """未接线则抛启动顺序错误。"""
        if 自身.面板 is None:#未接线
            raise Exception('layout: panel actions not wired (root entry not mounted)')#启动 bug
        return 自身.面板#已绑定

    def 切换侧栏(自身):#切换侧栏
        """关闭 ⟷ 约定默认宽度。"""
        自身.要求面板()['toggleSidebar']()#转发

    def 打开详情(自身):#打开详情栏
        """已打开则空操作。"""
        自身.要求面板()['openDetails']()#转发

    def 关闭详情(自身):#关闭详情栏
        """关闭详情面板。"""
        自身.要求面板()['closeDetails']()#转发
