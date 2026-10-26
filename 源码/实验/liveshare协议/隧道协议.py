'所有者宿主插件和它唯一的隧道工人之间的进程间帧，以及中继线路帧'
import json,re,datetime
from ...基础设施.通用工具 import 最大安全整数,是否有限json数字
from .查看者状态 import 查看者可达

__all__=[
    '查看者可达','协议版本','能力','查看者请求字段','发送帧','原始文本',
    '解析网关帧','解析中继帧','不支持帧拒绝','被拒命令的分享标识',
    '解析工人命令','解析工人事件','解析分享访问状态',
]

协议版本=1
能力=(
    'session-mode','fork','acl-subjects','expiry','owner-credential','scoped-rpc-response',
    'unsupported-frame-refusal','share-access-state','file-upload','actor-credential','direct-connection',
)
套接字打开=1
注册令牌=re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',re.I)

def 是安全整数(值):
    '有限整数且在安全范围内，拒绝布尔和负零'
    if isinstance(值,bool) or not isinstance(值,(int,float)):
        return False
    if isinstance(值,float):
        if not 值.is_integer() or not 是否有限json数字(值):
            return False
    if isinstance(值,int) and not 是否有限json数字(值):
        return False
    return abs(int(值))<=最大安全整数

def 是记录(值):
    '普通对象。数组不是'
    return isinstance(值,dict)

def 时间可解析(文本):
    '能被解析的 ISO 时间。空串不行'
    if not isinstance(文本,str) or 文本=='':
        return False
    试=文本[:-1]+'+00:00' if 文本.endswith('Z') else 文本
    try:
        datetime.datetime.fromisoformat(试)
        return True
    except ValueError:
        return False

def 查看者请求字段(体):
    '只为日志取出操作名和流标识。没有时用占位'
    if not isinstance(体,dict):
        return {'op':'unknown','streamId':'-'}
    操作=体['op'] if isinstance(体.get('op'),str) else 'unknown'
    流标识=str(体['id']) if isinstance(体.get('id'),(int,float)) and not isinstance(体.get('id'),bool) else '-'
    if not isinstance(体.get('id'),(int,float)) or isinstance(体.get('id'),bool):
        流标识='-'
    return {'op':操作,'streamId':流标识}

def 发送帧(套接字,帧):
    '套接字打开时发送一帧'
    if 套接字.readyState==套接字打开:
        套接字.send(json.dumps(帧,ensure_ascii=True,separators=(',',':')))

def 原始文本(数据):
    '把一帧完整消息解成 UTF-8 文本'
    if isinstance(数据,(list,tuple)):
        return b''.join(数据).decode('utf-8')
    if isinstance(数据,bytearray):
        return bytes(数据).decode('utf-8')
    if isinstance(数据,bytes):
        return 数据.decode('utf-8')
    if isinstance(数据,memoryview):
        return 数据.tobytes().decode('utf-8')
    return bytes(数据).decode('utf-8')

def 帧信封(值):
    '已解码值上的 id。不是接受的信封时没有'
    if not 是记录(值) or not 是安全整数(值.get('id')) or int(值['id'])<=0:
        return None
    return {'value':值,'id':int(值['id'])}

def 解码帧信封(文本):
    '原始文本的 JSON 和请求 id'
    try:
        值=json.loads(文本)
    except (TypeError,ValueError):
        return None
    return 帧信封(值)

def 解析网关帧(文本):
    '解析一帧网关到中继的帧。未知或畸形则丢掉'
    信封=解码帧信封(文本)
    if 信封 is None:
        return None
    值=信封['value']
    标识=信封['id']
    if 值.get('type')=='share-rpc-res':
        if not 是安全整数(值.get('status')) or int(值['status'])<100 or int(值['status'])>599:
            return None
        帧={'type':'share-rpc-res','id':标识,'status':int(值['status'])}
        if 'body' in 值 and 值['body'] is not None:
            帧['body']=值['body']
        elif 'body' in 值 and 值['body'] is None:
            帧['body']=值['body']
        return 帧
    return None

def 是分享行动者(值):
    '中继断言的行动者要有非空提供方、租户和主体'
    if not 是记录(值):
        return False
    if not isinstance(值.get('providerId'),str) or 值['providerId']=='':
        return False
    if not isinstance(值.get('tenantId'),str) or 值['tenantId']=='':
        return False
    if not isinstance(值.get('subjectId'),str) or 值['subjectId']=='':
        return False
    if 'credential' in 值 and not isinstance(值['credential'],str):
        return False
    return True

