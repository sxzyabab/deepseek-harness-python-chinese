from .启动客户端 import 网页错误#本包异常

__all__=['平台说明符','静态模块表','绑定静态模块']#仅中文公开名

平台说明符=(#与上游 PLATFORM_MODULES 对齐的说明符
    'react','react/jsx-runtime','react-dom','react-dom/client',
    '@deepseek-ai/cordis','@deepseek-ai/dsh-client-store',
    '@deepseek-ai/dsh-client-ui-slots','@deepseek-ai/dsh-client-ui-primitives',
    '@deepseek-ai/dsh-client-ui-dockkit',
)#说明符结束

静态实体=None#说明符 → 导出实体；启动前由宿主写入

def 绑定静态模块(实体表):
    """写入启动时交给模块加载器的静态表。实体表键须覆盖平台说明符。"""
    global 静态实体#写
    静态实体=实体表#记下

def 静态模块表():
    """构建启动时交给模块加载器的静态表。"""
    if 静态实体 is None:#未绑定
        raise 网页错误('web boot: static modules are not bound')#失败
    return 静态实体#表
