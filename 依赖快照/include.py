"""文件条目树：从 YAML/JSON 读入条目并写回。"""
import json,os,time,errno,threading
from urllib.parse import urljoin,urlparse,unquote#URL 拼接与解析
from urllib.request import pathname2url,url2pathname#路径与 file URL 互转
import yaml
from loader import 条目组,条目树,是否js表达式#条目树与 !!js 节点
from cordis import 服务#服务符号
from cosmokit import 克隆#深克隆条目列表

js标签='tag:yaml.org,2002:js'#YAML !!js 完整标签
可写类型={'.json':'application/json','.yaml':'application/yaml','.yml':'application/yaml'}#可写扩展
支持扩展=set(可写类型)#允许的扩展名
写入重试上限=10#改名失败重试次数
写入重试间隔毫秒=50#重试基础间隔

def 路径转文件url(路径):
    """把文件系统路径收成 file URL。"""
    #先收成绝对路径再按 file URL 规则编码
    绝对=os.path.abspath(路径)#绝对路径
    编码=pathname2url(绝对)#百分号编码
    if not 编码.startswith('/'):
        编码='/'+编码#补上根斜杠
    return 'file://'+编码#三斜杠 file URL

def 文件url转路径(网址):
    """把 file URL 收成文件系统路径。"""
    #拆出主机与路径
    解析=urlparse(网址)#解析 URL
    if 解析.netloc:
        return url2pathname(unquote('//'+解析.netloc+解析.path))#UNC 路径
    return url2pathname(unquote(解析.path))#本地路径

def 解析包含路径(相对,基准url):
    """按 ctx.baseUrl 解析配置文件路径。"""
    #反斜杠收成 URL 分隔
    片段=相对.replace('\\','/')#正斜杠
    if 基准url:
        合并=urljoin(基准url,片段)#相对基准拼接
    else:
        合并=片段#无基准则原样
    解析=urlparse(合并)#检查方案
    if not 解析.scheme:
        raise ValueError('Invalid URL')#相对路径缺少基准
    if 解析.scheme!='file':
        raise ValueError('URL must be of scheme file: '+合并)#只接受 file
    return 文件url转路径(合并)#收成路径

class 条目列表加载器(yaml.SafeLoader):
    """条目列表 YAML 方言加载器，支持 !!js。"""

class 条目列表转储器(yaml.SafeDumper):
    """条目列表 YAML 方言转储器，写出 !!js。"""

def 构造js表达式(加载器,节点):
    """把 !!js 标量收成表达式节点。"""
    return {'__jsExpr':加载器.construct_scalar(节点)}#表达式节点

def 表示字典(转储器,数据):
    """表达式节点写成 !!js 标量，其余按映射写出。"""
    if 是否js表达式(数据):
        return 转储器.represent_scalar(js标签,数据['__jsExpr'])#!!js 标量
    return yaml.SafeDumper.represent_dict(转储器,数据)#普通映射

条目列表加载器.add_constructor(js标签,构造js表达式)#登记 !!js 构造
条目列表转储器.add_representer(dict,表示字典)#登记映射写出

class 配置文件错误(Exception):
    """读、解析或校验配置文件失败。"""
    def __init__(自身,阶段,路径,原因):
        """记录阶段并把原错误挂到原因上。"""
        super().__init__('failed to '+阶段+' config file '+路径)#英文消息与 TS 一致
        自身.阶段=阶段#read/parse/validate
        自身.路径=路径#配置文件路径
        自身.name='ConfigFileError'#错误名
        自身.__cause__=原因#原错误

def 应用条目补丁(数据,补丁列表,警告):
    """按补丁列表改写条目列表，返回脱离原输入的新列表。"""
    #先脱离原对象，避免热重载把旧补丁烤进缓存
    数据=克隆(数据)#深克隆
    if not 补丁列表:
        return 数据#无补丁
    条目表={}#id 到条目
    def 建表(条目们):
        """按 id 索引本层及组内条目。"""
        for 条目 in 条目们:
            标识=条目.get('id')#条目 id
            if 标识:
                条目表[标识]=条目#登记
            if 条目.get('group') and isinstance(条目.get('config'),list):
                建表(条目.get('config'))#递归组
    建表(数据)#索引现有条目
    for 补丁 in 补丁列表:
        标识=补丁.get('id')#目标 id
        插入=补丁.get('insert')#插入列表
        名称=补丁.get('name')#期望插件名
        if 'insert' in 补丁 and 插入 is not None:
            if 标识:
                目标=条目表.get(标识)#目标组
                if not 目标:
                    警告('patch insert: entry %C not found',标识)#找不到
                    continue#跳过
                if not 目标.get('group'):
                    警告('patch insert: entry %C is not a group',标识)#不是组
                    continue#跳过
                if not isinstance(目标.get('config'),list):
                    目标['config']=[]#补成列表
                目标['config'].extend(插入)#插入到组
            else:
                数据.extend(插入)#插入到根
            建表(插入)#后序补丁可改刚插入的行
            continue#本条补丁结束
        if not 标识:
            警告('patch: id is required for non-insert patches')#非插入必须有 id
            continue#跳过
        目标=条目表.get(标识)#覆盖目标
        if not 目标:
            警告('patch: entry %C not found',标识)#找不到
            continue#跳过
        if 名称 and 名称!=目标.get('name'):
            警告('patch: name mismatch for %C (expected %C, got %C), skipping',标识,目标.get('name'),名称)#名不符
            continue#跳过
        for 键 in 补丁:
            if 键=='id' or 键=='insert' or 键=='name':
                continue#已拆出的字段
            目标[键]=补丁[键]#写入覆盖
    return 数据#已打补丁的新列表

