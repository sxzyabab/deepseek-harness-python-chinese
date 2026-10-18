from ...存储 import 创建快照存储

__all__=['权限目录']

class 权限目录:
    '整份浏览器进程一份权限目录。斜杠弹出和撰写器席共用'
    def __init__(自身,上下文):
        '先订失效源再读，关掉安装和第一次读取之间的空档'
        自身.上下文=上下文
        自身.存储=创建快照存储({'value':None})
        自身.失效滴答=创建快照存储({'count':0})
        自身.连接=上下文.获取服务('connection')
        自身.世代标识=None
        自身.已初始化=False
        自身.纪元=0
        自身.待决=None
        自身.失败=Exception('permission catalog has no complete value')
        自身.已拆除=False
        def 目录已变(*位置参数):
            '目录通知先作废已显示的选项，再读一份新的'
            自身.失效()
            自身.刷新()
        自身.停目录=上下文.remote.on('permission-presets/catalog-changed',目录已变)
        def 世代已变(*位置参数):
            '连接世代换了就丢掉旧宿主的目录'
            自身.同步世代()
        自身.停世代=自身.连接.generation.subscribe(世代已变)
        自身.同步世代()

    def 当前世代(自身):
        '活动连接的世代 id。没有连接则 None'
        快照=自身.连接.generation.getSnapshot()
        if isinstance(快照,dict) and 'id' in 快照:
            return 快照['id']
        return None

    def 失效(自身):
        '给还握着旧选项的界面一拍。拆除之后不会再进来'
        自身.失效滴答.set({'count':自身.失效滴答.getSnapshot()['count']+1})

    def 刷新(自身):
        '对活动世代强制再读一份完整目录'
        if 自身.已拆除:
            return
        世代标识=自身.当前世代()
        if 世代标识 is None:
            return
        if 世代标识!=自身.世代标识:
            自身.同步世代()
            return
        自身.开始读取(世代标识)

    def 加载(自身):
        '弹出打开时取当前世代的完整目录。进行中的刷新先落定'
        if 自身.待决 is None and 自身.存储.getSnapshot()['value'] is None:
            自身.刷新()
        while 自身.已拆除 is not True:
            世代标识=自身.当前世代()
            if 世代标识 is None:
                raise Exception('permission catalog has no active Host connection')
            if 世代标识!=自身.世代标识:
                自身.同步世代()
                continue
            if 自身.待决 is not None:
                状态=自身.存储.getSnapshot()
                if 状态['value'] is not None:
                    return 状态['value']
                raise 自身.失败
            状态=自身.存储.getSnapshot()
            if 状态['value'] is not None:
                return 状态['value']
            raise 自身.失败
        raise Exception('permission catalog directory is disposed')

    def 拆除(自身):
        '停止订阅，并让还没写回的读取作废'
        if 自身.已拆除:
            return
        自身.已拆除=True
        自身.纪元=自身.纪元+1
        自身.待决=None
        自身.停世代()
        自身.停目录()

    def 同步世代(自身):
        '世代丢掉或换代时清掉旧宿主的目录，再为新世代读一份'
        if 自身.已拆除:
            return
        世代标识=自身.当前世代()
        if 自身.已初始化 and 世代标识==自身.世代标识:
            return
        if 自身.已初始化:
            自身.失效()
        自身.已初始化=True
        自身.世代标识=世代标识
        自身.纪元=自身.纪元+1
        自身.待决=None
        自身.失败=Exception('permission catalog has no complete value')
        自身.存储.set({'value':None})
        if 世代标识 is not None:
            自身.开始读取(世代标识)

    def 开始读取(自身,世代标识):
        '同一世代里纪元最新的一次读取才写回'
        纪元=自身.纪元+1
        自身.纪元=纪元
        自身.失败=Exception('permission catalog has no complete value')
        操作={'纪元':纪元}
        自身.待决=操作
        try:
            try:
                结果=自身.上下文.remote.permissionPresets.catalog()
                if 结果['ok'] is not True:
                    错误体=结果['error']
                    if isinstance(错误体,dict):
                        码=错误体['code']
                        消息=错误体['message']
                    else:
                        码=错误体.code
                        消息=错误体.message
                    raise Exception(str(码)+': '+str(消息))
                if 自身.接受(纪元,世代标识) is not True:
                    return
                自身.存储.set({'value':结果['value']})
            except Exception as 错误:
                if 自身.接受(纪元,世代标识) is not True:
                    return
                自身.失败=错误
                自身.存储.set({'value':None})
        finally:
            if 自身.待决 is 操作:
                自身.待决=None

    def 接受(自身,纪元,世代标识):
        '拆除、纪元或连接世代对不上的读取不能写回'
        if 自身.已拆除:
            return False
        if 纪元!=自身.纪元:
            return False
        if 世代标识!=自身.世代标识:
            return False
        return 自身.当前世代()==世代标识
