'在应用中打开的主机半边：三条路由提供已解析的应用标识、图标和启动'
import json,os,shutil,tempfile,urllib.parse#正文、图标临时目录、路径
from ...工具.启动环境 import 取启动环境,经ssh拉起#进程层的 SSH 事实
from ...依赖.schemastery import 正整数字段,字典字段#有界毫秒配置
from ...工具.原生命令 import 桌面应用程序图标#Linux 桌面图标
from . import (
    异常,#失败类型
    共享,#线路径
    内部缝,#测试钩子
    目录,#白名单
    解析器,#解析与启动
)
from .共享 import 应用列表路由,图标前缀,打开路由#三条路由的路径
from .内部缝 import 内部#生产默认是空表
from .目录 import 在应用中打开目录#菜单顺序的白名单
from .解析器 import (
    补全内部事实,#补齐平台事实
    经注册表解析,#一条条目
    注册表视图一次,#一趟共用注册表
    启动已解析,#主启动器与回退
    取命令输出,#plutil、sips、powershell
    平台规格于,#Linux 的 desktop 标识
    查找桌面条目,#Linux 图标名
    xdg数据目录,#图标查找根
)

__all__=[
    '名称','依赖','配置','应用',
    '异常','共享','内部缝','目录','解析器',
]

名称='open-in-app'#插件名
依赖=['webServer','connection','subprocess']#路由载体、信任围栏、PATH 解析
正文上限字节=64*1024#打开路由的正文上限

def 有界毫秒():
    '1 到 600000 的整数毫秒，步长 1，必填'
    return 正整数字段(最大=600_000)

配置=字典字段(字典结构={#三个期限都必填，键是配置字段名
    'probeTimeoutMs':有界毫秒(),#目录解析的宿主命令期限
    'iconTimeoutMs':有界毫秒(),#图标提取的宿主命令期限
    'launchWatchMs':有界毫秒(),#启动早失败的看护窗口
})

def 发送json(响应,状态码,载荷):
    'application/json，不缓存。可用性和启动结局都是当场事实'
    响应.writeHead(状态码,{#状态与头
        'content-type':'application/json; charset=utf-8',#JSON 文本
        'cache-control':'no-store',#不缓存
    })
    响应.end(json.dumps(载荷,ensure_ascii=False,separators=(',',':')))#紧凑 JSON

def 发送方法不允许(响应,允许):
    '405，并写出这条路由唯一允许的方法'
    响应.writeHead(405,{'allow':允许})#Allow
    响应.end()#空正文

