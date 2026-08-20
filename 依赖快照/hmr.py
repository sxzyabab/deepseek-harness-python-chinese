"""Cordis 插件热替换。"""
import os,sys,errno,threading,time,weakref
import include,loader,timer,cordis,schemastery
from urllib.parse import urlparse as 解析网址,unquote as 百分号解码,urljoin as 拼接网址#网址解析
from cordis.工具 import 是否thenable#thenable 判断
服务=cordis.服务#服务基类
承诺=cordis.承诺#可等待承诺
模式=schemastery.模式#配置模式
线程=threading.Thread#线程
停止事件=threading.Event#停止事件
互斥锁=threading.Lock#互斥锁
弱键字典=weakref.WeakKeyDictionary#弱键表

def 是否构建失败(错误):
    """判断是否为带 errors 列表的构建失败。"""
    列表=getattr(错误,'errors',None)#错误列表
    if not isinstance(列表,list):
        return False#不是列表
    for 项 in 列表:
        if isinstance(项,dict):
            文本=项.get('text')#字典文本
        else:
            文本=getattr(项,'text',None)#对象文本
        if not 文本:
            return False#缺少 text
    return True#全部带 text

def 格式化代码框(源,行,列,消息):
    """按行列拼出代码框。"""
    行表=源.splitlines()#源行
    起始=max(0,行-2)#上文起点
    结束=min(len(行表),行+1)#下文终点
    宽=len(str(max(结束,1)))#行号宽度
    片段=[]#输出行
    for 下标 in range(起始,结束):
        标记='>' if 下标+1==行 else ' '#当前行标记
        片段.append(f'{标记} {str(下标+1).rjust(宽)} | {行表[下标]}')#源行
        if 下标+1==行:
            片段.append(f'  {" "*宽} | {" "*(max(列,1)-1)}^ {消息}')#列指针
    return '\n'.join(片段)#代码框

def 处理错误(ctx,错误):
    """有源位置时用代码框记录热替换构建失败。"""
    if not 是否构建失败(错误):
        ctx.logger.warn(错误)#普通错误
        return#结束
    for 项 in 错误.errors:
        if isinstance(项,dict):
            位置=项.get('location')#字典位置
            文本=项.get('text')#字典文本
        else:
            位置=getattr(项,'location',None)#对象位置
            文本=getattr(项,'text',None)#对象文本
        if not 位置:
            ctx.logger.warn(文本)#无位置只记文本
            continue#下一条
        try:
            if isinstance(位置,dict):
                文件=位置.get('file')#文件
                行=位置.get('line')#行
                列=位置.get('column')#列
            else:
                文件=位置.file#文件
                行=位置.line#行
                列=位置.column#列
            读取=open(文件,'r',encoding='utf-8')#打开源文件
            try:
                源=读取.read()#读出源码
            finally:
                读取.close()#关闭
            框=格式化代码框(源,行,列,文本)#代码框
            ctx.logger.warn(f'File: {文件}:{行}:{列}\n'+框)#带位置警告
        except Exception as 原因:
            ctx.logger.warn(原因)#读源或格式化失败

def 等待结果(值):
    """若为承诺则阻塞等待，否则原样返回。"""
    if 是否thenable(值):
        return 值.等待()#等待承诺
    return 值#同步值

def 路径转文件网址(路径):
    """把本地路径收成 file: 网址。"""
    绝对=os.path.abspath(路径)#绝对路径
    正斜=绝对.replace('\\','/')#正斜杠
    if len(正斜)>=2 and 正斜[1]==':':
        return 'file:///'+正斜#Windows 盘符
    if not 正斜.startswith('/'):
        正斜='/'+正斜#补根
    return 'file://'+正斜#POSIX

def 文件网址转路径(网址):
    """把 file: 网址收成本地路径。"""
    if not 网址.startswith('file:'):
        raise ValueError(网址)#非文件网址
    解析=解析网址(网址)#拆网址
    路径=百分号解码(解析.path)#解码
    if os.name=='nt' and 路径.startswith('/') and len(路径)>=3 and 路径[2]==':':
        路径=路径[1:]#去掉盘符前斜杠
    return 路径.replace('/',os.sep)#本地分隔符

