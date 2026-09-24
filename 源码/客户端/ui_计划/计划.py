from urllib.parse import quote as 百分编码,unquote as 百分解码#地址编解码
import json
import re as 正则#标题与地址

__all__=['已提交计划','计划地址','解析计划地址']#仅中文公开名

标题模式=正则.compile(r'^#\s+(\S[^\r\n]*)')#一级标题
计划地址模式=正则.compile(r'^dsh-resource://plan/([^?#]+)$')#计划地址

def 是记录(值):
    """普通对象且非列表。"""
    return isinstance(值,dict)#dict

def 已提交计划(事件):
    """从不可信已记录参数读出完整计划；无关或畸形则 None。"""
    种=事件['type']#事件种
    if 种 not in ('tool/call','tool/ptc-dispatch-start','tool/ptc-dispatch'):#无关
        return None#无
    数据=事件['data']#载荷
    if not 是记录(数据):#非对象
        return None#无
    if 'name' not in 数据 or 数据['name']!='exit_plan_mode':#非本工具
        return None#无
    if 种=='tool/call':#原生
        if 'callId' not in 数据:#无
            return None#无
        调用标识=数据['callId']#id
    else:#PTC
        if 'subCallId' not in 数据:#无
            return None#无
        调用标识=数据['subCallId']#id
    if not isinstance(调用标识,str) or 调用标识=='':#无效
        return None#无
    if 'arguments' not in 数据:#无参数
        return None#无
    参数=数据['arguments']#参数
    if 种=='tool/call':#原生调用
        if not isinstance(参数,str):#须 JSON 串
            return None#无
        try:
            参数=json.loads(参数)
        except (json.JSONDecodeError,TypeError):
            return None
    if not 是记录(参数) or 'plan' not in 参数 or not isinstance(参数['plan'],str):#无 plan
        return None#无
    正文=参数['plan']#正文
    命中=标题模式.match(正文.strip())#一级标题
    if 命中 is None:#无标题
        return None#无
    return {'callId':调用标识,'markdown':正文,'title':命中.group(1)}#已提交

def 计划地址(目标):
    """编码计划耐久身份。"""
    会话=目标['session']#会话地址
    调用=目标['callId']#调用
    if 会话['kind']=='session':#普通
        段表=[会话['sessionId'],调用]#两段
    else:#子智能体
        段表=['subagent',会话['parentSessionId'],会话['childSessionId'],会话['mode'],调用]#五段
    return 'dsh-resource://plan/'+'/'.join(百分编码(段,safe='') for 段 in 段表)#地址

def 解析计划地址(地址):
    """校验计划资源地址；不支持则 None。"""
    命中=计划地址模式.match(地址)#匹配
    if 命中 is None:#不匹配
        return None#无
    try:
        段表=[百分解码(段) for 段 in 命中.group(1).split('/')]
    except (ValueError,UnicodeError):
        return None
    if any(段=='' for 段 in 段表):#空段
        return None#无
    if len(段表)==2:#普通会话
        return {'session':{'kind':'session','sessionId':段表[0]},'callId':段表[1]}#身份
    if len(段表)==5 and 段表[0]=='subagent' and 段表[3] in ('one-shot','continuable','unknown'):#子智能体
        return {'session':{'kind':'subagent','parentSessionId':段表[1],'childSessionId':段表[2],'mode':段表[3]},'callId':段表[4]}#身份
    return None#其它
