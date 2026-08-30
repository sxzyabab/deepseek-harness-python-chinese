"""所选五份 Remote 贡献的方法目录与贡献对象（自上游 @Remote 清单与叶包抽出）。

对齐 `api/remotes/src/client/index.ts` 挂载序：commands → goals → dynamic →
plugin-inventory → message-feedback。公开面仅中文名。
完整 InvocationDescriptor（strict schema/codec）见各叶包 `远程.py`；
本目录承载包名/服务键/导出名，并再导出叶包 TYPERT_REMOTE 供组装面核对。
"""
from ...交互.指令.远程 import TYPERT_REMOTE as 命令远程#commands 贡献
from ...目标.目标.远程 import TYPERT_REMOTE as 目标远程#goals 贡献
from ...拓展.cordis_服务端.远程 import TYPERT_REMOTE as 动态远程#dynamic 贡献
from ...host.plugin_inventory.远程 import TYPERT_REMOTE as 插件清单远程#plugin-inventory 贡献
from ...反馈.消息反馈.远程 import TYPERT_REMOTE as 消息反馈远程#message-feedback 贡献

__all__=['所选远程目录','包名们','导出名们','所选远程贡献','核对目录与贡献']#仅中文公开名

所选远程目录=(#上游 client 挂载顺序
    {#commands
        'package':'@deepseek-ai/dsh-commands',
        'service':'commands',
        'namespace':'commands',
        'methods':(
            {'export':'list','implementation':'list','invocation':'direct','scope':'agent'},
            {'export':'execute','implementation':'execute','invocation':'direct','scope':'agent','cancellation':'signal'},
        ),
        'contribution':命令远程,#叶包贡献对象
    },
    {#goals
        'package':'@deepseek-ai/dsh-goal',
        'service':'goals',
        'namespace':'goals',
        'methods':(
            {'export':'create','implementation':'远程创建','invocation':'direct','scope':'agent'},
            {'export':'edit','implementation':'编辑','invocation':'direct','scope':'agent'},
            {'export':'pause','implementation':'暂停','invocation':'direct','scope':'agent'},
            {'export':'resume','implementation':'恢复','invocation':'direct','scope':'agent'},
            {'export':'complete','implementation':'完成','invocation':'direct','scope':'agent'},
            {'export':'clear','implementation':'清除','invocation':'direct','scope':'agent'},
        ),
        'contribution':目标远程,#叶包贡献对象
    },
    {#dynamic cordis-host-runner（服务键为 dynamicCordisRunner）
        'package':'@deepseek-ai/dsh-cordis-host-runner',
        'service':'dynamicCordisRunner',
        'namespace':'dynamicCordisRunner',
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
        'contribution':动态远程,#叶包贡献对象
    },
    {#plugin-inventory
        'package':'@deepseek-ai/dsh-host-plugin-inventory',
        'service':'pluginInventory',
        'namespace':'pluginInventory',
        'methods':(
            {'export':'list','implementation':'list','invocation':'direct'},
        ),
        'contribution':插件清单远程,#叶包贡献对象
    },
    {#message-feedback
        'package':'@deepseek-ai/dsh-message-feedback',
        'service':'messageFeedback',
        'namespace':'messageFeedback',
        'methods':(
            {'export':'list','implementation':'list','invocation':'direct'},
            {'export':'put','implementation':'put','invocation':'direct'},
            {'export':'delete','implementation':'delete','invocation':'direct'},
        ),
        'contribution':消息反馈远程,#叶包贡献对象
    },
)#目录结束

包名们=tuple(项['package'] for 项 in 所选远程目录)#五包名

导出名们=tuple(#扁平导出名，按挂载序
    方法['export'] for 项 in 所选远程目录 for 方法 in 项['methods']
)#结束

所选远程贡献=(#与目录同序的贡献对象元组
    命令远程,目标远程,动态远程,插件清单远程,消息反馈远程,
)#贡献结束

def 核对目录与贡献():#目录方法数与贡献描述符数对齐
    """返回 [(package, 目录方法数, 描述符数), ...]；不一致时仍返回事实供调用方断言。"""
    出=[]#结果
    for 项 in 所选远程目录:#逐包
        贡献=项['contribution']#贡献
        描述符们=贡献.get('descriptors') if isinstance(贡献,dict) else getattr(贡献,'descriptors',None)#描述符
        if 描述符们 is None and isinstance(贡献,dict):#可能嵌套
            描述符们=贡献.get('descriptors') or []#缺省空
        数=len(描述符们) if 描述符们 is not None else 0#描述符数
        出.append((项['package'],len(项['methods']),数))#一行
    return 出#事实表
