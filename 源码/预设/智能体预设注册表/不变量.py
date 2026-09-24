from .挂载 import 实时预设挂载表,已泄漏服务列表

包名='@deepseek-ai/dsh-agent-preset-registry'
名称='agent-presets-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','应用','默认']

def 安装(上下文,失败):
    """挂载后泄漏到根域的服务，以及名册在场却未加入预设的智能体。"""
    def 服务已变(名称,*剩余):
        """每次服务登记变化时复查仍活的挂载。"""
        for 挂载 in 实时预设挂载表():
            泄漏=已泄漏服务列表(上下文,挂载['fiber'])
            if len(泄漏)==0:
                continue
            失败(
                '预设 "'+挂载['presetId']+'" 在挂载审计之后向进程全局发布了服务 ['
                +', '.join(泄漏)+']（观察到通知 "'+str(名称)
                +'"）——预设服务必须放在 isolate 隔离域之后，或移到宿主组合'
            )
    上下文.监听('internal/service',服务已变,{'全局':True})
    def 组装监听(装配,上下文对象,下一步,*剩余):
        """模型组装前要求已加入预设。冷作用域读取没有智能体。"""
        预设表=上下文.获取服务('agentPresets',False)
        智能体=上下文对象.agent
        if (预设表 is not None and 智能体 is not None
                and 预设表.composedPreset(智能体.ctx) is None):
            失败(
                '智能体 "'+str(智能体.id)+'" 在已组合名册的部署里未加入任何智能体预设就寻址了模型；'
                +'其工具、提示词节和技能名录会落到空的全局层'
            )
        return 下一步()
    上下文.监听('system-prompt/assemble',组装监听)

def 应用(上下文):
    """登记本包不变量配套，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

默认=应用
name=名称
inject=依赖
apply=应用
default=默认
