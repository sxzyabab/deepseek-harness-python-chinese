'浏览器里的用户提问：文案、作曲卡片、迟到回复，以及转发来的提问瀑布'
from ...模块.客户端.通告 import 取握手窗口
import threading
from ....基础设施.通用工具 import 启动守护线程#认领结束与延迟释放
from ...存储 import 声明存储#草稿存储
from ..异常 import 提问拒绝#线路拒绝
from . import (
    文案,
    约定,
    问题回复,
    问题回复视图,
    提问撰写器,
    计划审阅面板,
)
from .文案 import 中文,英文#登记用的两份表
from .约定.槽位 import 待答提问#卡片
from .问题回复 import 问题回复定义#对话节点
from .问题回复视图 import 问题回复视图#气泡
from .提问撰写器 import 提问撰写器#作曲入口

__all__=['文案','约定','问题回复','问题回复视图','提问撰写器','计划审阅面板','依赖','应用']

命名空间='question'#文案命名空间
依赖=['sessions','remote','remote.userQuestions','uiSession','slots','locale','uiConversation']#所需服务


def 取(对象,键,默认=None):
    '字典用键，对象用同名属性'
    if isinstance(对象,dict):#字典
        return 对象[键] if 键 in 对象 else 默认#键
    return getattr(对象,键,默认)#属性


def 是记录(值):
    '非空对象，不是列表'
    return isinstance(值,dict)#字典


class 提问卡片表:
    '按卡片键保存已发布的提问。隐藏的卡片不在待处理表里，仍由这里决定何时结束'
    def __init__(自身,发布):
        '记下待处理交互的发布函数'
        自身.发布=发布#发布到会话
        自身._表={}#键到卡片

    def 按调用(自身,会话标识,调用标识):
        '按会话和工具调用找卡片'
        return 自身._表.get(待答提问.键于(会话标识,调用标识))#可能没有

    def 来源(自身,键):
        '键控钩子读的卡片。没有则缺席'
        卡片=自身._表.get(键)#卡片
        if 卡片 is None:#没有
            return None#缺席
        return 卡片['待答']#可观察卡片

    def 全部(自身):
        '当前所有卡片'
        return list(自身._表.values())#拷贝

    def 会话键(自身,会话标识):
        '这一会话还登记着的草稿键'
        结果=[]#键
        for 卡片 in 自身.全部():#逐张
            if 卡片['待答'].sessionId==会话标识:#同一会话
                结果.append(卡片['待答'].key)#键
        return 结果#键

    def 确保(自身,会话标识,问题,调用标识):
        '有调用标识就复用。没有则每次新建'
        if 调用标识 is not None:#点了名
            已有=自身.按调用(会话标识,调用标识)#已有
            if 已有 is not None:#复用
                return 已有#同一张
        def 同胞():
            '创建之后仍向登记表要这一会话的键'
            return 自身.会话键(会话标识)#活键
        return 自身._创建(待答提问(会话标识,问题,调用标识,同胞))#新建

    def _创建(自身,待):
        '发布到作曲座位，并记下这张卡片'
        请求集合=set()#还没结束的转发
        def 委托清理():
            '卸下时把瀑布交给下一环，并等转发结束'
            待.委托()#交给下一环
            for 门闩 in list(请求集合):#逐个
                门闩.wait()#等结束
        箱={'撤销':自身.发布(待,委托清理)}#当前发布
        def 隐藏():
            '从座位撤下，请求还在'
            if 箱['撤销'] is not None:#还发布着
                箱['撤销']()#撤销
                箱['撤销']=None#记下
        def 揭示():
            '重新发布，让它压过别的待处理'
            if 箱['撤销'] is not None:#先撤掉旧的
                箱['撤销']()#撤销
            箱['撤销']=自身.发布(待,委托清理)#再发布
        卡片={'待答':待}#先占位，移除要认出自己
        def 移除():
            '从登记表删掉并关掉卡片'
            if 自身._表.get(待.key) is not 卡片:#已经不是这一张
                return
            del 自身._表[待.key]#删掉
            待.关闭()#通知草稿
            if 箱['撤销'] is not None:#还发布着
                箱['撤销']()#撤销
                箱['撤销']=None#记下
        def 跟踪(门闩):
            '转发开始时记下，结束时摘掉'
            请求集合.add(门闩)#加入
            def 结束():
                '这一次转发已经结束'
                请求集合.discard(门闩)#摘掉
            return 结束#摘掉函数
        def 有请求():
            '还有转发没结束'
            return len(请求集合)>0#还有
        卡片['隐藏']=隐藏#撤下
        卡片['揭示']=揭示#再发布
        卡片['移除']=移除#结束
        卡片['跟踪']=跟踪#跟踪转发
        卡片['有请求']=有请求#是否还在转发
        if 待.review is None:#活请求关掉只是隐藏
            待.接上座位({'隐藏':隐藏})#隐藏
        else:#只读卡关掉就结束
            待.接上座位({'隐藏':移除})#移除
        自身._表[待.key]=卡片#登记
        return 卡片#这张

    def 揭示(自身,会话标识,调用标识):
        '把还能回答的那张放回座位'
        卡片=自身.按调用(会话标识,调用标识)#卡片
        if 卡片 is None:#没有
            return False#不能
        卡片['揭示']()#放回
        return True#放回了

    def 复核(自身,会话标识,调用标识,记录):
        '没有活卡片就按记录做一张只读卡，然后放回座位'
        卡片=自身.按调用(会话标识,调用标识)#已有
        if 卡片 is None:#没有活的
            def 同胞():
                '这张只读卡也参与草稿修剪'
                return 自身.会话键(会话标识)#活键
            卡片=自身._创建(待答提问(#只读
                会话标识,
                记录['questions'],
                调用标识,
                同胞,
                记录['answers'],
            ))
        卡片['揭示']()#放回
        return True#总是有一张

    def 释放(自身):
        '插件卸下时，把每张还活着的瀑布交回去'
        for 卡片 in 自身.全部():#逐张
            卡片['待答'].委托()#交给下一环
            卡片['移除']()#删掉


