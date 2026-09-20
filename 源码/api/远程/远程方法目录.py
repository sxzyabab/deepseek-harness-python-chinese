"""所选 Remote 贡献的方法目录与贡献对象。

挂载序：agentPresets → commands → settings →
goals → llm → dynamic → plugin-inventory → message-feedback → session-feedback →
file-uploads → session-reference → subagents → session → workspace → workspaceFiles。
完整 InvocationDescriptor 见各叶包 `远程.py`。
"""
from ...预设.智能体预设.远程 import 远程贡献表 as 智能体预设远程#agent-presets
from ...交互.命令.远程 import 远程贡献表 as 命令远程#commands
from ...api.设置控制器.远程 import 远程贡献表 as 设置控制器远程#settings
from ...目标.目标.远程 import 远程贡献表 as 目标远程#goals
from ...模型后端.llm.远程 import 远程贡献表 as 大模型远程#llm
from ...拓展.cordis服务端.远程 import 远程贡献表 as 动态远程#dynamic
from ...宿主.插件清单.远程 import 远程贡献表 as 插件清单远程#plugin-inventory
from ...反馈.消息反馈.远程 import 远程贡献表 as 消息反馈远程#message-feedback
from ...反馈.命令_反馈.远程 import 远程贡献表 as 会话反馈远程#command-feedback
from ...客户端.文件上传.远程 import 远程贡献表 as 文件上传远程#file-upload
from ...上下文.会话引用.远程 import 远程贡献表 as 会话引用远程#session-reference
from ...子智能体.子智能体.远程 import 远程贡献表 as 子智能体远程#subagent
from ...api.会话控制器.远程 import 远程贡献表 as 会话远程#session
from ...api.工作区控制器.远程 import 远程贡献表 as 工作区远程#workspace
from ...api.工作区文件.远程 import 远程贡献表 as 工作区文件远程#workspace-files

__all__=['所选远程目录','包名元组','导出名元组','所选远程贡献','核对目录与贡献']#仅中文公开名

