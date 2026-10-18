'迟到的提问回复：把 user-question-reply 收成问题和答案'
import json
from ....内核.会话.表面 import 是否追加表面事件#追加表面

__all__=['问题回复定义','回复答案值']


def 是记录(值):
    '非空对象，不是列表'
    return isinstance(值,dict)#字典才是记录


def 回复来源(事件):
    '持久消息上的提问回复来源。对不上则没有'
    来源=事件['data'].get('source')#来源
    if 是记录(来源) and 来源.get('kind')=='user-question-reply' and isinstance(来源.get('callId'),str) and 来源.get('outcome')=='answered':#是已回答的回复
        return {'callId':来源['callId'],'outcome':'answered'}#来源
    return None#不是回复


def 回复答案值(数据,编号):
    '一道题的展示顺序：先是选中的标签，再是非空白的自定义答案'
    答案=None#这一题
    for 项 in 数据['answers']:#逐条
        if 项.get('id')==编号:#命中
            答案=项#记下
            break#找到
    自定义=''#自定义文本
    if 答案 is not None and isinstance(答案.get('custom'),str):#有自定义
        自定义=答案['custom'].strip()#去掉空白
    选中=[]#选中的标签
    if 答案 is not None and isinstance(答案.get('selected'),list):#有选择
        选中=list(答案['selected'])#拷贝
    if 自定义=='':#没有自定义
        return 选中#只有选择
    return 选中+[自定义]#选择后面跟上自定义


def 匹配(事件):
    '只认追加进来的用户消息，而且来源必须是提问回复'
    if 事件.get('type')!='user/message' or not 是否追加表面事件(事件):#不是追加的用户消息
        return None#不认
    if 回复来源(事件) is None:#不是提问回复
        return None#不认
    return {'id':str(事件['data']['id']),'role':'start','exclusive':True}#独占这条消息


def 起始(_上下文,匹配结果,*其余):
    '开节点必须是带回复来源的用户消息。正文不是 JSON 时问题和答案留空'
    事件=匹配结果['event']#起始事件
    if 事件.get('type')!='user/message':#不是用户消息
        raise Exception('user-question-reply start requires user/message')#拒绝
    块=None#第一段文本
    内容=事件['data'].get('content')#内容
    if isinstance(内容,list):#有内容
        for 项 in 内容:#逐段
            if isinstance(项,dict) and 项.get('type')=='text':#文本段
                块=项#记下
                break#只用第一段
    文本=''#模型看到的文本
    if 块 is not None and isinstance(块.get('text'),str):#有文本
        文本=块['text']#原文
    来源=回复来源(事件)#回复来源
    if 来源 is None:#没有来源
        raise Exception('user-question-reply start requires a reply source')#拒绝
    问题表=[]#问题
    答案表=[]#答案
    值=None#解析结果
    try:#读 JSON
        值=json.loads(文本)#解析
    except (ValueError,TypeError):#不是 JSON
        值=None#当读不懂
    if 是记录(值) and isinstance(值.get('questions'),list):#有问题数组
        for 问题 in 值['questions']:#逐题
            if not 是记录(问题) or not isinstance(问题.get('id'),str) or not isinstance(问题.get('question'),str):#缺编号或题干
                continue#跳过
            一条={'id':问题['id'],'question':问题['question']}#必有字段
            if isinstance(问题.get('detail'),str):#有细节
                一条['detail']=问题['detail']#细节
            if isinstance(问题.get('header'),str):#有眉题
                一条['header']=问题['header']#眉题
            if isinstance(问题.get('options'),list):#有选项
                选项表=[]#可用选项
                for 选项 in 问题['options']:#逐项
                    if not 是记录(选项) or not isinstance(选项.get('label'),str):#没有标签
                        continue#跳过
                    选项条={'label':选项['label']}#标签
                    if isinstance(选项.get('description'),str):#有说明
                        选项条['description']=选项['description']#说明
                    选项表.append(选项条)#留下
                一条['options']=选项表#选项
            if isinstance(问题.get('multiSelect'),bool):#有多选标记
                一条['multiSelect']=问题['multiSelect']#多选
            问题表.append(一条)#留下
        原始答案=值.get('answers')#答案
        if not isinstance(原始答案,list):#没有数组
            原始答案=[]#当空
        for 答案 in 原始答案:#逐条
            if not 是记录(答案) or not isinstance(答案.get('id'),str) or not isinstance(答案.get('selected'),list):#缺编号或选择
                continue#跳过
            选择=[]#字符串选择
            for 项 in 答案['selected']:#逐项
                if isinstance(项,str):#是字符串
                    选择.append(项)#留下
            答案条={'id':答案['id'],'selected':选择}#必有字段
            if isinstance(答案.get('custom'),str):#有自定义
                答案条['custom']=答案['custom']#自定义
            答案表.append(答案条)#留下
    return {#节点状态
        'seq':事件['seq'],#锚点序号
        'time':事件['time'],#时间
        'callId':来源['callId'],#调用
        'outcome':来源['outcome'],#已回答
        'text':文本,#读不懂时显示原文
        'questions':问题表,#问题
        'answers':答案表,#答案
    }


def 更新(上下文,*其余):
    '迟到回复没有后续更新'
    return 上下文['state']#原状态


def 建视图(上下文):
    '交给聊天节点的可见数据。还没开出来则没有'
    状态=上下文.get('state')#状态
    if 状态 is None:#没有
        return None#不画
    数据=dict(状态)#拷贝
    序号=数据.pop('seq')#锚点不放进数据
    起始匹配=上下文.get('start')#起始匹配
    位置={'kind':'unresolved'}#还没有位置
    if isinstance(起始匹配,dict) and 起始匹配.get('location') is not None:#有位置
        位置=起始匹配['location']#用起始位置
    return {#视图节点
        'key':上下文['key'],#节点键
        'kind':'question-reply',#视图种类
        'id':上下文['id'],#标识
        'target':'chat',#聊天目标
        'anchorSeq':序号,#锚点
        'location':位置,#位置
        'visibility':'visible',#可见
        'data':数据,#展示数据
    }


问题回复定义={#对话节点
    'kind':'user-question-reply',#业务种类
    'target':'chat',#聊天目标
    'match':匹配,#认领消息
    'start':起始,#开节点
    'update':更新,#不改状态
    'buildViewNode':建视图,#视图
}
