'校验已声明的工作区路径，并给出原生打开地址'
from urllib.parse import urlencode

__all__=['呈现打开路径','呈现宿主路径','呈现打开路由','呈现宿主路由','是否已呈现宿主','是否已呈现文件','已呈现文件网址','是否已呈现数据','路径末段']

呈现打开路径='/api/present.open'
呈现宿主路径='/api/present.host'
呈现打开路由=呈现打开路径[1:]
呈现宿主路由=呈现宿主路径[1:]


def 是否已呈现宿主(值):
    '校验经 HTTP 收到的桌面元数据'
    if not isinstance(值,dict):
        return False
    管理器=值.get('fileManager')
    return isinstance(值.get('name'),str) and isinstance(值.get('available'),bool) and (
        管理器 is None or 管理器=='finder' or 管理器=='explorer' or 管理器=='directory'
    )


def 是否已呈现文件(值):
    '校验从会话日志读出的文件声明'
    if not isinstance(值,dict):
        return False
    路径=值.get('path')
    说明=值.get('description',None)
    有说明='description' in 值
    return isinstance(路径,str) and len(路径.strip())>0 and (not 有说明 or isinstance(说明,str))


def 已呈现文件网址(会话标识,序号,下标):
    '已声明文件的文档相对打开地址'
    return 呈现打开路由+'?'+urlencode({'sessionId':str(会话标识),'seq':str(序号),'index':str(下标)})


def 是否已呈现数据(值):
    '校验交付事件里的回合、调用和文件表'
    if not isinstance(值,dict):
        return False
    回合=值.get('turn')
    调用=值.get('callId')
    文件表=值.get('files')
    return isinstance(回合,int) and not isinstance(回合,bool) and 回合>=1 and isinstance(调用,str) and len(调用)>0 and isinstance(文件表,list)


def 路径末段(路径):
    '最后一段。没有分隔符则整串'
    斜杠=路径.rfind('/')
    反斜杠=路径.rfind('\\')
    位置=斜杠 if 斜杠>反斜杠 else 反斜杠
    if 位置<0:
        return 路径
    return 路径[位置+1:]
