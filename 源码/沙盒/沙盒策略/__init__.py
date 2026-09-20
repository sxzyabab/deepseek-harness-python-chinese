"""沙箱政策服务：部署回落与按会话解析的唯一所有者。

拥有文件效果 SandboxMode、`workspace-write` 根，以及覆盖套件（`sandbox/mode` 事件、折叠与写入路径，见会话模式）。每次智能体请求前把已解析政策写入可缓存的运行时上下文快照；智能体循环记入模型历史，回放时强制同一模式与根，不改写稳定系统提示词。

文件系统、一次性 bash 与终端后端在此读同一份已解析政策。上下文只描述政策，各后端保留自己的强制方言，各工具拥有操作级拒绝与升级指引。服务在每个操作边界读一次会话状态；执行器与提供方保持无会话。
"""
import json#工作区根写入模型可见字面量
import os#进程 cwd 回落
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 字符串字段,枚举字段#配置字段
服务=cordis.服务#Cordis 服务基类
from .会话模式 import (#覆盖套件
    沙盒模式表,#合法模式表
    生效沙盒模式,#折叠
    设沙盒模式,#写入
)#会话模式导出结束

名称='sandbox-policy'#Cordis 插件名（包目录用下划线，插件名保留上游连字符）

class 沙箱政策错误(Exception):
    """沙箱政策包的异常基类。"""

def 解析工作区根(路径):
    """保留执行世界拼写；强制提供方在其宿主上解析文件系统身份。"""
    if not os.path.isabs(路径):#必须绝对
        raise 沙箱政策错误('sandbox-policy: workspace root must be an absolute execution-world path')#非法相对根
    return 路径#原样拼写

def 渲染政策上下文(政策):
    """渲染政策，不声称挂载了哪些能力。政策是 dict。模型可见字面量不翻译。"""
    模式值=政策['mode']#取出模式
    if 模式值=='read-only':#只读
        return ('Current DSH file policy: read-only. Any available operation enforced by the DSH file sandbox '#只读政策前半
            +'cannot modify files in the standing mode. Do not refuse a required modification from this policy alone: '#站立模式不可改；勿仅凭政策拒改
            +'try an available tool normally and follow any denial and escalation guidance it returns.')#只读说明
    if 模式值=='workspace-write':#工作区可写
        return ('Current DSH file policy: workspace-write. Any available operation enforced by the DSH file sandbox '#工作区可写政策前半
            +'may modify files under the session workspace: '#可改会话工作区下文件
            +json.dumps(政策['workspaceRoot'],ensure_ascii=False,separators=(',',':'),allow_nan=False)#工作区根 JSON 字面量
            +'. Some platform temporary areas may also be writable.')#工作区可写说明
    if 模式值=='danger-full-access':#完全放开
        return ('Current DSH file policy: danger-full-access. The DSH file sandbox does not restrict file '#完全放开政策前半
            +'modifications by available operations.')#完全放开说明
    raise 沙箱政策错误('unreachable sandbox mode: '+str(模式值))#封闭联合穷尽守卫

配置模式={#插件配置：部署的沙箱默认；全部可选——Config 提供默认
    'mode':枚举字段('read-only','workspace-write','danger-full-access',默认值='read-only'),#会话起步的文件沙箱模式（失败即安全默认）
    'workspaceRoot':字符串字段(),#无智能体调用与没有 cwd 的会话的回落根；模式无默认，构造里回落进程 cwd
}#配置模式结束

沙箱政策请求字段=('session','mode')#为一次能力调用选择沙箱政策的输入字段

class 沙箱政策服务(服务):
    """拥有部署默认模式、回落工作区根，以及当前请求时政策段。"""
    Config=配置模式#静态配置模式
    def __init__(自身,ctx,配置):
        """记下部署默认，并把已解析政策贡献进系统提示词运行时上下文。配置是 dict。"""
        super().__init__(ctx,'sandboxPolicy')#服务名 sandboxPolicy
        自身.配置=配置#插件配置
        if 'mode' in 配置 and 配置['mode'] is not None and 配置['mode']!='':#配置给了模式；空串回落只读（原 ||）
            自身.defaultMode=配置['mode']#记下默认模式
        else:
            自身.defaultMode='read-only'#失败即安全默认
        if 'workspaceRoot' in 配置 and 配置['workspaceRoot'] is not None:#配置给了根
            自身.workspaceRoot=解析工作区根(配置['workspaceRoot'])#解析回落根
        else:
            自身.workspaceRoot=解析工作区根(os.getcwd())#回落进程 cwd
        def 挂提示(提示上下文,*位置参数):
            """登记政策上下文段。"""
            def 文本(组装上下文):
                """按调用会话渲染政策；没有会话则不贡献。组装上下文是 dict。"""
                if 'agent' not in 组装上下文 or 组装上下文['agent'] is None:#没有智能体
                    return ''#不贡献
                会话=组装上下文['agent'].session#调用会话
                if 会话 is None:#没有会话
                    return ''#不贡献
                return 渲染政策上下文(自身.解析({'session':会话}))#渲染该会话政策
            提示上下文.systemPrompt.context({#注册政策上下文段
                'name':'sandbox:policy',#段名
                'order':110,#排序
                'text':文本,#按请求渲染
            })#context 结束
        自身.ctx.依赖启动(['systemPrompt'],挂提示)#有系统提示词时贡献

    def 解析(自身,请求=None):
        """为一次能力调用解析完整政策。请求是 dict。"""
        if 请求 is None:#缺省空请求
            请求={}#空映射
        会话=请求['session'] if 'session' in 请求 else None#调用会话
        批准模式=请求['mode'] if 'mode' in 请求 else None#显式已批准模式
        if 批准模式 is not None:#批准优先
            模式值=批准模式#用批准
        elif 会话 is None:#无会话则无覆盖
            模式值=自身.defaultMode#部署默认
        else:
            覆盖=自身.覆盖于(会话)#读日志覆盖
            模式值=覆盖 if 覆盖 is not None else 自身.defaultMode#覆盖或默认
        if 会话 is not None:#有会话
            头=会话.header#会话头 dict
            cwd=头['cwd'] if 'cwd' in 头 else None#不可变 cwd
        else:
            cwd=None#无会话
        政策={#拼政策
            'mode':模式值,#按次模式
            'workspaceRoot':解析工作区根(cwd if cwd is not None else 自身.workspaceRoot),#会话 cwd 或回落根
        }#政策字段结束
        if 会话 is not None:#有会话才带会话 id
            政策['sessionId']=会话.id#会话 id
        return 政策#完全解析的按次模式与绝对工作区根

    def 覆盖于(自身,会话):
        """读会话覆盖，不应用部署默认。会话是对象。"""
        return 生效沙盒模式(会话.events)#折叠日志

__all__=[#仅中文公开名
    '名称','配置模式','沙箱政策服务','沙箱政策请求字段','沙箱政策错误',
    '生效沙盒模式','设沙盒模式','沙盒模式表','解析工作区根','渲染政策上下文',
]#结束
name=名称#Cordis 插件名
Config=配置模式#Cordis 配置模式
default=沙箱政策服务#Cordis 默认导出
