'会话外壳和页眉共用的每会话存储'
import json
from ...存储 import 声明存储
from .草稿 import 解析存储草稿

__all__=['创建会话存储','读会话草稿','读会话视图偏好']

会话存储键='dsh.conversation'

def 创建会话存储():
    '草稿持久化和视图选择'
    return 声明存储({
        'init':lambda: {'draft':'','view':None,'viewRequest':None},
        'persist':会话存储键,
        'actions':{
            'setDraft':lambda 草稿,文本:草稿.__setitem__('draft',文本),
            'setView':lambda 草稿,视图:草稿.__setitem__('view',视图),
            'openView':lambda 草稿,视图,焦点:_打开视图(草稿,视图,焦点),
            'completeViewRequest':lambda 草稿:草稿.__setitem__('viewRequest',None),
        },
    })

def _打开视图(草稿,视图,焦点):
    '同时写下视图和这次焦点请求'
    草稿['view']=视图
    草稿['viewRequest']={'view':视图,'focus':焦点}

def 读本地(会话标识):
    '读出这份会话的存储对象。没有或坏了就是 None'
    try:
        存储=localStorage
    except NameError:
        return None
    try:
        原始=存储.getItem(会话存储键+'.'+str(会话标识))
        if 原始 is None:
            return None
        存下=json.loads(原始)
    except Exception:
        return None
    if not isinstance(存下,dict):
        return None
    return 存下

def 读会话草稿(会话标识):
    '输入源发布之前读出语义草稿。没有则是空文档'
    空={'text':'','references':[]}
    存下=读本地(会话标识)
    if 存下 is None or 'draft' not in 存下:
        return 空
    解析=解析存储草稿(存下['draft'])
    if 解析 is None:
        return 空
    return 解析

def 读会话视图偏好(会话标识):
    '槽存储物化之前读出视图标识'
    存下=读本地(会话标识)
    if 存下 is None or 'view' not in 存下:
        return None
    if isinstance(存下['view'],str):
        return 存下['view']
    return None
