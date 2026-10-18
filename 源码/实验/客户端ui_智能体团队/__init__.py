'宿主侧没有团队行为。浏览器入口由网页壳按清单启动'
from . import 客户端,异常

__all__=['客户端']


def 应用():
    '宿主插件体。团队行为在浏览器导出和宿主 RPC 域'
    return None


apply=应用
