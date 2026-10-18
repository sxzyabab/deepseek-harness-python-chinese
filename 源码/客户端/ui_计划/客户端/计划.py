import json
import re
from urllib.parse import unquote as 百分解码#百分号解码

__all__=['已提交计划','解析计划地址']

标题模式=re.compile(r'^#\s+(\S[^\r\n]*)')
计划地址模式=re.compile(r'^dsh-resource://plan/([^?#]+)$')
百分坏=re.compile(r'%(?![0-9A-Fa-f]{2})')


def 是记录(值):
    '普通对象，列表和空都不算'
    return isinstance(值,dict)


def 已提交计划(事件):
    '从已记录的 exit_plan_mode 参数读出完整计划。无关或畸形则没有'
    种=事件['type']
    if 种 not in ('tool/call','tool/ptc-dispatch-start','tool/ptc-dispatch'):
        return None
    数据=事件['data']
    if 是记录(数据) is not True or 数据.get('name')!='exit_plan_mode':
        return None
    调用标识=数据.get('callId') if 种=='tool/call' else 数据.get('subCallId')
    if isinstance(调用标识,str) is not True or 调用标识=='':
        return None
    参数=数据.get('arguments')
    if 种=='tool/call':
        if isinstance(参数,str) is not True:
            return None
        try:
            参数=json.loads(参数)
        except ValueError:
            return None
    if 是记录(参数) is not True or isinstance(参数.get('plan'),str) is not True:
        return None
    正文=参数['plan']
    命中=标题模式.match(正文.strip())
    if 命中 is None:
        return None
    return {'callId':调用标识,'markdown':正文,'title':命中.group(1)}


def 解析计划地址(地址):
    '校验计划资源地址。不支持或百分号坏了则没有'
    命中=计划地址模式.match(地址)
    if 命中 is None:
        return None
    try:
        段表=[]
        for 段 in 命中.group(1).split('/'):
            if 百分坏.search(段) is not None:
                raise ValueError(段)
            段表.append(百分解码(段))
    except (ValueError,UnicodeError):
        return None
    if any(段=='' for 段 in 段表):
        return None
    if len(段表)==2:
        return {'session':{'kind':'session','sessionId':段表[0]},'callId':段表[1]}
    if len(段表)==5 and 段表[0]=='subagent' and 段表[3] in ('one-shot','continuable','unknown'):
        return {
            'session':{
                'kind':'subagent',
                'parentSessionId':段表[1],
                'childSessionId':段表[2],
                'mode':段表[3],
            },
            'callId':段表[4],
        }
    return None
