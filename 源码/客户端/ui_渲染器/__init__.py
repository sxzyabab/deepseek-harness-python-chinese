from . import 客户端#同目录的客户端包

__all__=['客户端']#只导出这个包名，不转发里面的类


def 应用():
    '宿主面无行为，只占 Loader 行'
    return#不调用客户端


apply=应用#宿主入口别名
