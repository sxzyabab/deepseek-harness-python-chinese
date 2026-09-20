from .设置存储 import 错误文,预设选项,读名册#错误文案、预设选项投影与读名册

__all__=['芯片控制器','芯片初始','共享暂存初始']#仅中文公开名

芯片初始={'showPicker':False,'options':[],'current':'','error':None,'busy':False,'introduce':False}#芯片初始快照
共享暂存初始={'id':None,'introduce':False}#Provider 绑定座位间共享的一次性暂存

class 简易快照存储:#快照存储
    """订阅 + set。"""
    def __init__(自身,初始):#初始
        """记下状态。"""
        自身.状态=dict(初始)#可变
        自身.订阅列表=[]#监听

    def getSnapshot(自身):#读
        """浅拷贝。"""
        return dict(自身.状态)#拷贝

    def subscribe(自身,监听器):#订阅
        """返回拆除器。"""
        自身.订阅列表.append(监听器)#登记
        def 拆除订阅():#拆除
            """去掉。"""
            if 监听器 in 自身.订阅列表:#仍在
                自身.订阅列表.remove(监听器)#删
        return 拆除订阅#拆除器

    def set(自身,下一快照):#整表替换
        """写快照并广播。"""
        自身.状态=dict(下一快照)#替换
        for 监听器 in list(自身.订阅列表):#广播
            监听器()#回调

def 取预设(会话):#从会话投影值取预设 id
    """投影里的 agentPreset；仅字符串才算。"""
    if 会话 is None:#无
        return None#空
    投影=会话['projectionValues'] if 'projectionValues' in 会话 else None#投影
    if 投影 is None:#无
        return None#空
    值=投影['agentPreset'] if 'agentPreset' in 投影 else None#预设
    return 值 if isinstance(值,str) else None#仅字符串

