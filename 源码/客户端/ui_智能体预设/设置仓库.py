"""智能体预设默认设置控制器。

对齐上游 `ui-agent-preset/src/client/settings-store.ts`。公开面仅中文名。
"""
from ...依赖 import cordis#外部依赖胶水
__all__=['设置命名空间','错误文','写默认预设','读名册','预设选项','预设设置控制器']#仅中文公开名

设置命名空间='agent-presets'#宿主设置 ns

def 解开(值):#承诺则等待
    """承诺则等待，否则原样。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

def 错误文(错误):#拒绝值收成文案
    """Error 取 message，其余 String。"""
    if isinstance(错误,BaseException) and 错误.args:#异常
        return str(错误.args[0])#消息
    return str(错误)#其它

def 写默认预设(接口,标识):#把预设写成后续会话默认
    """失败返回文案；成功返回 None。"""
    try:#调用 settings.update
        应答=解开(接口.settings.update({'ns':设置命名空间,'patch':{'default':标识}}))#写入
    except Exception as 错误:#传输拒绝
        return 错误文(错误)#文案
    结果=应答.get('result') if isinstance(应答,dict) else None#信封
    if 结果 is None:#无
        return 'settings.update returned no result'#失败
    if 结果.get('ok'):#成功
        return None#无文案
    错=结果.get('error') or {}#错误
    return 错.get('message') or str(错)#业务错误

def 读名册(接口):#读名册并折叠拒绝
    """成功 {ok,value} 或失败 {ok:False,error}。"""
    try:#列表 RPC
        应答=解开(接口.agentPresets.list({}))#列预设
        结果=应答.get('result') if isinstance(应答,dict) else None#信封
        if 结果 is None:#无
            return {'ok':False,'error':'agentPresets.list returned no result'}#失败
        if 结果.get('ok'):#成功
            return {'ok':True,'value':结果.get('value')}#名册
        错=结果.get('error') or {}#错误
        return {'ok':False,'error':错.get('message') or str(错)}#业务失败
    except Exception as 错误:#传输失败
        return {'ok':False,'error':错误文(错误)}#文案

def 预设选项(预设们):#名册 → 挑选器选项
    """仅健康预设。"""
    出=[]#结果
    for 项 in 预设们 or []:#逐项
        if 项.get('broken') is not None:#损坏
            continue#跳过
        选={'id':项['id'],'trust':项['trust']}#基础
        if 项.get('name') is not None:#有名
            选['name']=项['name']#名
        if 项.get('description') is not None:#有述
            选['description']=项['description']#述
        出.append(选)#加
    return 出#选项

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

class 预设设置控制器:#设置行控制器
    """读取名册并持久化所选默认。"""
    def __init__(自身,接口):#注入 API
        """记下接口与初始仓。"""
        自身.接口=接口#API
        自身.store=简易快照仓({#初始
            'status':'idle','error':None,'writable':True,'currentValue':'','options':[],
        })#仓

    def _合并(自身,补丁):#合并补丁
        """浅合并后写入。"""
        现=自身.store.getSnapshot()#现
        现.update(补丁)#合并
        自身.store.set(现)#写

    def load(自身):#拉名册并填设置行
        """空名册 → unavailable。"""
        前=自身.store.getSnapshot()#前
        if 前.get('status')=='loading':#并发
            return#让出
        自身._合并({'status':'loading','error':None})#loading
        名册=读名册(自身.接口)#读
        if not 名册.get('ok'):#失败
            自身._合并({'status':'error','error':名册.get('error')})#错误
            return#结束
        值=名册.get('value') or {}#值
        预设们=值.get('presets') or []#列表
        if len(预设们)==0:#空部署
            自身._合并({'status':'unavailable','options':[],'currentValue':''})#不可用
            return#结束
        try:#问可写性
            描述=解开(自身.接口.settings.describe({}))#describe
            结果=描述.get('result') if isinstance(描述,dict) else None#信封
            可写=bool(结果 and 结果.get('ok') and (结果.get('value') or {}).get('writable'))#可写
            默认=None#默认 id
            for 项 in 预设们:#找默认
                if 项.get('isDefault'):#默认
                    默认=项.get('id')#记下
                    break#停
            if 默认 is None:#无标
                默认=预设们[0].get('id')#首项
            自身._合并({#就绪
                'status':'ready','error':None,'writable':可写,
                'options':预设选项(预设们),'currentValue':默认 or '',
            })#写
        except Exception as 错误:#describe 失败
            自身._合并({'status':'error','error':错误文(错误)})#错误

    def select(自身,标识):#写成后续会话默认
        """已在跑的会话保持创建时组合。"""
        前=自身.store.getSnapshot()#前
        if 前.get('status')=='saving' or 标识==前.get('currentValue'):#忽略
            return#结束
        自身._合并({'status':'saving','error':None,'currentValue':标识})#乐观
        失败=写默认预设(自身.接口,标识)#写入
        if 失败 is not None:#失败
            自身._合并({'status':'ready','currentValue':前.get('currentValue'),'error':失败})#回滚
            return#结束
        自身.load()#重读名册
