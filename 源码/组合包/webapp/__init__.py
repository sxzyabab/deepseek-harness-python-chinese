'浏览器表面组合包的运行时粘合：提供 webApp，挂上前端 dist，登记 DSH_WEB_URL，并在就绪后打印网址、打开默认浏览器'
import json,os,re,subprocess,sys,weakref
from ...宿主 import 前端静态 as 前端静态插件#回退席上的 dist
from ...宿主.web服务器 import 绑定网址主机,是回环主机#网址主机与回环
from ...启动.app启动 import 审计启动条目#就绪前审计启动条目
from ...工具.启动环境 import 取启动环境,经ssh拉起#SSH 拉起时不打开浏览器
from ...子进程.子进程 import 擦洗父环境#子进程不继承 Harness 凭据
from .异常 import 网页错误#本包失败
from .公开网址 import 解析公开网址#公告根
from . import 异常,公开网址,启动#同目录模块，导入即执行顶层

__all__=[#包根导出同目录模块，以及本文件的公开名
    '异常','公开网址','启动',#同目录模块
    '名称','依赖','配置','应用','内部',#插件槽与测试钩子
]#结束

弱集合=weakref.WeakSet#已宣告根不钉住上下文
派生进程=subprocess.Popen#派生打开器
空设备=subprocess.DEVNULL#不接标准输入
管道=subprocess.PIPE#接下标准错误

名称='web-app'#插件名
依赖=['webServer']#挂载前需要网页服务器
网页地址环境键='DSH_WEB_URL'#公告网址的环境名
已宣告根=弱集合()#每个根只宣告一次

class 网页应用:
    '本进程提供的网页界面'
    def __init__(自身,取公告网址):
        '记下公告根函数'
        自身._取公告网址=取公告网址#闭包

    def getAdvertisedUrl(自身):
        '配置的 publicUrl，否则监听器源'
        return 自身._取公告网址()#公告根

class 配置模式:
    '组合后的部署设置，加上每次调用的命令行值'
    def 校验数据(自身,数据=None):
        '布尔缺席或空值用真。publicUrl 有字符串才收成带尾斜杠的 href；空值保持未设置'
        if not isinstance(数据,dict):#不是对象
            raise 网页错误('web-app: 配置必须是对象')#拒绝
        def 取布尔(键):
            '缺席或空值用真；显式假保留'
            if 键 not in 数据 or 数据[键] is None:#没给或空值
                return True#默认打开
            值=数据[键]#原文
            if not isinstance(值,bool):#不是布尔
                raise 网页错误('web-app: '+键+' 必须是布尔')#拒绝
            return 值#显式值
        结果={#归一结果
            'openBrowser':取布尔('openBrowser'),#打开浏览器
            'printUrl':取布尔('printUrl'),#打印网址
            'surfaceContext':取布尔('surfaceContext'),#登记运行时变量
        }#布尔结束
        if 'publicUrl' in 数据:#写了公告根
            原文=数据['publicUrl']#原文或空值
            if 原文 is None:#显式空值绕过字符串变换
                结果['publicUrl']=None#交给应用当成未设置
            elif not isinstance(原文,str):#不是字符串
                raise 网页错误('web-app: publicUrl 必须是字符串')#拒绝
            else:#收成 href
                结果['publicUrl']=解析公开网址(原文).href#带尾斜杠
        for 键 in 数据:#保留模式没声明的键
            if 键 not in 结果:#还没写过
                结果[键]=数据[键]#原样
        return 结果#归一配置

配置=配置模式()#供纤程校验

def 解析前端入口():
    'dist 位置是本组合包的工作区知识，锚在前端包清单上，不由用户配置'
    目录=os.path.dirname(os.path.abspath(__file__))#从本文件往上找
    相对=os.path.join('node_modules','@deepseek-ai','dsh-web-frontend','package.json')#前端包清单
    while True:#逐层 node_modules
        候选=os.path.join(目录,相对)#这一层
        if os.path.isfile(候选):#找到清单
            return os.path.join(os.path.dirname(候选),'dist','index.html')#dist 入口
        父目录=os.path.dirname(目录)#上一层
        if 父目录==目录:#到了根
            break#停止
        目录=父目录#继续
    raise 网页错误('web-app: 本组合无法解析 @deepseek-ai/dsh-web-frontend')#清单不在

def 打开浏览器(网址):
    '把一个网址交给操作系统的默认浏览器，父环境先擦掉 Harness 凭据'
    if os.name=='nt':#Windows。认证网址带 ?token，必须放进单引号，避免被当成 Where-Object
        引用=网址.replace("'","''")#PowerShell 单引号转义
        命令=['powershell','-NoProfile','-Command',"Start-Process -FilePath '"+引用+"'"]#整段命令
    elif sys.platform=='darwin':#macOS
        命令=['open',网址]#交给系统打开
    else:#其余系统
        命令=['xdg-open',网址]#交给系统打开
    启动器=派生进程(#argv，不是 shell 字符串
        命令,#打开器
        env=擦洗父环境(),#不转发凭据
        stdin=空设备,#不接标准输入
        stdout=None,#标准输出继承
        stderr=管道,#标准错误收回来
        shell=False,#argv
        text=True,#按文本读
        encoding='utf-8',#与 Node 的 utf8 一致
        errors='replace',#非法字节替换
    )#派生结束
    _标准输出,标准错误=启动器.communicate()#等到退出
    码=启动器.returncode#退出码
    if 标准错误 is None:#没有标准错误
        标准错误=''#当空
    if 码!=0:#打开失败
        去空白=标准错误.strip()#去掉两端空白
        if 去空白=='':#没有原因行
            原因='浏览器启动器以代码 '+str(码)+' 退出'#只用退出码
        else:#用第一行
            首行=re.split(r'\r?\n',去空白)[0]#第一行
            原因=re.sub(r'^(?:[A-Za-z]*Error):\s*','',首行)#去掉错误类型前缀
        raise 网页错误(原因)#交给调用方
    if 标准错误!='':#成功但有标准错误
        sys.stderr.write(标准错误)#原样写回

