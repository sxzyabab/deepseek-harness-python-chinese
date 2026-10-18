import hashlib,json,os,re,threading#哈希、清单、路径与冲刷排期
from urllib.parse import urljoin as 拼接网址,urlsplit as 拆分网址#组合地址与请求拆分
from ...依赖.cordis.服务 import 服务#服务基类
from ...依赖.工具 import 路径转文件url,文件url转路径#路径与 file URL
from ...基础设施.通用工具 import 紧凑json编码,读取json文件#稳定 JSON 与读清单
from .异常 import (
    缺客户端包错误,#缺构建产物
    客户端包组合错误,#激活聚合失败
    客户端模块错误,#本包失败
)
from .客户端.清单 import (
    精确包说明符,#裸包根
    解析客户端声明,#dsh.client
    剥客户端后缀,#剥 /client
)
from . import (
    异常,#异常类
    客户端,#浏览器半边
)


__all__=[#包根本身的名字，加上客户端这个包。不转发客户端里面的类
    '异常','客户端',
    '客户端模块注册表','按模块图排序','启动注入','剥客户端后缀',
    'orderByModuleGraph','bootInjections','stripClientSuffix',
    'default',
]

插件路由='/plugins'#插件资源前缀
不可变缓存='public, max-age=31536000, immutable'#带修订的响应
最大组合网址字节=3*1024#组合 URL 上限
修订长度=12#哈希截断
修订占位='0'*修订长度#划分时的占位修订
源映射尾=re.compile(r'(?:\r?\n)?//# sourceMappingURL=[^\r\n]*(?:\r?\n)?\Z')#包尾源映射
源地址尾=re.compile(r'(?:\r?\n)?//# sourceURL=([^\r\n]+)(?:\r?\n)?\Z')#包尾源地址
绝对或根=re.compile(r'^(?:[A-Za-z][A-Za-z\d+.-]*:|/)')#绝对地址或根路径
客户端分块名=re.compile(r'^client\.[A-Za-z0-9][A-Za-z0-9._-]*\.js\Z')#按需分块
客户端模块标识='@deepseek-ai/dsh-client-modules'#引导包
解析器预载标识=(客户端模块标识,)#引导批里的包


def 数字串(值):
    '贴近 JavaScript String(数字)。整值不带小数点'
    if isinstance(值,float) and 值.is_integer():#整值浮点
        return str(int(值))#不带 .0
    return str(值)#原样


def 框哈希(域,片段列表):
    '按字段长度分帧的 sha1，截成 12 位。字段之间不能串位'
    哈希=hashlib.sha1()#sha1
    哈希.update(域.encode('utf-8'))#域
    哈希.update(b'\0')#分隔
    for 片段 in 片段列表:#逐段
        字节=片段.encode('utf-8')#utf-8
        哈希.update((str(len(字节))+':').encode('utf-8'))#长度帧
        哈希.update(字节)#内容
    return 哈希.hexdigest()[:修订长度]#12 位


def 产物修订(基线):
    '用修改时间、状态时间和大小标识一次构建，不哈希文件内容'
    return 框哈希('plugin-artifact',[#产物帧
        数字串(基线['mtimeMs']),#修改时间
        数字串(基线['ctimeMs']),#状态时间
        数字串(基线['size']),#字节数
    ])#修订


def 组合查询(标识列表,修订,源映射=False):
    '一组有序插件文件的组合查询'
    资源=','.join(标识+'/client.js'+('.map' if 源映射 else '') for 标识 in 标识列表)#文件列表
    return '??'+资源+'&rev='+修订#查询


def 组合网址(标识列表,修订,源映射=False):
    '组合资源的绝对路由'
    return 插件路由+'/'+组合查询(标识列表,修订,源映射)#绝对地址


def 组合引用(标识列表,修订,源映射=False):
    '文档相对的组合引用。去掉路由键开头的斜杠'
    return 组合网址(标识列表,修订,源映射)[1:]#去掉斜杠


def 预计组合网址字节(记录列表):
    '这一组若打成带源映射的组合，浏览器看到的 URL 有多长'
    标识列表=[记录['entry']['id'] for 记录 in 记录列表]#标识
    return len(组合引用(标识列表,修订占位,True).encode('utf-8'))#字节


def 划分组合记录(记录列表):
    '按图顺序切分，不让生成的 URL 超过上限'
    块=[]#已切好的组
    当前=[]#正在累积
    for 记录 in 记录列表:#逐条
        候选=当前+[记录]#试着加上
        if 预计组合网址字节(候选)<=最大组合网址字节:#放得下
            当前=候选#留下
            continue#下一条
        if len(当前)==0:#单条就已经超限
            raise 客户端模块错误('client-modules: '+记录['entry']['id']+' exceeds the '+str(最大组合网址字节)+'-byte combo URL limit')#超限
        块.append(当前)#先交上一组
        当前=[记录]#新的一组
        if 预计组合网址字节(当前)>最大组合网址字节:#这一条自己超限
            raise 客户端模块错误('client-modules: '+记录['entry']['id']+' exceeds the '+str(最大组合网址字节)+'-byte combo URL limit')#超限
    if len(当前)>0:#最后一组
        块.append(当前)#收下
    return 块#分组


