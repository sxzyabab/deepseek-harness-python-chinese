"""宿主半 Fiber 生命周期：把沙箱产出的插件落成子 Fiber。

对齐上游 `拓展/cordis-host-runner/src/lifecycle.ts`。公开面仅中文名。
"""
from cordis.工具 import 是否thenable#可等待判定
from .守卫 import 守卫插件#带守卫的插件包装

__all__=['启动宿主半','缺失服务']#仅中文公开名

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 启动宿主半(组,插件,报告守卫失败):#启动宿主半
    """等待组就绪，启动并落定一个受守卫的子 Fiber；启动失败则先拆除再重抛。"""
    解开(组.await_()) if hasattr(组,'await_') else 解开(getattr(组,'await',lambda:None)())#组必须先就绪
    光纤=组.ctx.plugin(守卫插件(插件,报告守卫失败))#挂上受守卫插件
    try:#等它落定
        解开(光纤.await_()) if hasattr(光纤,'await_') else 解开(getattr(光纤,'await',lambda:None)())#激活或停在 pending
    except Exception as 错误:#启动失败
        解开(光纤.dispose())#先拆掉，不留失败 Fiber
        消息=错误.args[0] if 错误.args else str(错误)#失败文本
        if isinstance(消息,str) and 'already registered' in 消息:#名字已被占用
            raise Exception(f"{消息} — to REPLACE something an earlier dynamic package registered, first cordis_stop that package's id (find it with cordis_runtime_inspect what:\"temporary\"), then run the new version.")#教学错误
        raise#原样抛
    return 光纤#已落定

def 缺失服务(上下文,光纤):#仍缺的服务
    """Fiber 在 inject 里声明、但此刻还不存在的服务。"""
    注入=getattr(光纤,'inject',None) or {}#inject 表
    if isinstance(注入,dict):#按名字索引
        return [名 for 名 in 注入.keys() if 上下文.get(名) is None]#声明了但 ctx 上没有
    return []#无声明
