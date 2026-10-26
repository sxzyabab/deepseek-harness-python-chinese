'宿主侧没有引用行为。浏览器入口由网页壳按清单启动'
from . import 客户端

__all__=['客户端']


def 应用():
    '宿主插件体。引用在浏览器导出'
    return None


apply=应用
