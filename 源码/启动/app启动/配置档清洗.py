"""由调用方拥有配置档关机与写排除的文件系统恢复。"""
import os,time#路径与时间戳
from .配置档 import 配置补丁文件名,读配置清单#补丁文件名与读清单
from .配置档插件 import 写配置组合包#写组合包列表

__all__=['清洗配置档']#仅中文公开名

def 清洗配置档(二进制名,配置目录,组合包列表):
    """备份配置档补丁并只保留调用方的恢复组合包。"""
    清单路径=os.path.join(配置目录,'package.json')#清单路径
    清单=读配置清单(二进制名,配置目录) if os.path.exists(清单路径) else None#可选清单
    补丁路径=os.path.join(配置目录,配置补丁文件名)#用户补丁
    备份基=补丁路径+'.bak-'+str(int(time.time()*1000))#备份基名
    备份路径=备份基#选定路径
    序号=0#碰撞序号
    while os.path.exists(备份路径):#避碰
        序号+=1#加一
        备份路径=备份基+'-'+str(序号)#带序号
    try:#改名备份
        os.rename(补丁路径,备份路径)#移走补丁
    except FileNotFoundError:#本无补丁
        备份路径=None#无备份
    if 清单 is not None:#有清单
        写配置组合包(配置目录,清单,组合包列表)#写回组合包
    return 备份路径#备份路径或 None
