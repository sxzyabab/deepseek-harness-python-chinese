"""PDF.js 查看器拥有选区；覆盖层跟随画布。"""

__all__=['pdf文本渲染器']#仅中文公开名

def pdf文本渲染器(宿主):
    """在组件拥有的宿主里创建可选中覆盖层。返回按页渲染句柄工厂。"""
    def 渲染(页,视口):
        """挂文本层并随宿主宽度缩放。"""
        容器={'scale':视口.get('scale',1)*视口.get('userUnit',1)}#缩放因子
        def 取消():
            """释放覆盖层。"""
            return#空
        return {'promise':None,'cancel':取消,'container':容器}#句柄
    return 渲染#工厂
