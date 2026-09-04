"""与源载体无关的 Cordis 树查询执行。"""
#对齐上游 worker/inspection/cordis-query.ts

from .....内核.智能体循环.辅助 import 解开#可等待则等待

__all__=['执行检查器查询']#仅中文公开名

def 执行检查器查询(读取器,查询):#执行查询
    """对共享语义读取器执行一次封闭的检查器查询。"""
    return {'op':查询['op'],'tree':解开(读取器.getTree())}#返回树