def 解析基准目录(相对,基准网址):
    """按 ctx.baseUrl 解析热替换基准目录。"""
    基准=基准网址 or 路径转文件网址(os.getcwd())#缺省为工作目录
    if not str(基准).startswith('file:'):
        基准=路径转文件网址(基准)#收成文件网址
    if not str(基准).endswith('/'):
        基准=str(基准)+'/'#目录以斜杠结尾
    相对=相对 or '.'#缺省当前目录
    完整=拼接网址(基准,相对)#拼接
    return os.path.normpath(文件网址转路径(完整))#本地路径

def 通配命中(文本,模式):
    """判断相对路径是否命中 glob 模式。"""
    文本=文本.replace('\\','/')#统一为正斜杠
    模式=模式.replace('\\','/')#统一为正斜杠
    def 递归(当前,式):
        """递归匹配 glob。"""
        if 式=='**':
            return True#吃掉剩余
        if not 当前:
            if not 式:
                return True#双空
            if 式=='**':
                return True#空对双星
            if 式.startswith('**/'):
                return 递归('',式[3:])#空文本继续去掉 **/
            return False#空文本未命中
        if 式.startswith('**/'):
            其余=式[3:]#去掉 **/
            if 递归(当前,其余):
                return True#当前层命中
            斜=当前.find('/')#下一段
            if 斜<0:
                return False#没有下层
            return 递归(当前[斜+1:],式)#从下一段再试
        if not 式:
            return False#模式耗尽文本仍在
        if 式[0]=='*':
            斜=当前.find('/')#段尾
            段=当前 if 斜<0 else 当前[:斜]#当前段
            尾='' if 斜<0 else 当前[斜:]#含斜杠的剩余
            其余=式[1:]#星后
            位置=0#段内位置
            while 位置<=len(段):
                if 递归(段[位置:]+尾,其余):
                    return True#命中
                位置+=1#多吃一个
            return False#失败
        if 式[0]=='?':
            if 当前[0]=='/':
                return False#问号不吃斜杠
            return 递归(当前[1:],式[1:])#吃一个
        if 当前[0]!=式[0]:
            return False#字面量不等
        return 递归(当前[1:],式[1:])#继续
    return 递归(文本,模式)#开始匹配

def 寻找监视根(文件名):
    """从文件路径向上找到已存在的目录根。"""
    根=os.path.dirname(os.path.abspath(文件名))#起始父目录
    深度=0#向上层数
    while True:
        try:
            if not os.path.isdir(根):
                os.stat(根)#缺失则 ENOENT
                raise Exception('config watch parent is not a directory: '+根)#存在但非目录
            规范根=os.path.realpath(根)#规范路径
            return {'filename':os.path.abspath(os.path.join(规范根,os.path.relpath(os.path.abspath(文件名),根))),'root':规范根,'depth':深度}#监视目标
        except OSError as 错误:
            if 错误.errno!=errno.ENOENT:
                raise 错误#不是缺失
            父=os.path.dirname(根)#上一级
            if 父==根:
                raise 错误#已到文件系统根
            根=父#继续向上
            深度+=1#加深

def 加载依赖(任务,已忽略=None):
    """从模块任务递归收集用户代码依赖网址。"""
    if 已忽略 is None:
        已忽略=set()#空忽略集
    依赖=set()#依赖网址
    def 遍历(当前):
        """跳过内建与 node_modules。"""
        if 当前.url in 已忽略 or 当前.url in 依赖:
            return#已见过
        if 当前.url.startswith('node:') or '/node_modules/' in 当前.url:
            return#内建或依赖包
        依赖.add(当前.url)#记入
        子们=等待结果(当前.linked)#子任务
        for 子 in 子们:
            遍历(子)#递归
    遍历(任务)#从根开始
    return 依赖#依赖集