所选远程目录=(#上游 client 挂载顺序
    {#agent-presets
        'package':'@deepseek-ai/dsh-agent-presets',
        'service':'agentPresets','namespace':'agentPresets',
        'methods':(
            {'export':'list','implementation':'remoteExportList','invocation':'direct'},
            {'export':'read','invocation':'direct'},
            {'export':'copy','invocation':'direct'},
            {'export':'deletePreset','invocation':'direct'},
            {'export':'select','invocation':'direct'},
        ),
        'contribution':智能体预设远程,
    },
    {#commands
        'package':'@deepseek-ai/dsh-commands',
        'service':'commands','namespace':'commands',
        'methods':(
            {'export':'list','implementation':'list','invocation':'direct','scope':'agent'},
            {'export':'execute','implementation':'execute','invocation':'direct','scope':'agent','cancellation':'signal'},
        ),
        'contribution':命令远程,
    },
    {#settings-controller（含 credentials）
        'package':'@deepseek-ai/dsh-api-settings-controller',
        'service':'settingsController','namespace':'settings',
        'methods':(
            {'export':'describe','invocation':'direct'},
            {'export':'canOpenAgentPresetDirectory','invocation':'direct'},
            {'export':'update','invocation':'direct'},
            {'export':'replace','invocation':'direct'},
            {'export':'mutate','invocation':'direct'},
            {'export':'openSettingsDocument','invocation':'direct','cancellation':'signal'},
            {'export':'openAgentPresetDirectory','invocation':'direct','cancellation':'signal'},
            {'export':'describe','invocation':'direct','namespace':'credentials'},
            {'export':'set','invocation':'direct','namespace':'credentials'},
            {'export':'unset','invocation':'direct','namespace':'credentials'},
        ),
        'contribution':设置控制器远程,
    },
    {#goals
        'package':'@deepseek-ai/dsh-goal',
        'service':'goals','namespace':'goals',
        'methods':(
            {'export':'create','implementation':'远程创建','invocation':'direct','scope':'agent'},
            {'export':'edit','implementation':'编辑','invocation':'direct','scope':'agent'},
            {'export':'pause','implementation':'暂停','invocation':'direct','scope':'agent'},
            {'export':'resume','implementation':'恢复','invocation':'direct','scope':'agent'},
            {'export':'complete','implementation':'完成','invocation':'direct','scope':'agent'},
            {'export':'clear','implementation':'清除','invocation':'direct','scope':'agent'},
        ),
        'contribution':目标远程,
    },
    {#llm
        'package':'@deepseek-ai/dsh-llm',
        'service':'llm','namespace':'llm',
        'methods':(
            {'export':'listProviders','invocation':'direct'},
            {'export':'listConfigurableProviders','invocation':'direct'},
            {'export':'discoverModels','implementation':'remoteDiscoverModels','invocation':'direct','cancellation':'signal'},
        ),
        'contribution':大模型远程,
    },
    {#dynamic cordis-host-runner
        'package':'@deepseek-ai/dsh-cordis-host-runner',
        'service':'dynamicCordisRunner','namespace':'dynamicCordisRunner',
        'methods':(
            {'export':'undefineFromPanel','invocation':'direct','scope':'agent'},
            {'export':'runHostHalf','invocation':'direct','scope':'agent'},
            {'export':'getClientCode','invocation':'direct','scope':'agent'},
            {'export':'resolveRequestRun','invocation':'direct'},
            {'export':'settleUserRun','invocation':'direct','scope':'agent'},
            {'export':'stopFromPanel','invocation':'direct','scope':'agent'},
            {'export':'syncInspectManifest','invocation':'direct'},
            {'export':'resolveInspectQuery','invocation':'direct','scope':'agent'},
            {'export':'inventory','invocation':'direct'},
            {'export':'reportRenderFailure','invocation':'direct','scope':'agent'},
            {'export':'reportClientGuardFailure','invocation':'direct','scope':'agent'},
            {'export':'invoke','invocation':'direct'},
        ),
        'contribution':动态远程,
    },
    {#plugin-inventory
        'package':'@deepseek-ai/dsh-host-plugin-inventory',
        'service':'pluginInventory','namespace':'pluginInventory',
        'methods':(
            {'export':'list','implementation':'list','invocation':'direct'},
        ),
        'contribution':插件清单远程,
    },
    {#message-feedback
        'package':'@deepseek-ai/dsh-message-feedback',
        'service':'messageFeedback','namespace':'messageFeedback',
        'methods':(
            {'export':'list','implementation':'list','invocation':'direct'},
            {'export':'put','implementation':'put','invocation':'direct'},
            {'export':'delete','implementation':'delete','invocation':'direct'},
        ),
        'contribution':消息反馈远程,
    },
    {#command-feedback / sessionFeedback
        'package':'@deepseek-ai/dsh-command-feedback',
        'service':'sessionFeedback','namespace':'sessionFeedback',
        'methods':(
            {'export':'record','implementation':'record','invocation':'direct'},
        ),
        'contribution':会话反馈远程,
    },
    {#file-upload
        'package':'@deepseek-ai/dsh-client-file-upload',
        'service':'fileUploads','namespace':'fileUploads',
        'methods':(
            {'export':'upload','implementation':'上传','invocation':'direct','scope':'agent','cancellation':'signal'},
        ),
        'contribution':文件上传远程,
    },
    {#session-reference
        'package':'@deepseek-ai/dsh-session-reference',
        'service':'sessionReferenceResolver','namespace':'sessionReferenceResolver',
        'methods':(
            {'export':'candidates','implementation':'remoteExportCandidates','invocation':'direct','scope':'agent','cancellation':'signal'},
        ),
        'contribution':会话引用远程,
    },
    {#subagent
        'package':'@deepseek-ai/dsh-subagent',
        'service':'subagents','namespace':'subagents',
        'methods':(
            {'export':'list','implementation':'remoteExportList','invocation':'direct','cancellation':'signal'},
            {'export':'prompt','invocation':'direct','cancellation':'signal'},
            {'export':'interruptByParent','invocation':'direct'},
        ),
        'contribution':子智能体远程,
    },
    {#session-controller（含 skills / fileReferences）
        'package':'@deepseek-ai/dsh-api-session-controller',
        'service':'sessionController','namespace':'session',
        'methods':(
            {'export':'list','invocation':'direct','cancellation':'signal'},
            {'export':'search','invocation':'direct','cancellation':'signal'},
            {'export':'create','invocation':'direct'},
            {'export':'selectModel','invocation':'direct'},
            {'export':'modelCatalog','invocation':'direct'},
            {'export':'canOpenWorkspacePath','invocation':'direct'},
            {'export':'openWorkspacePath','invocation':'direct','cancellation':'signal'},
            {'export':'rename','invocation':'direct'},
            {'export':'fork','invocation':'direct'},
            {'export':'prompt','invocation':'direct','cancellation':'signal'},
            {'export':'attachment','invocation':'direct'},
            {'export':'updateQueue','invocation':'direct'},
            {'export':'cancel','invocation':'direct'},
            {'export':'page','invocation':'direct','cancellation':'signal'},
            {'export':'follow','invocation':'stream','cancellation':'signal'},
            {'export':'control','invocation':'stream','cancellation':'signal'},
            {'export':'list','invocation':'direct','namespace':'skills','cancellation':'signal'},
            {'export':'list','invocation':'direct','namespace':'fileReferences','scope':'agent','cancellation':'signal'},
        ),
        'contribution':会话远程,
    },
    {#workspace-controller（含 directoryPicker）
        'package':'@deepseek-ai/dsh-api-workspace-controller',
        'service':'workspaceController','namespace':'workspace',
        'methods':(
            {'export':'create','invocation':'direct'},
            {'export':'rename','invocation':'direct'},
            {'export':'delete','invocation':'direct'},
            {'export':'insertBefore','invocation':'direct'},
            {'export':'insertSessionBefore','invocation':'direct'},
            {'export':'archiveSession','invocation':'direct'},
            {'export':'follow','invocation':'stream','cancellation':'signal'},
            {'export':'pick','invocation':'direct','namespace':'directoryPicker','cancellation':'signal'},
            {'export':'list','invocation':'direct','namespace':'directoryPicker','cancellation':'signal'},
            {'export':'createDirectory','invocation':'direct','namespace':'directoryPicker'},
        ),
        'contribution':工作区远程,
    },
    {#workspace-files
        'package':'@deepseek-ai/dsh-api-workspace-files',
        'service':'workspaceFiles','namespace':'workspaceFiles',
        'methods':(
            {'export':'read','invocation':'direct','cancellation':'signal'},
            {'export':'readBytes','invocation':'direct','cancellation':'signal'},
            {'export':'readAll','invocation':'direct','cancellation':'signal'},
            {'export':'readRelated','invocation':'direct','cancellation':'signal'},
            {'export':'stat','invocation':'direct','cancellation':'signal'},
            {'export':'list','invocation':'direct','cancellation':'signal'},
            {'export':'changes','invocation':'stream','cancellation':'signal'},
        ),
        'contribution':工作区文件远程,
    },
)#目录结束

