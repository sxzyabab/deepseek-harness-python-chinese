import re#裸令牌后分隔判定
import threading#中止 Event
from ..服务 import 对话错误#本包异常

__all__=['输入机','已中止','若已中止则抛出','中止控制器']#仅中文公开名

def 不可达(值):
    """封闭输入事件的穷尽性兜底。"""
    raise 对话错误('unreachable input event: '+repr(值))#不可能到达

def 仍持认领(草稿,令牌):
    """完整命令名可单独站住；参数需要令牌的分隔。"""
    return 草稿.startswith(令牌) or 草稿==令牌.rstrip()#完整令牌或去尾空白的裸名

def 令牌后参数(草稿,令牌):
    """从提交时草稿剥掉认领命令令牌。"""
    文本=草稿.lstrip()#去掉前导空白
    if 文本.startswith(令牌):#完整令牌命中
        return 文本[len(令牌):]#切掉令牌
    基名=令牌.rstrip()#去掉令牌尾部分隔
    if 文本.startswith(基名):#裸令牌前缀命中
        余下=文本[len(基名):]#令牌后的余下
        return 余下[1:] if len(余下)>0 and re.match(r'\s',余下[0],re.ASCII) is not None else 余下#有分隔则再吃一个空白
    return ''#对不上则空参数

def 已中止(信号):
    """Event 已置位。"""
    return 信号.is_set()#已中止

def 若已中止则抛出(信号):
    """已置位则抛本包异常。"""
    if 已中止(信号):#已中止
        raise 对话错误('The operation was aborted.')#中止

class 中止控制器:#取消控制器
    """对齐 AbortController；机在进入时铸造。信号为 threading.Event。"""
    def __init__(自身):
        """绑定 Event。"""
        自身.signal=threading.Event()#信号

    def abort(自身):
        """置位 Event。"""
        自身.signal.set()#是