class 配置登记:
    """一份精确配置路径的监视登记。"""
    def __init__(自身,监视器):
        """保存监视器。"""
        自身.监视器=监视器#监视器

class 文件系统监视器:
    """线程轮询的文件监视器。"""
    def __init__(自身,路径列表,选项):
        """按选项监视路径列表。"""
        自身._路径列表=路径列表 if isinstance(路径列表,list) else [路径列表]#根列表
        自身._选项={} if 选项 is None else 选项#选项
        自身._监听={}#事件监听
        自身._快照={}#路径到修改时间
        自身._停止=停止事件()#停止信号
        自身._锁=互斥锁()#监听锁
        自身._线程=线程(target=自身._运行)#轮询线程
        自身._线程.start()#启动

    def on(自身,事件,回调):
        """登记事件回调。"""
        with 自身._锁:
            自身._监听.setdefault(事件,[]).append(回调)#追加
        return 自身#可链式

    def once(自身,事件,回调):
        """登记只触发一次的回调。"""
        def 一次(*位置参数):
            """先卸掉自身再跑原始回调。"""
            自身._取消(事件,一次)#卸掉
            回调(*位置参数)#原始
        return 自身.on(事件,一次)#登记

    def _取消(自身,事件,回调):
        """按引用删除监听。"""
        with 自身._锁:
            表=自身._监听.get(事件) or []#监听表
            自身._监听[事件]=[项 for 项 in 表 if 项 is not 回调]#过滤

    def _发出(自身,事件,*位置参数):
        """同步调用该事件的监听副本。"""
        with 自身._锁:
            表=list(自身._监听.get(事件) or [])#副本
        for 回调 in 表:
            回调(*位置参数)#调用

    def _对外路径(自身,绝对):
        """cwd 存在时交出相对路径。"""
        基准=自身._选项.get('cwd')#工作目录
        if not 基准:
            return 绝对#绝对路径
        return os.path.relpath(绝对,基准)#相对路径

    def _被忽略(自身,绝对):
        """忽略谓词命中则为真。"""
        忽略=自身._选项.get('ignored')#忽略
        if not 忽略:
            return False#不忽略
        return bool(忽略(绝对))#谓词

    def _列出(自身):
        """扫描监视根下的文件修改时间。"""
        结果={}#路径到时间
        基准=自身._选项.get('cwd') or os.getcwd()#工作目录
        深度上限=自身._选项.get('depth')#深度
        for 根路径 in 自身._路径列表:
            绝对根=根路径 if os.path.isabs(根路径) else os.path.join(基准,根路径)#绝对根
            绝对根=os.path.abspath(绝对根)#规范化
            if not os.path.exists(绝对根):
                continue#尚不存在
            if os.path.isfile(绝对根):
                if not 自身._被忽略(绝对根):
                    try:
                        结果[绝对根]=os.path.getmtime(绝对根)#单文件
                    except OSError:
                        pass#扫描中途消失则跳过
                continue#下一个根
            for 当前,目录们,文件们 in os.walk(绝对根):
                相对层=os.path.relpath(当前,绝对根)#相对层
                层=0 if 相对层=='.' else 相对层.count(os.sep)+1#深度
                if 深度上限 is not None and 层>深度上限:
                    目录们[:]=[]#不再下降
                    continue#跳过本层文件
                if 深度上限 is not None and 层==深度上限:
                    目录们[:]=[]#本层文件仍列出
                保留=[]#未忽略目录
                for 目录 in 目录们:
                    全=os.path.join(当前,目录)#子目录
                    if 自身._被忽略(全):
                        continue#忽略则不下降
                    保留.append(目录)#保留
                目录们[:]=保留#写回
                for 文件 in 文件们:
                    全=os.path.join(当前,文件)#文件路径
                    if 自身._被忽略(全):
                        continue#忽略
                    try:
                        结果[os.path.abspath(全)]=os.path.getmtime(全)#记录
                    except OSError:
                        pass#扫描中途消失则跳过
        return 结果#快照

    def _运行(自身):
        """首次扫描后进入轮询。"""
        try:
            新快照=自身._列出()#首次扫描
            if not 自身._选项.get('ignoreInitial'):
                for 路径 in 新快照:
                    自身._发出('add',自身._对外路径(路径))#初始 add
            自身._快照=新快照#记下
            自身._发出('ready')#就绪
            while not 自身._停止.wait(0.1):
                新快照=自身._列出()#再扫描
                for 路径 in 新快照:
                    if 路径 not in 自身._快照:
                        自身._发出('add',自身._对外路径(路径))#新增
                    elif 新快照[路径]!=自身._快照[路径]:
                        自身._发出('change',自身._对外路径(路径))#修改
                for 路径 in 自身._快照:
                    if 路径 not in 新快照:
                        自身._发出('unlink',自身._对外路径(路径))#删除
                自身._快照=新快照#更新
        except Exception as 错误:
            自身._发出('error',错误)#监视错误

    def 关闭(自身):
        """停止轮询并等待线程结束。"""
        自身._停止.set()#发停止
        自身._线程.join()#等待

