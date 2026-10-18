'存储、程序输入和编辑器恢复共用的语义草稿'
import re

__all__=['解析草稿输入','解析存储草稿','快照草稿']

def 复制引用(引用):
    '去掉编辑器本地出现标识，只留语义字段'
    出={
        'source':引用['source'],
        'ref':引用['ref'],
        'offset':引用['offset'],
        'length':引用['length'],
        'label':引用['label'],
        'clipboardText':引用['clipboardText'],
    }
    if 引用.get('appearance') is not None:
        出['appearance']=引用['appearance']
    if 引用.get('invalid') is not None:
        出['invalid']=引用['invalid']
    return 出

def 草稿合法(草稿):
    '命令在文首，引用按顺序、不重叠，并等于剪贴板原文'
    if not isinstance(草稿,dict) or not isinstance(草稿.get('text'),str) or not isinstance(草稿.get('references'),list):
        return False
    命令=草稿.get('command')
    拼写=None
    if isinstance(命令,dict) and isinstance(命令.get('token'),str):
        拼写=命令['token'].rstrip()
        if not re.match(r'^/\S',拼写) or not 草稿['text'].startswith(拼写):
            return False
    止=0 if 拼写 is None else len(拼写)
    for 引用 in 草稿['references']:
        if not isinstance(引用,dict):
            return False
        if not isinstance(引用.get('offset'),int) or 引用['offset']<0:
            return False
        if not isinstance(引用.get('length'),int) or 引用['length']<=0:
            return False
        if 引用['offset']<止 or 引用['length']!=len(引用.get('clipboardText') or ''):
            return False
        止=引用['offset']+引用['length']
        if 止>len(草稿['text']) or 草稿['text'][引用['offset']:止]!=引用['clipboardText']:
            return False
    return True

def 解析草稿输入(输入):
    '把纯文本或调用方结构收成编辑器可导入的快照'
    if isinstance(输入,str):
        return {'text':输入,'references':[]}
    出={'text':输入['text'],'references':[复制引用(项) for 项 in 输入['references']]}
    if 输入.get('command') is not None:
        出['command']={'token':输入['command']['token']}
    return 出

def 解析存储草稿(值):
    '接受旧的纯字符串。结构不合法则没有结果'
    if isinstance(值,str):
        return 解析草稿输入(值)
    if not 草稿合法(值):
        return None
    引用=[]
    for 项 in 值['references']:
        出=复制引用(项)
        引用.append(出)
    结果={'text':值['text'],'references':引用}
    if isinstance(值.get('command'),dict) and isinstance(值['command'].get('token'),str):
        结果['command']={'token':值['command']['token']}
    return 结果

def 快照草稿(文本,出现列,命令令牌=None):
    '导出引用身份，不带编辑器本地出现标识'
    出={'text':文本,'references':[复制引用(项) for 项 in 出现列]}
    if 命令令牌 is not None:
        出['command']={'token':命令令牌}
    return 出