def 准备源(资源):
    '去掉包自己的调试指令，并留下生成文件名'
    源=资源['bundle'].decode('utf-8')#脚本文本
    匹配=源地址尾.search(源)#源地址
    源网址=None if 匹配 is None else 匹配.group(1)#捕获
    源=源映射尾.sub('',源地址尾.sub('',源))#去掉两条尾指令
    if not 源.endswith('\n'):#补换行
        源=源+'\n'#换行
    if 源网址 is None:#没有源地址
        回退='/plugins/'+资源['id']+'/'+资源['fileName']#用生成名
    elif 绝对或根.match(源网址):#已经是绝对或根
        回退=源网址#原样
    else:#相对
        回退='/'+源网址#补成根路径
    return {'source':源,'fallbackSource':回退}#可执行源与回退名


def 换行数(值):
    '数换行，用来对齐索引映射的行偏移'
    数量=0#计数
    for 字符 in 值:#逐字符
        if 字符=='\n':#换行
            数量+=1#加一
    return 数量#行数


def 恒等段映射(源,源网址):
    '每一生成行映射到打包脚本的同一行'
    映射=[]#每行一条
    下标=0#行号
    行数=换行数(源)#行数
    while 下标<行数:#逐行
        映射.append('AAAA' if 下标==0 else 'AACA')#首行与续行
        下标+=1#下一行
    return {#恒等映射
        'version':3,#第三版
        'names':[],#无名
        'sources':[源网址],#一个源
        'sourcesContent':[源],#源文本
        'mappings':';'.join(映射),#行映射
    }#映射结束


def 惰性体(生产):
    '第一次取出才生成。失败不缓存，下次再产'
    门=threading.Lock()#并发共用一次生成
    槽={'有':False,'体':None}#缓存
    def 取():
        '取出或生成正文'
        with 门:#互斥
            if 槽['有']:#已经有了
                return 槽['体']#复用
            体=生产()#生成
            槽['体']=体#记下
            槽['有']=True#占住
            return 体#返回
    return 取#取出函数


def 构建组合脚本(资源列表,源映射地址=None):
    '拼一段可执行脚本。不读、也不组合源映射'
    源=''#正文
    for 资源 in 资源列表:#逐个
        源=源+准备源(资源)['source']+';\n'#接上
    if 源映射地址 is None:#没有映射
        文本=源#原样
    else:#盖上映射地址
        文本=源+'//# sourceMappingURL='+源映射地址+'\n'#尾指令
    return 文本.encode('utf-8')#字节


def 构建组合源映射(资源列表,源映射于,文件名='client.js'):
    '按这次请求读到的源映射拼成索引映射'
    段列表=[]#段
    行号=0#当前行
    for 资源 in 资源列表:#逐个
        准备=准备源(资源)#可执行源
        源映射=源映射于(资源['clientPath'])#磁盘映射，可以没有
        段=恒等段映射(准备['source'],准备['fallbackSource'])#默认同行映射
        if 源映射 is not None:#有作者映射
            try:#按原地址重定位 sources
                源路径列表=源映射['sources']#源路径
                源根=源映射['sourceRoot'] if isinstance(源映射.get('sourceRoot'),str) else ''#源根
                基='http://dsh.invalid/plugins/'+资源['id']+'/client.js.map'#重定位基址
                搬迁=[]#新 sources
                for 源项 in 源路径列表:#逐个源
                    分隔=''#源根与源之间
                    if 源根!='' and (not 源根.endswith('/')) and (not 源项.startswith('/')):#需要斜杠
                        分隔='/'#补上
                    解析=拼接网址(基,源根+分隔+源项)#解析
                    基拆=拆分网址(基)#基址部分
                    解拆=拆分网址(解析)#结果部分
                    if 解拆.scheme==基拆.scheme and 解拆.netloc==基拆.netloc:#同一源
                        尾=''#查询与片段
                        if 解拆.query:#有查询
                            尾='?'+解拆.query#查询
                        if 解拆.fragment:#有片段
                            尾=尾+'#'+解拆.fragment#片段
                        搬迁.append(解拆.path+尾)#站内路径
                    else:#其它源
                        搬迁.append(解析)#完整地址
                节=dict(源映射)#拷映射
                节['sources']=搬迁#换 sources
                节.pop('sourceRoot',None)#根已经折进路径
                段=节#用重定位后的段
            except Exception as 错误:#作者源地址不合法
                段=恒等段映射(准备['source'],准备['fallbackSource'])#仍用恒等映射
                跳过=错误#畸形映射不让整段不可调试
        段列表.append({'offset':{'line':行号,'column':0},'map':段})#这一段
        行号+=换行数(准备['source']+';\n')#加上这一段的行
    文本=紧凑json编码({'version':3,'file':文件名,'sections':段列表})+'\n'#索引映射
    return 文本.encode('utf-8')#字节


def 构建组合(记录列表,源映射于,修订=None):
    '描述一个组合，脚本和映射各自推迟到第一次取出'
    资源列表=[]#资源
    for 记录 in 记录列表:#逐条
        资源列表.append({#一条
            'id':记录['entry']['id'],#标识
            'rev':记录['entry']['rev'],#修订
            'clientPath':记录['meta']['clientPath'],#磁盘路径
            'fileName':'client.js',#文件名
            'bundle':记录['bundle'],#字节
        })#资源结束
    if 修订 is None:#按内容算修订
        片段=[]#帧
        for 资源 in 资源列表:#逐个
            片段.append(资源['id'])#标识
            片段.append(资源['rev'])#修订
        修订=框哈希('combo',片段)#组合修订
    条目=[资源['id'] for 资源 in 资源列表]#顺序
    地址=组合网址(条目,修订)#脚本路由
    源映射地址=组合网址(条目,修订,True)#映射路由
    拖车=组合查询(条目,修订,True)#相对脚本目录解析的映射引用
    def 脚本():
        '生成组合脚本'
        return 构建组合脚本(资源列表,拖车)#字节
    def 映射():
        '生成组合源映射'
        return 构建组合源映射(资源列表,源映射于)#字节
    return {#产物
        'url':地址,#绝对路由
        'rev':修订,#修订
        'entries':条目,#顺序
        'sourceMapUrl':源映射地址,#映射路由
        'scriptBody':惰性体(脚本),#脚本
        'sourceMapBody':惰性体(映射),#映射
    }#产物结束


