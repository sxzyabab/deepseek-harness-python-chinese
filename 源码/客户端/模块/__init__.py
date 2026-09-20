import hashlib,json,os,threading#哈希、JSON、路径与微任务近似
from urllib.parse import unquote as 百分号解码,urlparse as 解析URL
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
from .清单 import (#再导出启动清单类型
    客户端模块错误,#本包异常
    网页启动入口,#入口
    网页启动图,#图
    启动清单,#清单
    启动模块行,#模块行
    启动插件行,#插件行
    解析启动清单,#解析
    解析客户端声明,#dsh.client 声明
    精确包说明符,#裸包根说明符
    剥客户端后缀,#剥 /client
)#清单面

__all__=[#仅中文公开名
    '客户端模块错误',
    '客户端模块注册表',
    '缺客户端包错误',
    '客户端包组合错误',
    '注入启动清单',
    '网页启动入口',
    '网页启动图',
    '启动清单',
    '启动模块行',
    '启动插件行',
    '解析启动清单',
    '解析客户端声明',
    '精确包说明符',
    '剥客户端后缀',
]

构建指示='run `pnpm run build` before launch'#构建指示（错误串，不改）

class 缺客户端包错误(客户端模块错误):
    """缺失的已构建客户端导出。"""
    def __init__(自身,包名,客户端路径,原因):
        """拼结构化消息；路径只做属性，不进消息。"""
        消息='\n'.join([#行
            'client-modules: client bundle not found; '+构建指示+':',#缺包产物
            '  package: '+包名,#包名
        ])#拼多行
        super().__init__(消息)#消息
        自身.包名=包名#包名
        自身.客户端路径=客户端路径#路径不进消息
        自身.__cause__=原因#保留原因

class 客户端包组合错误(客户端模块错误):
    """激活失败按可行动的包构建错误与无关失败分组。"""
    def __init__(自身,失败列表):
        """分组拼消息。"""
        缺包列表=[错误 for 错误 in 失败列表 if isinstance(错误,缺客户端包错误)]#缺包产物
        其余=[错误 for 错误 in 失败列表 if not isinstance(错误,缺客户端包错误)]#其余失败
        名词='package' if len(失败列表)==1 else 'packages'#单复数
        行列表=['client-modules: '+str(len(失败列表))+' client '+名词+' failed to compose:']#标题行
        if len(缺包列表)>0:#有缺包
            行列表.append('  client bundles not found; '+构建指示+':')#缺包分组头
            for 错误 in 缺包列表:#每个缺包
                行列表.append('    - package: '+错误.包名)#只报名，不写路径
        if len(其余)>0:#有其余失败
            行列表.append('  other failures:')#其余分组
            for 错误 in 其余:#逐条
                行列表.append('    - '+str(错误))#消息
        super().__init__('\n'.join(行列表))#聚合错误
        自身.失败列表=失败列表#原失败列表

def 客户端导出路径(包名,导出字段):
    """把 exports['./client'] 解析成相对路径。"""
    if not isinstance(导出字段,dict):#没有 exports
        return None#无
    if './client' not in 导出字段:#没有该子路径
        return None#无
    客户端=导出字段['./client']#./client 条件
    if isinstance(客户端,str):#字符串形式
        return 客户端#路径
    if isinstance(客户端,dict) and 'default' in 客户端 and isinstance(客户端['default'],str):#一层条件 default 臂
        return 客户端['default']#路径
    raise 客户端模块错误('client-modules: '+包名+' exports["./client"] must be a string or an object with a string default')#形态非法

def 短哈希(输入):
    """sha1 内容哈希截成 12 个十六进制字符。"""
    if isinstance(输入,str):#字符串
        输入=输入.encode('utf-8')#编码
    return hashlib.sha1(输入).hexdigest()[:12]#sha1 前 12

def 图行(标识,修订,注入边,立即):
    """一个包 rev 的图行。"""
    行={'id':标识,'url':'/plugins/'+标识+'/client.js?rev='+修订,'rev':修订}#线入口
    if 注入边 is not None:#有注入
        行['inject']=注入边#注入边
    if 立即:#立即预取
        行['immediately']=True#标记
    return 行#入口

