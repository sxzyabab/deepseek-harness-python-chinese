'已配置插件索引的 Host 读取：发现页和 plugin_market 工具'
import os,re,time,threading#路径、版本、时限、共享获取
import urllib.request,urllib.error,urllib.parse#索引获取
from ...依赖.schemastery import 字符串字段,自然数字段,正整数字段,列表字段,枚举字段#配置
from ...类型化远程调用.协议 import 远程服务,远程,远程错误#远程服务
from ...工具.超时 import 定时器延迟上限毫秒#定时器上限
from ...内核.智能体循环.中止与并发 import 中止控制器,若已中止则抛出#寿命
from ...工具.插件详情 import 详情失败,语言链,npm文件来源,npm文件来源顺序,npm文件#详情与 npm 文件
from ...工具.插件市场索引 import 市场安装目标#安装参数
from ..app启动 import 评估插件兼容,获取dsh运行时版本#与安装时相同的兼容性
from .索引网址 import 规范化索引网址,序列化网址#索引网址
from .解析线程 import 在线程解析索引#不占调用线程做完解析
from .搜索 import 市场搜索#过滤与排序
from .仓库缓存 import 仓库缓存#部分克隆
from .详情 import 详情读取器,仓库于#详细介绍
from .详情文件 import 仓库文件,等到结果#仓库文件与期约
from .异常 import 文件过大#再导出
from . import (
    类型,
    异常,
    索引网址,
    解析,
    工作线程,
    解析线程,
    搜索,
    仓库缓存 as 仓库缓存模块,
    详情文件,
    详情,
    工具,
)#子模块

__all__=[#仅中文公开名；框架槽不在这里
    '插件市场','配置','文件过大','仓库缓存','详情读取器','市场搜索',
    '类型','异常','索引网址','解析','工作线程','解析线程','搜索','仓库缓存模块','详情文件','详情','工具',
]#公开面结束

