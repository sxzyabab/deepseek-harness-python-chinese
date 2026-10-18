from ...存储 import 创建快照存储
from ..引导文案 import 欢迎通知确认字段,欢迎通知版本

__all__=['解码欢迎节','欢迎通知存储']

def 解码欢迎节(节):
    '对象节原样收下。坏值当成空节，引导视为尚未确认'
    if isinstance(节,dict):
        return 节
    return {}

class 欢迎通知存储:
    '跟着欢迎设置域，把确认写回宿主'
    def __init__(自身,作用域):
        '空闲快照，还没跟随'
        自身.作用域=作用域
        自身.存储=创建快照存储({
            'status':'idle',
            'acknowledged':False,
            'error':None,
        })
        自身.保存中=False
        自身.跟随=None

    def 加载(自身):
        '开始跟随作用域，并发布当前答案'
        if 自身.跟随 is None:
            自身.跟随=自身.作用域.subscribe(自身.派生)
        自身.派生()

    def 确认(自身):
        '把当前文案版本写进作用域。写完后宿主里有这条确认才算成功'
        自身.保存中=True
        def 标保存(状态):
            '进入保存，清掉上一次错误'
            状态['status']='saving'
            状态['error']=None
        自身.存储.update(标保存)
        try:
            自身.作用域.set(欢迎通知确认字段,欢迎通知版本)
        finally:
            自身.保存中=False
        自身.派生()
        已确认=自身.存储.getSnapshot()['acknowledged']
        if 已确认 is not True:
            def 标失败(状态):
                '确认没有留在宿主里'
                状态['status']='error'
                状态['error']='the acknowledgement did not persist'
            自身.存储.update(标失败)
        return 已确认

    def 拆除(自身):
        '停止跟随作用域'
        if 自身.跟随 is not None:
            自身.跟随()
            自身.跟随=None

    def 派生(自身):
        '按作用域状态发布确认与否。保存进行中不覆盖'
        if 自身.保存中:
            return
        范围=自身.作用域.getSnapshot()
        状态名=范围['status']
        if 状态名=='loading':
            def 标加载(状态):
                '作用域还在加载'
                状态['status']='loading'
                状态['error']=None
            自身.存储.update(标加载)
            return
        if 状态名=='unavailable':
            def 标不可用(状态):
                '欢迎确认设置不可用'
                状态['status']='error'
                状态['acknowledged']=False
                状态['error']='welcome acknowledgement settings are unavailable'
            自身.存储.update(标不可用)
            return
        if 状态名=='ready':
            值=范围.get('value')
            已确认=isinstance(值,dict) and 值.get(欢迎通知确认字段)==欢迎通知版本
            def 标就绪(状态):
                '按字段是否等于当前版本'
                状态['status']='ready'
                状态['acknowledged']=已确认
                状态['error']=None
            自身.存储.update(标就绪)
            return
        raise Exception('unexpected welcome settings status')
