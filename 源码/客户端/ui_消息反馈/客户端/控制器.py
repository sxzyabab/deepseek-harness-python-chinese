'一场会话的消息反馈。写入带着上次看到的版本，冲突用回复里的权威项对齐'
from ...模块.客户端.通告 import 取握手窗口

__all__=['描述失败','消息反馈控制器','成功结果','已拆除结果']

成功结果={'ok':True}
已拆除结果={
    'ok':False,
    'error':{'code':'disposed','message':'feedback controller is disposed'},
}

def 描述失败(码):
    '一条业务失败码的开发说明。界面不显示这句'
    if 码=='session-not-found':
        return 'this session is no longer persisted'
    if 码=='target-not-found':
        return 'this message is not a persisted assistant message'
    if 码=='version-conflict':
        return 'feedback changed elsewhere'
    if 码=='note-blank':
        return 'a note must contain a non-whitespace character'
    if 码=='note-too-large':
        return 'the note is too long'
    return 码

def 失败(码):
    '按业务失败码造拒绝结果'
    return {'ok':False,'error':{'code':码,'message':描述失败(码)}}

def 载体失败(错误):
    '宿主载体自己的码和说明原样放进拒绝结果'
    return {'ok':False,'error':{'code':错误['code'],'message':错误['message']}}

class 消息反馈控制器:
    '一场会话的消息反馈。一次列表读数供这一场里每条消息用'
    def __init__(自身,远程,会话标识):
        '冷启动。还没有人来读之前保持 cold'
        自身.远程=远程
        自身.会话标识=会话标识
        自身.视图={'status':'cold','items':{},'error':None}
        自身.监听者=set()
        自身.已拆除=False

    def getSnapshot(自身):
        '返回当前视图'
        return 自身.视图

    def subscribe(自身,监听):
        '订阅视图替换，返回退订'
        自身.监听者.add(监听)
        def 退订():
            '卸下这一份订阅'
            自身.监听者.discard(监听)
        return 退订

    def 确保(自身):
        '已经就绪就直接成功。上次失败了还可以再读'
        if 自身.视图['status']=='ready':
            return 成功结果
        return 自身.刷新()

    def 刷新(自身):
        '重读整份列表并发布。同步调用当场返回结果'
        自身.发布({'status':'loading','items':自身.视图['items'],'error':None})
        载体=自身.远程.list({'sessionId':自身.会话标识})
        if 自身.已拆除:
            return 成功结果
        if not 载体['ok']:
            自身.发布({
                'status':'error',
                'items':自身.视图['items'],
                'error':载体['error']['message'],
            })
            return 载体失败(载体['error'])
        业务=载体['value']
        if not 业务['ok']:
            自身.发布({
                'status':'error',
                'items':自身.视图['items'],
                'error':描述失败(业务['error']['code']),
            })
            return 失败(业务['error']['code'])
        条目={}
        for 项 in 业务['value']['items']:
            条目[项['messageId']]=项
        自身.发布({'status':'ready','items':条目,'error':None})
        return 成功结果

    def 重同步(自身):
        '重连后的读取走变更队列的同一条路，避免盖掉刚写上的版本'
        def 再读():
            '这次操作本身就是读取，不再预播种'
            return 自身.刷新()
        return 自身.变更(再读,False)

    def 评分(自身,消息标识,评价,条目=None):
        '按上次看到的版本写入。条目里没有的说明和分类不会留在存储里'
        if 条目 is None:
            条目={}
        def 操作():
            '对着当前条目提交写入，冲突则改用回复里的权威项'
            表=自身.视图['items']
            观察=表[消息标识] if 消息标识 in 表 else None
            版本=None if 观察 is None else 观察['version']
            请求={
                'sessionId':自身.会话标识,
                'messageId':消息标识,
                'rating':评价,
                'ifVersion':版本,
            }
            if 'text' in 条目:
                请求['note']=条目['text']
            if 'category' in 条目:
                请求['category']=条目['category']
            载体=自身.远程.put(请求)
            if not 载体['ok']:
                return 载体失败(载体['error'])
            业务=载体['value']
            if 业务['ok']:
                自身.提交(消息标识,业务['value'])
                return 成功结果
            if 业务['error']['code']=='version-conflict':
                自身.提交(消息标识,业务['error']['current'])
            return 失败(业务['error']['code'])
        return 自身.变更(操作,True)

    def 撤回(自身,消息标识,评价):
        '当前评分仍是这一档才删除。中途被别人改过就什么也不写'
        def 操作():
            '排队之后再核对，避免把过期撤回写成一条空评分'
            表=自身.视图['items']
            观察=表[消息标识] if 消息标识 in 表 else None
            if 观察 is None or 观察['rating']!=评价:
                return 成功结果
            载体=自身.远程.delete({
                'sessionId':自身.会话标识,
                'messageId':消息标识,
                'ifVersion':观察['version'],
            })
            if not 载体['ok']:
                return 载体失败(载体['error'])
            业务=载体['value']
            if 业务['ok']:
                自身.提交(消息标识,None)
                return 成功结果
            if 业务['error']['code']=='version-conflict':
                自身.提交(消息标识,业务['error']['current'])
            return 失败(业务['error']['code'])
        return 自身.变更(操作,True)

    def 拆除(自身):
        '所属纤程卸下后不再通知，也不再接受变更'
        自身.已拆除=True
        自身.监听者.clear()

    def 变更(自身,操作,播种):
        '先保证列表已读，再跑这一次变更。同步返回结果'
        if 自身.已拆除:
            return 已拆除结果
        if 播种:
            已加载=自身.确保()
            if not 已加载['ok']:
                return 已加载
            if 自身.已拆除:
                return 已拆除结果
        return 操作()

    def 提交(自身,消息标识,项):
        '换掉这一条。其余条目仍是原来的对象'
        条目=dict(自身.视图['items'])
        if 项 is None:
            if 消息标识 in 条目:
                del 条目[消息标识]
        else:
            条目[消息标识]=项
        自身.发布({'status':'ready','items':条目,'error':None})

    def 发布(自身,视图):
        '换上新视图。某个订阅者抛错只记下来，不挡住其余'
        自身.视图=视图
        for 监听 in tuple(自身.监听者):
            try:
                监听()
            except Exception as 错误:
                取握手窗口().console.error(
                    '[ui-message-feedback] subscriber threw:',
                    错误,
                )