class 包含(条目树):
    """由 YAML 或 JSON 文件支撑的加载器条目树。"""
    inject=['loader']#依赖 loader 服务

    def __init__(自身,ctx,配置):
        """按路径解析文件并把基准 URL 切到该文件所在目录。"""
        super().__init__(ctx)#先建子树
        自身.配置=配置#插件配置
        启用=配置.get('enableLogs')#显式开关
        if 启用 is None:
            条目=getattr(ctx.fiber,'entry',None)#所属条目
            if 条目 is not None:
                启用=条目.parent.tree.enableLogs#继承父树
            if 启用 is None:
                启用=False#默认关闭
        自身.enableLogs=启用#树日志开关
        自身.文件名=解析包含路径(配置['path'],自身.ctx.baseUrl)#解析文件路径
        扩展=os.path.splitext(自身.文件名)[1]#扩展名
        if 扩展 not in 支持扩展:
            raise Exception('extension "'+扩展+'" not supported')#不支持的扩展
        自身.类型=可写类型[扩展]#媒体类型
        自身.只读=not 自身.类型#无类型则只读
        目录url=路径转文件url(os.path.dirname(自身.文件名))#文件所在目录
        if not 目录url.endswith('/'):
            目录url=目录url+'/'#目录 URL 必须带尾斜杠
        自身.ctx.__dict__['baseUrl']=目录url#子树基准切到该目录
        自身.内容=None#上次读到的文本
        自身.数据=None#未打补丁的解析结果
        自身.写入任务=None#延迟写出定时器
        自身.待写入=None#合并后的待写数据
        自身.应用锁=threading.Lock()#子树更新串行锁
        自身.写入锁=threading.Lock()#写出串行锁
        自身.__dict__[服务.初始化]=自身._初始化#挂上初始化钩子
        def 处理更新(新配置,不保存,下一步):
            """路径未变则只重打补丁，不走默认重启。"""
            if 新配置.get('path')!=自身.配置.get('path'):
                return 下一步()#路径变了则重启
            def 任务():
                """用新补丁刷新子条目。"""
                数据=自身.应用补丁(自身.数据,新配置.get('patches'))#重打补丁
                自身.root.update(数据)#事务更新
                自身.配置=新配置#保存新配置
            自身.入队(任务)#串行执行
        ctx.on('internal/update',处理更新)#挂更新瀑布

    def 入队(自身,任务):
        """串行执行子树更新，前序失败不挡住后续。"""
        自身.应用锁.acquire()#取锁
        try:
            return 任务()#执行本任务
        finally:
            自身.应用锁.release()#放锁

    def 检查访问(自身):
        """文件不可写则标成只读。"""
        if not 自身.类型:
            return#无可写类型
        if not os.access(自身.文件名,os.W_OK):
            自身.只读=True#标成只读

    def 读取(自身,强制=False):
        """读文件并解析成条目列表；文本未变则返回 None。"""
        try:
            文件=open(自身.文件名,'r',encoding='utf-8')#打开配置
            try:
                内容=文件.read()#读全部文本
            finally:
                文件.close()#关闭
        except Exception as 错误:
            raise 配置文件错误('read',自身.文件名,错误)#读失败
        if not 强制 and 自身.内容==内容:
            return None#内容未变
        try:
            if 自身.类型=='application/yaml':
                数据=yaml.load(内容,Loader=条目列表加载器)#YAML 方言
            elif 自身.类型=='application/json':
                数据=json.loads(内容)#JSON
        except Exception as 错误:
            raise 配置文件错误('parse',自身.文件名,错误)#解析失败
        if not isinstance(数据,list):
            raise 配置文件错误('validate',自身.文件名,TypeError('config file must be a top-level array'))#必须是数组
        return {'content':内容,'data':数据}#候选

    def 应用补丁(自身,数据,补丁列表=None):
        """用本树日志器打补丁。"""
        def 警告(消息,*参数):
            """把跳过的补丁打到 loader 日志。"""
            日志=getattr(自身.ctx.root,'logger',None)#根日志服务
            if 日志:
                日志('loader').warn(消息,*参数)#警告
        return 应用条目补丁(数据,补丁列表,警告)#打补丁

    def _初始化(自身):
        """读取配置文件并挂上子条目。"""
        try:
            候选=自身.读取(True)#强制读
        except 配置文件错误 as 错误:
            原因=错误.__cause__#原错误
            码=getattr(原因,'errno',None)#系统错误码
            if 错误.阶段!='read' or 码!=errno.ENOENT:
                raise 错误#不是缺文件
            if 自身.配置.get('initial') is not None:
                自身._写文件(自身.配置.get('initial'))#写出初值
                候选=自身.读取(True)#再读
            else:
                raise Exception('config file not found: '+自身.文件名)#没有初值
        yield 自身.停止#卸载时停子树并冲刷写出
        自身.应用(候选)#提交条目

    def 停止(自身):
        """停掉子条目并冲刷未写出的配置。"""
        自身.root.stop()#停根组
        自身.冲刷写入()#写出残留

    def 刷新(自身):
        """文件内容变化时事务性刷新子条目。"""
        def 任务():
            """在队列里读，才能跟已提交状态比内容。"""
            候选=自身.读取()#读文件
            if not 候选:
                return#未变
            自身._应用(候选)#提交
        自身.入队(任务)#串行

    def 应用(自身,候选):
        """把候选入队后提交。"""
        def 任务():
            """提交候选。"""
            自身._应用(候选)#实际提交
        return 自身.入队(任务)#串行

    def _应用(自身,候选):
        """打补丁、更新根组并记下原文。"""
        数据=自身.应用补丁(候选['data'],自身.配置.get('patches'))#打补丁
        自身.root.update(数据)#事务更新
        自身.内容=候选['content']#记下原文
        自身.数据=候选['data']#记下未打补丁的解析
        自身.检查访问()#更新只读

    def _写文件(自身,配置):
        """序列化后经临时文件改名写出。"""
        if 自身.只读:
            raise Exception('cannot overwrite readonly config')#只读拒绝
        if 自身.类型=='application/yaml':
            自身.内容=yaml.dump(配置,Dumper=条目列表转储器,allow_unicode=True,sort_keys=False,default_flow_style=False)#YAML
        elif 自身.类型=='application/json':
            自身.内容=json.dumps(配置,indent=2,ensure_ascii=False)#JSON
        临时=自身.文件名+'.tmp'#临时文件
        文件=open(临时,'w',encoding='utf-8')#打开临时文件
        try:
            文件.write(自身.内容)#写入文本
        finally:
            文件.close()#关闭
        重试=0#已重试次数
        while True:
            try:
                os.replace(临时,自身.文件名)#原子改名覆盖
                return#成功
            except Exception as 错误:
                码=getattr(错误,'errno',None)#系统错误码
                if 码 not in (errno.EACCES,errno.EBUSY,errno.EPERM) or 重试>=写入重试上限:
                    raise 错误#不可重试或次数用尽
                time.sleep((重试+1)*写入重试间隔毫秒/1000)#退避
                重试=重试+1#下一次

    def 调度写入(自身,配置):
        """合并同拍写出，延迟到定时器触发。"""
        自身.写入锁.acquire()#取锁
        try:
            if 自身.写入任务 is not None:
                自身.写入任务.cancel()#取消未触发的写出
                自身.写入任务=None#清空
            自身.待写入=配置#记下最新数据
            def 到期():
                """定时器到点后冲刷。"""
                自身.冲刷写入()#冲刷
            自身.写入任务=threading.Timer(0,到期)#零延迟定时器
            自身.写入任务.start()#启动
        finally:
            自身.写入锁.release()#放锁

    def 冲刷写入(自身):
        """立刻写出待写数据；无待写则等待进行中的写出。"""
        自身.写入锁.acquire()#取锁
        try:
            if 自身.写入任务 is not None:
                自身.写入任务.cancel()#取消定时器
                自身.写入任务=None#清空
            配置=自身.待写入#取出
            自身.待写入=None#清空
            if 配置 is None:
                return#没有新数据
            try:
                自身._写文件(配置)#实际写出
            except Exception as 错误:
                日志=getattr(自身.ctx.root,'logger',None)#根日志服务
                if 日志:
                    日志('loader').warn('failed to write config file %C',自身.文件名)#写出失败
                    日志('loader').warn(错误)#原错误
                raise 错误#仍抛给调用方
        finally:
            自身.写入锁.release()#放锁

    def 写入(自身):
        """把当前根条目数据安排写出。"""
        自身.ctx.emit('loader/config-update')#通知配置更新
        自身.调度写入(自身.root.data)#安排写出

setattr(包含,条目组.键,True)#树载体：条目与补丁列表保持字面量
包含.write=包含.写入#英文别名
包含.refresh=包含.刷新#英文别名
包含.stop=包含.停止#英文别名
默认=包含#加载器 default 导出
