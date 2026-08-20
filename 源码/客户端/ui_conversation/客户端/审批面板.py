"""审批接管面板：composer 链选中审批等待时。

对齐上游 `ui-conversation/src/client/skeleton/ApprovalPanel.tsx`。公开面仅中文名。
一次作答闩：点后禁用，失败再解锁。匹配载体经 `待决审批` 铸域面。
"""
import json#解析 command
from .约定.槽 import 待决审批#审批域面
from .约定.聊天节点 import 已结算工具#工具根谓词
from .工具节点读取 import 根工具调用#配对命令

__all__=['审批面板','取命令','待决审批']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 取命令(调用):#从 bash 族 args 取 command
    """不可解析则 None。"""
    if 调用 is None:#无
        return None#无
    原文=取字段(调用,'argsRaw')#原文
    if not isinstance(原文,str):#非串
        return None#无
    try:#解析
        参数=json.loads(原文)#JSON
    except Exception:#失败
        return None#无
    命令=参数.get('command') if isinstance(参数,dict) else None#command
    return 命令 if isinstance(命令,str) else None#命令

class 审批面板:#composer 接管
    """琥珀条+理由+命令+准/拒。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成
        自身.已答=False#一次闩

    def 更新(自身,属性):#刷新
        """刷新；换 key 则解锁。"""
        旧=取字段(自身.属性,'matched') or 取字段(自身.属性,'interaction')#旧
        自身.属性=属性 or {}#新
        新=取字段(自身.属性,'matched') or 取字段(自身.属性,'interaction')#新
        if 取字段(旧,'key')!=取字段(新,'key'):#新请求
            自身.已答=False#解锁

    def 铸待决(自身):#按 matched 铸域面
        """载体稳定身份。"""
        属性=自身.属性#props
        匹配=取字段(属性,'matched') or 取字段(属性,'interaction')#载体
        return 待决审批(匹配) if 匹配 is not None else None#域面

    def 作答(自身,结果):#allowed-once / rejected
        """闩+派 pending.answer。"""
        自身.已答=True#闩
        待=自身.铸待决()#域面
        if 待 is None:#无
            自身.已答=False#解锁
            return#停
        try:#派
            结果对象=待.answer(结果)#可能 Promise
            then=getattr(结果对象,'then',None)#Promise
            if callable(then):#失败解锁
                then(lambda *_:None,lambda *_:自身.__setattr__('已答',False))#解锁
            等待=getattr(结果对象,'等待',None)#中文承诺
            if callable(等待):#同步宿主半
                等待()#等
        except Exception:#同步失败
            自身.已答=False#解锁

    def 渲染(自身):#结构树
        """审批卡。"""
        属性=自身.属性#props
        待=自身.铸待决()#域面
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        命令=取字段(属性,'command')#命令
        if 命令 is None and 待 is not None:#未注入则从会话推
            用会话=取字段(属性,'useSession')#会话钩
            调用标识=待.callId#配对 id
            if callable(用会话) and 调用标识 is not None:#可推
                def 选(快照):#找运行中根
                    """配对且未结算才取 command。"""
                    根=根工具调用(快照,调用标识)#根
                    if 根 is None:#无
                        return None#无
                    if 取字段(根,'callId')!=调用标识:#非本调用
                        return None#无
                    if 已结算工具(根):#已结算
                        return None#无
                    return 取命令(根)#命令
                命令=用会话(选)#推
        理由=待.reason if 待 is not None else None#理由
        if 理由 is None:#缺
            工具名=待.toolName if 待 is not None else ''#工具
            理由=翻译('approval.escalation',{'toolName':工具名})#回退
        return {#审批
            'type':'approval-panel',#类型
            'key':待.key if 待 is not None else None,#请求键
            'stripLabel':翻译('approval.waiting'),#等待条
            'detailAria':翻译('approval.detail.aria'),#无障碍
            'headline':理由,#理由
            'command':命令,#命令
            'approveLabel':翻译('approval.allow'),#准（上游 allow）
            'rejectLabel':翻译('approval.reject'),#拒
            'answered':自身.已答,#已答
            'onApprove':lambda:自身.作答('allowed-once'),#准
            'onReject':lambda:自身.作答('rejected'),#拒
            'cssModule':'审批面板.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
