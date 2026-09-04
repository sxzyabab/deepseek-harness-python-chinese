"""跨 realm Inspector Worker 与完整 fetch 采集的 Host Cordis 插件。

对齐上游 `host/plugin.ts`。公开面仅中文名。
"""
from .桥接.控制器 import 解析检查器选项,启动检查器#控制器面
from ..共享.服务 import 创建检查器服务#服务门面工厂
from .检视.cordis import 发布cordis树#Cordis树发布

__all__=['应用','解析检查器选项','启动检查器']#仅中文公开名

def 释放检查器(句柄,清理们):#释放检查器与已注册清理项
    """释放检查器与已注册清理项。"""
    失败们=[]#失败收集
    for 卸 in reversed(list(清理们)):#逆序清理
        try:#单次清理
            卸()#执行清理
        except Exception as 错误:#收集失败
            失败们.append(错误)#记入列表
    try:#关闭句柄
        句柄.close()#关闭检查器
    except Exception as 错误:#关闭失败
        失败们.append(错误)#记入列表
    if len(失败们)>0:#汇总抛出
        raise Exception('experimental-inspector: disposal failed') from 失败们[0]#汇总

def 应用(上下文,配置):#应用Host插件
    """启动 Worker、暴露 ctx.inspector，并注入匹配的 Client bootstrap。"""
    def 效应():#插件效应作用域
        """插件效应作用域。"""
        规格=解析检查器选项(配置)#解析规格
        句柄=启动检查器(规格)#启动检查器
        清理们=[]#清理回调列表
        try:#安装服务与注入
            清理们.append(发布cordis树(上下文,句柄.source,{'maxNodes':规格.maxCordisNodes,'maxBytes':规格.maxSourceFrameBytes-4096}))#发布Cordis树
            清理们.append(上下文.provide('inspector',创建检查器服务(句柄.source)))#注册服务
            def 注入(表):#注入bootstrap
                """注入 bootstrap。"""
                表.append({'kind':'global','name':'__DSH_INSPECTOR__','value':句柄.endpoint.client})#写入全局
            清理们.append(上下文.on('webserver/index-inject',注入))#注入监听
            print(f'dsh inspector: {句柄.endpoint.devtoolsFrontendUrl}')#打印DevTools地址
        except Exception as 错误:#初始化失败则回滚
            try:#尽力清理
                释放检查器(句柄,清理们)#回滚
            except Exception as 回滚错误:#回滚失败
                上下文.logger.error('experimental-inspector: initialization rollback failed',回滚错误)#记录回滚失败
            raise 错误#继续抛出
        def 卸除():#效应清理
            """效应清理。"""
            释放检查器(句柄,清理们)#释放
        return 卸除#效应清理
    上下文.effect(效应,'experimental-inspector: Host Worker')#效应标签

apply=应用#Cordis入口
