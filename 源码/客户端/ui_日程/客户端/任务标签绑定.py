'刷新后按会话和页标识找回上次打开的任务'
from ...模块.客户端.通告 import 取握手窗口
import json

__all__=['任务标签绑定']

前缀='dsh.schedule.task-tab.v1.'

def 是记录(值):
    '普通字典，不是列表'
    return isinstance(值,dict)

class 任务标签绑定:
    '这一窗口的副本是读取权威。存储没有或拒绝写入时仍可用'
    def __init__(自身,活动页标识=None):
        '活动页标识用来在写入时丢掉已经关掉的页'
        自身.活动页标识=活动页标识
        自身.记忆={}

    def 读取(自身,会话标识,页):
        '种类或内容标识对不上就当没有，不改存储'
        条目=自身.文档(会话标识).get(页['id'])
        if 条目 is None:
            return None
        if 条目['kind']!=页['kind'] or 条目['contentId']!=页['contentId']:
            return None
        return {'sessionId':条目['sessionId'],'id':条目['id']}

    def 丢掉不配(自身,会话标识,页):
        '读完之后再删种类对不上的条目'
        条目=自身.文档(会话标识).get(页['id'])
        if 条目 is None:
            return
        if 条目['kind']==页['kind'] and 条目['contentId']==页['contentId']:
            return
        自身.忘记(会话标识,页)

    def 写入(自身,会话标识,页,目标):
        '记下这一页正在看的任务'
        条目=dict(自身.文档(会话标识))
        条目[页['id']]={'kind':页['kind'],'contentId':页['contentId'],'sessionId':目标['sessionId'],'id':目标['id']}
        自身.存储(会话标识,条目)

    def 忘记(自身,会话标识,页):
        '任务已经不在，删掉这一页的条目'
        条目=dict(自身.文档(会话标识))
        if 页['id'] in 条目:
            del 条目[页['id']]
        自身.存储(会话标识,条目)

    def 清空(自身):
        '放下这一窗口的缓存'
        自身.记忆={}

    def 文档(自身,会话标识):
        '先看窗口缓存，再读浏览器存储'
        已有=自身.记忆.get(会话标识)
        if 已有 is not None:
            return 已有
        存储=自身.取存储()
        if 存储 is None:
            return {}
        try:
            原文=存储.getItem(前缀+str(会话标识))
        except Exception:
            return {}
        if 原文 is None:
            return {}
        条目=自身.解析条目(原文)
        自身.记忆[会话标识]=条目
        return 条目

    def 解析条目(自身,原文):
        '坏 JSON 和不合格式的值丢掉'
        try:
            解析=json.loads(原文)
        except Exception:
            return {}
        if not 是记录(解析):
            return {}
        条目={}
        for 页标识,值 in 解析.items():
            if not 是记录(值):
                continue
            种类=值.get('kind')
            内容=值.get('contentId')
            会话=值.get('sessionId')
            标识=值.get('id')
            if not isinstance(种类,str) or not isinstance(内容,str):
                continue
            if not isinstance(会话,str) or not isinstance(标识,str):
                continue
            条目[页标识]={'kind':种类,'contentId':内容,'sessionId':会话,'id':标识}
        return 条目

    def 存储(自身,会话标识,条目):
        '非空的活动页名单会丢掉已经关掉的页。空文档删键'
        活动=None
        if 自身.活动页标识 is not None:
            活动=自身.活动页标识(会话标识)
        if 活动 is None or len(活动)==0:
            留下=条目
        else:
            留下={}
            for 页标识,值 in 条目.items():
                if 页标识 in 活动:
                    留下[页标识]=值
        自身.记忆[会话标识]=留下
        存储=自身.取存储()
        if 存储 is None:
            return
        try:
            键=前缀+str(会话标识)
            if len(留下)==0:
                存储.removeItem(键)
            else:
                存储.setItem(键,json.dumps(留下))
        except Exception as 错误:
            取握手窗口().console.error('Task tab binding persistence failed:',错误)

    def 取存储(自身):
        '浏览器 localStorage。没有就当不可用'
        窗口=取握手窗口()
        if 窗口 is None:
            return None
        return getattr(窗口,'localStorage',None)
