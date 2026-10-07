from ...存储 import 创建快照存储
import threading

__all__=['使用文件应用']

空结果={'apps':[],'loading':True,'failed':False}
_读表={}

def 空刷新():
    '未启用时的刷新'
    return None

def 查询已到(项,控,应用):
    '中止则丢；否则发布联想'
    if 控.is_set():#已中止
        return
    项['state'].set({'apps':[] if 应用 is None else list(应用),'loading':False,'failed':应用 is None})#发布

def 做成回调(项,控):
    '把这一次中止旗绑进同级回调'
    def 已查(应用):
        '查询解决'
        查询已到(项,控,应用)#发布
    def 失败(_错误):
        '查询拒绝当失败'
        查询已到(项,控,None)#失败
    return 已查,失败#成功臂与失败臂

def 接上(产出,成功,失败):
    '期约走 然后，上游 then 走 then；已是值则直接成功'
    if hasattr(产出,'然后'):#本层期约
        产出.然后(成功,失败)#接上
        return
    if hasattr(产出,'then'):#上游期约
        产出.then(成功,失败)#接上
        return
    成功(产出)#已是值

def _订阅(查询,目标,监听):
    键=id(查询)
    目标表=_读表.get(键)
    if 目标表 is None:
        目标表={}
        _读表[键]=目标表
    项=目标表.get(目标)
    初次=项 is None
    if 项 is None:
        项={'state':创建快照存储(空结果),'users':0,'controller':None}
        def 刷新():
            旧=项['controller']
            if 旧 is not None:
                旧.set()
            控=threading.Event()
            项['controller']=控
            已查,失败=做成回调(项,控)#这一次的回调
            try:#查询
                产出=查询(目标,控)#期约或值
            except Exception:#同步失败
                失败(None)#当失败
                return
            接上(产出,已查,失败)#落定后发布
        项['refresh']=刷新
        目标表[目标]=项
    项['users']+=1
    退=项['state'].subscribe(监听)
    if 初次:
        项['refresh']()
    def 释放():
        退()
        项['users']-=1
        if 项['users']==0:
            控=项['controller']
            if 控 is not None:
                控.set()
            if 目标 in 目标表:
                del 目标表[目标]
    return 释放

def 使用文件应用(目标,查询,启用):
    '同一文件与读取器的挂载控件共享联想与刷新'
    if not 启用:
        return {**空结果,'refresh':空刷新}
    箱={'state':空结果}
    def 听():
        目标表=_读表.get(id(查询))
        项=None if 目标表 is None else 目标表.get(目标)
        箱['state']=空结果 if 项 is None else 项['state'].getSnapshot()
    退=_订阅(查询,目标,听)
    听()
    def 刷新():
        目标表=_读表.get(id(查询))
        项=None if 目标表 is None else 目标表.get(目标)
        if 项 is not None:
            项['refresh']()
    态=箱['state']
    return {'apps':态.get('apps',[]),'loading':bool(态.get('loading')),'failed':bool(态.get('failed')),'refresh':刷新,'unsubscribe':退}
