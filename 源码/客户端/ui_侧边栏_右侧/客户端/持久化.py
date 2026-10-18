'校验过的当前布局。撤销历史归活动窗口，不写入存储'
from ...模块.客户端.通告 import 取握手窗口
import json
import re
from ..异常 import 右侧侧栏错误

__all__=['侧栏持久化前缀','读侧栏布局','写侧栏布局','清侧栏布局']

侧栏持久化前缀='dsh.sidebar-right.v1'
窗格样=re.compile(r'^(?:pane|float)[1-9][0-9]*$')
分割样=re.compile(r'^split[1-9][0-9]*$')
标签样=re.compile(r'^tab[1-9][0-9]*$')


def _存储():
    '浏览器 localStorage。读不到就当没有'
    try:
        return 取握手窗口().localStorage
    except Exception:
        return None


def _是数(值):
    '整数或浮点，排除布尔'
    if isinstance(值,bool):
        return False
    return isinstance(值,(int,float))


def _正数(值):
    '大于零的数'
    return _是数(值) and 值>0


def _标识号(文本):
    '去掉种类前缀后的序号'
    数字=''
    for 字 in 文本:
        if 字.isdigit():
            数字+=字
    if 数字=='':
        return 0
    return int(数字)


def _矩形(值):
    'x y 为数，宽高为正'
    if not isinstance(值,dict):
        return False
    if not _是数(值.get('x')) or not _是数(值.get('y')):
        return False
    if not _正数(值.get('width')) or not _正数(值.get('height')):
        return False
    return True


def _节点(值):
    '窗格或分割。键保持上游原文'
    if not isinstance(值,dict) or 'kind' not in 值:
        return False
    if 值['kind']=='pane':
        if not isinstance(值.get('id'),str) or 窗格样.fullmatch(值['id']) is None:
            return False
        if 值.get('host') not in ('dock','float'):
            return False
        签表=值.get('tabs')
        if not isinstance(签表,list) or any(not isinstance(项,str) or 标签样.fullmatch(项) is None for 项 in 签表):
            return False
        活动=值.get('activeTabId',None)
        if 'activeTabId' in 值 and 活动 is not None and (not isinstance(活动,str) or 标签样.fullmatch(活动) is None):
            return False
        if 'rect' in 值 and 值['rect'] is not None and not _矩形(值['rect']):
            return False
        return True
    if 值['kind']=='split':
        if not isinstance(值.get('id'),str) or 分割样.fullmatch(值['id']) is None:
            return False
        if 值.get('axis') not in ('row','column'):
            return False
        子=值.get('children')
        尺寸=值.get('sizes')
        if not isinstance(子,list) or len(子)<2:
            return False
        if not isinstance(尺寸,list) or len(尺寸)<2:
            return False
        if any(not isinstance(项,str) or (窗格样.fullmatch(项) is None and 分割样.fullmatch(项) is None) for 项 in 子):
            return False
        if any(not _正数(项) for 项 in 尺寸):
            return False
        return True
    return False


def _标签记录(值):
    '签记录'
    if not isinstance(值,dict):
        return False
    if not isinstance(值.get('id'),str) or 标签样.fullmatch(值['id']) is None:
        return False
    if not isinstance(值.get('kind'),str) or 值['kind']=='':
        return False
    if not isinstance(值.get('contentId'),str) or 值['contentId']=='':
        return False
    if not isinstance(值.get('title'),str):
        return False
    return True


def _布局(值):
    '布局对象'
    if not isinstance(值,dict):
        return False
    节点表=值.get('nodes')
    签表=值.get('tabs')
    if not isinstance(节点表,dict) or not isinstance(签表,dict):
        return False
    for 标识,节点 in 节点表.items():
        if not isinstance(标识,str) or (窗格样.fullmatch(标识) is None and 分割样.fullmatch(标识) is None):
            return False
        if not _节点(节点) or 节点.get('id')!=标识:
            return False
    for 标识,签 in 签表.items():
        if not isinstance(标识,str) or 标签样.fullmatch(标识) is None:
            return False
        if not _标签记录(签) or 签.get('id')!=标识:
            return False
    根=值.get('rootId')
    if not isinstance(根,str) or (窗格样.fullmatch(根) is None and 分割样.fullmatch(根) is None):
        return False
    浮动=值.get('floats')
    if not isinstance(浮动,list) or any(not isinstance(项,str) or 窗格样.fullmatch(项) is None for 项 in 浮动):
        return False
    活动窗=值.get('activePaneId')
    if not isinstance(活动窗,str) or 窗格样.fullmatch(活动窗) is None:
        return False
    if not isinstance(值.get('expanded'),bool) or 值.get('mode') not in ('push','fullscreen'):
        return False
    return True


