"""在应用中打开的主机半边：三条 webServer 路由提供已解析目录、图标与启动端点。

安全围栏在本文件：每条路由先过信任围栏；open 路由再校验媒体类型、64 KiB 上限、可用目录 id
与现存绝对目录路径。解析惰性、每插件生命一次。
"""
import json,os#JSON 与路径核验
from urllib.parse import urlsplit#取 pathname
from ...工具.启动环境 import 取启动环境,经ssh拉起#SSH 拉起事实
from ...依赖.schemastery import 正整数字段#有界毫秒
from .目录 import 在应用中打开目录#白名单目录
from .解析器 import 解析在应用中打开应用,解析启动,启动已解析#解析与启动
from .图标 import 提取应用图标#图标提取
from .内部缝 import 内部#测试钩子
from .共享 import 应用列表路由,图标前缀,打开路由#线路径

名称='open-in-app'#插件名（字面量）
依赖=['webServer','connection','subprocess']#路由载体、信任围栏、PATH 解析

有界毫秒=正整数字段(最大=600_000)#1…600000 毫秒
配置={#插件配置（键英文字面量）
    'probeTimeoutMs':有界毫秒,#目录解析宿主命令期限
    'iconTimeoutMs':有界毫秒,#图标提取宿主命令期限
    'launchWatchMs':有界毫秒,#启动早失败看护窗口
}

正文上限字节=64*1024#open 路由正文上限

__all__=[
    '名称','依赖','配置','应用',
    '应用列表路由','图标前缀','打开路由',
]

def 发送json(响应,状态码,载荷):#JSON 应答
    """application/json；no-store（可用性与启动结局是活事实）。"""
    正文=json.dumps(载荷,ensure_ascii=False,separators=(',',':'),allow_nan=False)#锁分隔与非 ASCII
    响应.writeHead(状态码,{#写头
        'content-type':'application/json; charset=utf-8',#类型
        'cache-control':'no-store',#不缓存
    })#头结束
    响应.end(正文)#正文

def 发送方法不允许(响应,允许):#405
    """405 并声明本路由唯一允许的方法。"""
    响应.writeHead(405,{'allow':允许})#Allow
    响应.end()#空体

def 读取有界正文(请求):#bounded body
    """收集有界 UTF-8 正文；超限则排空流并返回 None。"""
    块列表=[]#块
    大小=0#累计
    while True:#读至 EOF
        块=请求.read(65536)#一块
        if 块 is None or len(块)==0:#EOF
            break
        if isinstance(块,str):#文本块
            块=块.encode('utf-8')#转字节
        大小+=len(块)#累计
        if 大小>正文上限字节:#超限
            while True:#排空剩余
                余=请求.read(65536)#继续读
                if 余 is None or len(余)==0:#尽
                    break#停
            return None#拒绝
        块列表.append(块)#收下
    return b''.join(块列表).decode('utf-8')#UTF-8 文本

def 解析打开正文(文本):#open body
    """校验 open 路由正文：JSON 对象且 app/path 为字符串。"""
    try:#解析
        体=json.loads(文本)#JSON
    except json.JSONDecodeError:#非 JSON
        return None#拒绝
    if not isinstance(体,dict):#须对象
        return None#拒绝
    if 'app' not in 体 or 'path' not in 体:#缺键
        return None#拒绝
    应用标识,路径=体['app'],体['path']#字段
    if isinstance(应用标识,str) and isinstance(路径,str):#类型对
        return {'app':应用标识,'path':路径}#通过
    return None#拒绝

def 请求路径名(请求):#pathname
    """从请求 url 取出 pathname。"""
    原始=str(getattr(请求,'url','') or '')#url
    if 原始.startswith('http://') or 原始.startswith('https://'):#绝对
        return urlsplit(原始).path#路径
    return urlsplit('http://localhost'+原始).path#相对补主机

