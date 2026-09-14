#对齐上游 worker/inspection/cordis-query.ts

def 执行检查器查询(读取器,查询):#执行查询
    """对共享语义读取器执行一次封闭的检查器查询。"""
    return {'op':查询['op'],'tree':读取器()}#返回树