包名元组=tuple(项['package'] for 项 in 所选远程目录)#包名

导出名元组=tuple(#扁平导出名，按挂载序
    方法['export'] for 项 in 所选远程目录 for 方法 in 项['methods']
)#结束

所选远程贡献=(#与目录同序的贡献对象元组
    智能体预设远程,命令远程,设置控制器远程,目标远程,大模型远程,动态远程,
    插件清单远程,消息反馈远程,会话反馈远程,文件上传远程,会话引用远程,
    子智能体远程,会话远程,工作区远程,工作区文件远程,
)#贡献结束

def 核对目录与贡献():#目录方法数与贡献描述符数对齐
    """返回 [(package, 目录方法数, 描述符数), ...]；不一致时仍返回事实供调用方断言。"""
    出=[]#结果
    for 项 in 所选远程目录:#逐包
        贡献=项['contribution']#贡献
        描述符列表=贡献.get('descriptors') if isinstance(贡献,dict) else getattr(贡献,'descriptors',None)#描述符
        if 描述符列表 is None and isinstance(贡献,dict):#可能嵌套
            描述符列表=贡献.get('descriptors') or []#缺省空
        数=len(描述符列表) if 描述符列表 is not None else 0#描述符数
        出.append((项['package'],len(项['methods']),数))#一行
    return 出#事实表
