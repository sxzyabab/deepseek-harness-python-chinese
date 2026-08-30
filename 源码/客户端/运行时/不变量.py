"""`@deepseek-ai/dsh-client-runtime` 的本包拥有不变量配套。

对齐上游 `runtime/src/invariant.ts`。公开面仅中文名。

拥有关系：每一次 'slots/changed'(key) 发出时必须已经观察到变更已应用——SlotCore 在服务再发出之前同步抬该键的版本，因此派发时版本为零意味着事件在变更之前（或没有变更）就发出了。
"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-client-runtime'#本包的不变量所有权名
名称='client-runtime-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#值
        return 缺省#缺席
    return getattr(对象,键,缺省)#属性

def 安装(上下文对象,失败):#安装槽位变更必须跟在突变之后的检查
    """每一次 slots/changed 发出时该键版本必须已抬升。"""
    def 内部派发(_模式,事件名,参数,*其余):#监听内部派发
        """只审计槽位变更。"""
        if 事件名!='slots/changed':#非槽位变更
            return#放过
        键=参数[0] if 参数 else None#第一个实参应是槽键
        if (not isinstance(键,str)) or 键=='':#不是非空字符串
            失败("'slots/changed' dispatched without a slot key argument")#缺少槽键
            return#不再查版本
        槽位=上下文对象.get('slots')#可选槽位服务
        if 槽位 is not None and 槽位.getVersion(键)==0:#版本仍为零
            失败("'slots/changed' fired for \""+键+"\" before any mutation bumped its version — emission must follow the applied mutation")#报告发出早于突变
    上下文对象.on('internal/dispatch',内部派发,{'global':True})#全局监听

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺
