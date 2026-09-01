"""存储枢纽的具名后端注册表。"""
from .错误 import 存储错误#存储错误
__all__=['后端注册表']#仅中文公开名

class 后端注册表:#名到后端表
    """可变的名→后端表。多个后端并排挂着。"""
    def __init__(自身):#空注册表
        自身._后端={}#名到后端

    def register(自身,名称,后端):#注册一个具名后端
        """注册一个具名后端。注册是 effect：返回的 disposer 移除该名。拆除并不关闭后端。"""
        if 名称 in 自身._后端:#该名已占用
            raise 存储错误('duplicate-backend',f"storage backend '{名称}' is already registered")#重复注册
        自身._后端[名称]=后端#记下后端
        def 注销():#注销 disposer
            if 自身._后端.get(名称) is 后端:#仍是本次注册
                del 自身._后端[名称]#卸下该名
        return 注销#返回 disposer

    def get(自身,名称):#按名解析后端
        """按名解析后端。"""
        后端=自身._后端.get(名称)#查表
        if 后端 is None:#未注册
            已注册=','.join(自身._后端.keys()) or 'none'#已注册名
            raise 存储错误('backend-not-found',f"storage backend '{名称}' is not registered (registered: {已注册})")#找不到
        return 后端#返回后端

    def names(自身):#已注册后端名快照
        """已注册后端名，供诊断。"""
        return list(自身._后端.keys())#快照键表