def 应用(上下文,配置值):
    '在 connection 信任围栏后面登记应用列表、图标和打开三条路由'
    ssh=经ssh拉起(取启动环境(上下文))#只看进程层的 SSH 标记

    def 目录内部():
        '测试钩子盖在 SSH 事实和 PATH 解析上面。后写的键生效'
        def 解析可执行(名):
            '解析不到与不可用是同一件事'
            try:
                return 上下文.subprocess.解析可执行文件(名)#命中的路径
            except Exception as 错误:#提供方拒绝表示这个名字不可用
                return None
        缝={'ssh':ssh,'resolveExecutable':解析可执行}#插件补上的事实
        缝.update(内部['catalog'])#测试可以盖掉
        return 缝

    解析映射=None#这一生只解析一次

    def 可用性():
        '第一次需要目录时解析整表。SSH 拉起不探测，交回空表'
        nonlocal 解析映射
        if 解析映射 is None:#还没解析
            事实=补全内部事实(目录内部())#补齐这一次
            if 事实['ssh']:#远程拉起没有本地界面程序
                解析映射={}
            else:
                注册表=注册表视图一次(配置值['probeTimeoutMs'],事实)#整表共用一次注册表
                映射={}#标识 → 已验证启动。按目录顺序写入
                for 应用条目 in 在应用中打开目录:#菜单顺序，逐条同步解析
                    结果=经注册表解析(应用条目,配置值['probeTimeoutMs'],注册表,事实)
                    if 结果 is not None:#本机确实有
                        映射[应用条目['id']]=结果
                解析映射=映射#之后的点击和刷新都用这张表
        return 解析映射

    图标缓存={}#标识 → 图标或 None。None 表示已经判定没有

    def 已拒收(请求,响应):
        '不受信任或未认证就写状态码并结束。返回是否已经拒绝'
        拒收=上下文.connection.requestRejection(请求)#401、403 或放行
        if 拒收 is None:#围栏和认证都过了
            return False
        响应.writeHead(拒收)#拒绝状态
        响应.end()#空正文
        return True

    def 应用列表处理(请求,响应):
        '返回已经解析到的应用标识'
        if 已拒收(请求,响应):#围栏
            return
        if 请求.method!='GET':#只接受 GET
            发送方法不允许(响应,'GET')
            return
        发送json(响应,200,{'apps':list(可用性().keys())})#菜单顺序的键

    def 图标处理(请求,响应):
        '提供一条应用的图标字节'
        if 已拒收(请求,响应):#围栏
            return
        if 请求.method!='GET':#只接受 GET
            发送方法不允许(响应,'GET')
            return
        路径名=urllib.parse.urlparse(urllib.parse.urljoin('http://localhost/',str(请求.url))).path#pathname
        标识=路径名[len(图标前缀):]#前缀后面的一段
        if 标识.startswith('/'):#去掉一个斜杠
            标识=标识[1:]

        def 无图标():
            '这条标识没有可提供的图标'
            发送json(响应,404,{'code':'not-found','message':'no icon for '+标识})

        应用条目=None#白名单命中
        for 条目 in 在应用中打开目录:#目录顺序
            if 条目['id']==标识:
                应用条目=条目
                break
        if 应用条目 is None:#不在目录里
            无图标()
            return
        已解析=可用性().get(应用条目['id'])#本机有没有
        if 已解析 is None:
            无图标()
            return
        if 应用条目['id'] not in 图标缓存:#第一次才提取
            完成=补全内部事实(目录内部())#提取用的平台事实
            结果=None#默认没有图标
            if 完成['platform']=='linux':#图标来自 desktop 的 Icon=
                规格=平台规格于(应用条目,完成['platform'])
                桌面标识=None if 规格 is None else 规格.get('desktopId')
                if 桌面标识 is not None:
                    条目文本=查找桌面条目(桌面标识,完成)
                    图标名=None if 条目文本 is None else 条目文本.get('icon')
                    if 图标名 is not None and 图标名!='':
                        结果=桌面应用程序图标(图标名,xdg数据目录(完成))
            elif 已解析.get('icon') is None:#这条启动器没有自己的图
                结果=None
            elif 已解析['icon']['kind']=='app-bundle':#macOS：icns 转 128px PNG
                包路径=已解析['icon']['path']#bundle
                资源目录=os.path.join(包路径,'Contents','Resources')
                图标文件=None#icns 文件名
                plist文本=取命令输出(
                    'plutil',
                    ['-convert','json','-o','-',os.path.join(包路径,'Contents','Info.plist')],
                    配置值['iconTimeoutMs'],
                    完成,
                )
                if plist文本 is not None:
                    try:
                        声明=json.loads(plist文本)#Info.plist
                        值=声明.get('CFBundleIconFile') if isinstance(声明,dict) else None
                        if isinstance(值,str) and 值!='':
                            图标文件=值 if 值.endswith('.icns') else 值+'.icns'
                    except json.JSONDecodeError as 错误:#JSON 坏了，仍可扫 Resources
                        图标文件=None
                if 图标文件 is None:#声明没有，取 Resources 里第一个 icns
                    try:
                        for 名 in os.listdir(资源目录):
                            if 名.endswith('.icns'):
                                图标文件=名
                                break
                    except OSError as 错误:#没有 Resources
                        图标文件=None
                if 图标文件 is not None:
                    icns路径=os.path.join(资源目录,图标文件)
                    try:
                        os.stat(icns路径)#声明的文件要在磁盘上
                        有文件=True
                    except OSError as 错误:#plist 写了不存在的图标
                        有文件=False
                    if 有文件:
                        工作目录=tempfile.mkdtemp(prefix='dsh-open-in-app-')#sips 的临时目录
                        try:
                            输出png=os.path.join(工作目录,'icon.png')
                            跑过=取命令输出(
                                'sips',
                                ['-s','format','png','-Z','128',icns路径,'--out',输出png],
                                配置值['iconTimeoutMs'],
                                完成,
                            )
                            if 跑过 is not None:
                                try:
                                    with open(输出png,'rb') as 图片文件:
                                        字节=图片文件.read()
                                    结果={'bytes':字节,'contentType':'image/png'}
                                except OSError as 错误:#sips 退出 0 但没写出文件
                                    结果=None
                        finally:
                            shutil.rmtree(工作目录,ignore_errors=True)#无论成败都删临时目录
            else:#Windows：可执行文件的关联图标，32px PNG
                可执行路径=已解析['icon']['path']
                工作目录=tempfile.mkdtemp(prefix='dsh-open-in-app-')
                try:
                    脚本路径=os.path.join(工作目录,'extract-icon.ps1')
                    输出png=os.path.join(工作目录,'icon.png')
                    提取图标脚本='\n'.join([#路径走 -File 的位置参数，不进命令行解析
                        'param([string]$Source, [string]$Target)',
                        '$ErrorActionPreference = "Stop"',
                        'Add-Type -AssemblyName System.Drawing',
                        '$icon = [System.Drawing.Icon]::ExtractAssociatedIcon($Source)',
                        'if ($null -eq $icon) { exit 1 }',
                        '$bitmap = $icon.ToBitmap()',
                        '$bitmap.Save($Target, [System.Drawing.Imaging.ImageFormat]::Png)',
                        '',
                    ])
                    with open(脚本路径,'w',encoding='utf-8',newline='\n') as 脚本文件:
                        脚本文件.write(提取图标脚本)
                    跑过=取命令输出('powershell.exe',[
                        '-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass',
                        '-File',脚本路径,可执行路径,输出png,
                    ],配置值['iconTimeoutMs'],完成)
                    if 跑过 is not None:
                        try:
                            with open(输出png,'rb') as 图片文件:
                                字节=图片文件.read()
                            结果={'bytes':字节,'contentType':'image/png'}
                        except OSError as 错误:#脚本退出 0 但没写出文件
                            结果=None
                finally:
                    shutil.rmtree(工作目录,ignore_errors=True)#删掉脚本和 png
            图标缓存[应用条目['id']]=结果#含 None，避免重复提取
        图标=图标缓存[应用条目['id']]
        if 图标 is None:
            无图标()
            return
        响应.writeHead(200,{#图标可缓存一小时
            'content-type':图标['contentType'],
            'cache-control':'public, max-age=3600',
        })
        响应.end(图标['bytes'])#原始字节

    def 打开处理(请求,响应):
        '校验正文后启动已验证的启动器。可执行文件不见了就重解析这一条并再试一次'
        if 已拒收(请求,响应):#围栏
            return
        if 请求.method!='POST':#只接受 POST
            发送方法不允许(响应,'POST')
            return
        本质=str(请求.headers.get('content-type')).split(';',1)[0].strip().lower()#媒体类型本质
        if 本质!='application/json':#必须是 JSON
            发送json(响应,415,{
                'code':'unsupported-media-type',
                'message':'content-type must be application/json',
            })
            return
        try:#读有界正文。超限则排空剩余
            声明文本=请求.headers.get('content-length')
            if 声明文本 is None:#这条宿主没有读到正文结束的流
                文本=''
            else:
                剩余=int(声明文本)#声明的长度
                块列表=[]
                大小=0
                超限=False
                while 剩余>0:
                    块=请求.rfile.read(min(65536,剩余))#一块
                    if not 块:#流提前结束
                        break
                    if isinstance(块,str):
                        块=块.encode('utf-8')
                    大小+=len(块)
                    剩余-=len(块)
                    if 大小>正文上限字节:#超过 64KiB
                        超限=True
                        if 剩余>0:#排空，让拒绝仍是一条完整响应
                            请求.rfile.read(剩余)
                        break
                    块列表.append(块)
                if 超限:
                    文本=None
                else:
                    文本=b''.join(块列表).decode('utf-8','replace')
        except Exception as 错误:#读到一半连接断了
            发送json(响应,400,{'code':'bad-request','message':'request body unreadable'})
            return
        if 文本 is None:#正文太大
            发送json(响应,413,{'code':'payload-too-large','message':'request body is too large'})
            return
        解析体=None#app 与 path 都得是字符串
        try:
            体=json.loads(文本)#JSON
        except json.JSONDecodeError as 错误:#不是 JSON
            体=None
        if isinstance(体,dict):
            应用标识=体.get('app')
            路径值=体.get('path')
            if isinstance(应用标识,str) and isinstance(路径值,str):
                解析体={'app':应用标识,'path':路径值}
        if 解析体 is None:#形态不对
            发送json(响应,400,{
                'code':'bad-request',
                'message':'request body must be JSON with string "app" and "path"',
            })
            return
        应用条目=None
        for 条目 in 在应用中打开目录:
            if 条目['id']==解析体['app']:
                应用条目=条目
                break
        已解析=None if 应用条目 is None else 可用性().get(应用条目['id'])
        if 应用条目 is None or 已解析 is None:#未知或当前不可用
            发送json(响应,400,{
                'code':'bad-request',
                'message':'unknown or unavailable app: '+解析体['app'],
            })
            return
        if 解析体['path']=='' or not os.path.isabs(解析体['path']):#必须是绝对路径
            发送json(响应,400,{
                'code':'bad-request',
                'message':'path must be an absolute directory path',
            })
            return
        try:
            是目录=os.path.isdir(解析体['path'])#现存目录
        except OSError as 错误:#不存在或没有权限
            是目录=False
        if not 是目录:
            发送json(响应,404,{
                'code':'not-found',
                'message':'directory does not exist: '+解析体['path'],
            })
            return
        结局=启动已解析(已解析,解析体['path'],配置值['launchWatchMs'],目录内部())
        if 结局=='missing':#核验过的启动器已经不在，重解析这一条再试一次
            映射=可用性()#当前权威表
            事实=补全内部事实(目录内部())
            if 事实['ssh']:#SSH 下不会再有本地启动器
                新=None
            else:
                新=经注册表解析(
                    应用条目,
                    配置值['probeTimeoutMs'],
                    注册表视图一次(配置值['probeTimeoutMs'],事实),
                    事实,
                )
            图标缓存.pop(应用条目['id'],None)#旧图标作废
            if 新 is None:#重解析也没有
                映射.pop(应用条目['id'],None)#下次列表不再提供
                结局='failed'
            else:
                映射[应用条目['id']]=新#换成新启动器
                结局=启动已解析(新,解析体['path'],配置值['launchWatchMs'],目录内部())
        if 结局=='launched':
            发送json(响应,200,{'ok':True})
        else:
            发送json(响应,502,{
                'code':'launch-failed',
                'message':'failed to launch '+应用条目['id'],
            })

    def 挂应用列表():
        '登记精确的 GET 应用列表，并交出拆除器'
        return 上下文.webServer.register({
            'kind':'exact',
            'path':应用列表路由,
            'handler':应用列表处理,
        })

    def 挂图标():
        '登记图标前缀，并交出拆除器'
        return 上下文.webServer.register({
            'kind':'prefix',
            'path':图标前缀,
            'handler':图标处理,
        })

    def 挂打开():
        '登记精确的 POST 打开，并交出拆除器'
        return 上下文.webServer.register({
            'kind':'exact',
            'path':打开路由,
            'handler':打开处理,
        })

    上下文.副作用(挂应用列表,'open-in-app: GET '+应用列表路由)#应用列表
    上下文.副作用(挂图标,'open-in-app: GET '+图标前缀+'/<id>')#图标
    上下文.副作用(挂打开,'open-in-app: POST '+打开路由)#打开

name=名称#框架槽
inject=依赖#框架槽
Config=配置#框架槽
apply=应用#框架槽
