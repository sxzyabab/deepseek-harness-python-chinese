'PTC 执行器：模型只直接调用 run_code，嵌套调用仍走工具运行时的分阶段调度'
from ...基础设施.通用工具 import 紧凑json编码
from ..会话 import 快照json值
from ..工具 import 仅代码指令,工具错误
from ..工具.异常 import 工具未找到错误
from ..工具执行器_原生 import 执行工具批次
from .代码模式 import 运行代码名,创建运行代码工具
from .ts类型 import json模式转ts,渲染工具sdk
from .python类型 import json模式转py,渲染工具sdkpy
from .配置 import 配置
from .异常 import 代码运行失败错误

__all__=(
    '代码工具执行器',
    '配置','代码运行失败错误',
    '运行代码名','创建运行代码工具',
    'json模式转ts','渲染工具sdk',
    'json模式转py','渲染工具sdkpy',
    '名称','注入','应用',
)#英文槽 name/inject/apply/Config 不进此表

sdk渲染器={
    'typescript':渲染工具sdk,#TS SDK
    'python':渲染工具sdkpy,#Python SDK
}#语言到已有渲染器

class 代码工具执行器:
    '跑程序；嵌套工具调用走工具运行时已有的守卫和调度'
    def __init__(自身,上下文,配置值=None,最大并行=None):
        '校验子调用上限，并准备两段提示词'
        if 最大并行 is None:
            def 最大并行():
                '外层批次缺省最多 10 个并行安全调用'
                return 10
        已校验=配置.校验数据({} if 配置值 is None else 配置值)#与加载器同一份校验
        自身.上下文=上下文#挂载上下文
        自身.最大并行=最大并行#外层批次
        自身.最大并行子调用=已校验['maxParallelSubCalls']#程序内部
        自身.传输=None#惰性 run_code
        提示=上下文.systemPrompt#提示词服务
        自身.段落表=(
            {
                'name':'tools:ptc-only',#先读能调用什么
                'order':提示.获取段落顺序('PTC_ONLY'),#中央顺序
                'text':仅代码指令,#模型可见原文
                'interpolate':False,#不插值
            },
            {
                'name':'tools:sdk',#再读每个工具做什么
                'order':提示.获取段落顺序('TOOLS_SDK'),#中央顺序
                'text':自身.渲染sdk,#按可见定义生成
                'interpolate':False,#schema 里的花括号原样
            },
        )#执行器拥有的段

    def 要求运行时(自身):
        '读取已加载运行时；语言必须有 SDK 渲染器'
        运行时=自身.上下文.获取服务('ptcRuntime')#注入保证挂载后存在
        if 运行时 is None:
            raise 工具错误('dsh-tools: 模式 "ptc" 需要PTC运行时 — 请加载 ctx.ptcRuntime 实现（例如 @deepseek-ai/dsh-ptc-runtime-node）或把 tools 模式设为 "native"')#与工具包同一句
        语言=运行时.语言()#中文运行时的方法，不是 .language
        if 语言 not in sdk渲染器:
            已知=', '.join(紧凑json编码(名) for 名 in sdk渲染器)#已知语言
            raise 工具错误('dsh-tools: 运行时语言 '+紧凑json编码(语言)+' 没有已登记的 SDK 渲染器（已知: '+已知+'）')#与工具包同一句
        return 运行时#已校验

    def 渲染sdk(自身,工具列表):
        '按运行时语言渲染 SDK；渲染器来自内核.工具'
        运行时=自身.要求运行时()#语言
        渲染=sdk渲染器[运行时.语言()]#已有函数
        模式列表=[]#带输出模式
        for 定义 in 工具列表:
            项=自身.上下文.tools.投影模式(定义,False)#不脱离参数
            输出=快照json值(定义['output']['schema'])#输出模式必须无损
            if 输出 is None:
                raise 工具错误('工具 "'+定义['name']+'" 的输出模式在 SDK 投影前必须是无损 JSON')#与工具包同一句
            项['output']=输出#规范输出
            模式列表.append(项)#收下
        return 渲染(模式列表)#现有渲染器只有一个参数

    def 描述(自身,_工具列表):
        '模型只能直接看见 run_code'
        传输=自身.要求传输()#保留传输
        return {
            'schemas':[自身.上下文.tools.投影模式(传输,False)],#不脱离
            'knownNames':[运行代码名],#顺序校验只认传输
        }#折叠到 run_code

    def 拒绝直接调用(自身,名):
        '非传输的模型直呼在策略之前拒绝'
        if 名==运行代码名:
            return None#传输可以
        return 工具未找到错误(名,'only `'+运行代码名+'` is callable directly — call `'+名+'` from inside a `'+运行代码名+'` program instead')#模型可见原文

    def 要求传输(自身):
        '惰性构建 run_code；子调用上限用本执行器的配置'
        if 自身.传输 is not None:
            return 自身.传输#同一份
        工具=自身.上下文.tools#注册表
        def 窥探运行时():
            '组装描述时可以没有运行时'
            return 自身.上下文.获取服务('ptcRuntime')#可选

        def 窥探审批():
            '升级审批可以没有'
            return 自身.上下文.获取服务('approval')#可选

        def 解析沙箱政策(执行):
            '有围栏的运行时必须能解析站立政策'
            政策=自身.上下文.获取服务('sandboxPolicy')#沙箱政策
            if 政策 is None:
                raise 工具错误('dsh-tools: confined PTC runtime requires sandboxPolicy')#机器比对
            if 'agent' not in 执行 or 执行['agent'] is None:
                return 政策.解析({})#无会话
            return 政策.解析({'session':执行['agent'].session})#按会话

        def 解析工作目录(执行):
            '有智能体时必须有工作目录服务'
            if 'agent' not in 执行 or 执行['agent'] is None:
                return None#无智能体
            目录=自身.上下文.获取服务('workingDirectory')#工作目录
            if 目录 is None:
                raise 工具错误('dsh-tools: run_code with an Agent requires workingDirectory')#机器比对
            return 目录.ensure(执行['agent'],执行.get('signal'))#确保目录

        def 整形日志(派发):
            '走注册表上已有的瀑布'
            return 工具.整形派发日志(派发)#不另写
        自身.传输=创建运行代码工具(工具,{
            'requireRuntime':自身.要求运行时,#执行时必需
            'peekRuntime':窥探运行时,#描述时窥探
            'peekApprover':窥探审批,#可选审批
            'resolveSandboxPolicy':解析沙箱政策,#站立政策
            'resolveWorkingDirectory':解析工作目录,#会话目录
            'maxParallel':自身.最大并行子调用,#程序内部
            'shapeDispatchLog':整形日志,#日志瀑布
        })#已有传输
        return 自身.传输#共享实例

    def 执行(自身,输入):
        '外层批次走工具运行时的分阶段调度'
        return 执行工具批次(输入,自身.上下文.tools,自身.最大并行)#同一套管线

名称='ptc-tool-executor'#插件名保持字面量
注入=['tools','systemPrompt','ptcRuntime']#注册表、提示词、运行时

def 应用(上下文,配置值=None):
    '在挂载作用域选择 PTC 执行'
    上下文.tools.设置执行器(代码工具执行器(上下文,配置值))#挂上执行器

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
Config=配置#框架槽
