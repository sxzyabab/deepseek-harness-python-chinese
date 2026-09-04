"""直接向 Inspector Worker 发布浏览器观测的 Client Cordis 插件。

对齐上游 `client/plugin.ts`。公开面仅中文名。
"""
from ..共享.桥接.控制编解码 import 解析检查器客户端引导#引导解析
from ..共享.服务 import 创建检查器服务#服务门面
from .检视.cordis import 发布cordis树#Cordis树发布
from .桥接.控制器 import 启动检查器客户端#启动Client源

__all__=['应用','名称','注入']#仅中文公开名

名称='experimental-inspector'#插件名
注入=[]#无注入

def 取引导(引导,键):#取引导字段
    """兼容对象与字典引导。"""
    return getattr(引导,键) if hasattr(引导,键) else 引导[键]#取值

def 释放检查器客户端(源,清理们):#释放Client检查器
    """释放 Client 源与已注册清理项。"""
    失败们=[]#失败收集
    for 卸 in reversed(list(清理们)):#逆序
        try:#单次
            卸()#执行
        except Exception as 错误:#失败
            失败们.append(错误)#收集
    try:#关闭源
        源.关闭()#关闭
    except Exception as 错误:#失败
        失败们.append(错误)#收集
    if len(失败们)>0:#汇总
        raise Exception('experimental-inspector: Client disposal failed') from 失败们[0]#汇总

def 应用(上下文):#应用Client插件
    """挂载 Client source 与共享的 ctx.inspector 发布 API。"""
    import builtins as 内建#全局命名空间
    注入值=getattr(内建,'__DSH_INSPECTOR__',None)#读取引导全局
    if 注入值 is None:#缺失
        raise Exception('experimental inspector: Host bootstrap is missing')#拒绝
    引导=解析检查器客户端引导(注入值)#解析引导
    def 效应():#插件效应
        """插件效应作用域。"""
        源=启动检查器客户端(引导)#启动Client源
        清理们=[]#清理列表
        try:#安装
            清理们.append(发布cordis树(上下文,源,{'maxNodes':取引导(引导,'maxCordisNodes'),'maxBytes':取引导(引导,'maxFrameBytes')-4096}))#树发布
            清理们.append(上下文.provide('inspector',创建检查器服务(源)))#注册服务
        except Exception as 错误:#失败回滚
            try:#尽力清理
                释放检查器客户端(源,清理们)#清理
            except Exception as 回滚错误:#回滚失败
                上下文.logger.error('experimental-inspector: Client initialization rollback failed',回滚错误)#记录
            raise 错误#继续抛出
        def 卸除():#效应清理
            """效应清理。"""
            释放检查器客户端(源,清理们)#释放
        return 卸除#效应清理
    上下文.effect(效应,'experimental-inspector: Client source')#效应标签

apply=应用#Cordis入口