class 回答面板:
    '给工具行调用的两个动作。方法名保持 reveal 和 review'
    def __init__(自身,卡片):
        '记下卡片表'
        自身.卡片=卡片#卡片表

    def reveal(自身,会话标识,调用标识):
        '把面板放回输入框'
        return 自身.卡片.揭示(会话标识,调用标识)#是否还在

    def review(自身,会话标识,调用标识,记录):
        '打开只读记录'
        return 自身.卡片.复核(会话标识,调用标识,记录)#总是真


def 应用(上下文,配置=None):
    '登记文案、草稿、提问卡片、作曲链、迟到回复，并接上提问瀑布'
    def 登记词典():
        '登记中英文案表。页面上的字不读英文表'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记
    上下文.副作用(登记词典,'ui-user-questions: dictionaries')#词典寿命

    def 初始草稿():
        '每个会话一份空的进度表'
        return {'progressByRequest':{}}#空表
    def 替换(草稿,请求键,进度):
        '按请求键写下这一条进度'
        草稿['progressByRequest'][请求键]=进度#替换
    def 清除(草稿,请求键):
        '删掉这一条，其它请求留下'
        留下={}#剩下的
        for 键,值 in 草稿['progressByRequest'].items():#逐条
            if 键!=请求键:#不是这一条
                留下[键]=值#留下
        草稿['progressByRequest']=留下#换上
    def 修剪(草稿,保留):
        '只留下还活着的请求'
        活=set(保留)#还要的键
        留下={}#剩下的
        for 键,值 in 草稿['progressByRequest'].items():#逐条
            if 键 in 活:#还活着
                留下[键]=值#留下
        草稿['progressByRequest']=留下#换上
    提问草稿存储=声明存储({#会话草稿
        'init':初始草稿,#空表
        'persist':'dsh.user-questions.drafts.v1',#持久化名
        'actions':{'replace':替换,'clear':清除,'prune':修剪},#三个动作
    })

    def 优先级(交互):
        '计划审阅比普通提问更靠前'
        if 交互.kind=='plan-review':#计划
            return 2#更高
        return 1#普通提问
    登记待处理=上下文.uiSession.registerPendingInteraction(优先级)#发布函数
    卡片=提问卡片表(登记待处理)#卡片表
    def 卡片寿命():
        '插件卸下时交回每张瀑布'
        def 拆():
            '释放全部卡片'
            卡片.释放()#交回
        return 拆#拆除
    上下文.副作用(卡片寿命,'ui-user-questions: cards')#卡片寿命

    def 面板寿命():
        '把打开面板的两个动作交给工具行'
        return 上下文.reflect.provide('userQuestionPanels',回答面板(卡片))#窄接口
    上下文.副作用(面板寿命,'ui-user-questions: answer panels')#面板寿命

    def 继续提问():
        '把投影里还能回答的调用做成卡片。收件箱里排队的回复先不显示成可编辑'
        会话服务=上下文.sessions#会话
        停止表={}#会话到退订
        def 调和():
            '按当前会话列表重绑投影，并增删卡片'
            快照=会话服务.list.getSnapshot()#列表
            已绑={}#这一轮还在的会话
            for 摘要 in 快照['byId'].values():#逐场
                会话标识=摘要['id']#标识
                绑定=会话服务.binding(会话标识)#绑定
                if 绑定 is not None:#还持有
                    已绑[会话标识]=绑定#记下
            for 会话标识,停止 in list(停止表.items()):#旧的
                if 会话标识 in 已绑:#还在
                    continue#留着
                停止()#退订
                del 停止表[会话标识]#摘掉
            for 会话标识,绑定 in 已绑.items():#新的
                if 会话标识 in 停止表:#已经订了
                    continue#留着
                提问面=绑定['session'].projections.面('userQuestions')#提问投影
                收件面=绑定['session'].projections.面('inbox')#收件箱
                停提问=提问面['subscribe'](调和)#提问变化
                停收件=收件面['subscribe'](调和)#收件变化
                def 停止(停提问=停提问,停收件=停收件):
                    '这一场的两份投影都退订'
                    停提问()#提问
                    停收件()#收件
                停止表[会话标识]=停止#记下
            行表={}#还能回答的行
            for 会话标识,绑定 in 已绑.items():#逐场
                投影=绑定['session'].projections.面('userQuestions')['getSnapshot']()#提问
                收件=绑定['session'].projections.面('inbox')['getSnapshot']()#收件
                排队=set()#还没被接纳的回复
                下步=取(收件,'next-step',[]) or []#下一步
                下轮=取(收件,'next-turn',[]) or []#下一轮
                for 消息 in list(下步)+list(下轮):#两队
                    if not 是记录(消息):#不是对象
                        continue#跳过
                    来源=取(消息,'source')#来源
                    if not 是记录(来源):#不是对象
                        continue#跳过
                    if 来源.get('kind')=='user-question-reply' and isinstance(来源.get('callId'),str):#排队的回复
                        排队.add(来源['callId'])#记下
                活跃=取(投影,'active',[]) or []#还能回答的
                for 行 in 活跃:#逐行
                    if 取(行,'state')=='continued' and 取(行,'callId') in 排队:#回复还在队列里
                        continue#先不显示成可编辑
                    行表[待答提问.键于(会话标识,取(行,'callId'))]={'sessionId':会话标识,'row':行}#留下
            for 项 in 行表.values():#逐行接上
                会话标识=项['sessionId']#会话
                行=项['row']#行
                if 取(行,'state')=='continued':#已经继续
                    一张=卡片.确保(会话标识,取(行,'questions'),取(行,'callId'))#卡片
                    def 远程作答(答案,会话标识=会话标识,调用标识=取(行,'callId')):
                        '把答案送到宿主。失败用错误句，成功返回是否还接受'
                        结果=上下文.remote.userQuestions.answer(会话标识,调用标识,答案)#远程
                        if 取(结果,'ok') is not True:#失败
                            raise Exception(取(取(结果,'error'),'message'))#错误句
                        return 取(结果,'value')#是否接受
                    一张['待答'].接上远程({'作答':远程作答})#远程通道
                    一张['待答'].设状态('continued')#已继续
                    continue#下一行
                已有=卡片.按调用(会话标识,取(行,'callId'))#已有
                if 已有 is not None:#还在
                    已有['待答'].设状态('open')#打开
            for 一张 in 卡片.全部():#不再可答的删掉
                待=一张['待答']#卡片
                if 待.callId is None or 待.review is not None or 待.key in 行表 or 一张['有请求']() or 待.有瀑布():#还要留
                    continue#留着
                一张['移除']()#删掉
        调和()#先对齐一次
        停列表=会话服务.list.subscribe(调和)#列表变化
        def 停止():
            '退订列表和每一场的投影'
            停列表()#列表
            for 停止项 in 停止表.values():#逐场
                停止项()#退订
            停止表.clear()#清空
        return 停止#效果拆除
    上下文.副作用(继续提问,'ui-user-questions: continued questions')#投影寿命

    def 选择(属性):
        '只选中提问卡片'
        待=取(属性,'pendingInteraction')#当前待处理
        if isinstance(待,待答提问):#是提问
            return 待#命中
        return None#不是

    def 注入():
        '按卡片键提供可观察源'
        def 提问卡(键):
            '登记表里的那张卡片'
            return 卡片.来源(键)#可能没有
        return {'keyedHooks':{'questionCard':提问卡}}#键控钩子

    def 登记撰写():
        '等作曲链出现后登记提问入口'
        return 上下文.slots.register({#链条目
            'name':'conversation.composer',#槽名
            'select':选择,#只命中提问
            'locale':命名空间,#文案命名空间
            'store':提问草稿存储,#草稿
            'inject':注入,#卡片钩子
            'children':{#计划动作由别的包填
                'conversation.plan-review.actions':{'kind':'list','scope':'session'},
            },
        },提问撰写器)#入口
    上下文.slots.inject('conversation.composer',登记撰写)#等槽出现
    上下文.uiConversation.events.register(问题回复定义)#迟到回复
    def 登记回复():
        '等聊天节点出现后登记回复气泡'
        return 上下文.slots.register({#节点
            'name':'conversation.chat.node',#槽名
            'key':'question-reply',#键
            'locale':命名空间,#文案命名空间
        },问题回复视图)#气泡
    上下文.slots.inject('conversation.chat.node',登记回复)#等槽出现

    def 监听(拥有方,请求,下一):
        '有会话就把这次瀑布接到卡片上，作答、委托或取消后再把结果交回'
        会话标识=上下文.sessions.scopeOf(拥有方)#这条瀑布的会话
        if 会话标识 is None:#没有会话
            return 下一()#交给下一环
        等待=取(请求,'wait')#等待
        调用标识=取(等待,'callId')#调用
        一张=卡片.确保(会话标识,取(请求,'questions'),调用标识)#卡片
        窗口=取握手窗口()#浏览器
        认领寿命=窗口.AbortController()#认领寿命
        请求信号=取(请求,'signal')#请求信号
        if 请求信号 is None:#只有本地寿命
            认领信号=认领寿命.signal#本地
        else:#两边任一中止都算
            认领信号=窗口.AbortSignal.any([认领寿命.signal,请求信号])#合并
        认领=None#流
        认领线程=None#等第二帧
        委托请求=None#效果拆除时委托
        释放认领=None#效果拆除器
        if 取(等待,'timed') is True and 调用标识 is not None:#计时等待
            def 装认领():
                '向宿主要剩余时间。拆除时先委托再中止'
                nonlocal 认领
                认领=上下文.remote.userQuestions.attachWait(会话标识,调用标识,认领信号)#流
                def 拆():
                    '委托、中止，并等认领线程结束'
                    if 委托请求 is not None:#还没委托
                        委托请求()#交给下一环
                    认领寿命.abort()#中止
                    if 认领 is not None and callable(getattr(认领,'dispose',None)):#流有拆除
                        认领.dispose()#拆除
                    if 认领线程 is not None:#还在等第二帧
                        认领线程.join()#等它结束
                return 拆#拆除
            释放认领=上下文.副作用(装认领,'ui-user-questions: foreground claim')#认领寿命
        已放={'值':False}#认领效果只拆一次
        完成门=threading.Event()#转发结束
        结束跟踪=一张['跟踪'](完成门)#记入卡片
        箱={'种类':None,'答案':None,'错误':None}#瀑布或认领的结果
        门闩=threading.Event()#有结果了
        锁=threading.Lock()#只收第一个
        def 放入(种类,答案=None,错误=None):
            '竞速时只留下先到的结果'
            with 锁:#互斥
                if 箱['种类'] is not None:#已经有了
                    return False#丢掉
                箱['种类']=种类#种类
                箱['答案']=答案#答案
                箱['错误']=错误#错误
            门闩.set()#放行
            return True#收下了
        已结算=False#通道只结算一次
        委托标记=object()#这一次委托的身份
        通道={}#先占位，结束时要交给卡片
        def 结束(写入):
            '结算一次，并让卡片拆掉这条瀑布'
            nonlocal 已结算
            if 已结算:#已经结束
                return
            已结算=True#记下
            if hasattr(认领信号,'removeEventListener'):#浏览器信号
                认领信号.removeEventListener('abort',中止时)#摘掉
            写入()#写入结果
            一张['待答'].拆下瀑布(通道)#拆掉
        def 中止时(_事件=None):
            '请求中止时用 ASK_ABORTED 结束'
            def 写入():
                '拒绝为已中止'
                放入('错误',错误=提问拒绝('ASK_ABORTED'))#中止
            结束(写入)#结算
        def 解决(答案):
            '用户答完'
            def 写入():
                '记下答案'
                放入('答案',答案=答案)#答案
            结束(写入)#结算
        def 拒绝(码):
            '用线路码拒绝'
            def 写入():
                '记下拒绝'
                放入('错误',错误=提问拒绝(码))#拒绝
            结束(写入)#结算
        def 委托():
            '交给瀑布下一环'
            def 写入():
                '记下委托'
                放入('委托',错误=委托标记)#委托
            结束(写入)#结算
        通道['截止']=None#等第一帧再填
        通道['解决']=解决#作答
        通道['拒绝']=拒绝#拒绝
        通道['委托']=委托#委托
        if hasattr(认领信号,'addEventListener'):#浏览器信号
            认领信号.addEventListener('abort',中止时,{'once':True})#只听一次
            if 认领信号.aborted:#已经中止
                中止时()#马上结束
        try:#接到卡片并等待
            迭代=None#帧
            if 认领 is not None and hasattr(认领,'__iter__') and not isinstance(认领,(str,bytes,dict)):#可迭代的流
                迭代=iter(认领)#迭代器
            if 迭代 is None:#没有认领帧
                截止=None#不限时
            else:#读第一帧
                try:#第一帧
                    开头=next(迭代)#剩余时间
                except StopIteration:#流已经结束
                    return 下一()#交给下一环
                if 是记录(开头) and 开头.get('done') is True:#显式结束
                    return 下一()#交给下一环
                if 是记录(开头) and 是记录(开头.get('value')) and 'remainingMs' in 开头['value']:#异步迭代结果
                    剩余=开头['value']['remainingMs']#剩余
                else:#直接的帧
                    剩余=开头['remainingMs']#剩余
                截止=窗口.Date.now()+剩余#客户端截止
            通道['截止']=截止#填上
            if 已结算 or getattr(认领信号,'aborted',False) is True:#第一帧之前或之后已经中止
                门闩.wait()#等中止写入
                if 箱['错误'] is not None and 箱['错误'] is not 委托标记:#有错误
                    raise 箱['错误']#抛出
                return 箱['答案']#答案
            def 委托这一次():
                '效果拆除时把瀑布交给下一环'
                通道['委托']()#委托
            委托请求=委托这一次#留给拆除
            一张['待答'].接上瀑布(通道)#挂到卡片
            if 迭代 is not None:#还有后续帧
                def 等结束():
                    '第二帧或流结束都表示前台等待没了'
                    try:#再读一帧
                        next(迭代)#等待结束
                    except StopIteration:#正常结束
                        错误=Exception('the foreground question wait ended')#固定句
                    except Exception as 原因:#流自己的失败
                        错误=原因#原样
                    else:#读到了也算结束
                        错误=Exception('the foreground question wait ended')#固定句
                    放入('错误',错误=错误)#和瀑布竞速
                认领线程=启动守护线程(等结束)#不挡住作答
            门闩.wait()#等作答、委托、取消或认领结束
            if 箱['种类']=='委托' or 箱['错误'] is 委托标记:#交给下一环
                if 释放认领 is not None and 已放['值'] is False:#下一环之前先放开认领
                    已放['值']=True#记下
                    释放认领()#拆除
                return 下一()#下一环
            if 箱['错误'] is not None:#失败
                raise 箱['错误']#抛出
            return 箱['答案']#答案
        finally:#收尾
            if 已放['值'] is True:#委托时已经拆过
                pass#不再拆
            elif 释放认领 is None:#没有认领效果
                认领寿命.abort()#中止本地寿命
            elif 认领线程 is None:#认领没有第二帧
                释放认领()#马上拆
            else:#宿主要等结果送出后再关认领
                def 稍后释放(线程=认领线程,释放=释放认领):
                    '第二帧结束后再拆除认领'
                    线程.join()#等线程
                    释放()#拆除
                启动守护线程(稍后释放)#不挡住返回
            if 调用标识 is None:#没有投影行
                一张['移除']()#卡片跟瀑布一起结束
            完成门.set()#放行委托清理
            结束跟踪()#从集合摘掉
    getattr(上下文.remote,'$on')('user-questions/request',监听)#消费提问瀑布


inject=依赖#框架槽
apply=应用#框架槽