def 是主体标识(值):
    '非空字符串列表'
    return isinstance(值,list) and all(isinstance(项,str) and 项!='' for 项 in 值)

def 解析分享访问状态(值):
    '校验已提交的中继权威快照。任一权威字段非法则没有快照'
    if not 是记录(值) or 值.get('type')!='share-access-state':
        return None
    if not 是安全整数(值.get('version')) or int(值['version'])<0:
        return None
    if 值.get('accessMode') not in ('open','selected'):
        return None
    if not 是主体标识(值.get('allowedSubjectIds')):
        return None
    if 值.get('sessionMode') not in ('view','write'):
        return None
    if 'allowsFork' in 值 and not isinstance(值['allowsFork'],bool):
        return None
    if 'allowsFileUpload' in 值 and not isinstance(值['allowsFileUpload'],bool):
        return None
    if 'expiresAt' in 值 and not 时间可解析(值['expiresAt']):
        return None
    帧={
        'type':'share-access-state',
        'version':int(值['version']),
        'accessMode':值['accessMode'],
        'allowedSubjectIds':list(值['allowedSubjectIds']),
        'sessionMode':值['sessionMode'],
        'allowsFileUpload':值.get('allowsFileUpload') is True,
    }
    if 'allowsFork' in 值 and 值['allowsFork'] is not None:
        帧['allowsFork']=值['allowsFork']
    if 'expiresAt' in 值 and 值['expiresAt'] is not None:
        帧['expiresAt']=值['expiresAt']
    return 帧

def 解析中继值(值):
    '解析已经解码的中继到网关的值'
    状态=解析分享访问状态(值)
    if 状态 is not None:
        return 状态
    信封=帧信封(值)
    if 信封 is None:
        return None
    帧=信封['value']
    标识=信封['id']
    if 帧.get('type')=='share-rpc':
        if 'body' not in 帧:
            return None
        if not 是分享行动者(帧.get('actor')):
            return None
        return {'type':'share-rpc','id':标识,'body':帧['body'],'actor':帧['actor']}
    if 帧.get('type')=='share-rpc-cancel':
        return {'type':'share-rpc-cancel','id':标识}
    return None

def 解析中继帧(文本):
    '解析一帧中继到网关的帧。未知或畸形则丢掉'
    try:
        值=json.loads(文本)
    except (TypeError,ValueError):
        return None
    return 解析中继值(值)

def 不支持帧拒绝(文本):
    '本构建无法服务的帧要回答的拒绝。不是该回答的帧则没有'
    try:
        值=json.loads(文本)
    except (TypeError,ValueError):
        return None
    if 解析中继值(值) is not None:
        return None
    信封=帧信封(值)
    if 信封 is None:
        return None
    类型=信封['value'].get('type')
    if 类型=='share-rpc':
        return {'type':'share-rpc-res','id':信封['id'],'status':400,'body':{'error':'invalid-request'}}
    if 类型 in ('share-rpc-res','share-rpc-cancel'):
        return None
    if not isinstance(类型,str) or 类型=='':
        return None
    return {'type':'share-rpc-res','id':信封['id'],'status':501,'body':{'error':'unsupported-frame'}}

def 被拒命令的分享标识(值):
    '被拒绝的进程间命令点名的分享'
    if not 是记录(值):
        return None
    if isinstance(值.get('shareId'),str) and 值['shareId']!='':
        return 值['shareId']
    分享=值.get('share')
    if 是记录(分享) and isinstance(分享.get('shareId'),str) and 分享['shareId']!='':
        return 分享['shareId']
    return None

def 是注册令牌(值):
    '监督者签发的 UUID'
    return isinstance(值,str) and 注册令牌.fullmatch(值) is not None

def 是注册身份(值):
    '注册令牌加非空分享标识'
    return 是记录(值) and 是注册令牌(值.get('registrationToken')) and isinstance(值.get('shareId'),str) and 值['shareId']!=''

def 是请求身份(值):
    '注册身份再加非空请求令牌和正的安全整数 id'
    return 是注册身份(值) and isinstance(值.get('token'),str) and 值['token']!='' and 是安全整数(值.get('id')) and int(值['id'])>0

