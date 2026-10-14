'启动时按宿主处境采样一次，挂上 native 或 browse 交互两面'
import os,re,sys#环境与平台
from urllib.parse import urlsplit#权威主机名
from ...工具.启动环境 import 取启动环境,经ssh拉起#SSH 拉起事实
from .探测 import 能否执行,有Linux选择器二进制#PATH 探测
from .解析 import 解析目录选择后端#按宿主事实解析后端

_段规则=re.compile(r'^[0-9]{1,3}\Z')#127/8 每一段

def _主机名回环(主机名):#受信任主机名是否环回
    'localhost、[::1]、::1，以及 127/8'
    if 主机名 in ('localhost','[::1]','::1'):#名字或 IPv6 环回
        return True#环回
    段列表=主机名.split('.')#IPv4
    if len(段列表)!=4 or 段列表[0]!='127':#不是 127/8
        return False#不是
    for 段 in 段列表:#逐段
        if _段规则.fullmatch(段) is None or int(段)>255:#非法段
            return False#不是
    return True#环回

名称='directory-picker-auto'#插件名（字面量）
依赖=['webServer','connection','加载器']#网页服务、信任围栏与加载器

def _是远程权威(条目):#trustedHosts 一条是否算远程
    '解析失败或主机名不是环回，就算远程权威'
    if not isinstance(条目,str) or 条目=='':#空
        return True#算远程
    try:#按裸权威解析
        主机名=urlsplit('http://'+条目).hostname or ''#主机名
    except ValueError:#解析失败
        return True#算远程
    return not _主机名回环(主机名)#非环回即远程

def _允许远程权威(连接):#connection.allowsRemoteAuthorities
    '优先读连接上的事实；缺属性时按受信任主机表推导'
    已声明=getattr(连接,'allowsRemoteAuthorities',None)#已声明
    if isinstance(已声明,bool):#布尔
        return 已声明#原样
    主机表=getattr(连接,'受信任主机表',None)#中文表
    if 主机表 is None:#英文名
        主机表=getattr(连接,'trustedHosts',())#表
    for 条目 in 主机表:#逐条
        if _是远程权威(条目):#有远程
            return True#允许
    return False#全是环回或缺席

后端包={#kind → 宿主后端包名（线协议字面量）
    'native':'@deepseek-ai/dsh-host-directory-picker-native',#原生选择器后端
    'browse':'@deepseek-ai/dsh-host-directory-picker-browse',#应用内浏览后端
}

界面包={#kind → 客户端界面包名（线协议字面量）
    'native':'@deepseek-ai/dsh-client-ui-directory-picker-native',#原生选择器界面
    'browse':'@deepseek-ai/dsh-client-ui-directory-picker-browse',#应用内浏览界面
}

__all__=['名称','依赖','后端包','界面包','应用','能否执行','有Linux选择器二进制','解析目录选择后端']

def _节点平台():
    '把 sys.platform 粗映射为 win32/darwin/linux'
    名=sys.platform
    if 名=='win32':
        return 'win32'
    if 名=='darwin':
        return 'darwin'
    if 名.startswith('linux'):
        return 'linux'
    return 名#未识别平台原样返回

def 应用(上下文):
    '按启动时一次采样解析交互，并把后端与界面挂为加载器条目'
    网页服务=上下文.webServer#绑定主机来源
    连接=上下文.connection#信任围栏
    后端=解析目录选择后端({#按当前宿主事实
        'bindHost':getattr(网页服务,'host',None) if 网页服务 is not None else None,#有效绑定主机
        'allowsRemoteAuthorities':_允许远程权威(连接),#远程权威则只能 browse
        'platform':_节点平台(),
        'ssh':经ssh拉起(取启动环境(上下文)),#SSH 拉起则只能 browse
        'env':{#显示会话环境
            'DISPLAY':os.environ.get('DISPLAY'),
            'WAYLAND_DISPLAY':os.environ.get('WAYLAND_DISPLAY'),
        },
        'linuxChooser':有Linux选择器二进制(os.environ.get('PATH'),能否执行),#Linux 是否有原生选择器
    })
    def 挂载():
        '把解析出的交互两面挂进加载器根树；失败则倒序卸掉已挂条目'
        加载器=上下文.加载器
        if 加载器 is None:
            raise RuntimeError('directory-picker-auto: loader service is missing')
        标识列表=[]#本插件本趟创建的条目 id
        def 卸载():
            '倒序卸掉本插件挂上的全部条目；树拆掉后已经不在的直接跳过'
            for 标识 in reversed(list(标识列表)):#后挂先卸
                try:#可能已被摘
                    加载器.解析(标识)#还在树上才卸
                except LookupError:#树拆掉时已经没了
                    continue#跳过
                加载器.移除(标识)#停纤程并从树上摘掉
        try:#先后端后界面
            for 包名 in (后端包[后端],界面包[后端]):
                标识=加载器.创建({'name':包名})
                标识列表.append(标识)
                条目=加载器.解析(标识)
                纤程=条目.纤程
                if 纤程 is None:
                    raise RuntimeError('directory-picker-auto: failed to load '+包名)
                纤程.等待()#等这一面启动完成
        except BaseException:
            卸载()#中途失败卸残留
            raise
        return 卸载
    return 上下文.副作用(挂载,'directory-picker-auto: interaction entries')#登记可拆除副作用

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
