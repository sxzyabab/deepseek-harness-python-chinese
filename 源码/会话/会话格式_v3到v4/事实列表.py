"""历史子身份，收缩为父名录所需字段。"""
from ..会话格式 import (#从会话格式导入
    会话格式错误,#格式错误
    会话格式不支持迁移错误,#不支持迁移
    是否会话格式json对象,#是否JSON对象
    会话格式计数,#格式计数
)#从会话格式导入

def 历史子名录源(产物):#历史子名录源
    """收集子自身描述符，不要求在读父名录前就具备。"""
    头=产物['header']#头
    if 头.get('origin')!='subagent' or 'parentSession' not in 头:#须为带子父的子智能体
        raise 会话格式不支持迁移错误('catalog migration requires a subagent child with a direct parent')#拒绝
    描述符列表=[事件 for 事件 in 产物['events']
        if 事件['type']=='subagent/descriptor' and 事件['seq']>=产物['inheritedEventCount']]#当代描述符
    源={#紧缩身份
        'childId':头['id'],'childCreatedAt':头['createdAt'],#身份
        'descriptorCount':len(描述符列表),'descriptor':None if len(描述符列表)==0 else 描述符列表[0].get('data'),#描述符
    }#源结束
    子名录事实(源)#校验发现字段
    return 源#返回

def 子名录源(值):#子名录源
    """校验经迁移 JSON 接口供给的补充子证据。"""
    if (not 是否会话格式json对象(值) or not isinstance(值.get('childId'),str)
        or 'descriptor' not in 值):#须身份与描述符键
        raise 会话格式不支持迁移错误('catalog migration requires historical child identity and descriptor evidence')#拒绝
    会话格式计数(值['childCreatedAt'],'catalog child creation time')#创建时间
    会话格式计数(值['descriptorCount'],'child descriptor count')#描述符计数
    return 值#返回

def 子名录事实(源):#子名录事实
    """只解释已知历史描述符的发现字段。"""
    标识=源['childId']#子标识
    描述符=源.get('descriptor')#描述符
    计数=源['descriptorCount']#计数
    已知=是否会话格式json对象(描述符) and 描述符.get('version') in (1,2,3)#已知版本
    if 计数!=1 or not 已知:#非恰好一条已知描述符
        return None#无事实
    if not isinstance(描述符.get('provider'),str):#provider须串
        raise 会话格式不支持迁移错误(子名录主语(源)+' has an invalid subagent descriptor provider')#拒绝
    if 描述符.get('version')!=1 and 描述符.get('mode') not in ('continuable','one-shot'):#模式
        raise 会话格式不支持迁移错误(子名录主语(源)+' has an invalid subagent descriptor mode')#拒绝
    事实={'version':0,'childId':标识,'childCreatedAt':源['childCreatedAt'],
        'mode':'continuable' if 描述符.get('version')==1 else 描述符['mode']}#发现事实
    if 'label' in 描述符:#可选标签
        事实['label']=描述符['label']#写入
    return 名录事实(事实,子名录主语(源))#再经名录校验

def 名录事实(值,主语='subagent/catalog'):#名录事实
    """校验名录成员所用的历史字段，不解释扩展。"""
    if (not 是否会话格式json对象(值) or 值.get('version') not in (0,1)
        or not isinstance(值.get('childId'),str)
        or 值.get('mode') not in ('continuable','one-shot','unknown')
        or (值.get('version')==0 and 值.get('mode')=='unknown')
        or (值.get('mode')=='continuable' and not isinstance(值.get('label'),str))
        or ('label' in 值 and not isinstance(值['label'],str))):#不支持
        raise 会话格式错误(主语+' requires a supported versioned catalog fact')#错误
    会话格式计数(值['childCreatedAt'],'catalog child creation time')#创建时间
    return 值#返回

def 子名录主语(源):#子名录主语
    """在迁移诊断中命名该子。"""
    return 'Session '+str(源['childId'])#仅用子标识，不回显路径