def _表面(值):
    '布局加已铸造次数'
    if not isinstance(值,dict) or not _布局(值.get('layout')):
        return False
    次数=值.get('minted')
    if type(次数) is not int or 次数<0:
        return False
    return True


def _引用(值):
    '节点、签、根、浮动互相引用得上，且序号不超过已铸造次数'
    布局=值['layout']
    次数=值['minted']
    已访=set()
    已用签=set()
    待走=[{'id':布局['rootId'],'host':'dock'}]
    for 标识 in 布局['floats']:
        待走.append({'id':标识,'host':'float'})
    for 标识,条目 in list(布局['nodes'].items())+list(布局['tabs'].items()):
        if 条目['id']!=标识 or _标识号(标识)>次数:
            raise 右侧侧栏错误('Invalid saved sidebar layout references')
    while len(待走)>0:
        项=待走.pop(0)
        标识=项['id']
        宿主=项['host']
        条目=布局['nodes'].get(标识)
        if 标识 in 已访 or 条目 is None:
            raise 右侧侧栏错误('Invalid saved sidebar layout references')
        已访.add(标识)
        if 条目['kind']=='split':
            if 宿主!='dock' or 标识!=布局['rootId'] or 条目['axis']!='row' or len(条目['children'])!=2:
                raise 右侧侧栏错误('Invalid saved sidebar layout references')
            if len(条目['children'])!=len(条目['sizes']):
                raise 右侧侧栏错误('Invalid saved sidebar layout references')
            合计=0
            for 尺寸 in 条目['sizes']:
                合计+=尺寸
            if abs(合计-1)>1e-9:
                raise 右侧侧栏错误('Invalid saved sidebar layout references')
            for 子标识 in 条目['children']:
                待走.append({'id':子标识,'host':宿主})
        else:
            if 条目['host']!=宿主:
                raise 右侧侧栏错误('Invalid saved sidebar layout references')
            if 宿主=='float':
                if 条目.get('rect') is None or len(条目['tabs'])!=1:
                    raise 右侧侧栏错误('Invalid saved sidebar layout references')
            elif 条目.get('rect') is not None:
                raise 右侧侧栏错误('Invalid saved sidebar layout references')
            if len(条目['tabs'])==0:
                if 条目.get('activeTabId') is not None:
                    raise 右侧侧栏错误('Invalid saved sidebar layout references')
            elif 条目.get('activeTabId') not in 条目['tabs']:
                raise 右侧侧栏错误('Invalid saved sidebar layout references')
            for 签 in 条目['tabs']:
                if 签 in 已用签 or 签 not in 布局['tabs']:
                    raise 右侧侧栏错误('Invalid saved sidebar layout references')
                已用签.add(签)
    活动=布局['nodes'].get(布局['activePaneId'])
    if len(已访)!=len(布局['nodes']) or len(已用签)!=len(布局['tabs']) or 活动 is None or 活动.get('kind')!='pane':
        raise 右侧侧栏错误('Invalid saved sidebar layout references')


def 读侧栏布局(会话标识):
    '恢复一份校验过的会话布局，撤销历史换成空序列'
    存储=_存储()
    if 存储 is None:
        return None
    try:
        原文=存储.getItem(侧栏持久化前缀+'.'+str(会话标识))
    except Exception:
        return None
    if 原文 is None:
        return None
    try:
        信封=json.loads(原文)
        if not isinstance(信封,dict) or not isinstance(信封.get('bySession'),dict):
            raise 右侧侧栏错误('Invalid saved sidebar layout references')
        已存=信封['bySession'].get(会话标识)
        if 已存 is None:
            return None
        if not _表面(已存):
            raise 右侧侧栏错误('Invalid saved sidebar layout references')
        _引用(已存)
        return {'layout':已存['layout'],'minted':已存['minted'],'history':{'entries':[],'cursor':0}}
    except Exception:
        清侧栏布局(会话标识)
        return None


def 写侧栏布局(会话标识,表面):
    '只写布局和铸造次数'
    存储=_存储()
    if 存储 is None:
        return
    已存={'bySession':{会话标识:{'layout':表面['layout'],'minted':表面['minted']}}}
    try:
        存储.setItem(侧栏持久化前缀+'.'+str(会话标识),json.dumps(已存,ensure_ascii=False,separators=(',',':')))
    except Exception as 错误:
        取握手窗口().console.error('Sidebar layout persistence failed:',错误)


def 清侧栏布局(会话标识):
    '只删这一个会话的布局'
    存储=_存储()
    if 存储 is None:
        return
    try:
        存储.removeItem(侧栏持久化前缀+'.'+str(会话标识))
    except Exception:
        return
