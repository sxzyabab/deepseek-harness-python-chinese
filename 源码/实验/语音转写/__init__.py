import threading
from ...依赖.cordis.服务 import 服务
from ...依赖.schemastery import 字符串字段,字典字段
from ...工具.超时 import 中止控制器,合成信号,若已中止则抛出,已中止,等待中止
from .类型 import 语音提供方标识

__all__=['应用','配置','语音转写','依赖']

依赖=[]

配置=字典字段(字典结构={
    'defaultProvider':字符串字段(最小长度=1),
    'language':字符串字段(最小长度=1,默认值='auto'),
})

def 读易失(字段):
    """插件配置易失字段；有 get 则调，否则当值。"""
    if hasattr(字段,'get') and callable(字段.get):
        return 字段.get()
    return 字段

class 语音转写(服务):
    """具名识别器注册表，消费者先解析再执行。"""
    def __init__(自身,上下文,配置值=None):
        """登记服务并监听易失配置更新。"""
        super().__init__(上下文,'speechToText')
        自身.上下文=上下文
        自身.配置=配置值 if 配置值 is not None else {}
        自身.提供方表={}
        自身.监听者=set()
        自身.寿命=中止控制器()
        纤程=getattr(上下文,'fiber',None)
        条目=None if 纤程 is None else getattr(纤程,'entry',None)
        选项=None if 条目 is None else getattr(条目,'options',None)
        if isinstance(选项,dict):
            自身.条目标识=选项.get('id')
        else:
            自身.条目标识=None if 选项 is None else getattr(选项,'id',None)
        上下文.监听('loader/volatile-update',自身.已变)
        def 拆服务():
            """中止寿命并卸掉全部注册。"""
            def 拆():
                """join 已接收工作。"""
                自身.寿命.中止(RuntimeError('Speech service disposed'))
                for 注册 in list(自身.提供方表.values()):
                    自身.移除(注册)
                自身.监听者.clear()
            return 拆
        上下文.副作用(拆服务)

    def 登记(自身,提供方):
        """重复 id 失败且不替换原注册。"""
        若已中止则抛出(自身.寿命.信号)
        信息=提供方['info']
        标识=信息['id']
        if 标识 in 自身.提供方表:
            raise RuntimeError('Speech provider already registered: '+str(标识))
        准备=提供方.get('preparation')
        if 准备 is None:
            def 空退订():
                """无准备订阅。"""
                return
            退订=空退订
        else:
            退订=准备['subscribe'](自身.已变)
        注册={
            'provider':提供方,
            'lifetime':中止控制器(),
            'pending':set(),
            'unsubscribe':退订,
        }
        自身.提供方表[标识]=注册
        自身.已变()
        def 卸():
            """拒绝新请求并 join 已接收工作。"""
            自身.移除(注册)
        return 卸

    def 移除(自身,注册):
        """幂等卸掉一条注册。"""
        信息=注册['provider']['info']
        if 自身.提供方表.get(信息['id']) is not 注册:
            return
        del 自身.提供方表[信息['id']]
        注册['unsubscribe']()
        自身.已变()
        注册['lifetime'].中止(RuntimeError('Speech provider unloaded'))
        for 完成 in list(注册['pending']):
            完成.wait()

    def 列出提供方(自身):
        """按登记顺序给出公开事实。"""
        return [注册['provider']['info'] for 注册 in 自身.提供方表.values()]

    def 已变(自身):
        """通知快照观察者。"""
        for 监听 in list(自身.监听者):
            监听()

    def 跟随(自身,调用方):
        """完整就绪快照；慢读者合并中间进度。"""
        信号=合成信号(调用方,自身.寿命.信号)
        若已中止则抛出(信号)
        醒=threading.Event()
        已改=[True]
        def 通知():
            """标脏并叫醒。"""
            已改[0]=True
            醒.set()
        自身.监听者.add(通知)
        def 桥():
            """调用方或寿命中止时叫醒。"""
            等待中止(信号)
            通知()
        threading.Thread(target=桥,daemon=True).start()
        try:
            while not 已中止(信号):
                if not 已改[0]:
                    醒.wait()
                if 已中止(信号):
                    break
                醒.clear()
                已改[0]=False
                yield 自身.快照()
        finally:
            自身.监听者.discard(通知)

    def 快照(自身):
        """提供方就绪与当前偏好。"""
        视图=[]
        for 注册 in 自身.提供方表.values():
            提供方=注册['provider']
            准备=提供方.get('preparation')
            态={'phase':'ready'} if 准备 is None else 准备['snapshot']()
            视图.append({**提供方['info'],'preparation':态})
        return {
            'providers':视图,
            'selection':{
                'providerId':语音提供方标识(读易失(自身.配置['defaultProvider'])),
                'language':读易失(自身.配置['language']),
            },
        }

    def 配置选择(自身,补丁):
        """把传入字段写入本插件 profile 条目。"""
        设置=自身.上下文.获取服务('settings')
        条目=自身.条目标识
        if 设置 is None or 条目 is None:
            raise RuntimeError('Speech selection requires the settings service and a profile entry')
        标识=补丁['providerId'] if 'providerId' in 补丁 and 补丁['providerId'] is not None else 语音提供方标识(读易失(自身.配置['defaultProvider']))
        语言=补丁['language'] if 'language' in 补丁 and 补丁['language'] is not None else 读易失(自身.配置['language'])
        自身.选定提供方(标识,语言)
        更新={}
        if 'providerId' in 补丁 and 补丁['providerId'] is not None:
            更新['defaultProvider']=补丁['providerId']
        if 'language' in 补丁 and 补丁['language'] is not None:
            更新['language']=补丁['language']
        设置.update(条目,更新)

    def 选定提供方(自身,标识,语言):
        """缺失或不支持语言则明确失败。"""
        注册=自身.提供方表.get(标识)
        if 注册 is None:
            raise RuntimeError('Speech provider is unavailable: '+str(标识))
        if 语言 not in 注册['provider']['info']['languages']:
            raise RuntimeError('Speech provider '+str(标识)+' does not support language: '+语言)
        return 注册['provider']

    def 准备(自身,标识,选项=None):
        """启动或加入提供方拥有的准备任务。"""
        注册=自身.提供方表.get(标识)
        if 注册 is None:
            raise RuntimeError('Speech provider is unavailable: '+str(标识))
        准备=注册['provider'].get('preparation')
        if 准备 is not None:
            准备['prepare'](选项)

    def 取消准备(自身,标识):
        """显式取消准备。"""
        注册=自身.提供方表.get(标识)
        if 注册 is None:
            raise RuntimeError('Speech provider is unavailable: '+str(标识))
        准备=注册['provider'].get('preparation')
        if 准备 is not None:
            准备['cancel']()

    def 解析(自身,请求):
        """套组合默认并钉死已登记提供方。"""
        标识=请求['providerId'] if 'providerId' in 请求 and 请求['providerId'] is not None else 语音提供方标识(读易失(自身.配置['defaultProvider']))
        语言=请求['language'] if 'language' in 请求 and 请求['language'] is not None else 读易失(自身.配置['language'])
        return {
            'provider':自身.选定提供方(标识,语言),
            'audio':请求['audio'],
            'language':语言,
        }

    def 转写(自身,规格,信号):
        """只走已解析提供方，不回退。"""
        若已中止则抛出(信号)
        提供方=规格['provider']
        标识=提供方['info']['id']
        注册=自身.提供方表.get(标识)
        if 注册 is None or 注册['provider'] is not 提供方:
            raise RuntimeError('Resolved speech provider is no longer registered')
        合并=合成信号(信号,注册['lifetime'].信号)
        完成=threading.Event()
        注册['pending'].add(完成)
        try:
            若已中止则抛出(合并)
            结果=提供方['transcribe']({'audio':规格['audio'],'language':规格['language']},合并)
            若已中止则抛出(合并)
            return 结果
        finally:
            完成.set()
            注册['pending'].discard(完成)

def 应用(上下文,配置值=None):
    """挂上语音转写服务。"""
    return 语音转写(上下文,配置值)

name='speechToText'
inject=依赖
apply=应用
Config=配置
default=语音转写