详情文件路径='/api/plugin-market/detail-file'#图片路由
公共注册表=set(['registry.npmjs.org','registry.npmmirror.com'])#公共 npm 文件 CDN 能提供的注册表
页上限=100#search 一页最多这么个
最大原因=4#原因链到此截断
版本表达式=re.compile(r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$')#SemVer

索引字段=列表字段(字符串字段(格式=r'^https?://\S+$'),默认值=[])#显示顺序
索引字段.meta={'volatile':True}#设置和 setIndexes 不重挂服务
配置={#部署配置，键是配置文件里的英文名
    'indexes':索引字段,#索引网址
    'fetchTimeoutMs':正整数字段(默认值=15000,最大=定时器延迟上限毫秒),#单次获取时限
    'maxBytes':正整数字段(默认值=128*1024*1024),#索引正文上限
    'cacheTtlMs':自然数字段(默认值=600000),#成功文档、详情和默认分支提交
    'detailMaxBytes':正整数字段(默认值=1024*1024),#详情文档
    'detailImageMaxBytes':正整数字段(默认值=5*1024*1024),#详情旁的图片
    'detailRepositoryMaxBytes':正整数字段(默认值=50*1024*1024),#一条 Git 命令的增量
    'detailCacheMaxBytes':正整数字段(默认值=500*1024*1024),#部分克隆总量
    'detailCacheDir':字符串字段(可空=True),#相对配置档；没有配置档时必须绝对
    'detailGitTimeoutMs':正整数字段(默认值=60000,最大=定时器延迟上限毫秒),#克隆回退的一条命令
    'detailNpmFileSources':列表字段(枚举字段(*tuple(npm文件来源)),最小数量=1,默认值=list(npm文件来源)),#npm 文件 CDN
    'detailGitlabHosts':列表字段(字符串字段(),默认值=['gitlab.com']),#GitLab 文件 API
}#配置结束

class 拒绝重定向(urllib.request.HTTPRedirectHandler):
    '索引获取拒绝重定向'
    def redirect_request(自身,请求对象,响应,状态码,消息,响应头,新网址):
        '不跟随'
        raise RuntimeError('redirect mode is set to error')#交给获取失败

def 读取易失(字段):
    '易失配置在加载器里带无参 get；列表和字符串原样返回'
    读取=getattr(字段,'get',None)#可能是易失包装
    if callable(读取) and not isinstance(字段,(str,bytes,list,dict,tuple)):#包装
        return 读取()#当前值
    return 字段#原样

def 错误消息(错误):
    '确切诊断，含不是异常的失败'
    if isinstance(错误,BaseException):#异常
        消息=getattr(错误,'message',None)#远程错误写在 message 上
        if isinstance(消息,str) and 消息!='':#有
            return 消息#原文
        if len(错误.args)>0:#args
            return str(错误.args[0])#首个
    return str(错误)#其余

def 原因链(错误,深度=0):
    '带上 cause。再深或成环就停'
    原因=错误.__cause__ if isinstance(错误,BaseException) else None#显式原因
    if 原因 is not None and 深度<最大原因:#还没到顶
        return 错误消息(错误)+': '+原因链(原因,深度+1)#接上
    return 错误消息(错误)#到此

def 拆版本(文本):
    '合法 SemVer 拆成主次补丁和先行段。不合法则没有'
    if not isinstance(文本,str):#不是字符串
        return None#没有
    匹配=版本表达式.fullmatch(文本)#整段
    if 匹配 is None:#不合法
        return None#没有
    return (int(匹配.group(1)),int(匹配.group(2)),int(匹配.group(3)),匹配.group(4))#四段

def 有先行(文本):
    '有先行版本号。不合法的版本当成没有，与 semver.prerelease 空结果一致'
    拆开=拆版本(文本)#拆
    return 拆开 is not None and 拆开[3] is not None#有先行段

def 比较标识(左标识,右标识):
    '先行标识：纯数字按数值，数字小于非数字'
    左是数=左标识.isdigit()#纯数字
    右是数=右标识.isdigit()#纯数字
    if 左是数 and 右是数:#都是数
        左值=int(左标识)#数
        右值=int(右标识)#数
        return (左值>右值)-(左值<右值)#-1、0、1
    if 左是数:#数字更小
        return -1#左小
    if 右是数:#数字更小
        return 1#左大
    if 左标识>右标识:#字典序
        return 1#左大
    if 左标识<右标识:#字典序
        return -1#左小
    return 0#相等

def 比较先行(左段,右段):
    '没有先行段的正式版更大。字段多的一方在共同前缀相同时更大'
    if 左段 is None and 右段 is None:#都没有
        return 0#相等
    if 左段 is None:#左是正式版
        return 1#左大
    if 右段 is None:#右是正式版
        return -1#左小
    左标识表=左段.split('.')#左
    右标识表=右段.split('.')#右
    长度=max(len(左标识表),len(右标识表))#较长
    for 下标 in range(长度):#逐段
        if 下标>=len(左标识表):#左更短
            return -1#左小
        if 下标>=len(右标识表):#右更短
            return 1#左大
        标识差=比较标识(左标识表[下标],右标识表[下标])#这一段
        if 标识差!=0:#不同
            return 标识差#结果
    return 0#相等

def 版本更大(左文本,右文本):
    '左是否严格大于右。任一不合法则为假'
    左拆=拆版本(左文本)#左
    右拆=拆版本(右文本)#右
    if 左拆 is None or 右拆 is None:#不合法
        return False#不能比
    if 左拆[:3]!=右拆[:3]:#主次补丁
        return 左拆[:3]>右拆[:3]#数值
    return 比较先行(左拆[3],右拆[3])>0#先行

def 解析缓存目录(配置档,配置目录):
    '有配置档时相对其目录。没有配置档则必须已经是绝对路径'
    if 配置档 is None:#没有 dsh 配置档
        if not isinstance(配置目录,str) or not os.path.isabs(配置目录):#不是绝对路径
            raise RuntimeError('plugin-market: detailCacheDir must be an absolute path when the service runs without a dsh profile')#比对用原文
        return 配置目录#原样
    相对=配置目录 if isinstance(配置目录,str) and 配置目录!='' else os.path.join('.plugin-market','repositories')#默认相对目录
    if os.path.isabs(相对):#已经绝对
        return 相对#原样
    return os.path.abspath(os.path.join(配置档['dir'],相对))#相对配置档

def 详情文件响应(结局,缓存控制):
    '连接路由要的状态、头和正文。图片私有缓存，失败不缓存'
    安全={#SVG 不能在已认证源上跑脚本
        'X-Content-Type-Options':'nosniff',#不嗅探
        'Content-Security-Policy':"sandbox; default-src 'none'; style-src 'unsafe-inline'",#沙箱
    }#安全结束
    if isinstance(结局,dict):#图片
        状态=200#成功
        正文=bytes(结局['bytes'])#字节
        类型=结局['mediaType']#媒体类型
        缓存=缓存控制#私有缓存
    elif 结局 is None:#没有
        状态=404#找不到
        正文='not found'#比对用正文
        类型='text/plain; charset=utf-8'#文本
        缓存='no-store'#不缓存
    else:#失败原因
        失败状态={'too-large':413,'network':502,'denied':403,'git-unavailable':503,'invalid':400}#原因到状态
        状态=失败状态[结局]#状态
        正文=结局#原因原文
        类型='text/plain; charset=utf-8'#文本
        缓存='no-store'#不缓存
    头={'Content-Type':类型,'Cache-Control':缓存}#头
    头.update(安全)#加上
    return {'status':状态,'headers':头,'body':正文}#路由结果

def 条目于(插件,组合包表,豁免,运行时版本):
    '给一页里的插件补上默认版本、安装状态和每个版本的兼容性'
    版本表=[]#带安装参数的版本
    for 版本 in 插件['versions']:#从高到低
        一项=dict(版本)#拷贝
        一项['install']=市场安装目标(插件['name'],版本)#安装参数
        一项['compatibility']=兼容于(插件['name'],版本,豁免,运行时版本)#兼容
        版本表.append(一项)#收下
    兼容版本=[版本 for 版本 in 版本表 if 版本['compatibility']['compatible']]#能跑的
    有正式版=any(not 有先行(版本['version']) for 版本 in 插件['versions'])#有不带先行号的版本
    默认版本=None#尚未
    for 版本 in 兼容版本:#仍按原顺序
        if not 有正式版 or not 有先行(版本['version']):#全部是先行，或这一条是正式版
            默认版本=版本['version']#最高的那条
            break#停
    度量=默认版本#用来比安装状态
    if 度量 is None and len(版本表)>0:#没有兼容版本
        度量=版本表[0]['version']#最高版本
    if 度量 is None:#空表
        度量=''#没有
    条目=dict(插件)#拷贝插件
    条目['versions']=版本表#换掉
    if 默认版本 is not None:#有默认
        条目['defaultVersion']=默认版本#写入
    条目['installation']=安装于(插件['name'],度量,组合包表)#安装状态
    return 条目#条目

def 安装于(名称,版本,组合包表):
    '按包名对照配置档里的组合包'
    组合=None#命中
    for 候选 in 组合包表:#逐个
        if 候选.get('name')==名称:#同名
            组合=候选#记下
            break#停
    if 组合 is None or (not 组合.get('installed') and 组合.get('availability')!='installation'):#还没装，含按需目录
        return {'status':'not-installed'}#未安装
    if not 组合.get('installed'):#安装提供但本配置档还没装
        结果={'status':'provided'}#随附
        if 组合.get('version') is not None:#有版本
            结果['installedVersion']=组合['version']#写入
        return 结果#随附
    if 组合.get('version') is None:#装了但不知道版本
        return {'status':'different-version'}#不同
    已装版本=组合['version']#已装
    if 已装版本==版本:#相同
        return {'status':'installed','installedVersion':已装版本}#已装
    更新=拆版本(已装版本) is not None and 版本更大(版本,已装版本)#列出的更高
    return {'status':'update-available' if 更新 else 'different-version','installedVersion':已装版本}#状态

def 兼容于(名称,版本,豁免,运行时版本):
    'engines.dsh 与版本豁免，和安装检查相同'
    清单={'name':名称,'version':版本['version']}#身份
    引擎=版本.get('engines') or {}#引擎
    if 引擎.get('dsh') is not None:#声明了
        清单['engines']={'dsh':引擎['dsh']}#只这一项
    问题=评估插件兼容(清单,豁免,运行时版本)#未满足则有结果
    if 问题 is None:#满足
        return {'compatible':True}#兼容
    return {'compatible':False,'runtimeVersion':问题['runtimeVersion'],'requirements':问题['requirements'],'exempted':问题['exempted']}#不兼容

class 插件市场(远程服务):
    '获取、校验并缓存配置的市场索引，再标上本配置档的安装事实'
    inject=['pluginManager']#装载服务
    Config=配置#框架配置槽

    def __init__(自身,上下文,配置值):
        '登记 pluginMarket，并准备克隆目录、详情读取和图片路由'
        super().__init__(上下文,'pluginMarket')#服务键
        自身.配置=配置值#已解析配置
        纤程=上下文.纤程#所属纤程
        插件配置=纤程.插件配置 if 纤程 is not None else None#插件配置
        自身.条目标识=None if 插件配置 is None else 插件配置.选项.get('id')#profile 条目 id
        自身.寿命=中止控制器()#整服务中止
        自身.缓存={}#网址到文档
        自身.进行中={}#同一网址的获取共用一次
        自身.错误={}#上次失败的诊断
        自身.表锁=threading.Lock()#进行中
        配置档=上下文.get('profileContext')#可能没有
        缓存目录=解析缓存目录(配置档,配置值.get('detailCacheDir'))#绝对目录
        自身.仓库=仓库缓存({#部分克隆
            '目录':缓存目录,#根
            '单库上限':配置值['detailRepositoryMaxBytes'],#一条命令
            '缓存上限':配置值['detailCacheMaxBytes'],#总量
            '超时毫秒':配置值['detailGitTimeoutMs'],#Git 时限
            '存活毫秒':配置值['cacheTtlMs'],#默认分支提交
            '传输':['https','http','ssh'],#url.<base>.insteadOf 仍可能改到 ssh
            '寿命':自身.寿命.信号,#拆服务时停 Git
            '轮询毫秒':200,#取回时量目录的间隔
        })#仓库结束
        自身.详情=详情读取器(#详情
            {'文档上限':配置值['detailMaxBytes'],'图片上限':配置值['detailImageMaxBytes'],'ttl毫秒':配置值['cacheTtlMs']},#限度
            自身.详情仓库选项(),#仓库读
        )#详情结束

        def 接线(范围):
            '有连接才挂图片路由'
            def 登记路由():
                'GET 详情旁的图片'
                def 处理(请求):
                    '交给本服务'
                    return 自身.提供详情文件(请求)#响应
                return 范围.connection.fetch.register({#精确路由
                    'path':详情文件路径,#路径
                    'methods':['GET'],#方法
                    'requestBody':'buffered',#不流式
                    'fetch':处理,#处理
                })#登记结束
            范围.副作用(登记路由,'plugin-market: '+详情文件路径)#随连接纤程拆

        上下文.inject(['connection'],接线)#连接可选

        def 易变更新(*位置参数):
            '丢掉已从配置里移除的网址，并通告'
            已配置=set(来源['url'] for 来源 in 自身.来源() if 'error' not in 来源)#仍可用
            for 网址 in list(自身.缓存.keys())+list(自身.错误.keys()):#缓存和错误
                if 网址 not in 已配置:#已移除
                    自身.缓存.pop(网址,None)#丢文档
                    自身.错误.pop(网址,None)#丢错误
            上下文.广播('plugin-market/changed')#已提交的列表变了

        上下文.监听('loader/volatile-update',易变更新)#易失配置

        def 拆除工厂():
            '拆服务时停获取和 Git'
            def 拆除():
                '中止并等到进行中的获取和 Git 结束'
                自身.寿命.中止(RuntimeError('Plugin market disposed'))#中止
                for 进行 in list(自身.进行中.values()):#每次获取
                    进行['事件'].wait()#等它记下结果或错误
                自身.仓库.等结束()#Git
            return 拆除#拆除器

        上下文.副作用(拆除工厂,'plugin-market: disposal')#随纤程拆

    @远程('listIndexes')
    def 列出索引(自身):
        '不获取。返回每个源、上次成功的标题，以及上次失败的诊断'
        结果=[]#源
        for 一项 in 自身.来源():#配置顺序
            文档=自身.缓存.get(一项['url'])#上次成功
            索引=None if 文档 is None else 文档['document']['index']#索引
            错误=一项.get('error')#配置时就不可用
            if 错误 is None:#上次获取
                错误=自身.错误.get(一项['url'])#诊断
            源行={'url':一项['url']}#网址
            if 索引 is not None:#有成功文档
                源行['title']=索引['title']#标题
                if 索引.get('description') is not None:#有描述
                    源行['description']=索引['description']#描述
            if 错误 is not None:#有失败
                源行['error']=错误#诊断原文
            结果.append(源行)#收下
        return 结果#列表

    @远程('setIndexes')
    def 设置索引(自身,网址表):
        '经设置替换索引源，不重挂服务。已配置的网址保持原样'
        已配置=set(读取易失(自身.配置['indexes']))#当前
        规范表=[]#新列表
        for 网址 in 网址表:#逐个
            if 网址 in 已配置:#已有
                规范表.append(网址)#原样
            else:#新的
                规范表.append(规范化索引网址(网址))#规范形式
        键表=[]#用来认重复
        for 网址 in 规范表:#每个
            解析=urllib.parse.urlparse(网址)#拆
            if 解析.scheme in ('http','https') and 解析.netloc!='':#能解析
                键表.append(序列化网址(解析))#规范键
            else:#不能
                键表.append(网址)#原样
        for 位置,网址 in enumerate(规范表):#找重复
            if 键表.index(键表[位置])!=位置:#之前出现过
                raise 远程错误('plugin-market/invalid-index-url','Index source listed twice: '+网址,{'url':网址,'reason':'duplicate'})#重复
        设置=自身.ctx.get('settings')#设置
        if 设置 is None or 自身.条目标识 is None:#没有设置或条目
            raise 远程错误('plugin-market/settings-unavailable','Index sources require the settings service and a profile entry',{})#不能存
        等到结果(设置.更新(自身.条目标识,{'indexes':规范表}))#写入后易失更新会通告

    @远程('search')
    def 搜索(自身,网址,查询):
        '返回一页匹配插件。同一网址的并发获取共用一次'
        偏移=查询.get('offset')#偏移
        限额=查询.get('limit')#限额
        if isinstance(偏移,bool) or not isinstance(偏移,int) or 偏移<0:#越界
            raise 远程错误('plugin-market/invalid-query','offset must be a non-negative integer',{'field':'offset','reason':'range'})#拒绝
        if isinstance(限额,bool) or not isinstance(限额,int) or 限额<1 or 限额>页上限:#越界
            raise 远程错误('plugin-market/invalid-query','limit must be an integer from 1 to '+str(页上限),{'field':'limit','reason':'range'})#拒绝
        文档=自身.取文档(网址,查询.get('refresh') is True,查询.get('fetchedAt'))#文档
        匹配=文档['search'].选择(查询)#全部匹配
        页切片=匹配[偏移:偏移+限额]#这一页
        标注=自身.标注器()#当前安装事实
        下一=偏移+len(页切片)#下一偏移
        索引=文档['index']#头
        结果={#一页
            'url':网址,#源
            'title':索引['title'],#标题
            'metadata':索引['metadata'],#声明
            'fetchedAt':文档['fetchedAt'],#这份文档
            'entries':[标注(插件) for 插件 in 页切片],#这一页
            'total':len(匹配),#匹配总数
            'nextOffset':下一 if 下一<len(匹配) else None,#最后一页为 null
        }#结果结束
        if 索引.get('description') is not None:#有描述
            结果['description']=索引['description']#写入
        return 结果#页

    def 条目(自身,网址,名称):
        '已配置索引里的一个插件。没列出则没有。不是远程方法'
        插件=None#命中
        for 候选 in 自身.取文档(网址,False)['index']['plugins']:#逐个
            if 候选['name']==名称:#同名
                插件=候选#记下
                break#停
        if 插件 is None:#没有
            return None#未列出
        return 自身.标注器()(插件)#带安装事实

    @远程('readEntryDetail')
    def 读条目详情(自身,网址,名称,版本,语言,选项=None):
        '读一个已列出版本的详细介绍。其它注册表的 npm 版本只读条目仓库'
        if 选项 is None:#缺省
            选项={}#空
        语言们=自身.语言们(语言)#回退链
        文档=自身.取文档(网址,False)#用缓存文档
        插件=None#插件
        for 候选 in 文档['index']['plugins']:#逐个
            if 候选['name']==名称:#同名
                插件=候选#记下
                break#停
        列出=None#版本
        if 插件 is not None:#有插件
            for 候选 in 插件['versions']:#逐个版本
                if 候选['version']==版本:#命中
                    列出=候选#记下
                    break#停
        if 插件 is None or 列出 is None:#未列出
            raise 远程错误('plugin-market/unknown-plugin',网址+' lists no '+名称+'@'+版本,{'name':名称,'version':版本})#拒绝
        声明=插件.get('repository')#条目仓库
        找到=None if not isinstance(声明,dict) else 仓库于(声明.get('url') or '')#解析
        仓库=None#最后才读的仓库
        if 找到 is not None:#有
            仓库=dict(找到)#拷贝
            目录=声明.get('directory') if isinstance(声明.get('directory'),str) else ''#目录
            仓库['directory']=目录#写入
        来源=列出['source']#版本来源
        if 来源['type']=='git':#固定提交
            引用=仓库于(来源['url'])#仓库
            if 引用 is None:#索引不会给出这种网址
                return {'status':'none'}#没有
            目录=来源.get('path') or ''#包目录
            if 仓库 is not None and 仓库.get('url')==引用['url'] and 仓库.get('directory')==目录:#仓库就是来源目录
                仓库=None#不再重复读
            位置={'files':仓库文件(引用,来源.get('commit'),自身.详情仓库选项()),'dir':目录,'repository':仓库}#Git
        elif 来源.get('registry') is None or 注册表主机(来源.get('registry')) in 公共注册表:#公共 npm
            仓库或清单=仓库 if 仓库 is not None else 'manifest'#没有条目仓库则读清单
            优先=选项.get('npmFileSources') or []#本次优先的 CDN
            位置=自身.npm位置(名称,版本,仓库或清单,优先)#CDN
        else:#其它注册表没有可读取的包文件
            位置={'dir':'','repository':仓库}#只读条目仓库
        return 自身.读详情(位置,语言们,选项.get('refresh') is True)#文档

    def 语言们(自身,语言):
        '显示语言及其前缀，最后是英文'
        try:#校验
            return 语言链(语言)#链
        except Exception as 错误:#不是语言标识
            raise 远程错误('plugin-market/invalid-query',错误消息(错误),{'field':'language','reason':'format'},错误)#拒绝

    def 详情仓库选项(自身):
        '单文件接口和克隆回退'
        return {#选项
            '超时毫秒':自身.配置['fetchTimeoutMs'],#接口时限
            '寿命':自身.寿命.信号,#服务寿命
            'gitlab主机':[主机.lower() for 主机 in 自身.配置['detailGitlabHosts']],#小写比较
            '缓存':自身.仓库,#克隆
        }#选项结束

    def npm位置(自身,名称,版本,仓库,优先):
        '公共 npm 版本。优先列出的 CDN 排前面，没配置的不请求'
        来源=npm文件来源顺序(自身.配置['detailNpmFileSources'],优先)#顺序
        文件源=npm文件(名称,版本,来源,{'timeoutMs':自身.配置['fetchTimeoutMs'],'lifetime':自身.寿命.信号})#CDN
        return {'dir':'','repository':仓库,'files':文件源}#位置

    def 读详情(自身,位置,语言们,刷新):
        '详情失败收成远程错误，其它失败原样抛'
        try:#读
            return 自身.详情.读取(位置,语言们,刷新)#文档
        except 详情失败 as 错误:#可报告的失败
            raise 远程错误('plugin-market/detail-unavailable',错误消息(错误),{'reason':错误.reason},错误)#带原因

    def 提供详情文件(自身,请求):
        'GET 详情文档旁的一张图片'
        网址=请求['url'] if isinstance(请求,dict) else getattr(请求,'url','')#请求网址
        参数=urllib.parse.parse_qs(urllib.parse.urlparse(网址).query,keep_blank_values=True)#查询
        文档表=参数.get('document') or []#文档
        路径表=参数.get('path') or []#路径
        文档=文档表[0] if len(文档表)>0 else None#标识
        路径=路径表[0] if len(路径表)>0 else None#目标
        缓存='private, max-age='+str(int(自身.配置['cacheTtlMs']//1000))#与文档结果一样久
        if 文档 is None or 路径 is None:#缺参数
            return 详情文件响应('invalid',缓存)#400
        try:#读
            return 详情文件响应(自身.详情.图片(文档,路径),缓存)#图片或 404
        except 详情失败 as 错误:#读失败
            return 详情文件响应(错误.reason,缓存)#对应状态

    def 取文档(自身,网址,刷新,获取时刻=None):
        '可用缓存，或共用一次获取。带上先前的 fetchedAt 时，过期文档仍可回答后续页'
        来源=None#命中
        for 候选 in 自身.来源():#配置的源
            if 候选['url']==网址:#同一个
                来源=候选#记下
                break#停
        if 来源 is None:#没配置
            raise 远程错误('plugin-market/unknown-index','Not a configured index source: '+网址,{'url':网址})#拒绝
        if 'error' in 来源:#不可用
            raise 远程错误('plugin-market/invalid-index-url',来源['error'],{'url':网址,'reason':'configured'})#不获取
        缓存=自身.缓存.get(网址)#已有
        现在=int(time.time()*1000)#现在
        可用=缓存 is not None and (缓存['expiresAt']>现在 or (获取时刻 is not None and 缓存['document']['fetchedAt']==获取时刻))#还能用
        if not 刷新 and 可用:#用缓存
            return 缓存['document']#文档
        return 自身.共享获取(网址)#获取

    def 标注器(自身):
        '按现在的组合包和版本豁免标注'
        组合包表=自身.ctx.pluginManager.列出组合包()#组合包
        豁免体=自身.ctx.pluginManager.列出版本豁免()#豁免
        豁免=豁免体['exemptions']#name@version 到运行时版本
        运行时版本=获取dsh运行时版本()#本进程

        def 标注(插件):
            '一个插件'
            return 条目于(插件,组合包表,豁免,运行时版本)#条目

        return 标注#函数

    def 来源(自身):
        '按写下的顺序。不可用的源带上拒绝原因，重复网址只留一次'
        见过=set()#已出现
        结果=[]#源
        for 网址 in 读取易失(自身.配置['indexes']):#当前配置
            if 网址 in 见过:#重复
                continue#跳过
            见过.add(网址)#记下
            try:#校验
                规范=规范化索引网址(网址)#规范形式
            except Exception as 错误:#不可用
                结果.append({'url':网址,'error':错误消息(错误)})#带诊断
                continue#下一个
            if 规范==网址:#已经是规范形式
                结果.append({'url':网址})#可用
            else:#写法不同
                结果.append({'url':网址,'error':'Index URL is not in canonical form; use '+规范})#不获取
        return 结果#源

    def 已配置(自身,网址):
        '获取完成时网址是否仍是可用源'
        for 来源 in 自身.来源():#当前
            if 来源['url']==网址 and 'error' not in 来源:#可用
                return True#是
        return False#已移除或不可用

    def 共享获取(自身,网址):
        '同一网址只获取一次'
        with 自身.表锁:#登记
            进行=自身.进行中.get(网址)#已有
            if 进行 is None:#本调用负责
                进行={'事件':threading.Event(),'盒子':{}}#盒子
                自身.进行中[网址]=进行#登记
                负责=True#负责
            else:#等待
                负责=False#不负责
        if not 负责:#等那一次
            进行['事件'].wait()#阻塞
            if '错误' in 进行['盒子']:#失败
                raise 进行['盒子']['错误']#再抛
            return 进行['盒子']['文档']#文档
        try:#获取
            索引=自身.获取索引(网址)#校验后的索引
            先前=自身.缓存.get(网址)#上一份
            先前时刻=0 if 先前 is None else 先前['document']['fetchedAt']#上一时刻
            获取时刻=max(int(time.time()*1000),先前时刻+1)#同一毫秒也要不同
            文档={'index':索引,'fetchedAt':获取时刻,'search':市场搜索(索引)}#文档
            if 自身.已配置(网址):#完成时仍配置着
                自身.缓存[网址]={'document':文档,'expiresAt':int(time.time()*1000)+自身.配置['cacheTtlMs']}#缓存
                自身.错误.pop(网址,None)#清掉旧错误
            进行['盒子']['文档']=文档#交给等待者
            return 文档#文档
        except Exception as 错误:#失败
            if 自身.已配置(网址):#仍配置着才记录
                自身.错误[网址]=错误消息(错误)#给 listIndexes
            进行['盒子']['错误']=错误#交给等待者
            raise#再抛
        finally:#摘掉
            进行['事件'].set()#放开
            with 自身.表锁:#摘
                if 自身.进行中.get(网址) is 进行:#仍是这一次
                    del 自身.进行中[网址]#摘掉

    def 获取索引(自身,网址):
        '拒绝重定向，正文超过 maxBytes 立即停'
        若已中止则抛出(自身.寿命.信号)#已拆

        def 失败(理由,原因=None):
            '获取失败'
            return 远程错误('plugin-market/fetch-failed','Could not fetch '+网址+': '+理由,{'url':网址,'reason':理由},原因)#上报

        请求=urllib.request.Request(网址,headers={'accept':'application/json'},method='GET')#只要 JSON
        开启器=urllib.request.build_opener(拒绝重定向)#不跟随
        try:#发出
            响应=开启器.open(请求,timeout=自身.配置['fetchTimeoutMs']/1000.0)#时限
        except urllib.error.HTTPError as 错误:#非 2xx
            raise 失败('HTTP '+str(错误.code))#状态
        except Exception as 错误:#网络、超时、重定向
            raise 失败(原因链(错误),错误)#原因链
        try:#读正文
            if not (200<=响应.status<=299):#不是成功
                raise 失败('HTTP '+str(响应.status))#状态
            字节=自身.读正文(响应,失败)#有上限
        finally:#关掉
            响应.close()#释放
        try:#解析
            结果=在线程解析索引(字节,网址,自身.寿命.信号)#工作线程
        except Exception as 错误:#解析进程失败
            raise 失败(错误消息(错误),错误)#获取失败
        if 结果['ok']:#通过
            return 结果['index']#索引
        raise 远程错误('plugin-market/invalid-index',网址+': '+结果['message'],{'url':网址,'path':结果['path'],'reason':结果['reason']})#格式

    def 读正文(自身,响应,失败):
        '读完全部正文。一超过 maxBytes 就拒绝'
        上限=自身.配置['maxBytes']#上限
        过大='body exceeds '+str(上限)+' bytes'#诊断原文
        长度文本=响应.headers.get('Content-Length')#声明的长度
        if isinstance(长度文本,str) and 长度文本.isdigit() and int(长度文本)>上限:#声明已超
            raise 失败(过大)#拒绝
        块表=[]#块
        大小=0#已读
        try:#逐块
            while True:#直到结束
                若已中止则抛出(自身.寿命.信号)#中途拆服务
                正文档=响应.read(65536)#一块
                if not 正文档:#读完
                    break#停
                大小+=len(正文档)#加上
                if 大小>上限:#超了
                    raise 失败(过大)#拒绝
                块表.append(正文档)#留下
        except 远程错误:#已经是获取失败
            raise#原样
        except Exception as 错误:#读的途中断了
            raise 失败(错误消息(错误),错误)#获取失败
        return b''.join(块表)#正文

def 注册表主机(注册表):
    '注册表网址的主机。没有主机则空串'
    if not isinstance(注册表,str):#不是网址
        return ''#空
    主机=urllib.parse.urlparse(注册表).hostname#主机
    return '' if 主机 is None else 主机.lower()#小写

inject=插件市场.inject#Cordis 依赖
Config=插件市场.Config#Cordis 配置
default=插件市场#Cordis 默认导出
