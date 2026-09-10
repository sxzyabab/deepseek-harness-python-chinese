"""对已加载 Session 表面的仅系统提示不可变解释。

对齐上游 `ui-conversation/src/client/contract/system-prompt.ts`。公开面仅中文名。
状态与事件为 dict；替换映射为 dict。
"""
from .....内核.会话 import 是否表面事件#是否表面事件

__all__=['检视系统提示']#仅中文公开名

# 系统提示节点形（对齐 SystemPromptNode）：seq/time/turn/step/text/update
# 系统提示状态形：firstSeq/uncertain/nodes/replacements/effective/introduced
# nodes 项为 {position, node}

def 检视系统提示(先前,事件):
    """应用系统事件或位置替换，不保留普通消息。

    替换位置继承其起点端点，而非时间序 seq。
    更早端点顺序未知时扣住提示，直到前置回放解析。
    先前为上一相关事件处的解释（dict 或 None）；事件为已接纳的会话事件 dict。
    """
    操作=事件['surfaceOp'] if 是否表面事件(事件) and 'surfaceOp' in 事件 else None#表面操作
    首序号=先前['firstSeq'] if 先前 is not None and 'firstSeq' in 先前 else 事件['seq']#首相关序号
    节点表=list(先前['nodes']) if 先前 is not None and 'nodes' in 先前 else []#节点表
    替换=dict(先前['replacements']) if 先前 is not None and 'replacements' in 先前 else {}#替换映射
    def 未知端点(序号):
        """序号早于首相关且未登记替换。"""
        return 序号<首序号 and 序号 not in 替换#未知端点
    先前不确定=先前 is not None and 'uncertain' in 先前 and 先前['uncertain'] is True#先前不确定
    本次不确定=操作 is not None and 操作!='append' and (未知端点(操作['startSeq']) or 未知端点(操作['endSeq']))#本次
    不确定=先前不确定 or 本次不确定#是否不确定
    if 不确定:#不确定态
        return {'firstSeq':首序号,'uncertain':True,'nodes':[],'replacements':{},'effective':None,'introduced':None}#不确定
    位置=事件['seq']#默认表面位置
    if 操作 is not None and 操作!='append':#替换
        位置=替换[操作['startSeq']] if 操作['startSeq'] in 替换 else 操作['startSeq']#继承起点位置
        终点=替换[操作['endSeq']] if 操作['endSeq'] in 替换 else 操作['endSeq']#终点位置
        节点表=[项 for 项 in 节点表 if 项['position']<位置 or 项['position']>终点]#剪影
        保留={键:值 for 键,值 in 替换.items() if 值<位置 or 值>终点}#保留映射
        保留[事件['seq']]=位置#登记本次替换
        替换=保留#写回
    引入=None#本事件引入
    if 事件['type']=='system/message':#系统消息
        数据=事件['data']#载荷
        消息=数据['message']#消息
        内容=消息['content'] if 'content' in 消息 else []#块表
        文本=''.join(块['text'] for 块 in 内容 if isinstance(块,dict) and 'type' in 块 and 块['type']=='text' and 'text' in 块)#文本
        有非空=先前 is not None and 'nodes' in 先前 and any(项['node']['text']!='' for 项 in 先前['nodes'])#曾有非空
        引入={#节点
            'seq':事件['seq'],#序号
            'time':事件['time'],#时间
            'turn':数据['turn'],#回合
            'step':数据['step'],#步骤
            'text':文本,#文本
            'update':操作=='append' and 有非空 is True,#是否更新卡
        }#引入结束
        节点表=节点表+[{'position':位置,'node':引入}]#插入
        节点表=sorted(节点表,key=lambda 项:项['position'])#排序
    存活=None#存活非空
    for 项 in reversed(节点表):#自后向前
        if 项['node']['text']!='':#非空
            存活=项['node']#记下
            break#停
    先前存活=None#先前存活
    if 先前 is not None and 'nodes' in 先前:#有先前节点
        for 项 in reversed(先前['nodes']):#自后向前
            if 项['node']['text']!='':#非空
                先前存活=项['node']#记下
                break#停
    if 存活 is 先前存活:#未变则沿用
        有效=先前['effective'] if 先前 is not None and 'effective' in 先前 else None#沿用
    elif 引入 is not None and 引入 is 存活:#本事件即有效
        有效=引入#有效
    else:#派生有效态
        有效={#派生
            'seq':事件['seq'],
            'time':事件['time'],
            'turn':存活['turn'] if 存活 is not None and 'turn' in 存活 else 0,
            'step':存活['step'] if 存活 is not None and 'step' in 存活 else 0,
            'text':存活['text'] if 存活 is not None and 'text' in 存活 else '',
            'update':False,
        }#派生结束
    return {'firstSeq':首序号,'uncertain':False,'nodes':节点表,'replacements':替换,'effective':有效,'introduced':引入}#状态
