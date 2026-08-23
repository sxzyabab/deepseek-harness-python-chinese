"""共享的助手步骤计时折叠。

对齐上游 `runtime/src/client/sessions/assistant-timing.ts`。公开面仅中文名。
聊天定义与轨迹历史折叠从同一条 step/start → 首个 token 增量 → assistant/message 序列派生计时。
"""
from ....模型后端.llm import 是否词增量#导入 token 增量谓词

__all__=['是否词增量','助手步骤键','索引助手步骤计时','落定助手计时']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 助手步骤键(回合,步骤):#步骤键
    """一个助手步骤的复合映射键。

    @param 回合 - 事件载荷里的回合号。
    @param 步骤 - 事件载荷里的步骤号。
    @returns 无碰撞的 turn/step 键（NUL 分隔）。
    """
    return str(回合)+'\u0000'+str(步骤)#回合与步骤用 NUL 拼接

def 索引助手步骤计时(步骤表,事件):#索引步骤计时
    """把一条事件折进逐步计时索引。

    step/start 打开条目，第一个非空 token 增量只盖一次首 token 时间。其它事件类型空操作。
    @param 步骤表 - 可变逐步索引，键为 助手步骤键。
    @param 事件 - 原始窗口事件。
    """
    类型=取字段(事件,'type')#事件类型
    数据=取字段(事件,'data')#载荷
    if 类型=='step/start':#步骤开始
        步骤表[助手步骤键(取字段(数据,'turn'),取字段(数据,'step'))]={#写入新条目
            'stepStartTime':取字段(事件,'time'),#记下开始
            'firstTokenTime':None,#首 token 未到
        }#结束
        return#完
    if 类型=='assistant/chunk' and 是否词增量(取字段(数据,'chunk')):#助手块且是 token 增量
        键=助手步骤键(取字段(数据,'turn'),取字段(数据,'step'))#该步骤键
        当前=步骤表.get(键) or {'stepStartTime':None,'firstTokenTime':None}#已有或空边界
        if 当前.get('firstTokenTime') is None:#尚未盖首 token
            步骤表[键]={'stepStartTime':当前.get('stepStartTime'),'firstTokenTime':取字段(事件,'time')}#只盖一次

def 落定助手计时(步骤表,回合,步骤,完成时间):#落定助手计时
    """从步骤条目落定一条已定稿助手消息的计时。

    开始或首 token 落在窗口外的步骤给出空边界。
    @param 步骤表 - 索引助手步骤计时 建好的逐步索引。
    @param 回合 - assistant/message 的回合号。
    @param 步骤 - assistant/message 的步骤号。
    @param 完成时间 - assistant/message 事件时间戳（纪元毫秒）。
    @returns 节点可用的计时记录。
    """
    边界=步骤表.get(助手步骤键(回合,步骤)) or {'stepStartTime':None,'firstTokenTime':None}#步骤边界或空
    return {#计时记录
        'stepStartTime':边界.get('stepStartTime'),#步骤开始
        'firstTokenTime':边界.get('firstTokenTime'),#首 token
        'completedTime':完成时间,#完成时间
    }#结束