def 构建批次(阶段,记录列表,源映射于):
    '给组合加上首屏调度描述。描述里的 url 是文档相对的'
    产物=构建组合(记录列表,源映射于)#组合
    结果=dict(产物)#拷一份
    结果['descriptor']={#线描述
        'phase':阶段,#bootstrap 或 application
        'url':产物['url'][1:],#去掉开头斜杠
        'rev':产物['rev'],#修订
        'entries':产物['entries'],#顺序
    }#描述结束
    return 结果#批次


def 图行(标识,修订,字段):
    '一个包修订的图行。引用上的 rev 用来打破缓存'
    行={'id':标识,'url':组合引用([标识],修订),'rev':修订}#行
    if 'inject' in 字段:#有注入
        行['inject']=字段['inject']#注入
    if 字段['immediately']:#立即预取
        行['immediately']=True#标记
    if len(字段['external'])>0:#有外部请求
        行['external']=字段['external']#外部
    return 行#行


def 按模块图排序(入口列表):
    '让被请求的动态包排在消费方前面。扫描顺序打破平局'
    按标识={}#id 到行
    for 入口 in 入口列表:#逐行
        按标识[入口['id']]=入口#记下
    有序=[]#结果
    已放=set()#已经放入
    开=[]#当前路径
    def 访问(入口):
        '深度优先。环和自请求都抛错'
        if 入口['id'] in 已放:#已经放过
            return#停
        try:#是否在当前路径上
            环起点=开.index(入口['id'])#环起点
        except ValueError:#不在
            环起点=-1#无环
        if 环起点!=-1:#有环
            raise 客户端模块错误(
                'client-modules: module graph cycle '+' -> '.join(开[环起点:]+[入口['id']])
                +' — a requested package row must precede its consumers, and factory-form CJS cannot deliver partial exports',
            )#环
        开.append(入口['id'])#进入
        for 名 in 入口.get('external',[]):#外部请求
            依赖=按标识.get(名)#同名行
            if 依赖 is None:#再剥 /client
                依赖=按标识.get(剥客户端后缀(名))#包行
            if 依赖 is 入口:#请求自己
                raise 客户端模块错误(
                    'client-modules: "'+入口['id']+'" requests module "'+名+'" that it answers itself '
                    +'— a row must not declare its own package in dsh.client.external',
                )#自请求
            if 依赖 is not None:#图上有这条依赖
                访问(依赖)#先放依赖
        开.pop()#离开
        已放.add(入口['id'])#记下
        有序.append(入口)#放入
    for 入口 in 入口列表:#扫描顺序
        访问(入口)#访问
    return 有序#排序结果


def 启动注入(图):
    '索引注入行。顺序是队列脚本、应用预加载、阻塞引导脚本、图全局'
    引导标识=紧凑json编码(客户端模块标识)#带引号的包名
    队列=(#引导门面。这段脚本原样进页面
        '(()=>{\n'
        'const pendingQueue=[]\n'
        'window.__ModuleLoader__={\n'
        '  mode:"queue",\n'
        '  pendingQueue,\n'
        '  load(registration){pendingQueue.push(registration)},\n'
        '  create(options){\n'
        '    if(this.mode!=="queue")throw new Error("client-modules: window.__ModuleLoader__.create called after module-system boot")\n'
        '    const index=pendingQueue.findIndex(registration=>registration.id==='+引导标识+')\n'
        '    const registration=pendingQueue[index]\n'
        '    if(registration===undefined)throw new Error("client-modules: HTML did not preload '+客户端模块标识+'/client.js")\n'
        '    pendingQueue.splice(index,1)\n'
        '    const exports=registration.factory(specifier=>{\n'
        '      throw new Error(\'client-modules: '+客户端模块标识+'/client.js requested external "\'+specifier+\'" before the module system existed\')\n'
        '    })\n'
        '    if(typeof exports!=="object"||exports===null||typeof exports.createClientModuleSystem!=="function"||typeof exports.apply!=="function"){\n'
        '      throw new Error("client-modules: '+客户端模块标识+'/client.js did not export the bootstrap module face")\n'
        '    }\n'
        '    return exports.createClientModuleSystem(this,{id:registration.id,exports},options)\n'
        '  }\n'
        '}\n'
        '})()'
    )#脚本结束
    引导批=[批 for 批 in 图['batches'] if 批['phase']=='bootstrap']#引导
    应用批=[批 for 批 in 图['batches'] if 批['phase']=='application']#应用
    行列表=[{'kind':'script','placement':'head','text':队列}]#队列脚本
    for 批 in 应用批:#应用预加载
        行列表.append({'kind':'script-preload','src':批['url']})#预加载
    for 批 in 引导批:#阻塞引导
        行列表.append({'kind':'script-src','placement':'head','src':批['url']})#脚本
    行列表.append({'kind':'global','name':'__DSH_BOOT__','value':图})#图全局
    return 行列表#执行顺序


