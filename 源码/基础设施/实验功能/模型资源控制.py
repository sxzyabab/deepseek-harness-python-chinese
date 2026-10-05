from threading import Lock as 锁
from typing import Optional as 可选

class Agent执行状态:
    停止=object()
    运行中=object()
    挂起=object() #等待资源释放
    故障=object() #异常退出,通常应人类或领导Agent接管
    封禁=object() #被封禁的Agent必须人类手动解禁才能继续运行,用于防止智障AI乱搞
    ...


class 资源池:
    def __init__(self,名称:str,描述:str,*,资源使用上限:int,父资源池:可选['资源池']=None):
        self.名称=名称
        self.描述=描述
        self.资源使用上限=资源使用上限
        self.父资源池=父资源池
        self.资源存取锁=锁()
        self.资源使用量=0

    def 申请使用(self,数量:int)->bool:
        with self.资源存取锁:
            if self.资源使用量+数量>self.资源使用上限:
                return False
            self.资源使用量+=数量
            return True


    def 归还资源(self,数量:int):
        with self.资源存取锁:
            self.资源使用量-=数量