def 应用(上下文,配置值):#登记三条路由
    """在 connection 信任围栏后登记 apps / icon / open 路由。"""
    ssh=经ssh拉起(取启动环境(上下文))#SSH 拉起事实
    def 目录内部():#测试缝 + PATH 解析
        """补上组合的 subprocess PATH 解析。"""
        def 解析可执行(名):#检测用：找不到 → None
            """找不到与不可用同义。"""
            try:#解析
                return 上下文.subprocess.解析可执行文件(名)#命中路径
            except (OSError,LookupError,AttributeError):
                return None
        缝=dict(内部['目录'])#测试可覆盖
        缝['ssh']=ssh#SSH 时整表为空
        缝['解析可执行']=解析可执行#必填
        return 缝#内部事实

    解析映射=None#惰性权威

    def 可用性():#lazy once
        """每插件生命解析一次。"""
        nonlocal 解析映射#可变
        if 解析映射 is None:#首次
            解析映射=解析在应用中打开应用(配置值['probeTimeoutMs'],目录内部())#解析
        return 解析映射#映射

    图标缓存={}#标识 → 应用图标|None

    def 图标于(应用条目,已解析):#per-app cache
        """进程内缓存；None 表示已判定无图标。"""
        if 应用条目.标识 not in 图标缓存:#未提取
            图标缓存[应用条目.标识]=提取应用图标(#提取
                应用条目,已解析,配置值['iconTimeoutMs'],目录内部(),
            )#缓存
        return 图标缓存[应用条目.标识]#结果

    def 刷新解析(应用条目):#ENOENT 后重解析一条
        """替换或移除一条陈旧解析，并丢掉其图标缓存。"""
        映射=可用性()#当前权威
        新=解析启动(应用条目,配置值['probeTimeoutMs'],目录内部())#重解析
        图标缓存.pop(应用条目.标识,None)#丢图标
        if 新 is None:#不再可用
            映射.pop(应用条目.标识,None)#移出
            return None#无
        映射[应用条目.标识]=新#替换
        return 新#新启动

    def 已拒收(请求,响应):#信任围栏
        """未认证/不受信则写状态码并结束；返回是否已拒。"""
        拒收=上下文.connection.requestRejection(请求)#401|403|None
        if 拒收 is None:#放行
            return False#未拒
        响应.writeHead(拒收)#状态
        响应.end()#空体
        return True#已拒

    def 应用列表处理(请求,响应):#GET apps
        """返回已解析应用标识列表。"""
        if 已拒收(请求,响应):#围栏
            return
        if 请求.method!='GET':#方法
            发送方法不允许(响应,'GET')#405
            return
        发送json(响应,200,{'apps':list(可用性().keys())})#菜单序 keys

    def 图标处理(请求,响应):#GET icon/<id>
        """提供一条应用的提取图标。"""
        if 已拒收(请求,响应):#围栏
            return
        if 请求.method!='GET':#方法
            发送方法不允许(响应,'GET')#405
            return
        路径名=请求路径名(请求)#pathname
        标识=路径名[len(图标前缀):].lstrip('/')#id
        def 无图标():#404
            """无可提供图标。"""
            发送json(响应,404,{'code':'not-found','message':'no icon for '+标识})#404
        应用条目=None
        for 条目 in 在应用中打开目录:#白名单
            if 条目.标识==标识:#命中
                应用条目=条目#记下
                break#停
        if 应用条目 is None:#不在目录
            无图标()#404
            return
        已解析=可用性().get(应用条目.标识)#可用性
        if 已解析 is None:#未解析到
            无图标()#404
            return
        图标=图标于(应用条目,已解析)#提取
        if 图标 is None:#无
            无图标()#404
            return
        响应.writeHead(200,{#成功
            'content-type':图标.内容类型,#媒体类型
            'cache-control':'public, max-age=3600',#可缓存一小时
        })#头
        响应.end(图标.字节)#原始字节

    def 打开处理(请求,响应):#POST open
        """校验正文后启动已验证启动器。"""
        if 已拒收(请求,响应):#围栏
            return
        if 请求.method!='POST':#方法
            发送方法不允许(响应,'POST')#405
            return
        头=请求.headers#请求头
        if 'content-type' in 头:#小写
            原始类型=头['content-type']#类型
        elif 'Content-Type' in 头:#原样
            原始类型=头['Content-Type']#类型
        else:#缺席
            原始类型=None#无
        if isinstance(原始类型,list):#多值
            原始类型=原始类型[0] if len(原始类型)>0 else None#首个
        本质=str(原始类型).split(';',1)[0].strip().lower()#媒体本质
        if 本质!='application/json':#必须 JSON
            发送json(响应,415,{'code':'unsupported-media-type','message':'content-type must be application/json'})#415
            return
        try:#读正文
            文本=读取有界正文(请求)#有界
        except (OSError,UnicodeDecodeError,AttributeError):
            发送json(响应,400,{'code':'bad-request','message':'请求正文无法读取'})
            return
        if 文本 is None:#超限
            发送json(响应,413,{'code':'payload-too-large','message':'request body is too large'})#413
            return
        解析体=解析打开正文(文本)#校验
        if 解析体 is None:#形态错
            发送json(响应,400,{'code':'bad-request','message':'request body must be JSON with string "app" and "path"'})#400
            return
        应用条目=None
        for 条目 in 在应用中打开目录:#白名单
            if 条目.标识==解析体['app']:#命中
                应用条目=条目#记下
                break#停
        已解析=None if 应用条目 is None else 可用性().get(应用条目.标识)#可用性
        if 应用条目 is None or 已解析 is None:#未知或不可用
            发送json(响应,400,{'code':'bad-request','message':'unknown or unavailable app: '+解析体['app']})#400
            return
        if 解析体['path']=='' or (not os.path.isabs(解析体['path'])):#须绝对
            发送json(响应,400,{'code':'bad-request','message':'path must be an absolute directory path'})#400
            return
        try:#目录探针
            是目录=os.path.isdir(解析体['path'])#是否目录
        except OSError:#ENOENT/EACCES
            是目录=False#不可用
        if not 是目录:#不是现存目录
            发送json(响应,404,{'code':'not-found','message':'directory does not exist: '+解析体['path']})#404
            return
        结局=启动已解析(已解析,解析体['path'],配置值['launchWatchMs'],目录内部())
        if 结局=='missing':#可执行已消失
            新=刷新解析(应用条目)#重解析一次
            结局='failed' if 新 is None else 启动已解析(新,解析体['path'],配置值['launchWatchMs'],目录内部())#再试
        if 结局=='launched':#成功
            发送json(响应,200,{'ok':True})#200
        else:#失败
            发送json(响应,502,{'code':'launch-failed','message':'failed to launch '+应用条目.标识})#502

    def 挂应用列表():#登记 apps
        """精确 GET 应用列表。"""
        return 上下文.webServer.register({'kind':'exact','path':应用列表路由,'handler':应用列表处理})#登记

    def 挂图标():#登记 icon
        """前缀 GET 图标。"""
        return 上下文.webServer.register({'kind':'prefix','path':图标前缀,'handler':图标处理})#登记

    def 挂打开():#登记 open
        """精确 POST 打开。"""
        return 上下文.webServer.register({'kind':'exact','path':打开路由,'handler':打开处理})#登记

    上下文.副作用(挂应用列表,'open-in-app: GET '+应用列表路由)#效应
    上下文.副作用(挂图标,'open-in-app: GET '+图标前缀+'/<id>')#效应
    上下文.副作用(挂打开,'open-in-app: POST '+打开路由)#效应

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