class 输入机:#纯提交平面状态机
    """事件进、效应出；零副作用。相位、认领与尝试属主。"""
    def __init__(自身):
        """明文相位、无认领、无飞行。"""
        自身.相位='plain'#当前相位
        自身.认领=None#活认领
        自身.序号=0#尝试序号
        自身.飞行=None#冻结飞行槽
        自身.脱离表={}#seq → 脱离发送控制器

    @property
    def state(自身):
        """提交平面只读切片。"""
        快照={'phase':自身.相位}#相位
        if 自身.认领 is not None:#有认领
            认领快照={'name':自身.认领['name'] if 'name' in 自身.认领 else '','token':自身.认领['token']}#目录名与令牌
            if 'hint' in 自身.认领 and 自身.认领['hint'] is not None:#有 hint
                认领快照['hint']=自身.认领['hint']#带上
            if 'attachments' in 自身.认领 and 自身.认领['attachments'] is True:#接受附件
                认领快照['attachments']=True#带上
            快照['claim']=认领快照#写入
        return 快照#快照

    def dispatch(自身,事件):
        """按事件判别标签分发。"""
        种类=事件['type']#标签
        if 种类=='draft-changed':#草稿已变
            return 自身.草稿已变(事件['draft'])#派发
        if 种类=='claim':#认领
            return 自身.认领命令(事件['claim'])#派发
        if 种类=='enter':#回车
            return 自身.回车(事件['mode'],事件['draft'])#派发
        if 种类=='adjudicated':#已裁决
            结局=事件['outcome'] if 'outcome' in 事件 else None#结局
            return 自身.已裁决(事件['attempt'],结局)#派发
        if 种类=='adjudication-failed':#裁决失败
            return 自身.裁决失败(事件['attempt'],事件['message'])#派发
        if 种类=='submit-settled':#命令提交结算
            return 自身.提交已结算(事件)#派发
        if 种类=='sink-settled':#默认汇结算
            return 自身.汇已结算(事件)#派发
        if 种类=='send-committed':#附件直送已提交
            return 自身.发送已提交()#派发
        if 种类=='release':#拆除
            return 自身.释放()#派发
        return 不可达(事件)#漏分支

    def 草稿已变(自身,草稿):
        """完整命令名在有无参数分隔时都保住认领。"""
        if 自身.相位=='claimed' and 自身.认领 is not None and 仍持认领(草稿,自身.认领['token']) is False:#丢掉认领
            自身.相位='plain'#明文
            自身.认领=None
        return []#无效应

    def 认领命令(自身,认领):
        """编辑器已替换令牌；忙碌相位拒绝再认领。"""
        if 自身.相位!='plain' and 自身.相位!='claimed':#忙碌
            return []#空
        自身.认领=认领#记下
        自身.相位='claimed'#已认领
        return []#无效应

    def 铸造尝试(自身,模式,草稿):
        """铸造尝试与控制器，不指定生命周期属主。"""
        控制器=中止控制器()#取消
        自身.序号+=1#前进
        尝试={'seq':自身.序号,'signal':控制器.signal,'draftSnapshot':草稿,'mode':模式}#尝试
        return {'attempt':尝试,'controller':控制器}#飞行件

    def 开始尝试(自身,模式,草稿):
        """铸造冻结的命令/裁决尝试。"""
        飞行=自身.铸造尝试(模式,草稿)#铸造
        自身.飞行=飞行#占槽
        return 飞行['attempt']#尝试

    def 开始脱离(自身,模式,草稿):
        """铸造普通发送，相位回到明文。"""
        飞行=自身.铸造尝试(模式,草稿)#铸造
        自身.脱离表[飞行['attempt']['seq']]=飞行['controller']#脱离
        自身.认领=None认领
        自身.相位='plain'#明文
        return 飞行['attempt']#尝试

    def 脱离效应(自身,尝试):
        """默认发送效应在编辑器提交前捕获汇入。"""
        return [{'type':'default-sink','attempt':尝试,'draft':尝试['draftSnapshot'],'mode':尝试['mode']},{'type':'commit-draft','retainSuffixOf':尝试['draftSnapshot']}]#汇+清草稿

    def 回车(自身,模式,草稿):
        """认领走冻结提交；斜杠行走裁决；其余脱离发送。"""
        if 自身.相位=='adjudicating' or 自身.相位=='submitting':#忙碌
            return []#空
        if 自身.相位=='claimed' and 自身.认领 is not None:#已认领
            尝试=自身.开始尝试(模式,草稿)#冻结
            自身.相位='submitting'#提交中
            return [{'type':'begin-submit','attempt':尝试,'claim':自身.认领,'args':令牌后参数(草稿,自身.认领['token'])}]#提交
        修剪=草稿.strip()#修剪
        if 修剪=='':#空
            return []#空
        if 修剪.startswith('/'):#斜杠
            尝试=自身.开始尝试(模式,草稿)#冻结
            自身.相位='adjudicating'#裁决中
            return [{'type':'adjudicate','attempt':尝试,'draft':草稿}]#裁决
        return 自身.脱离效应(自身.开始脱离(模式,草稿))#脱离发送

    def 已裁决(自身,尝试,结局):
        """裁决命中认领则提交；无结局则改脱离发送。"""
        飞行=自身.飞行#飞行槽
        if 自身.相位!='adjudicating' or 飞行 is None or 飞行['attempt']['seq']!=尝试['seq']:#过期
            return []#空
        if 结局 is not None and 结局!='handled' and 'claim' in 结局:#认领结局
            自身.认领=结局['claim']#记下
            自身.相位='submitting'#提交中
            return [{'type':'begin-submit','attempt':尝试,'claim':结局['claim'],'args':令牌后参数(尝试['draftSnapshot'],结局['claim']['token'])}]#提交
        自身.飞行=None槽
        自身.相位='plain'#明文
        if 结局 is not None:#已处理且无认领
            return []#空
        自身.脱离表[尝试['seq']]=飞行['controller']#改脱离
        return 自身.脱离效应(尝试)#脱离发送

    def 裁决失败(自身,尝试,消息):
        """裁决失败：通知并留草稿。"""
        if 自身.相位!='adjudicating' or 自身.飞行 is None or 自身.飞行['attempt']['seq']!=尝试['seq']:#过期
            return []#空
        自身.飞行=None槽
        自身.相位='plain'#明文
        return [{'type':'notice','level':'error','text':消息}]#通知

    def 提交已结算(自身,事件):
        """已认领命令结算，保留冻结事务语义。"""
        飞行=自身.飞行#飞行槽
        if 自身.相位!='submitting' or 飞行 is None or 飞行['attempt']['seq']!=事件['attempt']['seq']:#过期
            return []#空
        自身.飞行=None槽
        if 事件['ok'] is True:#成功
            自身.相位='plain'#明文
            自身.认领=None
            效应表=[{'type':'commit-draft','retainSuffixOf':飞行['attempt']['draftSnapshot']}]#清草稿
            结局=事件['outcome'] if 'outcome' in 事件 else None#结局
            if 结局 is not None and 'text' in 结局 and 结局['text'] is not None:#有文案
                级别='error' if 结局['kind']=='error' else 'info'#级别
                效应表.append({'type':'notice','level':级别,'text':结局['text']})#通知
            return 效应表#效应
        消息=事件['message'] if 'message' in 事件 else None#消息
        结局=事件['outcome'] if 'outcome' in 事件 else None#结局
        if 消息 is None and 结局 is not None and 'text' in 结局:#从结局取
            消息=结局['text']#文案
        草稿=事件['draft'] if 'draft' in 事件 else None#结算时草稿
        if (草稿==飞行['attempt']['draftSnapshot'] and 自身.认领 is not None and 仍持认领(草稿,自身.认领['token']) is True):#仍可认领
            自身.相位='claimed'#回到认领
            return [] if 消息 is None else [{'type':'notice','level':'error','text':消息}]#通知
        自身.相位='plain'#明文
        自身.认领=None
        return [] if 消息 is None else [{'type':'notice','level':'error','text':消息}]#通知

    def 汇已结算(自身,事件):
        """普通发送独立于当前相位与其他脱离发送结算。"""
        序号=事件['attempt']['seq']#序号
        if 序号 not in 自身.脱离表:#不是本机脱离
            return []#空
        del 自身.脱离表[序号]#摘掉
        消息=事件['message'] if 'message' in 事件 else None#消息
        结局=事件['outcome'] if 'outcome' in 事件 else None#结局
        if 消息 is None and 结局 is not None and 'text' in 结局:#从结局取
            消息=结局['text']#文案
        if 消息 is None:#无文案
            return []#空
        成功=事件['ok'] is True and (结局 is None or 结局['kind']!='error')#信息级
        return [{'type':'notice','level':'info' if 成功 is True else 'error','text':消息}]#通知

    def 发送已提交(自身):
        """附件直送已接受；无正文后缀可留。"""
        if 自身.相位!='plain':#非明文
            return []#空
        自身.认领=None
        return [{'type':'commit-draft','retainSuffixOf':None}]#整根清空

    def 释放(自身):
        """拆除：中止飞行与脱离发送。"""
        if 自身.飞行 is not None:#有冻结
            自身.飞行['controller'].abort()#中止
            自身.飞行=None
        for 控制器 in list(自身.脱离表.values()):#脱离
            控制器.abort()#中止
        自身.脱离表.clear()#清
        自身.相位='plain'#明文
        自身.认领=None
        return []#无效应