def 监视(路径列表,选项=None):
    """按选项打开文件监视器。"""
    return 文件系统监视器(路径列表,{} if 选项 is None else 选项)#监视器

class 热替换(服务):
    """监视源文件并重载受影响的插件入口。"""
    inject=['loader','timer']#依赖加载器与定时器
    Config=模式.对象({'base':模式.字符串(),#可选基准目录
        'root':模式.数组(str).角色('table').默认(['.']),#监视根
        'ignored':模式.数组(str).角色('table').默认(['**/node_modules','**/.*','cache','data']),#忽略
        'debounce':模式.自然数().角色('ms').默认(100)})#防抖毫秒
    def __init__(自身,ctx,config):
        """注册 hmr 服务并解析基准目录。"""
        服务.__init__(自身,ctx,'hmr')#登记服务
        自身.config=config#配置
        自身.__dict__[服务.初始化]=自身._初始化#符号初始化
        if not 自身.ctx.loader.internal:
            raise Exception('--expose-internals is required for HMR service')#需要内部加载器
        自身.内部加载器=自身.ctx.loader.internal#内部加载器
        自身.基准目录=解析基准目录(自身.config.get('base'),ctx.baseUrl)#基准目录
        自身.配置表={}#规范路径到登记
        自身.配置刷新表=弱键字典()#键到刷新状态
        自身.刷新任务集=set()#进行中的刷新
        自身.暂存集=set()#待处理变更
        自身.监视器=None#主监视器
        自身.外部集=set()#框架依赖
        自身.接受集=set()#应重载
        自身.拒绝集=set()#不重载

    def 登记配置(自身,文件名,刷新):
        """监视配置路径之外的精确配置文件，串行刷新。"""
        if not 自身.监视器:
            raise Exception('HMR is not active')#尚未启动
        文件名=os.path.abspath(os.path.join(自身.基准目录,文件名))#相对基准解析
        目标=寻找监视根(文件名)#已存在祖先
        监视文件名=目标['filename']#规范文件名
        if 监视文件名 in 自身.配置表:
            raise Exception('config path already registered: '+文件名)#重复登记
        根=目标['root']#监视根
        深度=目标['depth']#深度
        选项=dict(自身.config)#展开配置
        选项['cwd']=None#绝对路径
        选项['depth']=深度#限制深度
        选项['ignored']=None#不过滤
        选项['ignoreInitial']=False#登记时扫一次
        监视器=监视(根,选项)#打开监视
        登记=配置登记(监视器)#登记对象
        自身.配置表[监视文件名]=登记#写入
        def 当路径变化(路径):
            """只处理该精确文件。"""
            观测=os.path.abspath(路径)#观测路径
            if 观测!=文件名 and 观测!=监视文件名:
                return#其它文件
            自身.刷新配置(登记,文件名,刷新)#串行刷新
        监视器.on('add',当路径变化)#添加
        监视器.on('change',当路径变化)#修改
        监视器.on('unlink',当路径变化)#删除
        就绪=承诺()#就绪承诺
        就绪状态=['pending']#可变状态
        def 当就绪():
            """监视就绪。"""
            就绪状态[0]='resolved'#已兑现
            就绪.兑现()#放行
        def 当错误(错误):
            """启动失败则拒绝，否则记日志。"""
            if 就绪状态[0]=='pending':
                就绪状态[0]='rejected'#已拒绝
                就绪.拒绝(错误)#失败
            else:
                自身.ctx.logger.warn(错误)#运行期错误
        监视器.once('ready',当就绪)#一次就绪
        监视器.on('error',当错误)#错误
        try:
            就绪.等待()#等到就绪
            def 执行体():
                """拆除该精确监视。"""
                def 释放():
                    """关掉监视并等刷新结束。"""
                    if 自身.配置表.get(监视文件名) is 登记:
                        自身.配置表.pop(监视文件名,None)#摘掉
                    监视器.关闭()#关闭
                    状态=自身.配置刷新表.get(登记)#刷新状态
                    if 状态 and 状态.get('进行中'):
                        等待结果(状态['进行中'])#等刷新
                return 释放#释放器
            return 自身.ctx.effect(执行体,'hmr.registerConfig()')#副作用
        except Exception as 错误:
            自身.配置表.pop(监视文件名,None)#失败则摘掉
            监视器.关闭()#关闭
            raise 错误#继续抛

    def _解析(自身,说明符,父网址,属性):
        """按内部加载器版本解析模块说明符。"""
        版本=自身.内部加载器.version#版本
        if 版本=='v1':
            return 等待结果(自身.内部加载器.resolve(说明符,父网址,属性))#v1 异步解析
        if 版本=='v2':
            return 自身.内部加载器.resolveSync(父网址,{'specifier':说明符,'attributes':属性})#v2 同步解析

    def _初始化(自身):
        """打开主监视并收集入口外部依赖。"""
        def 清理():
            """关闭监视并等刷新结束。"""
            if 自身.监视器:
                自身.监视器.关闭()#关主监视
            for 登记 in list(自身.配置表.values()):
                try:
                    登记.监视器.关闭()#关配置监视
                except Exception:
                    pass#吞掉配置监视关闭失败，对应 allSettled
            自身.配置表.clear()#清空登记
            for 任务 in list(自身.刷新任务集):
                try:
                    等待结果(任务)#等刷新
                except Exception:
                    pass#吞掉刷新任务失败，对应 allSettled
        yield 清理#先交出拆除
        加载器=自身.ctx.loader#加载器
        根=自身.config['root']#监视根
        忽略=自身.config['ignored']#忽略
        if not 自身.config.get('base'):
            自身.ctx.logger.info('watching %o',根)#无基准
        else:
            自身.ctx.logger.info('watching %o in %s',根,自身.基准目录)#有基准
        def 匹配(相对路径):
            """任一忽略模式命中则为真。"""
            正斜=相对路径.replace('\\','/')#正斜杠
            for 通配式 in 忽略:
                if 通配命中(正斜,通配式):
                    return True#命中
            return False#未命中
        os.stat(自身.基准目录)#不存在则抛出
        监视基准目录=os.path.realpath(自身.基准目录)#规范基准
        入口网址=路径转文件网址(os.path.abspath(sys.argv[0]))#进程入口
        入口任务=自身.内部加载器.loadCache.get(入口网址)#入口任务
        if 入口任务:
            自身.外部集=加载依赖(入口任务)#框架依赖
        else:
            自身.外部集=set()#无入口任务
        def 忽略路径(路径):
            """相对监视基准匹配忽略。"""
            return 匹配(os.path.relpath(路径,监视基准目录))#相对路径
        选项=dict(自身.config)#展开配置
        选项['cwd']=监视基准目录#相对基准
        选项['ignored']=忽略路径#忽略谓词
        选项['ignoreInitial']=True#避免启动死锁
        自身.监视器=监视(根,选项)#主监视
        防抖毫秒=自身.config['debounce']#防抖
        部分重载=自身.ctx.debounce(自身.部分重载,防抖毫秒)#防抖重载
        def 当变更(种类,路径):
            """配置刷新、整进程退出或暂存部分重载。"""
            自身.ctx.logger.debug('%s detected at %C',种类,路径)#调试
            文件名=os.path.abspath(os.path.join(监视基准目录,路径))#规范路径
            配置文件名=os.path.abspath(os.path.join(自身.基准目录,路径))#配置拼写
            for 条目 in 加载器.entries():
                包含树=getattr(条目,'subtree',None)#子树
                包含文件=getattr(包含树,'filename',None) if 包含树 is not None else None#配置文件
                if 包含文件!=文件名 and 包含文件!=配置文件名:
                    continue#不是该配置
                自身.刷新配置(包含树,包含树.filename,包含树.refresh)#串行刷新
                return#配置路径不走模块重载
            if 种类!='change':
                return#仅 change 触发模块重载
            网址=路径转文件网址(文件名)#文件网址
            if 网址 in 自身.外部集:
                return 加载器.exit()#框架文件则整进程退出
            if 网址 in 自身.内部加载器.loadCache:
                自身.暂存集.add(网址)#暂存
                return 部分重载()#防抖部分重载
            自身.ctx.emit('hmr/change',网址)#未加载文件
        def 当添加(路径):
            """转发 add。"""
            当变更('add',路径)#添加
        def 当修改(路径):
            """转发 change。"""
            当变更('change',路径)#修改
        def 当删除(路径):
            """转发 unlink。"""
            当变更('unlink',路径)#删除
        自身.监视器.on('add',当添加)#添加
        自身.监视器.on('change',当修改)#修改
        自身.监视器.on('unlink',当删除)#删除
        就绪=承诺()#就绪承诺
        就绪状态=['resolved' if len(根)==0 else 'pending']#空根立刻就绪
        if len(根)==0:
            就绪.兑现()#空根
        else:
            def 当就绪():
                """主监视就绪。"""
                就绪状态[0]='resolved'#已兑现
                就绪.兑现()#放行
            自身.监视器.once('ready',当就绪)#一次就绪
        def 当错误(错误):
            """启动失败则拒绝，否则记日志。"""
            if 就绪状态[0]=='pending':
                就绪状态[0]='rejected'#已拒绝
                就绪.拒绝(错误)#失败
            else:
                自身.ctx.logger.warn(错误)#运行期错误
        自身.监视器.on('error',当错误)#错误
        就绪.等待()#等到就绪

    def 刷新配置(自身,键,文件名,刷新):
        """把同一键上的刷新串成单队列，失败只记日志。"""
        状态=自身.配置刷新表.get(键)#已有状态
        if 状态 is None:
            状态={'脏':False}#新状态
            自身.配置刷新表[键]=状态#写入
        状态['脏']=True#标脏
        if 状态.get('进行中'):
            return#已有队列
        任务=承诺()#本轮承诺
        def 任务体():
            """循环直到不再脏。"""
            try:
                while True:
                    状态['脏']=False#本轮开始
                    try:
                        等待结果(刷新())#执行刷新
                    except Exception as 原因:
                        错误=原因 if isinstance(原因,Exception) else Exception(str(原因))#归一错误
                        if not isinstance(原因,Exception):
                            错误.__cause__=原因#挂上原因
                        自身.ctx.logger.warn('config reload at %C failed',文件名)#失败摘要
                        自身.ctx.logger.warn(错误)#失败详情
                        try:
                            自身.ctx.parallel('hmr/config-update-failed',文件名,错误)#平行通知
                        except Exception as 拒绝:
                            自身.ctx.logger.warn(拒绝)#监听失败
                    if not 状态['脏']:
                        break#干净则结束
            finally:
                状态['进行中']=None#清进行中
                自身.刷新任务集.discard(任务)#摘掉
                任务.兑现()#结算
        工作=线程(target=任务体)#刷新线程
        工作.start()#启动
        状态['进行中']=任务#记下
        自身.刷新任务集.add(任务)#登记

    def 取外层栈(自身):
        """返回空栈以隐藏热替换调用帧。"""
        return []#空栈

    def 取链接(自身,网址):
        """取出模块任务已链接的子网址。"""
        任务=自身.内部加载器.loadCache.get(网址)#模块任务
        if not 任务:
            return []#未加载
        链接=等待结果(任务.linked)#子任务
        return [项.url for 项 in 链接]#子网址

    def 分析变更(自身):
        """把暂存文件及其依赖方分成接受集与拒绝集。"""
        待定=[]#待分类网址
        自身.接受集=set(自身.暂存集)#直接变更已接受
        自身.拒绝集=set(自身.外部集)#外部一律拒绝
        def 是否排除(网址):
            """内建与依赖包不参与分类。"""
            return 网址.startswith('node:') or '/node_modules/' in 网址#排除
        for 网址 in list(自身.暂存集):
            子们=自身.取链接(网址)#子网址
            for 子 in 子们:
                if 子 in 自身.接受集 or 子 in 自身.拒绝集 or 是否排除(子):
                    continue#已分类
                待定.append(子)#待定
        while 待定:
            下标=0#扫描位置
            有更新=False#本轮是否推进
            while 下标<len(待定):
                网址=待定[下标]#当前
                子们=自身.取链接(网址)#子网址
                是拒绝=True#暂定拒绝
                是接受=False#暂定未接受
                for 子 in 子们:
                    if 子 in 自身.拒绝集 or 是否排除(子):
                        continue#跳过
                    if 子 in 自身.接受集:
                        是接受=True#依赖方已接受
                        break#可定
                    else:
                        是拒绝=False#尚有未定依赖方
                        if 子 not in 待定:
                            有更新=True#新节点
                            待定.append(子)#压入
                if 是接受 or 是拒绝:
                    有更新=True#可移出
                    待定.pop(下标)#移出
                    if 是接受:
                        自身.接受集.add(网址)#接受
                    else:
                        自身.拒绝集.add(网址)#拒绝
                else:
                    下标+=1#继续
            if not 有更新:
                break#无法再推进
        for 网址 in 待定:
            自身.拒绝集.add(网址)#剩余视为拒绝

    def 部分重载(自身):
        """清接受集模块缓存并重载受影响的插件入口。"""
        自身.分析变更()#分类
        待处理={}#任务到插件
        重载表={}#插件到重载信息
        名称表={}#树基准网址到插件名
        for 条目 in 自身.ctx.loader.entries():
            基准=条目.parent.tree.ctx.baseUrl#树基准
            if 基准 not in 名称表:
                名称表[基准]=set()#新建
            名称表[基准].add(条目.options.name)#登记
        for 基准网址 in 名称表:
            for 名称 in 名称表[基准网址]:
                try:
                    解析=自身._解析(名称,基准网址,{})#解析网址
                    网址=解析.url#模块网址
                    if 网址 in 自身.拒绝集:
                        continue#已拒绝
                    任务=自身.内部加载器.loadCache.get(网址)#模块任务
                    模块=任务.module if 任务 is not None else None#模块包装
                    命名空间=模块.getNamespace() if 模块 is not None else None#命名空间
                    插件=自身.ctx.loader.unwrapExports(命名空间)#插件导出
                    if not 任务 or not 插件:
                        continue#无法重载
                    待处理[任务]=插件#待检查
                    自身.拒绝集.add(网址)#暂标拒绝以免重复
                except Exception as 错误:
                    自身.ctx.logger.warn(错误)#解析失败
        for 任务,插件 in list(待处理.items()):
            自身.拒绝集.discard(任务.url)#检查前放开
            依赖=list(加载依赖(任务,自身.拒绝集))#依赖树
            自身.拒绝集.add(任务.url)#重新拒绝入口
            if not any(项 in 自身.接受集 for 项 in 依赖):
                continue#未命中接受集
            for 项 in 依赖:
                自身.接受集.add(项)#依赖一并接受
            重载表[插件]={'filename':任务.url,'runtime':自身.ctx.registry.get(插件)}#记下运行时
        模块备份={}#加载缓存备份
        缓存备份={}#sys.modules 备份
        for 文件名 in 自身.接受集:
            任务=自身.内部加载器.loadCache.get(文件名)#原任务
            模块备份[文件名]=任务#备份
            自身.内部加载器.loadCache.pop(文件名,None)#删除
            try:
                文件路径=文件网址转路径(文件名)#本地路径
                规范=os.path.normpath(os.path.abspath(文件路径))#规范路径
                for 模名,模 in list(sys.modules.items()):
                    模文件=getattr(模,'__file__',None)#模块文件
                    if not 模文件:
                        continue#无文件
                    if os.path.normpath(os.path.abspath(模文件))==规范:
                        缓存备份[模名]=模#备份
                        del sys.modules[模名]#清掉
            except Exception:
                pass#非 file: 网址则忽略
        def 回滚():
            """恢复加载缓存与 sys.modules。"""
            for 文件名 in 模块备份:
                自身.内部加载器.loadCache[文件名]=模块备份[文件名]#写回加载缓存
            for 模名 in 缓存备份:
                sys.modules[模名]=缓存备份[模名]#写回模块表
        尝试表={}#新导出
        try:
            for 插件键 in 重载表:
                文件名=重载表[插件键]['filename']#入口网址
                导出=等待结果(自身.ctx.loader.import(文件名,自身.取外层栈))#再导入
                尝试表[文件名]=自身.ctx.loader.unwrapExports(导出)#解开导出
        except Exception as 原因:
            处理错误(自身.ctx,原因)#构建失败
            return 回滚()#恢复缓存
        def 重载(插件,运行时):
            """用新插件替换运行时上的全部光纤。"""
            if not 运行时:
                return#无运行时
            光纤表=运行时['fibers']#光纤表
            for 旧光纤 in list(光纤表):
                光纤=旧光纤.parent.registry.plugin(插件,旧光纤._配置,自身.取外层栈)#新光纤
                光纤.entry=旧光纤.entry#继承条目
                if 光纤.entry:
                    光纤.entry.fiber=光纤#回写
        try:
            for 插件,信息 in list(重载表.items()):
                运行时=信息['runtime']#运行时
                if not 运行时:
                    continue#跳过
                文件名=信息['filename']#入口网址
                路径=os.path.relpath(文件网址转路径(文件名),自身.基准目录)#相对路径
                try:
                    自身.ctx.registry.delete(插件)#拆除旧插件
                except Exception as 错误:
                    自身.ctx.logger.warn('failed to dispose plugin at %C',路径)#拆除失败
                    自身.ctx.logger.warn(错误)#详情
                try:
                    重载(尝试表[文件名],运行时)#装上新插件
                    自身.ctx.logger.info('reload plugin at %C',路径)#成功
                except Exception as 错误:
                    自身.ctx.logger.warn('failed to reload plugin at %C',路径)#重载失败
                    自身.ctx.logger.warn(错误)#详情
                    raise 错误#触发回滚
        except Exception:
            回滚()#恢复缓存
            for 插件,信息 in list(重载表.items()):
                运行时=信息['runtime']#运行时
                if not 运行时:
                    continue#跳过
                文件名=信息['filename']#入口网址
                try:
                    自身.ctx.registry.delete(尝试表[文件名])#拆掉新插件
                    重载(插件,运行时)#装回旧插件
                except Exception as 错误:
                    自身.ctx.logger.warn(错误)#回滚失败
            return#结束
        自身.ctx.emit('hmr/reload',重载表)#广播
        自身.暂存集=set()#清空暂存