def 是分享规格(值):
    '所有者要求工人携带的分享规格'
    if not 是记录(值):
        return False
    模式=值.get('sessionMode')
    if not isinstance(值.get('shareId'),str) or 值['shareId']=='':
        return False
    if not isinstance(值.get('sessionId'),str) or not isinstance(值.get('sessionTitle'),str):
        return False
    if 值.get('accessMode') not in ('open','selected'):
        return False
    if not isinstance(值.get('relay'),str) or not isinstance(值.get('gatewayToken'),str) or not isinstance(值.get('ownerDisplayName'),str):
        return False
    for 键 in ('ownerProviderId','ownerTenantId','dshVersion','ownerInstanceId','ownerCredential'):
        if 键 in 值 and not isinstance(值[键],str):
            return False
    if 'allowsFork' in 值 and not isinstance(值['allowsFork'],bool):
        return False
    if 'sessionMode' in 值 and 模式 not in ('view','write'):
        return False
    if 'allowsFileUpload' in 值 and not isinstance(值['allowsFileUpload'],bool):
        return False
    if 'connection' in 值 and not (是记录(值['connection']) and 值['connection'].get('mode') in ('relay','direct')):
        return False
    if not 是主体标识(值.get('allowedSubjectIds')):
        return False
    if 'expiresAt' in 值 and not 时间可解析(值['expiresAt']):
        return False
    return True

def 解析工人命令(值):
    '解析宿主到工人的进程间命令。未知或畸形则丢掉'
    if not 是记录(值):
        return None
    类型=值.get('type')
    if 类型=='shutdown':
        return {'type':'shutdown'}
    if 类型=='remove-share':
        if isinstance(值.get('shareId'),str) and 值['shareId']!='':
            return {'type':'remove-share','shareId':值['shareId']}
        return None
    if 类型=='add-share':
        if not 是注册令牌(值.get('registrationToken')) or not 是分享规格(值.get('share')):
            return None
        分享=dict(值['share'])
        if 分享.get('connection') is None:
            分享['connection']={'mode':'relay'}
        return {'type':'add-share','registrationToken':值['registrationToken'],'share':分享}
    if 类型=='share-rpc-response':
        if not 是请求身份(值) or not 是安全整数(值.get('status')) or int(值['status'])<100 or int(值['status'])>599:
            return None
        帧={
            'type':'share-rpc-response',
            'registrationToken':值['registrationToken'],
            'token':值['token'],
            'id':int(值['id']),
            'shareId':值['shareId'],
            'status':int(值['status']),
        }
        if 'body' in 值:
            帧['body']=值['body']
        return 帧
    return None

def 解析工人事件(值):
    '解析工人到宿主的进程间事件。未知或畸形则丢掉'
    if not 是记录(值):
        return None
    类型=值.get('type')
    if 类型=='ready':
        return {'type':'ready'}
    if 类型 in ('share-connected','share-closed'):
        if not 是注册身份(值):
            return None
        return {'type':类型,'registrationToken':值['registrationToken'],'shareId':值['shareId']}
    if 类型=='share-access-state':
        状态=解析分享访问状态(值)
        if 状态 is None or not 是注册身份(值):
            return None
        状态['registrationToken']=值['registrationToken']
        状态['shareId']=值['shareId']
        return 状态
    if 类型=='share-error':
        if not 是注册身份(值) or not isinstance(值.get('message'),str):
            return None
        return {'type':'share-error','registrationToken':值['registrationToken'],'shareId':值['shareId'],'message':值['message']}
    if 类型=='share-rpc-cancel':
        if not 是请求身份(值):
            return None
        return {'type':'share-rpc-cancel','registrationToken':值['registrationToken'],'token':值['token'],'id':int(值['id']),'shareId':值['shareId']}
    if 类型=='share-rpc-request':
        if not 是请求身份(值) or 'body' not in 值 or not 是分享行动者(值.get('actor')):
            return None
        return {
            'type':'share-rpc-request',
            'registrationToken':值['registrationToken'],
            'token':值['token'],
            'id':int(值['id']),
            'shareId':值['shareId'],
            'body':值['body'],
            'actor':值['actor'],
        }
    return None
