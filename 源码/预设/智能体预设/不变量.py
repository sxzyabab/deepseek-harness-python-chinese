"""`@deepseek-ai/dsh-agent-presets` 的本包拥有不变量配套。

对齐上游 `agent-presets/src/invariant.ts`。公开面仅中文名。
"""
from cordis.工具 import 已兑现#立刻兑现的拆除器
from .挂载 import 泄漏服务,活预设挂载#泄漏服务与活挂载

包名='@deepseek-ai/dsh-agent-presets'#本包的不变量所有权名
名称='agent-presets-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键,缺省)#映射
    return getattr(对象,键,缺省)#属性

def 安装(上下文对象,失败):#安装运行时不变量
    """断言已安装的预设组合没有到达根服务域，且配置了名册的部署会让每个智能体从名册组合。"""
    def 服务变化(名,*其余):#服务注册变化时复查泄漏
        """每当服务注册变化时，对每个活挂载再检查一遍。"""
        for 挂载 in 活预设挂载():#每个仍活着的预设挂载
            泄漏=泄漏服务(上下文对象,取字段(挂载,'fiber'))#根域泄漏
            if len(泄漏)==0:#无泄漏
                continue#过
            失败(
                'preset "'+取字段(挂载,'presetId')+'" published process-global service(s) ['+', '.join(泄漏)+'] '
                +'after its mount was audited (observed while notifying "'+str(名)+'") — '
                +'a preset service must sit behind an `isolate` realm or move to the host composition'
            )#失败
    上下文对象.on('internal/service',服务变化,{'global':True})#全局监听
    def 组装检查(组装,上下文块,下一步):#组装系统提示词时检查是否已加入预设
        """有名册却未加入就寻址模型则失败。"""
        名册=上下文对象.get('agentPresets')#名册服务
        智能体=取字段(上下文块,'agent')#本次组装是否属于智能体
        if 名册 is not None and len(取字段(名册,'roots') or [])>0 and 智能体 is not None:#有名册且是智能体
            if 名册.composedPreset(取字段(智能体,'ctx')) is None:#未加入
                失败(
                    'agent "'+取字段(智能体,'id')+'" addressed a model without joining any agent preset while a roster is '
                    +'composed; its tools, prompt sections, and skill catalog resolve against the empty global layer'
                )#失败
        return 下一步()#瀑布必须委托
    上下文对象.on('system-prompt/assemble',组装检查)#组装检查

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记
