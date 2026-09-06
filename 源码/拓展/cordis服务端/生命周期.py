"""宿主半 Fiber 生命周期：把沙箱产出的插件落成子 Fiber。

对齐上游 `拓展/cordis-host-runner/src/lifecycle.ts`。公开面仅中文名。
"""
from .沙箱边界 import 包装沙箱插件#带门面包装的插件
from .类型 import 动态插件错误#本包异常

__all__=['启动宿主半','缺失服务']#仅中文公开名

def 启动宿主半(组,插件,报告门面失败):
    """等待组就绪，启动并落定一个经沙箱包装的子 Fiber；启动失败则先拆除再重抛。"""
    组.等待()#组必须先就绪；纤程.等待 不是空操作
    光纤=组.ctx.启动插件(包装沙箱插件(插件,报告门面失败))#挂上包装后的插件
    try:#等它落定
        光纤.等待()#激活或停在 pending；启动失败把原错误抛出
    except Exception as 错误:#纤程.等待 重抛插件启动错误，类型由插件决定，无法再收窄
        光纤.拆除()#先拆掉，不留失败 Fiber
        消息=错误.args[0] if len(错误.args)>0 else str(错误)#失败文本
        if isinstance(消息,str) and 'already registered' in 消息:#名字已被占用
            raise 动态插件错误(消息+' — to REPLACE something an earlier dynamic package registered, first cordis_stop that package\'s id (find it with cordis_runtime_inspect what:"temporary"), then run the new version.') from 错误#教学错误
        raise#原样抛
    return 光纤#已落定

def 缺失服务(上下文,光纤):
    """Fiber 在 inject 里声明、但此刻还不存在的服务。inject 是框架槽字面量。"""
    注入=光纤.inject#框架 inject 表；缺席则为 None
    if 注入 is None:#无声明
        return []#空
    结果=[]#仍缺的服务
    for 名 in 注入.keys():#声明了的服务名
        if 上下文.获取服务(名) is None:#此刻 ctx 上没有
            结果.append(名)#记下
    return 结果#仍缺
