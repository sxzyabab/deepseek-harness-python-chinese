'重载后按会话和标签 id 找回上次打开的任务'
import json
from ..异常 import 页面失败文案

__all__=['任务标签绑定']

前缀='dsh.schedule.task-tab.v1.'

def _存储():
    '浏览器 localStorage；没有则 None'
    try:
        return localStorage
    except NameError:
        return None

def _是记录(值):
    '排除数组和标量'
    return isinstance(值,dict)

def _条目(值):
    '缺字段的存储值丢掉'
    if not _是记录(值):
        return None
    if 'kind' not in 值 or 'contentId' not in 值 or 'sessionId' not in 值 or 'id' not in 值:
        return None
    if not isinstance(值['kind'],str) or not isinstance(值['contentId'],str):
        return None
    if not isinstance(值['sessionId'],str) or not isinstance(值['id'],str):
        return None
    return {'kind':值['kind'],'contentId':值['contentId'],'sessionId':值['sessionId'],'id':值['id']}

class 任务标签绑定:
    '窗口内存为准，存储只是重载后的副本'
    def __init__(自身,活动标签=None):
        '活动标签用来在写入时丢掉已关的页'
        自身.活动标签=活动标签
        自身.内存={}

    def 读取(自身,会话标识,页):
        '种类或内容不符则当没有'
        文档=自身._文档(会话标识)
        条目=文档[页['id']] if 'id' in 页 and 页['id'] in 文档 else None
        if 条目 is None:
            return None
        if 条目['kind']!=页['kind'] or 条目['contentId']!=页['contentId']:
            return None
        return {'sessionId':条目['sessionId'],'id':条目['id']}

    def 丢掉不符(自身,会话标识,页):
        '渲染之后再删种类不符的条目'
        文档=自身._文档(会话标识)
        条目=文档[页['id']] if 'id' in 页 and 页['id'] in 文档 else None
        if 条目 is None:
            return
        if 条目['kind']==页['kind'] and 条目['contentId']==页['contentId']:
            return
        自身.忘记(会话标识,页)

    def 写入(自身,会话标识,页,目标):
        '记下这一页正在看的任务'
        文档=dict(自身._文档(会话标识))
        文档[页['id']]={'kind':页['kind'],'contentId':页['contentId'],'sessionId':目标['sessionId'],'id':目标['id']}
        自身._存放(会话标识,文档)

    def 忘记(自身,会话标识,页):
        '任务已经不在目录里'
        文档=dict(自身._文档(会话标识))
        if 'id' in 页 and 页['id'] in 文档:
            del 文档[页['id']]
        自身._存放(会话标识,文档)

    def _文档(自身,会话标识):
        '先内存，再存储'
        if 会话标识 in 自身.内存:
            return 自身.内存[会话标识]
        存储=_存储()
        if 存储 is None:
            return {}
        try:
            原文=存储.getItem(前缀+str(会话标识))
        except (TypeError,AttributeError,OSError):
            return {}
        if not isinstance(原文,str):
            return {}
        try:
            解析=json.loads(原文)
        except ValueError:
            return {}
        if not isinstance(解析,dict):
            return {}
        文档={}
        for 标签标识,值 in 解析.items():
            条目=_条目(值)
            if 条目 is not None:
                文档[标签标识]=条目
        自身.内存[会话标识]=文档
        return 文档

    def _存放(自身,会话标识,文档):
        '非空的已提交标签列表才裁剪'
        保留=文档
        if callable(自身.活动标签):
            活动=自身.活动标签(会话标识)
            if isinstance(活动,(list,tuple)) and len(活动)>0:
                保留={键:值 for 键,值 in 文档.items() if 键 in 活动}
        自身.内存[会话标识]=保留
        存储=_存储()
        if 存储 is None:
            return
        try:
            键=前缀+str(会话标识)
            if len(保留)==0:
                存储.removeItem(键)
            else:
                存储.setItem(键,json.dumps(保留,ensure_ascii=False,separators=(',',':')))
        except (TypeError,ValueError,AttributeError,OSError) as 错误:
            print('任务标签绑定写入失败:',页面失败文案(错误))
