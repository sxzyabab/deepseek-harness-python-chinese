"""一次待处理审批 waterfall 的 composer 接管。

对齐上游 `ui-approval/src/client/ApprovalPanel.tsx`。公开面仅中文名。
无真 React：返回结构树字典；一次作答闩。
"""
from .约定.槽 import 待决审批#待处理面

__all__=['审批面板','审批流']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 审批流:#一次性作答流
    """等待条+理由+详情+准/拒。"""

    def __init__(自身,待处理,详情,翻译):#构造
        """记下待处理面、可选详情与翻译。"""
        自身.pending=待处理#待处理面
        自身.detail=详情#可选详情节点
        自身.t=翻译#翻译函数
        自身.已答=False#作答门闩

    def 作答(自身,结果):#提交决定
        """先禁用按钮；失败则恢复可点。"""
        自身.已答=True#先禁用
        try:#投递
            自身.pending.answer(结果)#作答
        except Exception:#失败
            自身.已答=False#恢复可点

    def 渲染(自身):#结构树
        """审批卡片树。"""
        翻译=自身.t if callable(自身.t) else (lambda 键,_=None:键)#文案
        理由=自身.pending.reason#理由
        if 理由 is None:#缺
            理由=翻译('escalation',{'toolName':自身.pending.toolName})#回退
        return {#审批
            'type':'approval-panel',#类型
            'key':自身.pending.key,#请求键
            'stripLabel':翻译('waiting'),#等待条
            'detailAria':翻译('detail.aria'),#无障碍
            'headline':理由,#理由
            'detail':自身.detail,#可选详情
            'rejectLabel':翻译('reject'),#拒
            'allowOnceLabel':翻译('allowOnce'),#准一次
            'answered':自身.已答,#已答
            'onReject':lambda:自身.作答('rejected'),#拒
            'onAllowOnce':lambda:自身.作答('allowed-once'),#准
            'cssModule':'审批面板.module.css',#样式
        }#视图结束

class 审批面板:#链条目入口
    """渲染一个待处理审批及其可选的 Tool 自有详情。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成
        自身._流=None#当前流
        自身._流键=None#流身份

    def 更新(自身,属性):#刷新
        """换 key 则重建流。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """按 key 重挂载流。"""
        属性=自身.属性#props
        审批=取字段(属性,'matched')#命中的待处理面
        if 审批 is None:#无
            return None#空
        渲染槽=取字段(属性,'renderSlot')#子槽渲染
        详情=None#可选详情
        if 审批.callId is not None and callable(渲染槽):#有关联调用
            详情=渲染槽('conversation.approval.detail',{'callId':审批.callId})#拉可选详情
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        if 自身._流 is None or 自身._流键!=审批.key:#按 key 重挂载
            自身._流=审批流(审批,详情,翻译)#新流
            自身._流键=审批.key#记下键
        else:#同键刷新详情/翻译
            自身._流.detail=详情#详情
            自身._流.t=翻译#翻译
            自身._流.pending=审批#面
        return 自身._流.渲染()#渲

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

ApprovalPanel=审批面板#上游名