内部={#测试替换 dist 与打开浏览器；生产不改
    'resolveDistIndex':解析前端入口,#dist 入口
    'openBrowser':打开浏览器,#默认浏览器
}#钩子结束

def 应用(上下文,配置值):
    '挂载网页运行时：dist、bash 运行时变量、网址行，以及默认浏览器交接'
    #模式已校验字符串；缺席或显式空值都表示未设置，后面按监听器源公告
    公开地址=配置值['publicUrl'] if 'publicUrl' in 配置值 else None#公告根或空
    绑定主机=上下文.webServer.host#监听地址，区号还在
    if 公开地址 is None and 绑定网址主机(绑定主机) is None:#区号写不进网址
        消息='web-app: 绑定地址 '+json.dumps(绑定主机)+' 带有接口区号，网址写不进去；请传入 --public-url，填浏览器实际访问到的根'#失败
        raise 网页错误(消息)#拒绝挂载
    if 上下文.webServer.protocol=='http:' and not 是回环主机(绑定主机):#非回环明文
        sys.stderr.write('dsh web: 正在 '+绑定主机+' 上以明文 HTTP 监听；请把该端口限制在受信任的代理或网络\n')#警告
    #绑定网址属于这台主机。SSH 下操作者走本地转发，本进程推不出来
    交出浏览器=配置值['openBrowser'] and not 经ssh拉起(取启动环境(上下文))#SSH 抑制打开
    def 应用根网址():
        '公告根：规范 publicUrl，否则监听器自己的源'
        if 公开地址 is not None:#配置了公告根
            return 公开地址#公告根
        return 上下文.webServer.getOrigin()#监听器源
    上下文.提供服务('webApp',网页应用(应用根网址))#网页应用
    上下文.启动插件(前端静态插件,{'distIndex':内部['resolveDistIndex']()})#回退席
    if 配置值['surfaceContext']:#登记 bash 变量
        def 环境接线(运行时上下文,接线配置=None):
            '登记 DSH_WEB_URL'
            def 解析环境(执行=None):
                '按当前公告根提供 DSH_WEB_URL'
                地址=应用根网址()#当前公告根
                return {网页地址环境键:地址}#只返回已声明的键
            运行时上下文.shellEnv.登记({#web-runtime 行
                'name':'web-runtime',#贡献方名
                'variables':{#声明的键
                    网页地址环境键:{#公告网址
                        'description':'Advertised URL of the DeepSeek Harness Web GUI serving this session.',#模型可见描述，不翻译字面量
                    },#DSH_WEB_URL 结束
                },#variables 结束
                'resolve':解析环境,#按次解析
            })#登记结束
        上下文.依赖启动(['shellEnv'],环境接线)#有 shell 环境再登记
    if 配置值['printUrl'] or 交出浏览器:#网址行或打开浏览器
        def 连接接线(连接上下文,接线配置=None):
            '网址行和浏览器交接是就绪信号，等加载器树落定；没有加载器则树已经完整'
            def 宣告就绪():
                '同一根只宣告一次。打印带令牌的网址，并按配置打开浏览器'
                if 连接上下文.根 in 已宣告根:#已经宣告过
                    return#停
                网页地址=应用根网址()#公告根
                认证地址=连接上下文.connection.authenticatedUrl(网页地址)#带启动令牌
                已宣告根.add(连接上下文.根)#先记下，避免重复打开
                if 配置值['printUrl']:#打印就绪行
                    print('dsh web: '+认证地址)#监督方认这一行
                if 交出浏览器:#打开默认浏览器
                    print('dsh web: 正在打开默认浏览器；传入 --no-open 可关闭')#提示
                    try:#打开失败不撤销就绪行
                        内部['openBrowser'](认证地址)#系统浏览器
                    except Exception as 错误:#打开器失败
                        if len(错误.args)>0:#有消息
                            原因=str(错误.args[0])#消息
                        else:#没有消息
                            原因=str(错误)#文本
                        sys.stderr.write('web-app: 无法打开默认浏览器，因为 '+原因+'；请使用启动时打印的 dsh web 网址\n')#警告
            #本树把加载器登记为「加载器」
            加载器=连接上下文.获取服务('加载器',False)#可选
            if 加载器 is None:#手搭的树已经完整
                宣告就绪()#立刻宣告
                return#停
            def 吞警告(行=None):
                '审计可选失败不印到标准错误'
                return#丢掉这一行
            try:#引导自己报失败；这里不发布就绪
                加载器.等待()#等树落定
                审计启动条目(连接上下文.根,'dsh web',吞警告)#必需条目失败则抛
                服务器还在=连接上下文.获取服务('webServer') is not None#监听器还在
                连接还在=连接上下文.获取服务('connection') is not None#连接还在
                if 服务器还在 and 连接还在:#拆掉的服务不再宣告
                    宣告就绪()#打印并打开
            except Exception as 启动失败:#启动诊断归引导所有
                return#就绪保持不发布
        上下文.依赖启动(['connection'],连接接线)#有连接再等就绪

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
