from .挂载 import 泄漏服务,活预设挂载#泄漏服务与活挂载

包名='@deepseek-ai/dsh-agent-presets'#本包的不变量所有权名
名称='agent-presets-invariant'#配套不变量插件名
依赖=['invariants']#依赖 invariants 服务

def 安装(上下文,失败):
    """断言已安装的预设组合没有到达根服务域，且配置了名册的部署会让每个智能体从名册组合。"""
    def 服务变化(名,*其余):
        """每当服务注册变化时，对每个活挂载再检查一遍。"""
        for 挂载 in 活预设挂载():#每个仍活着的预设挂载
            泄漏=泄漏服务(上下文,挂载['fiber'])#根域泄漏
            if len(泄漏)==0:#无泄漏
                continue#过
            失败(
                'preset "'+挂载['presetId']+'" published process-global service(s) ['+', '.join(泄漏)+'] '
                +'after its mount was audited (observed while notifying "'+str(名)+'") — '
                +'a preset service must sit behind an `isolate` realm or move to the host composition'
            )#失败
    上下文.监听('internal/service',服务变化,{'全局':True})#全局监听
    def 组装检查(组装,上下文块,下一步):
        """有名册却未加入就寻址模型则失败。上下文块是 dict，可选 agent。"""
        名册=上下文.获取服务('agentPresets',False)#名册服务
        智能体=上下文块['agent'] if 'agent' in 上下文块 else None#本次组装是否属于智能体
        根列表=名册.roots if 名册 is not None else []#扫描根
        if 名册 is not None and len(根列表)>0 and 智能体 is not None:#有名册且是智能体
            if 名册.composedPreset(智能体.ctx) is None:#未加入
                失败(
                    'agent "'+智能体.id+'" addressed a model without joining any agent preset while a roster is '
                    +'composed; its tools, prompt sections, and skill catalog resolve against the empty global layer'
                )#失败
        return 下一步()#瀑布必须委托
    上下文.监听('system-prompt/assemble',组装检查)#组装检查

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)#登记

__all__=['包名','名称','依赖','安装','应用']#仅中文公开名
name=名称#Cordis 插件名
inject=依赖#Cordis 依赖声明
apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出