def 拆请求网址(网址):
    '把绝对地址或路径收成 urlsplit 结果'
    文本='/' if 网址 is None else 网址#空则根
    if '://' in 文本:#绝对地址
        return 拆分网址(文本)#拆开
    if not 文本.startswith('/'):#相对路径
        文本='/'+文本#补斜杠
    return 拆分网址('http://x'+文本)#补一个基址再拆


def 条目名(条目):
    '加载器条目的 name。中文加载器的选项是字典'
    选项=getattr(条目,'选项',None)#选项
    if isinstance(选项,dict) and 'name' in 选项:#有名字
        return 选项['name']#名字
    return None#没有


class 客户端模块注册表(服务):
    '网页插件表：增量扫描 dsh.client、组合线、包路由、索引注入'
    def __init__(自身,上下文,配置=None):
        '订阅、播种，并同步跑完激活冲刷'
        super().__init__(上下文,'clientModules')#服务名
        清单路径=os.path.join(os.path.dirname(__file__),'package.json')#本包清单
        包数据=读取json文件(清单路径)#version
        版本=包数据['version']#版本
        提交=os.environ.get('DSH_CLIENT_COMMIT_HASH')#构建写进宿主产物的提交
        自身.发行={'version':版本} if 提交 is None else {'version':版本,'commit':提交}#每张图都带
        自身.表={}#包名到表行
        自身.来源表={}#源键到来源
        自身.包元数据={}#源键到元数据或 None
        自身.重建监听=set()#重建订阅
        自身.图监听=set()#图变更订阅
        自身.脏集=set()#待对账的条目名
        自身.响应表={}#地址到惰性响应
        自身.批响应={}#当前批
        自身.先前批响应={}#上一代表
        自身.已排冲刷=False#微任务是否已排
        自身.已组合=None#当前图，冲刷前会先组合一次
        def 纤程事件(纤程):
            '把这条纤程的条目名标脏'
            插件配置=getattr(纤程,'插件配置',None)#加载器条目
            if 插件配置 is None:#不是加载器行
                return#丢掉
            名=条目名(插件配置)#名字
            if 名 is None:#没有名字
                return#丢掉
            自身.脏集.add(名)#标脏
            if 自身.已排冲刷:#已经排了
                return#幂等
            自身.已排冲刷=True#记下
            def 微任务():
                '稳态只警告'
                自身.已排冲刷=False#清排期
                def 警告(错误):
                    '记警告'
                    上下文.日志.警告(错误)#警告
                自身.冲刷(警告)#冲刷
            定时器=threading.Timer(0,微任务)#当前段之后
            定时器.daemon=True#随进程退出
            定时器.start()#排上
        上下文.监听('internal/plugin',纤程事件)#订阅
        for 条目 in 上下文.加载器.列出插件配置():#播种当前条目
            名=条目名(条目)#名字
            if 名 is not None:#有名字
                自身.脏集.add(名)#播种
        自身.已组合=自身.组合()#先有一份图
        失败列表=[]#激活失败
        def 收集(错误):
            '激活遍收集'
            失败列表.append(错误)#追加
        自身.冲刷(收集)#同步冲刷
        if len(失败列表)>0:#有失败
            raise 客户端包组合错误(失败列表)#一次抛出
        def 登记网页载体(网页上下文,配置值=None):
            '有 webServer 时登记包路由'
            def 路由效应():
                '登记前缀路由并返回拆除器'
                return 网页上下文.webServer.register({#路由
                    'kind':'prefix',#前缀
                    'path':插件路由,# /plugins
                    'handler':自身.提供包,#处理
                })#登记
            网页上下文.副作用(路由效应,'client-modules: bundle route')#包路由
        上下文.依赖启动(['webServer'],登记网页载体)#可选网页载体
        def 注入索引(表):
            '把当前图的启动行追加进索引表'
            表.extend(启动注入(自身.已组合))#追加
        上下文.监听('webserver/index-inject',注入索引)#索引注入

    def graph(自身):
        '当前入口图，变更之间保持同一个对象'
        return 自身.已组合#当前图

    def clientPath(自身,标识):
        '一条目客户端包的绝对路径。未知标识返回 None'
        记录=自身.表.get(标识)#表行
        if 记录 is None:#未知
            return None#无
        return 记录['meta']['clientPath']#路径

    def fetchBundle(自身,请求):
        '没有网页服务器时，按已公布的修订地址给出同样的响应'
        结果=自身.包资源(请求.method,请求.url)#资源
        return {'status':结果['status'],'headers':结果.get('headers'),'body':结果.get('body')}#响应

    def artifactBaseline(自身,标识):
        '读当前字节之前捕获的文件系统基线。未知标识返回 None'
        记录=自身.表.get(标识)#表行
        if 记录 is None:#未知
            return None#无
        return dict(记录['baseline'])#拷一份

    def rebuilt(自身,标识):
        '发布一次构建。修改时间、状态时间和大小都没变则不重读文件'
        记录=自身.表.get(标识)#表行
        if 记录 is None:#未知
            return None#无
        基线=自身.捕获基线(记录['meta']['clientPath'])#先取状态
        修订=产物修订(基线)#新修订
        if 修订==记录['entry']['rev']:#没变
            return 修订#原修订
        文件=open(记录['meta']['clientPath'],'rb')#重读
        try:#读字节
            包=文件.read()#字节
        finally:#关上
            文件.close()#关
        记录['baseline']=基线#换基线
        记录['entry']=图行(标识,修订,记录['meta'])#换行
        记录['bundle']=包#换字节
        自身.已组合=自身.组合()#重组合
        for 通知 in list(自身.重建监听):#通知重建
            try:#一个订阅者
                通知(标识,修订)#通知
            except Exception as 错误:#不能打断后面的订阅者
                自身.所属上下文.日志.错误(错误)#只记日志
        自身.通知图变更()#再通知图
        return 修订#新修订

    def onRebuilt(自身,监听):
        '订阅包重建。只有修订变了才调用'
        自身.重建监听.add(监听)#加入
        def 退订():
            '退订重建'
            自身.重建监听.discard(监听)#删除
        return 退订#退订函数

    def onGraphChanged(自身,监听):
        '图被重新组合之后调用。监听方自己再读 graph'
        自身.图监听.add(监听)#加入
        def 退订():
            '退订图变更'
            自身.图监听.discard(监听)#删除
        return 退订#退订函数

    def 组合(自身):
        '按模块图排序后切成引导批和应用批'
        入口列表=按模块图排序([记录['entry'] for 记录 in 自身.表.values()])#排序
        引导=[]#引导记录
        for 标识 in 解析器预载标识:#预载名单
            记录=自身.表.get(标识)#表行
            if 记录 is not None:#在表上
                引导.append(记录)#收下
        引导标识=set(记录['entry']['id'] for 记录 in 引导)#引导 id
        应用=[]#应用记录
        for 入口 in 入口列表:#图顺序
            if 入口['id'] in 引导标识:#属于引导
                continue#跳过
            记录=自身.表.get(入口['id'])#表行
            if 记录 is not None:#在表上
                应用.append(记录)#收下
        产物=[]#批次产物
        for 一组 in 划分组合记录(引导):#引导分组
            产物.append(构建批次('bootstrap',一组,自身.读取源映射))#引导批
        for 一组 in 划分组合记录(应用):#应用分组
            产物.append(构建批次('application',一组,自身.读取源映射))#应用批
        批响应={}#这一代批响应
        for 一项 in 产物:#逐个产物
            已有脚本=自身.响应表.get(一项['url'])#复用脚本
            if 已有脚本 is None:#没有
                已有脚本={'body':一项['scriptBody'],'contentType':'text/javascript; charset=utf-8'}#新建
            批响应[一项['url']]=已有脚本#脚本
            已有映射=自身.响应表.get(一项['sourceMapUrl'])#复用映射
            if 已有映射 is None:#没有
                已有映射={'body':一项['sourceMapBody'],'contentType':'application/json; charset=utf-8'}#新建
            批响应[一项['sourceMapUrl']]=已有映射#映射
        响应=dict(批响应)#从批响应拷出
        for 记录 in 自身.表.values():#每个包再挂单资源组合
            一项=构建组合([记录],自身.读取源映射,记录['entry']['rev'])#单资源
            if 一项['url'] not in 响应:#批里没有
                旧脚本=自身.响应表.get(一项['url'])#旧脚本
                if 旧脚本 is None:#没有旧的
                    旧脚本={'body':一项['scriptBody'],'contentType':'text/javascript; charset=utf-8'}#新建
                响应[一项['url']]=旧脚本#脚本
            if 一项['sourceMapUrl'] not in 响应:#批里没有映射
                旧映射=自身.响应表.get(一项['sourceMapUrl'])#旧映射
                if 旧映射 is None:#没有旧的
                    旧映射={'body':一项['sourceMapBody'],'contentType':'application/json; charset=utf-8'}#新建
                响应[一项['sourceMapUrl']]=旧映射#映射
        for 资源地址,旧响应 in list(自身.响应表.items()):#留下仍有效的分块响应
            if 自身.分块请求(拆请求网址(资源地址)) is not None:#仍是分块
                响应[资源地址]=旧响应#留下
        自身.先前批响应=自身.批响应#上一代表
        自身.批响应=批响应#这一代
        自身.响应表=响应#全部响应
        批列表=[一项['descriptor'] for 一项 in 产物]#线描述
        摘要=hashlib.sha1(紧凑json编码({'entries':入口列表,'batches':批列表}).encode('utf-8')).hexdigest()[:修订长度]#图修订
        return {'rev':摘要,'release':自身.发行,'entries':入口列表,'batches':批列表}#图

    def 通知图变更(自身):
        '通知每个图监听。一个抛错不能跳过其余'
        for 监听 in list(自身.图监听):#逐个
            try:#隔离
                监听()#通知
            except Exception as 错误:#不能打断
                自身.所属上下文.日志.错误(错误)#只记日志

    def 源键(自身,加载器名,基址):
        '同一说明符在不同配置树里可以解析到不同的包'
        return str(基址)+'\0'+加载器名#基址与说明符

    def 解析元数据(自身,加载器名,基址):
        '解析一份来源的包元数据。否定结果缓存到重启'
        键=自身.源键(加载器名,基址)#缓存键
        if 键 in 自身.包元数据:#命中，包含否定
            return 自身.包元数据[键]#缓存
        定位=自身.定位包清单(加载器名,基址)#package.json
        if 定位 is None:#不是包根
            自身.包元数据[键]=None#否定
            return None#不是客户端行
        包名=定位['packageName']#包名
        包路径=定位['path']#清单路径
        包=读取json文件(包路径)#解析
        dsh=包.get('dsh') if isinstance(包,dict) else None#dsh
        if isinstance(dsh,dict) and 'client' in dsh:#声明在场
            声明=解析客户端声明(包名,dsh['client'])#解析
        else:#缺席
            声明=None#无
        if 声明 is None or 声明['platform']!='web':#不是 web 客户端
            自身.包元数据[键]=None#否定
            return None#不是客户端行
        导出字段=包.get('exports') if isinstance(包,dict) else None#exports
        相对=None#./client
        if isinstance(导出字段,dict) and './client' in 导出字段:#有这个子路径
            客户端导出=导出字段['./client']#值
            if isinstance(客户端导出,str):#字符串
                相对=客户端导出#路径
            elif isinstance(客户端导出,dict) and isinstance(客户端导出.get('default'),str):#一层 default
                相对=客户端导出['default']#路径
            else:#形态不对
                raise 客户端模块错误('client-modules: '+包名+' exports["./client"] must be a string or an object with a string default')#非法
        if 相对 is None:#声明了却没有导出
            raise 客户端模块错误('client-modules: '+包名+' declares dsh.client but exports no "./client" bundle')#缺导出
        元数据={#元数据
            'clientPath':os.path.join(os.path.dirname(包路径),相对),#绝对包路径
            'external':[] if 声明.get('external') is None else list(声明['external']),#外部请求
            'immediately':声明.get('immediately') is True,#立即预取
        }#元数据基
        if 'inject' in 声明:#有注入
            元数据['inject']=list(声明['inject'])#注入
        已解析={'packageName':包名,'meta':元数据}#结果
        自身.包元数据[键]=已解析#缓存
        return 已解析#返回

    def 定位包清单(自身,加载器名,基址):
        '定位这一行挂上的包清单。解析不到包根则 None'
        if 加载器名.startswith('cordis:'):#内建
            return None#不是包
        像路径=加载器名.startswith('.') or 加载器名.startswith('file:') or os.path.isabs(加载器名)#路径形态
        期望包名=None if 像路径 else 精确包说明符(加载器名)#裸包名
        if (not 像路径) and 期望包名 is None:#子路径或带 scheme
            return None#不是包根
        内部=自身.所属上下文.加载器.内部加载器#内部加载器
        解析同步=None if 内部 is None else getattr(内部,'resolveSync',None)#Node 解析
        if not callable(解析同步):#没有 Node 内部解析
            if 期望包名 is None:#路径形态
                if 加载器名.startswith('file:'):#已经是网址
                    模块网址=加载器名#原样
                elif os.path.isabs(加载器名):#绝对路径
                    模块网址=路径转文件url(加载器名)#转网址
                else:#相对说明符
                    基=str(基址)#基址文本
                    if '://' not in 基:#本地路径
                        基=路径转文件url(基)#转网址
                    if not 基.endswith('/'):#补目录斜杠
                        基=基+'/'#斜杠
                    模块网址=拼接网址(基,加载器名)#拼上
                return 自身.最近包(模块网址)#最近的清单
            目录=基址#从树基址向上找 node_modules
            if isinstance(目录,str) and 目录.startswith('file:'):#网址
                目录=文件url转路径(目录)#转路径
            if os.path.isfile(str(目录)):#指向文件
                目录=os.path.dirname(str(目录))#取目录
            目录=os.path.abspath(str(目录))#绝对
            找到=None#清单路径
            while True:#向上
                候选=os.path.join(目录,'node_modules',期望包名,'package.json')#常见布局
                if os.path.isfile(候选):#存在
                    找到=候选#记下
                    break#停
                父=os.path.dirname(目录)#上一层
                if 父==目录:#到根
                    break#停
                目录=父#继续
            if 找到 is None:#解析不到
                return None#不是客户端行
            return {'path':找到,'packageName':期望包名}#清单
        try:#走内部解析
            if getattr(内部,'version',None)=='v2':#第二版
                模块网址=解析同步(基址,{'specifier':加载器名,'attributes':{}})['url']#网址
            else:#第一版
                模块网址=解析同步(加载器名,基址,{})['url']#网址
        except Exception:#解析不了
            return None#不是客户端行
        return 自身.最近包(模块网址,期望包名)#最近且名字相符的清单

    def 最近包(自身,模块网址,期望包名=None):
        '从模块文件向上找声明了期望包名的 package.json'
        if not str(模块网址).startswith('file:'):#不是文件网址
            return None#无
        目录=os.path.dirname(文件url转路径(str(模块网址)))#所在目录
        while True:#向上
            候选=os.path.join(目录,'package.json')#这一层
            if os.path.isfile(候选):#有清单
                try:#读名字
                    数据=读取json文件(候选)#解析
                    名=数据.get('name') if isinstance(数据,dict) else None#名字
                    if isinstance(名,str) and (期望包名 is None or 名==期望包名):#相符
                        return {'path':候选,'packageName':名}#命中
                except (OSError,json.JSONDecodeError) as 错误:#读不了或不是 JSON
                    跳过=错误#这一层不能当包根，继续向上
            父=os.path.dirname(目录)#上一层
            if 父==目录:#到根
                break#停
            目录=父#继续
        return None#没有

    def 捕获基线(自身,客户端路径):
        '读字节之前先捕获文件状态'
        信息=os.stat(客户端路径)#状态
        return {#基线
            'path':客户端路径,#路径
            'mtimeMs':信息.st_mtime_ns/1000000,#修改时间毫秒
            'ctimeMs':信息.st_ctime_ns/1000000,#状态时间毫秒
            'size':信息.st_size,#字节数
        }#基线结束

    def 初始包快照(自身,包名,客户端路径):
        '读激活时的包字节。只有找不到文件才收成缺包错误'
        try:#读
            基线=自身.捕获基线(客户端路径)#先状态
            文件=open(客户端路径,'rb')#打开
            try:#读字节
                包=文件.read()#字节
            finally:#关上
                文件.close()#关
            return {'bundle':包,'baseline':基线}#快照
        except FileNotFoundError as 错误:#没有文件
            raise 缺客户端包错误(包名,客户端路径,错误) from 错误#结构化错误

    def 读取源映射(自身,客户端路径):
        '缺文件当作没有映射。坏映射记警告并退回恒等段'
        try:#读文件
            文件=open(客户端路径+'.map','rb')#打开
        except FileNotFoundError:#没有映射文件
            return None#没有
        try:#解析并校验
            try:#读字节
                体=文件.read()#字节
            finally:#关上
                文件.close()#关
            值=json.loads(体.decode('utf-8'))#解析
            解析=值 if isinstance(值,dict) else None#对象
            源列表=None if 解析 is None else 解析.get('sources')#sources
            名列表=None if 解析 is None else 解析.get('names')#names
            源合格=isinstance(源列表,list) and all(isinstance(源,str) for 源 in 源列表)#源是字符串
            名合格=isinstance(名列表,list) and all(isinstance(名,str) for 名 in 名列表)#名是字符串
            映射合格=解析 is not None and isinstance(解析.get('mappings'),str)#mappings
            if 解析 is None or 解析.get('version')!=3 or (not 源合格) or (not 名合格) or (not 映射合格):#不是正规第三版
                raise 客户端模块错误('client-modules: '+客户端路径+'.map is not a regular Source Map v3 object')#非法
            return 解析#映射
        except Exception as 错误:#坏映射或读失败
            自身.所属上下文.日志.警告(错误)#警告
            return None#退回恒等段

    def 解析来源(自身,条目):
        '一条活着的加载器行对应的包来源。不是客户端包则 None'
        加载器名=条目.选项['name']#说明符
        基址=条目.父组.所属树.所属上下文.基准网址#这棵树的基址
        if 基址 is None:#没有基址
            raise 客户端模块错误('client-modules: loader entry '+加载器名+' has no resolution base URL')#缺基址
        已解析=自身.解析元数据(加载器名,基址)#元数据
        if 已解析 is None:#不是客户端包
            return None#无
        来源=dict(已解析)#包名与元数据
        来源['loaderName']=加载器名#说明符
        来源['baseUrl']=基址#基址
        来源['sourceKey']=自身.源键(加载器名,基址)#源键
        return 来源#来源

    def 处理一行(自身,名字,遇错):
        '把一个条目名对照活着的加载器来源对账'
        下一={}#这一次仍活着的来源
        for 条目 in 自身.所属上下文.加载器.列出插件配置():#活条目
            if 条目名(条目)!=名字:#不是这个名字
                continue#跳过
            if 条目.纤程 is None or 条目.已禁用:#没有纤程或已禁用
                continue#跳过
            来源=自身.解析来源(条目)#解析
            if 来源 is not None:#是客户端包
                下一[来源['sourceKey']]=来源#记下
        受影响=set()#包名
        for 源键,来源 in list(自身.来源表.items()):#旧来源
            if 来源['loaderName']!=名字:#别的条目名
                continue#跳过
            受影响.add(来源['packageName'])#这个包要重算
            if 源键 not in 下一:#不再活着
                del 自身.来源表[源键]#摘掉
        for 源键,来源 in 下一.items():#新来源
            受影响.add(来源['packageName'])#这个包要重算
            自身.来源表[源键]=来源#写入
        变更=False#表是否变了
        for 包名 in 受影响:#逐包
            try:#调和
                if 自身.调和包(包名):#变了
                    变更=True#记下
            except Exception as 错误:#一行失败
                遇错(错误)#交给调用方
        return 变更#是否变了

    def 调和包(自身,包名):
        '一个浏览器包只能有一个活着的加载器来源'
        来源列表=[]#这个包的来源
        for 来源 in 自身.来源表.values():#全部来源
            if 来源['packageName']==包名:#这个包
                来源列表.append(来源)#收下
        if len(来源列表)>1:#多个来源
            位置=[]#诊断
            for 来源 in 来源列表:#逐个
                位置.append(紧凑json编码(来源['loaderName'])+' from '+str(来源['baseUrl']))#位置
            raise 客户端模块错误(
                'client-modules: package '+包名+' resolves from multiple active Loader sources: '+', '.join(位置)+'; remove one entry',
            )#多个来源
        if len(来源列表)==0:#没有来源了
            return 包名 in 自身.表 and 自身.表.pop(包名,None) is not None#从表删除
        来源=来源列表[0]#唯一来源
        已有=自身.表.get(包名)#旧行
        if 已有 is not None and 已有['sourceKey']==来源['sourceKey']:#同一个来源
            return False#不动
        快照=自身.初始包快照(包名,来源['meta']['clientPath'])#读包
        修订=产物修订(快照['baseline'])#修订
        自身.表[包名]={#写入
            'entry':图行(包名,修订,来源['meta']),#入口
            'loaderName':来源['loaderName'],#说明符
            'sourceKey':来源['sourceKey'],#源键
            'meta':来源['meta'],#元数据
            'bundle':快照['bundle'],#字节
            'baseline':快照['baseline'],#基线
        }#行结束
        return True#变了

    def 冲刷(自身,遇错):
        '冲掉脏集。整张图排不出序时保留上一张可排序的图'
        变更=False#是否变了
        for 名字 in list(自身.脏集):#拷一份
            自身.脏集.discard(名字)#先拿掉
            try:#对账
                if 自身.处理一行(名字,遇错):#变了
                    变更=True#记下
            except Exception as 错误:#一行失败不毒化其它行
                遇错(错误)#交给调用方
        if not 变更:#表没变
            return#停
        try:#重组合
            组成=自身.组合()#新图
        except Exception as 错误:#整张图的序有问题
            遇错(错误)#激活时聚合，稳态时警告
            return#保留上一张图
        自身.已组合=组成#换图
        自身.通知图变更()#通知

    def 分块请求(自身,请求网址):
        '匹配当前修订的包内分块地址。不读文件'
        资源地址=请求网址.path#路径
        if 请求网址.query:#有查询
            资源地址=资源地址+'?'+请求网址.query#路径加查询
        for 记录 in 自身.表.values():#逐包
            前缀='/plugins/'+记录['entry']['id']+'/'#这个包的目录
            if not 请求网址.path.startswith(前缀):#不是这个包
                continue#下一个
            请求名=请求网址.path[len(前缀):]#目录内的名字
            是源映射=请求名.endswith('.map')#映射
            文件名=请求名[:-len('.map')] if 是源映射 else 请求名#脚本名
            if 客户端分块名.match(文件名) is None or 文件名=='client.node.js' or 文件名.startswith('client.node.'):#不是浏览器分块
                return None#不提供
            if 是源映射:#映射
                期望=插件路由+'/'+记录['entry']['id']+'/'+文件名+'.map?rev='+记录['entry']['rev']#当前修订
            else:#脚本
                期望=插件路由+'/'+记录['entry']['id']+'/'+文件名+'?rev='+记录['entry']['rev']#当前修订
            if 资源地址!=期望:#不是当前修订
                return None#不提供
            return {'record':记录,'fileName':文件名,'sourceMap':是源映射,'resourceUrl':资源地址}#命中
        return None#没有

    def 分块响应(自身,请求网址):
        '只有地址被请求时才读包内分块'
        请求=自身.分块请求(请求网址)#匹配
        if 请求 is None:#不是分块
            return None#无
        记录=请求['record']#表行
        文件名=请求['fileName']#文件名
        是源映射=请求['sourceMap']#是否映射
        资源地址=请求['resourceUrl']#地址
        客户端路径=os.path.join(os.path.dirname(记录['meta']['clientPath']),文件名)#分块路径
        if not os.path.isfile(客户端路径):#磁盘上没有
            return None#无
        源映射地址=文件名+'.map?rev='+记录['entry']['rev']#相对脚本目录的映射引用
        def 资源():
            '读出这一分块的字节'
            文件=open(客户端路径,'rb')#打开
            try:#读
                字节=文件.read()#字节
            finally:#关上
                文件.close()#关
            return {#资源
                'id':记录['entry']['id'],#标识
                'rev':记录['entry']['rev'],#修订
                'clientPath':客户端路径,#路径
                'fileName':文件名,#文件名
                'bundle':字节,#字节
            }#资源结束
        if 是源映射:#映射
            def 生产():
                '生成这一分块的源映射'
                return 构建组合源映射([资源()],自身.读取源映射,文件名)#字节
            响应={'body':惰性体(生产),'contentType':'application/json; charset=utf-8'}#映射响应
        else:#脚本
            def 生产():
                '生成这一分块的脚本'
                return 构建组合脚本([资源()],源映射地址)#字节
            响应={'body':惰性体(生产),'contentType':'text/javascript; charset=utf-8'}#脚本响应
        自身.响应表[资源地址]=响应#缓存
        return 响应#响应

    def 包资源(自身,方法,网址):
        'GET 与 HEAD 返回不可变正文。其它方法 405，未知地址 404'
        if 方法!='GET' and 方法!='HEAD':#只读
            return {'status':405}#不允许
        请求网址=拆请求网址(网址)#拆开
        资源地址=请求网址.path#路径
        if 请求网址.query:#有查询
            资源地址=资源地址+'?'+请求网址.query#带查询
        响应=自身.响应表.get(资源地址)#当前
        if 响应 is None:#当前没有
            响应=自身.先前批响应.get(资源地址)#上一代表
        if 响应 is None:#上一代表也没有
            响应=自身.分块响应(请求网址)#按需分块
        if 响应 is not None:#命中
            结果={'status':200,'headers':{'content-type':响应['contentType'],'cache-control':不可变缓存}}#头
            if 方法!='HEAD':#需要正文
                结果['body']=响应['body']()#生成
            return 结果#成功
        return {'status':404}#未知资源

    def 提供包(自身,请求,响应):
        '网页路由上的 /plugins 处理'
        网址=请求.url if 请求.url is not None else '/'#node 请求总有 url，缺了用根
        结果=自身.包资源(请求.method,网址)#资源
        响应.writeHead(结果['status'],结果.get('headers'))#状态与头
        响应.end(结果.get('body'))#正文


客户端模块注册表.inject=['加载器']#宿主加载器。上游服务名是 loader
default=客户端模块注册表#默认导出
orderByModuleGraph=按模块图排序#导出名
bootInjections=启动注入#导出名
stripClientSuffix=剥客户端后缀#导出名