def 注入启动清单(网页,图):
    """把启动入口图注入 index.html。"""
    正文=json.dumps(图,ensure_ascii=False,separators=(',',':'),allow_nan=False).replace('<','\\u003c')#转义 < 防冲出
    脚本='<script>window.__DSH_BOOT__ = '+正文+'</script>'#启动脚本
    头=网页.find('<head>')#head 起点
    if 头!=-1:#有 head
        return 网页[:头+6]+脚本+网页[头+6:]#插进 head 开头
    return 脚本+网页#没有 head 则前置

class 客户端模块注册表(服务):
    """网页插件表服务：增量 dsh.client 扫描 + 线组合 + 包路由 + index 挂钩。"""
    def __init__(自身,上下文):
        """建造服务：订阅、播种、并跑激活 flush。"""
        super().__init__(上下文,'clientModules')#服务名 clientModules
        自身.表={}#已组合表
        自身.包元数据={}#包元数据缓存
        自身.重建监听=set()#包重建监听器
        自身.图监听=set()#图变更监听器
        自身.脏集=set()#待对账条目名
        自身.已排冲刷=False#是否已排微任务 flush
        if 上下文.baseUrl is None:#没有配置树锚
            raise 客户端模块错误('client-modules: ctx.baseUrl is unset — the node half needs the config-tree anchor to resolve plugin packages')#缺锚
        自身.解析包json=自身.造解析器(上下文.baseUrl)#解析 package.json
        def 纤程事件(纤程):
            """把该 fiber 的条目名标脏。纤程持有 插件配置。"""
            条目=纤程.插件配置#loader 条目
            if 条目 is None:#不是 loader 行
                return#丢掉
            选项=条目.选项#配置文件 dict
            if 'name' not in 选项:#无名
                return#丢掉
            条目名=选项['name']#名字
            自身.脏集.add(条目名)#标脏
            if 自身.已排冲刷:#已排 flush
                return#幂等
            自身.已排冲刷=True#记下排期
            def 微任务冲刷():
                """稳态只警告。"""
                自身.已排冲刷=False#清排期
                def 警告(错误):
                    """记警告。"""
                    上下文.日志.警告(错误)#警告
                自身.冲刷(警告)#冲刷
            threading.Timer(0,微任务冲刷).start()#近似 queueMicrotask
        上下文.监听('internal/plugin',纤程事件)#订阅
        for 条目 in 上下文.loader.列出插件配置():#播种当前条目
            选项=条目.选项#配置文件 dict
            if 'name' not in 选项:#无名
                continue#跳过
            自身.脏集.add(选项['name'])#播种
        自身.已组合=自身.组合()#先有一份空图
        失败列表=[]#激活失败
        def 收集(错误):
            """激活遍收集。"""
            失败列表.append(错误)#追加
        自身.冲刷(收集)#同步 flush
        if len(失败列表)>0:#有失败
            raise 客户端包组合错误(失败列表)#聚合成一次大声抛
        def 包路由效应():
            """登记前缀路由。"""
            return 上下文.webServer.register({'kind':'prefix','path':'/plugins','handler':自身.提供包})#登记
        上下文.副作用(包路由效应,'client-modules: bundle route')#包路由
        def 清单效应():
            """挂钩 index。"""
            def 钩子(网页):
                """注入启动清单。"""
                return 注入启动清单(网页,自身.已组合)#注入
            return 上下文.webServer.tapIndex(钩子)#挂钩
        上下文.副作用(清单效应,'client-modules: boot manifest injection')#清单注入

    def 造解析器(自身,基址):
        """从配置树锚解析包根。"""
        def 解析(说明符):
            """解析 package.json 绝对路径。"""
            候选=os.path.join(基址,'node_modules',说明符,'package.json')#常见布局
            if os.path.isfile(候选):#存在
                return 候选#路径
            候选2=os.path.join(基址,说明符,'package.json')#相对基址
            if os.path.isfile(候选2):#存在
                return 候选2#路径
            raise FileNotFoundError(说明符+'/package.json')#解析不到
        return 解析#解析器

    def graph(自身):
        """当前已组合入口图。"""
        return 自身.已组合#当前组合

    def clientPath(自身,标识):
        """一条目客户端包的绝对路径。"""
        if 标识 not in 自身.表:#未知
            return None#无
        return 自身.表[标识]['clientPath']#路径

    def rebuilt(自身,标识):
        """给一个包重新哈希。"""
        if 标识 not in 自身.表:#未知 id
            return None#无
        记录=自身.表[标识]#表行
        with open(记录['clientPath'],'rb') as 文件:#重读
            修订=短哈希(文件.read())#哈希
        if 修订==记录['entry']['rev']:#内容没变
            return 修订#原 rev
        入口=记录['entry']#旧入口
        注入边=入口['inject'] if 'inject' in 入口 else None#注入边
        立即='immediately' in 入口 and 入口['immediately'] is True#立即预取
        记录['entry']=图行(标识,修订,注入边,立即)#换新行
        自身.已组合=自身.组合()#重组合
        for 通知 in list(自身.重建监听):#通知重建监听器
            try:#单个订阅者
                通知(标识,修订)#通知
            except BaseException as 错误:#订阅者回调契约未定
                自身.所属上下文.日志.错误(错误)#只打日志
        自身.通知图变更()#再通知图变更
        return 修订#新 rev

    def onRebuilt(自身,监听):
        """订阅包重建；仅在重哈希改变了 rev 时开火。"""
        自身.重建监听.add(监听)#加入集
        def 退订():
            """退订重建。"""
            自身.重建监听.discard(监听)#删除
        return 退订#退订函数

    def onGraphChanged(自身,监听):
        """任何重组合了图的 flush 之后开火。"""
        自身.图监听.add(监听)#加入集
        def 退订():
            """退订图变更。"""
            自身.图监听.discard(监听)#删除
        return 退订#退订函数

    def 组合(自身):
        """组合当前入口图。"""
        入口列表=[记录['entry'] for 记录 in 自身.表.values()]#当前全部入口
        return {'rev':短哈希(json.dumps(入口列表,ensure_ascii=False,separators=(',',':'),allow_nan=False)),'entries':入口列表}#图

    def 通知图变更(自身):
        """通知每个图监听器。"""
        for 监听 in list(自身.图监听):#每个订阅者
            try:#单个订阅者
                监听()#通知
            except BaseException as 错误:#订阅者回调契约未定
                自身.所属上下文.日志.错误(错误)#只打日志

    def 解析元数据(自身,包名):
        """解析包元数据；否定裁决缓存为 None。"""
        if 包名 in 自身.包元数据:#命中（含否定）
            return 自身.包元数据[包名]#缓存
        try:#解析包根
            包路径=自身.解析包json(包名)#resolve package.json
        except FileNotFoundError:#解析不到
            自身.包元数据[包名]=None#否定缓存
            return None#不是客户端行
        try:#读 package.json
            with open(包路径,'r',encoding='utf-8') as 文件:#读
                包=json.load(文件)#解析
        except OSError:#读失败
            自身.包元数据[包名]=None#否定缓存
            return None#不是客户端行
        except json.JSONDecodeError as 错误:#非法 JSON
            raise 客户端模块错误('client-modules: '+包名+' package.json is not valid JSON') from 错误#大声失败
        dsh=包['dsh'] if 'dsh' in 包 else None#dsh 字段
        if not isinstance(dsh,dict):#无或非对象；数据入口
            自身.包元数据[包名]=None#否定缓存
            return None#不是客户端行
        声明值=dsh['client'] if 'client' in dsh else None#client 声明
        声明=解析客户端声明(包名,声明值)#解析
        if 声明 is None or 声明['platform']!='web':#没有声明或不是 web
            自身.包元数据[包名]=None#否定缓存
            return None#不是客户端行
        导出字段=包['exports'] if 'exports' in 包 else None#exports
        相对=客户端导出路径(包名,导出字段)#./client 相对路径
        if 相对 is None:#声明了却没有导出
            raise 客户端模块错误('client-modules: '+包名+' declares dsh.client but exports no "./client" bundle')#缺导出
        元数据={#已解析元数据
            'clientPath':os.path.join(os.path.dirname(包路径),相对),#绝对包路径
            'immediately':'immediately' in 声明 and 声明['immediately'] is True,#立即预取
        }#结束元数据
        if 'inject' in 声明:#有注入
            元数据['inject']=声明['inject']#注入边
        if 'external' in 声明:#有外部请求
            元数据['external']=声明['external']#外部请求
        自身.包元数据[包名]=元数据#写入缓存
        return 元数据#返回元数据

    def 初始包修订(自身,包名,客户端路径):
        """读激活时的包修订。"""
        try:#读包
            with open(客户端路径,'rb') as 文件:#读
                return 短哈希(文件.read())#内容短哈希
        except FileNotFoundError as 错误:#缺文件
            raise 缺客户端包错误(包名,客户端路径,错误)#结构化错误
        except OSError as 错误:#其它磁盘错误
            raise 缺客户端包错误(包名,客户端路径,错误)#结构化错误

    def 处理一行(自身,条目名):
        """把一个条目名对照活着的 loader 条目对账。"""
        合格=False#是否仍是活着的客户端候选
        for 条目 in 自身.所属上下文.loader.列出插件配置():#活条目
            选项=条目.选项#配置文件 dict
            if 'name' not in 选项:#无名
                continue#跳过
            名=选项['name']#名字
            纤程=条目.纤程#纤程
            if 名==条目名 and 纤程 is not None and 条目.已禁用 is not True:#同名、有纤程、未禁用
                合格=True#合格
                break#找到即可
        if not 合格:#不再合格
            return 条目名 in 自身.表 and 自身.表.pop(条目名) is not None#从表删
        if 条目名 in 自身.表:#已在表上
            return False#不动
        元数据=自身.解析元数据(条目名)#解析元数据
        if 元数据 is None:#不是客户端包
            return False#不动
        修订=自身.初始包修订(条目名,元数据['clientPath'])#激活哈希
        注入边=元数据['inject'] if 'inject' in 元数据 else None#注入边
        自身.表[条目名]={#写入表
            'entry':图行(条目名,修订,注入边,元数据['immediately']),#入口
            'clientPath':元数据['clientPath'],#路径
        }#表行结束
        return True#表变了

    def 冲刷(自身,遇错):
        """冲脏集。"""
        变更=False#表是否变了
        for 条目名 in list(自身.脏集):#拷一份再迭代
            自身.脏集.discard(条目名)#先从脏集拿掉
            try:#对账一行
                if 自身.处理一行(条目名):#变了
                    变更=True#记下
            except (缺客户端包错误,客户端模块错误,OSError,json.JSONDecodeError) as 错误:#一行失败
                遇错(错误)#交给调用方
        if 变更:#表变了
            自身.已组合=自身.组合()#重组合
            自身.通知图变更()#通知

    def 提供包(自身,请求,响应):
        """提供 /plugins/<id>/client.js 及其源映射。请求与响应是 webServer 对象。"""
        方法=请求.method#HTTP 方法
        if 方法!='GET' and 方法!='HEAD':#只允许读
            响应.writeHead(405)#方法不允许
            响应.end()#空体
            return
        网址=请求.url#url
        if 网址 is None:#无
            网址='/'#回退根
        路径名=百分号解码(解析URL(网址).path)
        前缀='/plugins/'#前缀
        映射后缀='/client.js.map'#源映射后缀
        包后缀='/client.js'#包后缀
        是源映射=路径名.startswith(前缀) and 路径名.endswith(映射后缀)#是否源映射
        后缀=映射后缀 if 是源映射 else 包后缀#选用后缀
        客户端路径=None#磁盘路径基
        if 路径名.startswith(前缀) and 路径名.endswith(后缀):#路径形态合法
            客户端路径=自身.clientPath(路径名[len(前缀):-len(后缀)])#抽出 id 查表
        路径=None if 客户端路径 is None else (客户端路径+('.map' if 是源映射 else ''))#磁盘路径
        if 路径 is None:#未知资源
            响应.writeHead(404)#未找到
            响应.end()#空体
            return
        try:#读文件
            with open(路径,'rb') as 文件:#读
                体=文件.read()#字节
            类型='application/json; charset=utf-8' if 是源映射 else 'text/javascript; charset=utf-8'#类型
            响应.writeHead(200,{'content-type':类型,'cache-control':'no-cache'})#成功头
            响应.end(体)#写出
        except OSError:#已登记但读不到
            响应.writeHead(404)#未找到
            响应.end()#空体

客户端模块注册表.inject=['webServer','loader']#框架槽
default=客户端模块注册表#框架槽