class 芯片控制器:#主界面芯片控制器
    """暂存下一场会话的预设，并在会话出现时套用。list/select 返回任务。"""
    def __init__(自身,接口,当前会话,共享暂存=None):#注入 API、当前会话、共享暂存
        """记下依赖与初始存储。"""
        自身.接口=接口#预设 RPC
        自身.当前会话=当前会话#读当前会话摘要
        自身.共享暂存=dict(共享暂存初始) if 共享暂存 is None else 共享暂存#共享暂存对象
        自身.存储=简易快照存储(芯片初始)#芯片状态存储
        自身.回退预设=''#部署默认预设 id
        自身.加载世代=0#名册读取世代

    def _合并(自身,补丁):#合并补丁进快照
        """浅合并后写入。"""
        当前快照=自身.存储.getSnapshot()#现
        当前快照.update(补丁)#合并
        自身.存储.set(当前快照)#写

    def load(自身):#拉名册并填芯片
        """快照已反映宿主之后。"""
        自身.加载世代+=1#本趟世代
        世代=自身.加载世代#记下
        名册=读名册(自身.接口)#读名册
        if 世代!=自身.加载世代:#已被更新的读取取代
            return#丢掉
        if not 名册['ok']:#失败
            自身._合并({'error':名册['error']})#记下错误
            return#不再往下填
        应答值=名册['value'] if 名册['value'] is not None else {}#值
        预设列表=应答值['presets'] if 'presets' in 应答值 and 应答值['presets'] is not None else []#名册
        选择启用=bool(应答值['modeSelectionEnabled']) if 'modeSelectionEnabled' in 应答值 else False#选择器开关
        if not 选择启用:#关闭选择则丢掉暂存
            自身.共享暂存['id']=None#清暂存
            自身.共享暂存['introduce']=False#清介绍
        默认=None#默认 id
        for 项 in 预设列表:#找默认
            if 'isDefault' in 项 and 项['isDefault']:#默认
                默认=项['id']#记下
                break#停
        if 默认 is None and len(预设列表)>0:#无标
            默认=预设列表[0]['id']#首项
        自身.回退预设=默认 if 默认 is not None else ''#默认或空
        会话=自身.当前会话()#当前会话摘要
        暂存标识=自身.共享暂存['id']#共享暂存
        会话预设=取预设(会话)#会话已有
        if 暂存标识 is not None:#暂存优先
            当前=暂存标识#暂存
        elif 会话 is None:#无会话
            当前=自身.回退预设#默认
        else:#有会话
            当前=会话预设 if 会话预设 is not None else ''#会话已有
        补丁={'showPicker':选择启用,'options':预设选项(预设列表),'current':当前 if 当前 is not None else '','error':None,'introduce':选择启用 and 自身.共享暂存['introduce']}#写入
        自身._合并(补丁)#写快照
        自身.apply()#立刻尝试套用

    def select(自身,标识):#挑选并尽量立刻套用
        """套用中则忽略。"""
        if 自身.存储.getSnapshot()['busy']:#套用中
            return#忽略
        自身.stage(标识)#先暂存
        自身.apply()#再尝试套到当前会话
        错=自身.存储.getSnapshot()['error']#拒绝文案
        return 错#有则返回

    def stage(自身,标识,介绍=False):#只暂存不套用
        """给「先挑选、再开接收会话」的流程。"""
        自身.共享暂存['id']=标识#记下待套用预设
        自身.共享暂存['introduce']=介绍#记下是否介绍
        自身._合并({'current':标识,'error':None,'introduce':介绍})#芯片立刻显示该挑选

    def blankSessionId(自身):#当前空白会话 id
        """记下本次设置动作可能带走的那一场空白会话。"""
        会话=自身.当前会话()#当前会话摘要
        if 会话 is None:#无
            return None#不在空白会话
        if 'blank' in 会话 and 会话['blank'] is True:#空白
            return 会话['id'] if 'id' in 会话 else None#其 id
        return None#非空白

    def syncBlankSession(自身,期望会话标识,标识):#把设置选择同步到仍空白的捕获会话
        """仅当捕获的会话仍是当前且空白时才套用。"""
        会话=自身.当前会话()#当前会话摘要
        if 会话 is None:#无
            return None#无关
        if 'blank' not in 会话 or 会话['blank'] is not True:#不再空白
            return None#无关
        if 'id' not in 会话 or 会话['id']!=期望会话标识:#已换会话
            return None#无关
        自身.stage(标识)#暂存有效默认
        自身.apply()#立刻套用
        return 自身.存储.getSnapshot()['error']#拒绝文案

    def introduced(自身):#清掉介绍提示
        """芯片播完介绍后确认。"""
        if not 自身.存储.getSnapshot()['introduce']:#本就没提示
            return
        自身.共享暂存['introduce']=False#清共享标记
        自身._合并({'introduce':False})#标记已播过

    def apply(自身):#把暂存套到当前会话
        """select 与观察当前会话变化的人都会调用。"""
        暂存=自身.共享暂存['id']#取出暂存
        会话=自身.当前会话()#当前会话摘要
        if 暂存 is None:#没有暂存
            if 会话 is None:#无会话
                当前=自身.回退预设#展示默认
            else:#有会话
                已有=取预设(会话)#会话已有
                当前=已有 if 已有 is not None else ''#展示
            if 当前!=自身.存储.getSnapshot()['current']:#展示落后
                自身._合并({'current':当前})#跟上展示
            return#无暂存可套
        if 会话 is None:#没有会话可接
            return
        标识=会话['id'] if 'id' in 会话 else None#会话 id
        是否空白=会话['blank'] if 'blank' in 会话 else None#是否空白
        会话预设=取预设(会话)#会话预设
        if 是否空白 is not True or 会话预设==暂存:#已开过或已经是该预设
            自身.共享暂存['id']=None#丢掉暂存
            自身.共享暂存['introduce']=False#清介绍
            return#不向宿主发切换
        自身._合并({'busy':True,'error':None})#开始套用
        try:#调用选定 RPC
            应答=自身.接口.agentPresets.select({'sessionId':标识,'agentPreset':暂存}).等待()#向宿主选定预设
            自身.共享暂存['id']=None#无论成败都消费掉暂存
            自身.共享暂存['introduce']=False#清介绍
            结果=应答['result'] if 'result' in 应答 else None#信封
            if 结果 is None or not 结果['ok']:#宿主拒绝
                错误体=(结果['error'] if 结果 is not None and 'error' in 结果 else None) or {}#错误
                原因=None#细节原因
                if isinstance(错误体,dict) and 'details' in 错误体 and isinstance(错误体['details'],dict) and 'reason' in 错误体['details'] and isinstance(错误体['details']['reason'],str):#有 reason 细节
                    原因=错误体['details']['reason']#用细节原因
                elif isinstance(错误体,dict) and 'message' in 错误体:#整框
                    原因=错误体['message']#用整框文案
                else:#其它
                    原因=str(错误体)#字符串化
                自身._合并({'busy':False,'error':原因,'current':会话预设 if 会话预设 is not None else ''})#回退
                return
            应答值=结果['value'] if 'value' in 结果 and 结果['value'] is not None else {}#值
            已套用标识=应答值['agentPreset'] if isinstance(应答值,dict) and 'agentPreset' in 应答值 else 应答值#已套用的预设
            自身._合并({'busy':False,'current':已套用标识})#芯片跟上
        except Exception as 错误:#传输失败；RPC 异常契约未定
            自身.共享暂存['id']=None#消费暂存
            自身.共享暂存['introduce']=False#清介绍
            自身._合并({'busy':False,'error':错误文(错误),'current':会话预设 if 会话预设 is not None else 自身.回退预设})#回退并报错
