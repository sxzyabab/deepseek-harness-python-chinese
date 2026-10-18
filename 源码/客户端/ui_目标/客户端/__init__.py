'浏览器里的目标条、命令输入气泡和命令引用'
from ..异常 import 抛出会话不可用
from . import (
    文案,
    命令输入,
    命令输入视图,
    命令引用,
    槽位,
    用户文本规则,
    目标条,
)

__all__=[
    '文案','槽位','命令输入','用户文本规则','命令引用','命令输入视图','目标条',
    '依赖','应用',
]

依赖=['slots','sessions','remote','remote.goals','locale','uiConversation']#槽位、会话、远程、目标远程、文案、对话
inject=依赖#框架槽


def 应用(上下文,配置=None):
    '登记词典、命令引用、命令输入气泡和目标坞'
    上下文.uiConversation.events.register(命令输入.目标命令输入定义)#命令输入节点
    上下文.uiConversation.userText.register(用户文本规则.目标命令引用规则)#命令原文
    def 登记词典():
        '把中英文案表留在 locale。界面上的字不走翻译函数'
        return 上下文.locale.register(文案.命名空间,{'zh':文案.中文,'en':文案.英文})#登记
    上下文.副作用(登记词典,'ui-goal: dictionaries')#词典
    def 登记命令引用():
        'conversation.user.text.node 的 command 条目'
        return 上下文.slots.register({#等文本节点槽
            'name':'conversation.user.text.node',#槽名
            'key':'command',#命令
            'priority':100,#优先级
        },命令引用.命令引用)#芯片
    上下文.slots.inject('conversation.user.text.node',登记命令引用)#命令芯片
    def 登记命令输入():
        'conversation.chat.node 的 command-input 条目'
        return 上下文.slots.register({#等聊天节点槽
            'name':'conversation.chat.node',#槽名
            'key':'command-input',#命令输入
            'locale':文案.命名空间,#文案
        },命令输入视图.命令输入视图)#气泡
    上下文.slots.inject('conversation.chat.node',登记命令输入)#气泡
    会话服务=上下文.sessions#会话服务
    无当前目标={#没有 CAS 时的本地失败
        'ok':False,#失败
        'error':{'code':'no-current-goal','message':'no current goal to mutate'},#码和说明
    }#失败结束
    def 引用于(会话标识):
        '调用动词时读投影上的当前引用'
        当前绑定=会话服务.binding(会话标识)#此刻绑定
        if 当前绑定 is None:#没有绑定
            return None#无可改
        投影=当前绑定['session'].projections.面('goal')['getSnapshot']()#goal 投影
        if 投影 is None:#没有目标
            return None#无可改
        return {'id':投影['goal']['id'],'revision':投影['goal']['revision']}#CAS
    def 登记坞():
        'conversation.input.dock 的 goal 条目'
        def 注入坞(会话标识):
            '这一会话的激活源和四个变更动词'
            绑定=会话服务.binding(会话标识)#登记时的绑定
            if 绑定 is None:#不可用
                抛出会话不可用(会话标识)#两处共用
            会话=绑定['session']#会话面
            投影面=会话.projections.面('goal')#投影面
            def 读目标():
                '等初始历史打开后再读实时目标'
                if 会话服务.binding(会话标识) is not 绑定:#绑定已换
                    抛出会话不可用(会话标识)#不可用
                def 打开后读(引用):
                    '没打开就抛打开错误，否则读目标'
                    状态=引用.binding['session'].getSnapshot()#会话快照
                    if 状态['openState']!='open':#还没打开
                        打开错误=状态['openError']#打开失败
                        if 打开错误 is None:#没有现成错误
                            raise Exception('session "'+str(会话标识)+'" is not open')#未打开
                        raise 打开错误#原错误
                    return 上下文.remote.goals.get(会话标识)#实时目标
                return 会话服务.using(会话标识,{'source':'goalActivation'},打开后读)#持有到读完
            def 订激活(监听):
                '只把这一会话的激活边交出去'
                def 转发(事件):
                    '会话对上才转 goal'
                    if 事件['sessionId']==会话标识:#这一会话
                        监听(事件.get('goal'))#可能缺席
                return 上下文.remote.on('goal/activation-changed',转发)#退订器
            def 订重置(监听):
                '连接代次重置后再读'
                return 上下文.监听('connection/reset',监听)#退订器
            盒={#激活源闭包
                '快照':{},#当前快照
                '订阅数':0,#观察者
                '拆除器':[],#四份退订
                '运行中':会话.getSnapshot()['running'],#运行位
                '事件代':0,#激活边代次
                '投影代':0,#投影代次
                '读取代':0,#读取代次
                '监听':set(),#快照监听
            }#盒结束
            def 通知():
                '逐个叫监听'
                for 监听 in list(盒['监听']):#先复制
                    监听()#通知
            def 发布(下一份):
                '三个字段都没变就不通知'
                当前=盒['快照']#旧快照
                if 当前.get('id')==下一份.get('id') and 当前.get('revision')==下一份.get('revision') and 当前.get('activation')==下一份.get('activation'):#同值
                    return#不动
                盒['快照']=下一份#换上
                通知()#通知
            def 活跃引用(投影):
                '只有 active 才拿得到引用'
                if not isinstance(投影,dict):#没有投影
                    return None#非活跃
                目标=投影.get('goal')#目标
                if isinstance(目标,dict) and 目标.get('phase')=='active':#活跃
                    return 目标#整份当引用
                return None#非活跃
            def 开始读取(引用):
                '没有引用不读。代次变了就丢掉结果'
                if 引用 is None:#没有活跃目标
                    return#不读
                盒['读取代']=盒['读取代']+1#新的一次
                本次=盒['读取代']#这次的代次
                开始时事件=盒['事件代']#当时的事件代
                开始时投影=盒['投影代']#当时的投影代
                try:#读失败只警告
                    结果=读目标()#同步读
                except Exception as 错误:#对应读取被拒绝
                    print('[ui-goal] goal activation read failed:',错误)#上游警告
                    return#快照不动
                if 本次!=盒['读取代'] or 开始时事件!=盒['事件代'] or 开始时投影!=盒['投影代']:#过期
                    return#丢掉
                if 结果['ok'] is not True:#读失败
                    return#快照不动
                目标=结果['value']#实时目标
                if 目标 is None:#没有实时目标
                    if 活跃引用(投影面['getSnapshot']()) is None:#投影也已空
                        发布({})#清空
                    return#结束
                发布({#带上武装
                    'id':目标['id'],#身份
                    'revision':目标['revision'],#修订
                    'activation':目标['activation'],#武装
                })#发布结束
            def 刷新投影():
                '投影驱动清空或换修订，并再读一次'
                盒['投影代']=盒['投影代']+1#投影代
                之前=盒['快照']#通知前的对象
                引用=活跃引用(投影面['getSnapshot']())#当前活跃引用
                if 引用 is None:#不再活跃
                    if 'id' in 盒['快照']:#原来有目标
                        发布({})#清空
                else:#仍活跃
                    if 盒['快照'].get('id')!=引用['id'] or 盒['快照'].get('revision')!=引用['revision']:#身份或修订变了
                        发布({'id':引用['id'],'revision':引用['revision']})#先去掉旧武装
                    开始读取(引用)#再读权威武装
                if 盒['快照'] is 之前:#激活快照没变
                    通知()#条仍要重读投影
            def 激活变化(目标):
                '激活边直接覆盖快照，并作废进行中的读取'
                盒['事件代']=盒['事件代']+1#事件代
                盒['读取代']=盒['读取代']+1#作废读取
                if 目标 is None:#目标没了
                    发布({})#清空
                else:#有目标
                    发布({#整份边
                        'id':目标['id'],#身份
                        'revision':目标['revision'],#修订
                        'activation':目标['activation'],#武装
                    })#发布结束
            def 运行变化():
                '运行位翻转才重读'
                下一份=会话.getSnapshot()['running']#现在是否在跑
                if 下一份==盒['运行中']:#没翻
                    return#不动
                盒['运行中']=下一份#记下
                开始读取(活跃引用(投影面['getSnapshot']()))#重读
            def 连接重置():
                '代次重置后按当前投影重读'
                盒['事件代']=盒['事件代']+1#事件代
                盒['投影代']=盒['投影代']+1#投影代
                开始读取(活跃引用(投影面['getSnapshot']()))#重读
            def 取快照():
                '当前激活快照'
                return 盒['快照']#同一对象直到发布
            def 订阅(监听):
                '第一个订阅者才挂上投影、运行、激活和重置'
                盒['监听'].add(监听)#登记
                if 盒['订阅数']==0:#还没人看
                    盒['拆除器']=[#四份退订
                        投影面['subscribe'](刷新投影),#投影
                        会话.订阅(运行变化),#运行位
                        订激活(激活变化),#激活边
                        订重置(连接重置),#连接重置
                    ]#退订结束
                    盒['运行中']=会话.getSnapshot()['running']#此刻运行位
                    刷新投影()#立刻对齐
                盒['订阅数']=盒['订阅数']+1#加一
                def 退订():
                    '最后一个订阅者卸掉四份监听'
                    盒['监听'].discard(监听)#拿掉
                    盒['订阅数']=盒['订阅数']-1#减一
                    if 盒['订阅数']==0:#没人看了
                        for 拆除 in 盒['拆除器']:#逐个
                            拆除()#卸
                        盒['拆除器']=[]#清空
                        盒['读取代']=盒['读取代']+1#作废读取
                return 退订#退订
            目标激活={'getSnapshot':取快照,'subscribe':订阅}#激活源
            def 编辑(陈述):
                '按当前引用替换陈述'
                引用=引用于(会话标识)#CAS
                if 引用 is None:#没有目标
                    return 无当前目标#本地失败
                return 上下文.remote.goals.edit(会话标识,引用,{'objective':陈述})#编辑
            def 暂停():
                '暂停活跃目标'
                引用=引用于(会话标识)#CAS
                if 引用 is None:#没有目标
                    return 无当前目标#本地失败
                return 上下文.remote.goals.pause(会话标识,引用)#暂停
            def 恢复():
                '恢复暂停的目标'
                引用=引用于(会话标识)#CAS
                if 引用 is None:#没有目标
                    return 无当前目标#本地失败
                return 上下文.remote.goals.resume(会话标识,引用)#恢复
            def 清除():
                '清除当前目标'
                引用=引用于(会话标识)#CAS
                if 引用 is None:#没有目标
                    return 无当前目标#本地失败
                return 上下文.remote.goals.clear(会话标识,引用)#清除
            return {#注入面
                'hooks':{'goalActivation':目标激活},#激活钩子
                'onEdit':编辑,#编辑
                'onPause':暂停,#暂停
                'onResume':恢复,#恢复
                'onClear':清除,#清除
            }#注入结束
        return 上下文.slots.register({#等输入坞
            'name':'conversation.input.dock',#槽名
            'id':'goal',#条目
            'order':10,#顺序
            'locale':文案.命名空间,#文案
            'inject':注入坞,#按会话注入
        },目标条.目标坞)#目标坞
    上下文.slots.inject('conversation.input.dock',登记坞)#坞


apply=应用
