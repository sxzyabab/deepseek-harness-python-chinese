'当前 Host 代际的一份模型目录，所有会话选择器共用'

from ...存储 import 创建快照存储

__all__=['代际目录']

class 代际目录:
    '当前 Host 代际最多加载一份模型目录'
    def __init__(自身,上下文):
        '记下远程上下文、推理表和空闲快照'
        自身.上下文=上下文
        自身.存储=创建快照存储({
            'value':None,
            'status':'idle',
            'error':None,
        })
        自身.推理={}
        自身.世代=0
        自身.飞行=None

    def reasoningFor(自身,选定):
        '读这一代见过的推理元数据。模型已经离开目录也还留着'
        return 自身.推理.get((选定['provider'],选定['model']))

    def load(自身):
        '返回当前代际的目录。已经在飞的那一次不再另打远程'
        态=自身.存储.getSnapshot()
        if 态['status']=='ready' and 态['value'] is not None:
            return 态['value']
        if 自身.飞行 is not None:
            return 自身.存储.getSnapshot()['value']
        世代=自身.世代
        操作=object()
        自身.飞行=操作
        def 标加载(稿):
            '标成正在加载'
            稿['status']='loading'
            稿['error']=None
        自身.存储.update(标加载)
        try:
            应答=自身.上下文.remote.session.modelCatalog()
            if 应答['ok'] is not True:
                错=应答['error']
                raise Exception(str(错['code'])+': '+str(错['message']))
            if 世代==自身.世代:
                for 组 in 应答['value']['groups']:
                    for 模型 in 组['models']:
                        自身.推理[(组['id'],模型['id'])]=模型.get('reasoning')
                自身.存储.set({
                    'value':应答['value'],
                    'status':'ready',
                    'error':None,
                })
            return 应答['value']
        except Exception as 错误:
            if 世代==自身.世代:
                文=str(错误)
                def 写错(稿):
                    '标成失败'
                    稿['status']='error'
                    稿['error']=文
                自身.存储.update(写错)
            raise
        finally:
            if 世代==自身.世代 and 自身.飞行 is 操作:
                自身.飞行=None

    def 失效(自身,清空=False):
        '使已加载目录失效。下次菜单读取会重载'
        自身.世代+=1
        自身.飞行=None
        值=None if 清空 else 自身.存储.getSnapshot()['value']
        自身.存储.set({'value':值,'status':'idle','error':None})

    def refresh(自身):
        'Host 侧模型输入变了就失效并重载。失败留在目录快照上'
        自身.失效()
        try:
            自身.load()
        except Exception:
            return

    def resetGeneration(自身):
        '清掉上一代 Host 的值，再加载这一代'
        自身.推理.clear()
        自身.失效(True)
        try:
            自身.load()
        except Exception:
            return
