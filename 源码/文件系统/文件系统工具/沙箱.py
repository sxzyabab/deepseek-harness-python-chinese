"""write 与 edit 工具共享的沙箱升级 API：每调用策略解析、广告的升级字段、拒绝标记映射。词汇与失败关闭的审批序列都委托给 sandbox（与 tool-bash 使用的相同零件），因此 bash 与 fs 以同一方式升级。插件应用时按 ctx.fs.sandboxMode 构造一次，由两个变更工具共享。对齐上游 tool-fs/src/sandbox.ts。"""
from ...沙盒.沙盒 import (#从 sandbox 导入升级 API（公开符号已是中文名）
    升级目标,#可广告的升级目标
    批准升级,#批准升级
    升级提示标记,#升级提示标记
    沙箱拒绝标记,#沙箱拒绝标记
    校验升级参数,#校验升级参数配对
)#sandbox 导入结束
from .. import 文件系统 as fs#文件系统错误类
from .辅助 import 取字段,试取,解开#字段读取与承诺展开

class 文件系统沙箱控制器:#文件系统沙箱升级控制器
    """文件系统升级 API：广告门控、每调用策略解析、一次已批准的更宽重试、拒绝标记映射。插件应用时由 ctx 纯构造。"""
    def __init__(自身,上下文):#按当前挂载的文件系统能力构造
        """按当前挂载的文件系统能力构造。隔离后端却缺少策略服务时加载失败。"""
        自身.上下文=上下文#保存上下文
        默认模式=上下文.fs.沙箱模式#读取后端默认沙箱模式
        自身.升级模式=[] if 默认模式 is None else list(升级目标)#无隔离则不广告升级；有隔离则广告封闭升级目标
        自身.政策=None if 默认模式 is None else 上下文.get('sandboxPolicy')#有隔离则取出策略服务
        if 默认模式 is not None and 自身.政策 is None:#隔离后端却缺少策略服务
            raise Exception('tool-fs: the mounted filesystem confines but ctx.sandboxPolicy is missing')#加载时大声失败

    def 模式字段(自身):#给出升级参数schema
        """变更工具 parameters 的升级 schema 字段。仅在隔离后端下调用（用升级模式守卫）；枚举钉死封闭目标词汇，严格更宽检查在每次执行时进行。"""
        return {#两个升级字段
            'sandbox_permissions':{#更宽模式
                'type':'string',#字符串
                'enum':list(自身.升级模式),#封闭升级目标
                'description':'The wider sandbox mode this file operation needs. Only valid as a one-shot retry of an operation the sandbox just denied; requires justification and user approval.',#仅作为沙箱刚拒绝后的一次性重试
            },#sandbox_permissions结束
            'justification':{#理由
                'type':'string',#字符串
                'description':'Required with sandbox_permissions: one sentence for the user explaining why this exact file operation needs the wider access.',#必须与sandbox_permissions一起
            },#justification结束
        }#字段结束

    def 解析政策(自身,工具名,参数,执行):#解析此次变更的沙箱策略
        """盖到此次变更上的策略：已批准的升级授予（在任何执行之前经 ctx.approval 解析的严格更宽重试），否则为会话的常驻模式。调用会话的 cwd 始终作为 workspace 根携带。先校验升级参数配对。"""
        校验升级参数(试取(参数,'sandbox_permissions'),试取(参数,'justification'))#先校验升级参数配对
        请求={}#常驻政策请求
        智能体=试取(执行,'agent')#调用方智能体
        if 智能体 is not None:#有智能体
            请求['session']=取字段(智能体,'session')#带上会话
        常驻政策=自身.政策.解析(请求) if 自身.政策 is not None else None#解析会话常驻策略
        if 试取(参数,'sandbox_permissions') is None or 试取(参数,'justification') is None:#没有升级请求
            return 常驻政策#使用常驻策略
        if len(自身.升级模式)==0:#组合未广告升级
            raise Exception('sandbox_permissions is not available in this composition (no sandboxing filesystem to escalate)')#无隔离文件系统可升级
        审批上下文={#审批上下文
            'approver':自身.上下文.get('approval'),#审批服务
            'agent':智能体,#调用方agent
            'callId':取字段(执行,'callId'),#此次调用id
            'toolName':工具名,#工具名
            'signal':试取(执行,'signal'),#取消信号
        }#审批上下文结束
        批准模式=解开(批准升级(#走审批得到更宽模式
            {'requestedMode':取字段(参数,'sandbox_permissions'),'justification':取字段(参数,'justification'),'effectiveMode':取字段(常驻政策,'mode'),'subject':'operation'},#升级请求
            审批上下文,#审批上下文
        ))#审批结束
        已批=dict(常驻政策)#拷贝常驻策略
        已批['mode']=批准模式#用批准模式覆盖
        return 已批#覆盖后的策略

    def 映射错误(自身,错误,政策):#把沙箱拒绝映射为面向模型的标记错误
        """为模型映射抛出的提供方错误：FS_SANDBOX_DENIED 变成共享 [sandbox: …] 拒绝标记加上本回合升级提示的 FsError，使策略拒绝读起来与 bash 相同，同时保留结构化码。其他错误原样穿过。FS_SANDBOX_DENIED 只在隔离后端下出现，而隔离后端总是广告升级字段，因此此处提示总是适用。"""
        if (not isinstance(错误,fs.文件系统错误)) or 错误.code!='FS_SANDBOX_DENIED':#非沙箱拒绝
            return 错误#原样返回
        # FS_SANDBOX_DENIED 只在隔离后端下出现，其工具路径在变更前总会解析出策略。
        模式=取字段(政策,'mode')#取出拒绝时的模式
        return fs.文件系统错误(沙箱拒绝标记(模式)+'\n'+升级提示标记('operation'),'FS_SANDBOX_DENIED',{'cause':错误})#拼接拒绝标记与升级提示
