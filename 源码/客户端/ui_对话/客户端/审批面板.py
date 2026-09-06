"""审批接管面板：composer 链选中审批等待时。

对齐上游 `ui-conversation/src/client/skeleton/ApprovalPanel.tsx`。公开面仅中文名。
一次作答闩：点后禁用，失败再解锁。匹配载体经 `待决审批` 铸域面。
属性与根块为 dict。
"""
import json#解析 command
from .服务 import 对话错误#本包异常
from .约定.槽 import 待决审批#审批域面
from .约定.聊天节点 import 已结算工具#工具根判断
from .工具节点读取 import 根工具调用#配对命令

__all__=['审批面板','取命令','待决审批']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

def 取命令(调用):
    """不可解析则 None。"""
    if 调用 is None:#无
        return None#无
    原文=调用['argsRaw'] if 'argsRaw' in 调用 else None#原文
    if not isinstance(原文,str):#非串
        return None#无
    try:#解析
        参数=json.loads(原文)#JSON
    except json.JSONDecodeError:#失败
        return None#无
    命令=参数['command'] if isinstance(参数,dict) and 'command' in 参数 else None#command
    return 命令 if isinstance(命令,str) else None#命令

class 审批面板:
    """琥珀条+理由+命令+准/拒。"""

    def __init__(自身,属性=None):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.已答=False#一次闩

    def 更新(自身,属性):
        """刷新；换 key 则解锁。"""
        旧=自身.属性['matched'] if 'matched' in 自身.属性 else None#旧匹配
        if 旧 is None:#无匹配
            旧=自身.属性['interaction'] if 'interaction' in 自身.属性 else None#旧交互
        自身.属性=属性 if 属性 is not None else {}#新
        新=自身.属性['matched'] if 'matched' in 自身.属性 else None#新匹配
        if 新 is None:#无匹配
            新=自身.属性['interaction'] if 'interaction' in 自身.属性 else None#新交互
        旧键=旧['key'] if 旧 is not None and 'key' in 旧 else None#旧键
        新键=新['key'] if 新 is not None and 'key' in 新 else None#新键
        if 旧键!=新键:#新请求
            自身.已答=False#解锁

    def 铸待决(自身):
        """载体稳定身份。"""
        属性=自身.属性#props
        匹配=属性['matched'] if 'matched' in 属性 else None#载体
        if 匹配 is None:#无
            匹配=属性['interaction'] if 'interaction' in 属性 else None#交互
        return 待决审批(匹配) if 匹配 is not None else None#域面

    def 准许(自身):
        """allowed-once。"""
        自身.作答('allowed-once')#准

    def 拒绝(自身):
        """rejected。"""
        自身.作答('rejected')#拒

    def 作答(自身,结果):
        """闩+派 pending.answer。"""
        自身.已答=True#闩
        待=自身.铸待决()#域面
        if 待 is None:#无
            自身.已答=False#解锁
            return#停
        try:#派
            出=待.answer(结果)#任务或空
            if 出 is not None:#有任务
                出.等待()#等
        except 对话错误:#同步失败
            自身.已答=False#解锁

    def 渲染(自身):
        """审批卡。"""
        属性=自身.属性#props
        待=自身.铸待决()#域面
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        命令=属性['command'] if 'command' in 属性 else None#命令
        if 命令 is None and 待 is not None:#未注入则从会话推
            用会话=属性['useSession'] if 'useSession' in 属性 else None#会话钩
            调用标识=待.callId#配对 id
            if 用会话 is not None and 调用标识 is not None:#可推
                def 选(快照,钉标识=调用标识):
                    """配对且未结算才取 command。"""
                    根=根工具调用(快照,钉标识)#根
                    if 根 is None:#无
                        return None#无
                    根标识=根['callId'] if 'callId' in 根 else None#根 id
                    if 根标识!=钉标识:#非本调用
                        return None#无
                    if 已结算工具(根) is True:#已结算
                        return None#无
                    return 取命令(根)#命令
                命令=用会话(选)#推
        理由=待.reason if 待 is not None else None#理由
        if 理由 is None:#缺
            工具名=待.toolName if 待 is not None else ''#工具
            理由=翻译('approval.escalation',{'toolName':工具名})#回退
        键=待.key if 待 is not None else None#请求键
        return {#审批
            'type':'approval-panel',#类型
            'key':键,#请求键
            'stripLabel':翻译('approval.waiting'),#等待条
            'detailAria':翻译('approval.detail.aria'),#无障碍
            'headline':理由,#理由
            'command':命令,#命令
            'approveLabel':翻译('approval.allow'),#准（上游 allow）
            'rejectLabel':翻译('approval.reject'),#拒
            'answered':自身.已答,#已答
            'onApprove':自身.准许,#准
            'onReject':自身.拒绝,#拒
            'cssModule':'审批面板.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
