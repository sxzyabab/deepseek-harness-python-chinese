"""沙箱政策所在（`ctx.sandboxPolicy`）：部署沙箱回落与按会话解析的唯一所有者：文件效果 SandboxMode、`workspace-write` 根，以及覆盖套件（`sandbox/mode` 事件、其折叠与写入路径，来自 `会话模式`）。每次智能体请求之前，所有者还把已解析政策贡献进缓存安全的运行时上下文快照。智能体循环把该快照记为模型历史，因此回放重建强制消费方解析的同一模式与根，而不改写稳定系统提示词。

强制文件系统、一次性 bash 与终端后端在这里读同一份已解析政策。上下文描述该政策而不清点能力，每个后端保留自己的强制方言，每个工具拥有其操作特定的拒绝与升级指引。服务在每个操作边界读一次会话状态；执行器与提供方保持无会话。
"""
import json#工作区根写入模型可见字面量
import os#进程 cwd 回落
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 字符串字段,枚举字段#配置字段
服务=cordis.服务#Cordis 服务基类
from ..沙盒 import 规范路径#导入规范路径
from .会话模式 import (#覆盖套件
    沙盒模式表,#合法模式表
    生效沙盒模式,#折叠
    设沙盒模式,#写入
)#会话模式导出结束

名称='sandbox-policy'#Cordis 插件名（包目录用下划线，插件名保留上游连字符）
name=名称#Cordis 插件名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解析工作区根(路径):#解析工作区根
    """在词法归一化抹掉对符号链接敏感的分量之前解析文件系统身份。"""
    return os.path.abspath(规范路径(路径))#先规范再词法绝对化

def 渲染政策上下文(政策):#渲染面向模型的政策上下文
    """渲染政策，不声称挂载了哪些能力。模型可见字面量不翻译。"""
    模式值=取字段(政策,'mode')#取出模式
    if 模式值=='read-only':#只读
        return ('Current DSH file policy: read-only. Any available operation enforced by the DSH file sandbox '#只读政策前半
            +'cannot modify files in the standing mode. Do not refuse a required modification from this policy alone: '#站立模式不可改；勿仅凭政策拒改
            +'try an available tool normally and follow any denial and escalation guidance it returns.')#只读说明
    if 模式值=='workspace-write':#工作区可写
        return ('Current DSH file policy: workspace-write. Any available operation enforced by the DSH file sandbox '#工作区可写政策前半
            +'may modify files under the session workspace: '#可改会话工作区下文件
            +json.dumps(取字段(政策,'workspaceRoot'),ensure_ascii=False)#工作区根 JSON 字面量
            +'. Some platform temporary areas may also be writable.')#工作区可写说明
    if 模式值=='danger-full-access':#完全放开
        return ('Current DSH file policy: danger-full-access. The DSH file sandbox does not restrict file '#完全放开政策前半
            +'modifications by available operations.')#完全放开说明
    raise Exception('unreachable sandbox mode: '+str(模式值))#封闭联合穷尽守卫

配置模式={#插件配置：部署的沙箱默认；全部可选——Config 提供默认
    'mode':枚举字段('read-only','workspace-write','danger-full-access',默认值='read-only'),#会话起步的文件沙箱模式（失败即安全默认）
    'workspaceRoot':字符串字段(),#无智能体调用与没有 cwd 的会话的回落根；模式无默认，构造里回落进程 cwd
}#配置模式结束
Config=配置模式#Cordis 配置模式

沙箱政策请求字段=('session','mode')#为一次能力调用选择沙箱政策的输入字段

class 沙箱政策服务(服务):#沙箱政策服务（ctx.sandboxPolicy）
    """拥有部署默认模式、回落工作区根，以及当前请求时政策段。工具层为每次执行调用 resolve，使会话的模式日志与不可变 cwd 一起到达每个强制能力。"""
    Config=配置模式#静态配置模式
    def __init__(自身,ctx,配置):#安装 sandboxPolicy 服务
        """记下部署默认，并把已解析政策贡献进系统提示词运行时上下文。"""
        super().__init__(ctx,'sandboxPolicy')#服务名 sandboxPolicy
        自身.config=配置#插件配置
        自身.配置=配置#中文别名
        #schemastery（Config）已经填了 mode；workspaceRoot 没有模式默认，因此回落到进程 cwd 是真分支，两种情况都解析成绝对路径
        自身.defaultMode=取字段(配置,'mode') or 'read-only'#记下默认模式
        自身.默认模式=自身.defaultMode#中文别名
        自身.workspaceRoot=解析工作区根(取字段(配置,'workspaceRoot') if 取字段(配置,'workspaceRoot') is not None else os.getcwd())#解析回落根
        自身.工作区根=自身.workspaceRoot#中文别名
        def 挂提示(提示上下文,*其余):#有系统提示词时贡献上下文
            """登记政策上下文段。"""
            def 文本(组装上下文):#按请求渲染
                """按调用会话渲染政策；没有会话则不贡献。"""
                智能体=取字段(组装上下文,'agent')#组装时的智能体
                会话=取字段(智能体,'session')#调用会话
                if 会话 is None:#没有会话
                    return ''#不贡献
                return 渲染政策上下文(自身.解析({'session':会话}))#渲染该会话政策
            提示上下文.systemPrompt.context({#注册政策上下文段
                'name':'sandbox:policy',#段名
                'order':110,#排序
                'text':文本,#按请求渲染
            })#context 结束
        自身.ctx.inject(['systemPrompt'],挂提示)#有系统提示词时贡献

    def 解析(自身,请求=None):#解析按次政策
        """为一次能力调用解析完整政策。已批准的显式模式优先于会话最后一条 `sandbox/mode` 事件，后者优先于部署默认。会话 cwd 是其 workspace-write 边界；配置根是无智能体调用与没有 cwd 的会话的回落。"""
        if 请求 is None:#缺省空请求
            请求={}#空映射
        会话=取字段(请求,'session')#调用会话
        批准模式=取字段(请求,'mode')#显式已批准模式
        if 批准模式 is not None:#批准优先
            模式值=批准模式#用批准
        elif 会话 is None:#无会话则无覆盖
            模式值=自身.defaultMode#部署默认
        else:#有会话
            覆盖=自身.覆盖于(会话)#读日志覆盖
            模式值=覆盖 if 覆盖 is not None else 自身.defaultMode#覆盖或默认
        头=取字段(会话,'header') if 会话 is not None else None#会话头
        cwd=取字段(头,'cwd')#不可变 cwd
        政策={#拼政策
            'mode':模式值,#按次模式
            'workspaceRoot':解析工作区根(cwd if cwd is not None else 自身.workspaceRoot),#会话 cwd 或回落根
        }#政策字段结束
        if 会话 is not None:#有会话才带会话 id
            政策['sessionId']=取字段(会话,'id')#会话 id
        return 政策#完全解析的按次模式与绝对工作区根

    def 覆盖于(自身,会话):#读会话覆盖
        """读会话覆盖，不应用部署默认。返回最后一次记下的模式；没有则为 None。"""
        return 生效沙盒模式(取字段(会话,'events'))#折叠日志

default=沙箱政策服务#Cordis 默认导出
默认=沙箱政策服务#中文默认导出

__all__=[#公开面
    '名称','name','配置模式','Config','沙箱政策服务','沙箱政策请求字段',
    '生效沙盒模式','设沙盒模式','沙盒模式表','解析工作区根','渲染政策上下文',
    '默认','default',
]#结束
