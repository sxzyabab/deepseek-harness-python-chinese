"""智能体预设默认设置控制器。

对齐上游 `ui-agent-preset/src/client/settings-store.ts`。公开面仅中文名。
"""
__all__=['设置命名空间','错误文','写智能体预设设置','写默认预设','写模式选择启用','读名册','预设选项','预设设置控制器','智能体预设错误']#仅中文公开名

设置命名空间='agent-presets'#宿主设置 ns

class 智能体预设错误(Exception):
    """本包预设线失败。"""
    def __init__(自身,消息):
        """记下英文消息。"""
        super().__init__(消息)#消息原样英文

def 错误文(错误):#拒绝值收成文案
    """Error 取 message，其余 String。"""
    if isinstance(错误,BaseException) and len(错误.args)>0:#异常
        return str(错误.args[0])#消息
    return str(错误)#其它

def 写智能体预设设置(接口,补丁):#统一写入 default / modeSelectionEnabled
    """失败返回文案；成功返回 None。settings.update 返回任务。"""
    try:#调用 settings.update
        应答=接口.settings.update({'ns':设置命名空间,'patch':补丁}).等待()#写入
    except Exception as 错误:#传输拒绝；RPC 异常契约未定
        return 错误文(错误)#文案
    if 'result' not in 应答:#无
        return 'settings.update returned no result'#失败
    结果=应答['result']#信封
    if 结果['ok']:#成功
        return None#无文案
    错误体=结果['error'] if 'error' in 结果 and 结果['error'] is not None else {}#错误
    return 错误体['message'] if 'message' in 错误体 else str(错误体)#业务错误

def 写默认预设(接口,标识):#把预设写成后续会话默认
    """失败返回文案；成功返回 None。"""
    return 写智能体预设设置(接口,{'default':标识})#只写 default

def 写模式选择启用(接口,启用):#写出选择器开关
    """失败返回文案；成功返回 None。"""
    return 写智能体预设设置(接口,{'modeSelectionEnabled':启用})#只写 modeSelectionEnabled

空名册={'presets':[],'authorable':False,'modeSelectionEnabled':False}#无服务时等同空名册

def 读名册(接口):#读名册并折叠拒绝
    """成功 {ok,value} 或失败 {ok:False,error}。list 返回任务。"""
    try:#列表 RPC
        应答=接口.agentPresets.list({}).等待()#列预设
        if 'result' not in 应答:#无
            return {'ok':False,'error':'agentPresets.list returned no result'}#失败
        结果=应答['result']#信封
        if 结果['ok']:#成功
            return {'ok':True,'value':结果['value'] if 'value' in 结果 else None}#名册
        错误体=结果['error'] if 'error' in 结果 and 结果['error'] is not None else {}#错误
        码=错误体['code'] if isinstance(错误体,dict) and 'code' in 错误体 else None#错误码
        if 码=='gateway/invocation-unavailable':#服务缺席
            return {'ok':True,'value':空名册}#当空名册
        return {'ok':False,'error':错误体['message'] if 'message' in 错误体 else str(错误体)}#业务失败
    except Exception as 错误:#传输失败；RPC 异常契约未定
        return {'ok':False,'error':错误文(错误)}#文案

def 预设选项(预设列表):#名册 → 挑选器选项
    """仅健康预设。"""
    出=[]#结果
    列表=预设列表 if 预设列表 is not None else []#名册
    for 项 in 列表:#逐项
        if 'broken' in 项 and 项['broken'] is not None:#损坏
            continue#跳过
        选={'id':项['id'],'trust':项['trust']}#基础
        if 'name' in 项:#有名
            选['name']=项['name']#名
        if 'description' in 项:#有述
            选['description']=项['description']#述
        出.append(选)#加
    return 出#选项

class 简易快照存储:#快照存储
    """订阅 + set。"""
    def __init__(自身,初始):#初始
        """记下状态。"""
        自身.状态=dict(初始)#可变
        自身.订阅列表=[]#监听

    def getSnapshot(自身):#读
        """浅拷贝。"""
        return dict(自身.状态)#拷贝

    def subscribe(自身,监听):#订阅
        """返回拆除器。"""
        自身.订阅列表.append(监听)#登记
        def 拆除订阅():#拆除
            """去掉。"""
            if 监听 in 自身.订阅列表:#仍在
                自身.订阅列表.remove(监听)#删
        return 拆除订阅#拆除器

    def set(自身,下一):#整表替换
        """写快照并广播。"""
        自身.状态=dict(下一)#替换
        for 监听 in list(自身.订阅列表):#广播
            监听()#回调

class 预设设置控制器:#设置行控制器
    """读取名册并持久化所选默认。"""
    def __init__(自身,接口):#注入 API
        """记下接口与初始存储。"""
        自身.接口=接口#API
        自身.存储=简易快照存储({#初始
            'status':'idle','error':None,'writable':True,'currentValue':'','options':[],
        })#存储结束

    def _合并(自身,补丁):#合并补丁
        """浅合并后写入。"""
        现=自身.存储.getSnapshot()#现
        现.update(补丁)#合并
        自身.存储.set(现)#写

    def load(自身):#拉名册并填设置行
        """空名册 → unavailable。describe 返回任务。"""
        前=自身.存储.getSnapshot()#前
        if 前['status']=='loading':#并发
            return#让出
        自身._合并({'status':'loading','error':None})#loading
        名册=读名册(自身.接口)#读
        if not 名册['ok']:#失败
            自身._合并({'status':'error','error':名册['error']})#错误
            return#结束
        值=名册['value'] if 名册['value'] is not None else {}#值
        预设列表=值['presets'] if 'presets' in 值 and 值['presets'] is not None else []#列表
        if len(预设列表)==0:#空部署
            自身._合并({'status':'unavailable','options':[],'currentValue':''})#不可用
            return#结束
        try:#问可写性
            描述=自身.接口.settings.describe({}).等待()#describe
            结果=描述['result'] if 'result' in 描述 else None#信封
            可写=结果 is not None and 结果['ok'] and (结果['value']['writable'] if 'value' in 结果 and 结果['value'] is not None and 'writable' in 结果['value'] else False)#可写
            默认=None#默认 id
            for 项 in 预设列表:#找默认
                if 'isDefault' in 项 and 项['isDefault']:#默认
                    默认=项['id']#记下
                    break#停
            if 默认 is None:#无标
                默认=预设列表[0]['id']#首项
            自身._合并({#就绪
                'status':'ready','error':None,'writable':bool(可写),
                'options':预设选项(预设列表),'currentValue':默认 if 默认 is not None else '',
            })#写
        except Exception as 错误:#describe 失败；RPC 异常契约未定
            自身._合并({'status':'error','error':错误文(错误)})#错误

    def select(自身,标识):#写成后续会话默认
        """已在跑的会话保持创建时组合。"""
        前=自身.存储.getSnapshot()#前
        if 前['status']=='saving' or 标识==前['currentValue']:#忽略
            return#结束
        自身._合并({'status':'saving','error':None,'currentValue':标识})#乐观
        失败=写默认预设(自身.接口,标识)#写入
        if 失败 is not None:#失败
            自身._合并({'status':'ready','currentValue':前['currentValue'],'error':失败})#回滚
            return#结束
        自身.load()#重读名册
