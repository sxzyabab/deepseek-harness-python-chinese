from .开发者工具设置 import 开发者工具设置字段

__all__=['应用','配置']

配置={'enabled':开发者工具设置字段['enabled']}#插件配置，经配置表单投影到浏览器

def 应用(上下文):
    """宿主偏好经配置表单投影；此处只把设置面关掉自动呈现。"""
    def 接线(子上下文):
        """有 settings 才关掉自动呈现。"""
        def 挂():
            """auto:false 绑到本纤程。"""
            return 子上下文.settings.configure({'auto':False},上下文.纤程)
        子上下文.副作用(挂)
    上下文.依赖启动(['settings'],接线)

apply=应用
Config=配置
