"""发现、挂载与消费方共用的智能体预设词汇。

对齐上游 `agent-presets/src/preset.ts`。公开面仅中文名。
"""
import re#预设 id 文法

__all__=[#仅中文公开名
    '预设标识规则','未知预设错误','预设挂载错误',
]#公开面结束

预设标识规则=re.compile(r'^[a-z0-9][a-z0-9-]*$')#预设目录名文法

class 未知预设错误(Exception):#未知预设
    """没有任何已配置根提供所请求的预设。"""
    def __init__(自身,预设标识,可用):#构造
        """记下请求 id 与可用列表。"""
        super().__init__('agent-presets: preset "'+预设标识+'" not found (available: '+(', '.join(可用) if 可用 else 'none')+')')#诊断
        自身.presetId=预设标识#请求的 id
        自身.available=list(可用)#可用 id

class 预设挂载错误(Exception):#预设挂载失败
    """预设存在但其组合无法安装。"""
    def __init__(自身,预设标识,原因,原因链=None):#构造
        """记下失败预设与原因。"""
        super().__init__('agent-presets: preset "'+预设标识+'" failed to mount: '+原因)#诊断
        自身.presetId=预设标识#失败的预设 id
        自身.reason=原因#失败原因
        if 原因链 is not None:#链式原因
            自身.__cause__=原因链#挂上
