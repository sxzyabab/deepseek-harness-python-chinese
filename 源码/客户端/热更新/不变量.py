"""`@deepseek-ai/dsh-client-hmr` 的本包拥有不变量配套。

对齐上游 `hmr/src/invariant.ts`。公开面仅中文名。
拥有关系：节点半边启动的每个打包 stat 监视器必须随光纤一起消亡。
"""
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现的拆除器

包名='@deepseek-ai/dsh-client-hmr'#本包的不变量所有权名
名称='client-hmr-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 安装(上下文对象,失败):#安装光纤拆除后监视器不得残留的检查
    """按基线差值检查：光纤创建时观察到的监视计数，必须在拆除排空后恢复。"""
    基线表={}#光纤 → 创建时监视基线
    def 内部插件(光纤):#监听插件光纤构造与拆除
        """只审计本插件光纤。"""
        if 取字段(光纤,'name')!='client-hmr':#只审计本插件
            return#放过
        if 取字段(光纤,'uid') is not None:#光纤仍在世，记录基线
            基线表[光纤]=取字段(上下文对象,'__hmr_stat_watchers__',0)#记下创建时的监视器数
            return#创建路径结束
        基线=基线表.get(光纤)#取出该光纤的基线
        if 基线 is None:#未见过创建
            return#跳过
        解开等待(光纤)#等到光纤拆除排空
        剩余=取字段(上下文对象,'__hmr_stat_watchers__',0)#拆除后仍存活的监视器数
        if 剩余>基线:#比基线多，说明有残留
            失败('client-hmr fiber disposed but '+str(剩余-基线)+' bundle stat watcher(s) survived teardown')#报告残留监视器
    上下文对象.on('internal/plugin',内部插件,{'global':True})#全局监听

def 解开等待(光纤):#等到光纤拆除排空
    """微任务跳后等待光纤拆除。"""
    等待=getattr(光纤,'await',None) or getattr(光纤,'await_',None)#等待方法
    if 等待 is None:#无等待面
        return#跳过
    结果=等待()#调用
    if hasattr(结果,'等待'):#承诺
        结果.等待()#等待

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺
