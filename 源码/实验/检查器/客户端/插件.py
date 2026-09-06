"""直接向 Inspector Worker 发布浏览器观测的 Client Cordis 插件。

对齐上游 `client/plugin.ts`。公开面仅中文名。
"""
from ..共享.json import 检查器错误#本包错误
from ..共享.桥接.控制编解码 import 解析检查器客户端引导#引导解析
from ..共享.服务 import 创建检查器服务#服务门面
from .检视.cordis import 发布cordis树#Cordis树发布
from .桥接.控制器 import 启动检查器客户端#启动Client源

__all__=['应用','名称','注入']#仅中文公开名

名称='experimental-inspector'#插件名
注入=[]#无注入

def 拆除检查器客户端(源,清理列表):#拆除Client检查器
    """拆除 Client 源与已注册清理项。"""
    失败列表=[]#失败收集
    for 卸 in reversed(list(清理列表)):#逆序
        try:#单次
            卸()#执行
        except Exception as 错误:#插件清理回调什么都可能抛，收不窄
            失败列表.append(错误)#收集
    try:#关闭源
        源.关闭()#关闭
    except Exception as 错误:#插件关闭面什么都可能抛，收不窄
        失败列表.append(错误)#收集
    if len(失败列表)>0:#汇总
        raise 检查器错误('experimental-inspector: Client disposal failed') from 失败列表[0]#汇总

def 应用(上下文):#应用Client插件
    """挂载 Client source 与共享的 ctx.inspector 发布 API。"""
    import builtins as 内建#全局命名空间
    注入值=getattr(内建,'__DSH_INSPECTOR__',None)#读取引导全局
    if 注入值 is None:#缺失
        raise 检查器错误('experimental inspector: Host bootstrap is missing')#拒绝
    引导=解析检查器客户端引导(注入值)#解析引导
    def 效应():#插件效应
        """插件效应作用域。"""
        源=启动检查器客户端(引导)#启动Client源
        清理列表=[]#清理列表
        try:#安装
            清理列表.append(发布cordis树(上下文,源,{'maxNodes':引导['maxCordisNodes'],'maxBytes':引导['maxFrameBytes']-4096}))#树发布
            清理列表.append(上下文.提供服务('inspector',创建检查器服务(源)))#注册服务
        except Exception as 错误:#插件 inject 失败，体什么都可能抛，收不窄
            try:#尽力清理
                拆除检查器客户端(源,清理列表)#清理
            except Exception as 回滚错误:#回滚路径同样收不窄
                上下文.日志.错误('experimental-inspector: Client initialization rollback failed',回滚错误)#记录
            raise 错误#继续抛出
        def 卸除():#效应清理
            """效应清理。"""
            拆除检查器客户端(源,清理列表)#拆除
        return 卸除#效应清理
    上下文.副作用(效应,'experimental-inspector: Client source')#效应标签

apply=应用#Cordis入口
