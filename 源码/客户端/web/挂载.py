"""经依赖光纤挂载应用。

对齐上游 `web/src/mount.ts`。公开面仅中文名。
替换 `uiRenderer` 时重挂。inject 返回的光纤须显式 等待()。
"""

__all__=['挂载客户端']#仅中文公开名

def 挂载客户端(上下文,容器):
    """经 uiRenderer 依赖光纤把渲染器挂进容器。"""
    def 安装(作用域):
        """服务提供时安装挂载效应。"""
        def 挂():
            """挂到容器。"""
            return 作用域.uiRenderer.mount(容器)#挂载
        作用域.副作用(挂,'web boot: application mount')#效应
    已挂=上下文.inject(['uiRenderer'],安装)#等 uiRenderer
    已挂.等待()#等光纤就绪
