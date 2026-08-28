"""主界面芯片控制器：决定「下一场会话」用哪个预设。

对齐上游 `ui-agent-preset/src/client/seat-store.ts`。公开面仅中文名。
新建会话屏当时还没有会话，所以挑选先暂存、不立刻套用。
"""
from ...依赖 import cordis#外部依赖胶水
是否thenable=cordis.工具.是否thenable#可等待判定
from .设置仓库 import 错误文,预设选项#错误文案与预设选项投影

__all__=['芯片控制器','芯片初始']#仅中文公开名

芯片初始={'options':[],'current':'','error':None,'busy':False,'introduce':False}#芯片初始快照

def 解开(值):#承诺则等待
    """承诺则等待，否则原样。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

class 简易快照仓:#快照仓
    """订阅 + set。"""
    def __init__(自身,初始):#初始
        """记下状态。"""
        自身.状态=dict(初始)#可变
        自身.订阅们=[]#监听

    def getSnapshot(自身):#读
        """浅拷贝。"""
        return dict(自身.状态)#拷贝

    def subscribe(自身,听):#订阅
        """返回拆除器。"""
        自身.订阅们.append(听)#登记
        def 拆():#拆除
            """去掉。"""
            if 听 in 自身.订阅们:#仍在
                自身.订阅们.remove(听)#删
        return 拆#拆除器

    def set(自身,下一):#整表替换
        """写快照并广播。"""
        自身.状态=dict(下一)#替换
        for 听 in list(自身.订阅们):#广播
            听()#回调

class 芯片控制器:#主界面芯片控制器
    """暂存下一场会话的预设，并在会话出现时套用。"""
    def __init__(自身,接口,当前会话,已套用=None):#注入 API、当前会话、套用回调
        """记下依赖与初始仓。"""
        自身.接口=接口#预设 RPC
        自身.当前会话=当前会话#读当前会话摘要
        自身.已套用=已套用#套用成功后通知列表
        自身.store=简易快照仓(芯片初始)#芯片状态仓库
        自身.回落=''#部署默认预设 id
        自身.暂存=None#尚未套用的暂存预设

    def _合并(自身,补丁):#合并补丁进快照
        """浅合并后写入。"""
        现=自身.store.getSnapshot()#现
        现.update(补丁)#合并
        自身.store.set(现)#写

    def load(自身):#拉名册并填芯片
        """快照已反映宿主之后。"""
        try:#列表 RPC
            应答=解开(自身.接口.agentPresets.list({}))#列预设
            结果=应答.get('result') if isinstance(应答,dict) else None#信封
            if not 结果 or not 结果.get('ok'):#业务失败
                错=(结果 or {}).get('error') or {}#错误
                自身._合并({'error':错.get('message') if isinstance(错,dict) else str(错)})#记下错误
                return#不再往下填
            值=结果.get('value') or {}#值
            预设们=值.get('presets') or []#名册
            默认=None#默认 id
            for 项 in 预设们:#找默认
                if 项.get('isDefault'):#默认
                    默认=项.get('id')#记下
                    break#停
            if 默认 is None and 预设们:#无标
                默认=预设们[0].get('id')#首项
            自身.回落=默认 or ''#默认或空
            会话=自身.当前会话()#当前会话摘要
            会话预设=会话.get('agentPreset') if isinstance(会话,dict) else getattr(会话,'agentPreset',None) if 会话 else None#会话已有
            当前=自身.暂存 if 自身.暂存 is not None else (会话预设 if 会话预设 is not None else 自身.回落)#暂存 / 会话已有 / 默认
            自身._合并({'options':预设选项(预设们),'current':当前 or '','error':None})#写入
        except Exception as 错误:#传输或解析失败
            自身._合并({'error':错误文(错误)})#记下异常文案

    def select(自身,标识):#挑选并尽量立刻套用
        """套用中则忽略。"""
        if 自身.store.getSnapshot().get('busy'):#套用中
            return#忽略
        自身.stage(标识)#先暂存
        自身.apply()#再尝试套到当前会话

    def stage(自身,标识,介绍=False):#只暂存不套用
        """给「先挑选、再开接收会话」的流程。"""
        自身.暂存=标识#记下待套用预设
        自身._合并({'current':标识,'error':None,'introduce':介绍})#芯片立刻显示该挑选

    def introduced(自身):#清掉介绍提示
        """芯片播完介绍后确认。"""
        if not 自身.store.getSnapshot().get('introduce'):#本就没提示
            return#结束
        自身._合并({'introduce':False})#标记已播过

    def apply(自身):#把暂存套到当前会话
        """select 与观察当前会话变化的人都会调用。"""
        暂存=自身.暂存#取出暂存
        会话=自身.当前会话()#当前会话摘要
        if 暂存 is None or 会话 is None:#没有暂存或没有会话
            return#结束
        标识=会话.get('id') if isinstance(会话,dict) else getattr(会话,'id',None)#会话 id
        空白=会话.get('blank') if isinstance(会话,dict) else getattr(会话,'blank',None)#是否空白
        会话预设=会话.get('agentPreset') if isinstance(会话,dict) else getattr(会话,'agentPreset',None)#会话预设
        if not 空白 or 会话预设==暂存:#已开过或已经是该预设
            自身.暂存=None#丢掉暂存
            return#不向宿主发切换
        自身._合并({'busy':True,'error':None})#开始套用
        try:#调用选定 RPC
            应答=解开(自身.接口.agentPresets.select({'sessionId':标识,'agentPreset':暂存}))#向宿主选定预设
            自身.暂存=None#无论成败都消费掉暂存
            结果=应答.get('result') if isinstance(应答,dict) else None#信封
            if not 结果 or not 结果.get('ok'):#宿主拒绝
                错=(结果 or {}).get('error') or {}#错误
                自身._合并({'busy':False,'error':错.get('message') if isinstance(错,dict) else str(错),'current':自身.回落})#回退
                return#结束本次套用
            值=结果.get('value') or {}#值
            已=值.get('agentPreset')#已套用的预设
            自身._合并({'busy':False,'current':已})#芯片跟上
            if 自身.已套用 is not None:#有回调
                自身.已套用(标识,已)#通知列表改标题
        except Exception as 错误:#传输失败
            自身.暂存=None#消费暂存
            自身._合并({'busy':False,'error':错误文(错误),'current':自身.回落})#回退并报错
