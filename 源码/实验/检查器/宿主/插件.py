from ..共享.json import 检查器错误#本包错误
from .桥接.控制器 import 解析检查器选项,启动检查器#控制器面
from ..共享.服务 import 创建检查器服务#服务门面工厂
from .检视.cordis import 发布cordis树#Cordis树发布

__all__=['应用','解析检查器选项','启动检查器']#仅中文公开名

def 拆除检查器(句柄,清理列表):#拆除检查器与已注册清理项
    """拆除检查器与已注册清理项。"""
    失败列表=[]#失败收集
    for 卸 in reversed(list(清理列表)):#逆序清理
        try:#单次清理
            卸()#执行清理
        except Exception as 错误:#插件清理回调什么都可能抛，收不窄
            失败列表.append(错误)#记入列表
    try:#关闭句柄
        句柄.关闭()#关闭检查器
    except Exception as 错误:#插件关闭面什么都可能抛，收不窄
        失败列表.append(错误)#记入列表
    if len(失败列表)>0:#汇总抛出
        raise 检查器错误('experimental-inspector：拆除失败') from 失败列表[0]#汇总

def 应用(上下文,配置):#应用Host插件
    """启动 Worker、暴露 ctx.inspector，并注入匹配的 Client bootstrap。"""
    def 效应():#插件效应作用域
        """插件效应作用域。"""
        规格=解析检查器选项(配置)#解析规格
        句柄=启动检查器(规格)#启动检查器
        清理列表=[]#清理回调列表
        try:#安装服务与注入
            清理列表.append(发布cordis树(上下文,句柄.source,{'maxNodes':规格.maxCordisNodes,'maxBytes':规格.maxSourceFrameBytes-4096}))#发布Cordis树
            清理列表.append(上下文.提供服务('inspector',创建检查器服务(句柄.source)))#注册服务
            def 注入(表):#注入bootstrap
                """注入 bootstrap。"""
                表.append({'kind':'global','name':'__DSH_INSPECTOR__','value':句柄.endpoint.client})#写入全局
            清理列表.append(上下文.监听('webserver/index-inject',注入))#注入监听
            print(f'dsh inspector: {句柄.endpoint.devtoolsFrontendUrl}')#打印DevTools地址
        except Exception as 错误:#插件 inject 失败，体什么都可能抛，收不窄
            try:#尽力清理
                拆除检查器(句柄,清理列表)#回滚
            except Exception as 回滚错误:#回滚路径同样收不窄
                上下文.日志.错误('experimental-inspector：初始化回滚失败',回滚错误)#记录回滚失败
            raise 错误#继续抛出
        def 卸除():#效应清理
            """效应清理。"""
            拆除检查器(句柄,清理列表)#拆除
        return 卸除#效应清理
    上下文.副作用(效应,'experimental-inspector: Host Worker')#效应标签

apply=应用#Cordis入口
