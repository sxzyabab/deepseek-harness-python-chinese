"""PDF.js 查看器拥有选区；覆盖层跟随画布。"""

__all__=['pdf文本渲染器']#仅中文公开名

def pdf文本渲染器(宿主):
    """在组件拥有的宿主里创建可选中覆盖层。返回按页渲染句柄工厂。"""
    def 渲染(页,视口):
        """挂文本层并随宿主宽度缩放。"""
        缩放=视口['scale'] if 'scale' in 视口 else 1
        用户单位=视口['userUnit'] if 'userUnit' in 视口 else 1
        容器={'scale':缩放*用户单位}
        def 取消():
            """释放覆盖层。"""
            return#空
        return {'promise':None,'cancel':取消,'container':容器}#句柄
    return 渲染#工厂
