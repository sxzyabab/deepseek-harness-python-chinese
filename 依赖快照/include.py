"""由 YAML 或 JSON 文件支撑的条目树。"""
import errno,json,os,re,threading,time
from urllib.parse import urljoin as 拼接网址,urlparse as 解析网址,unquote as 解百分号
from urllib.request import pathname2url as 路径转网址片段,url2pathname as 网址片段转路径
import yaml
from .loader import (
    条目树,#嵌套配置文件的树基类
    标记为组插件,#把本插件登记成组载体
    是否表达式节点,#配置表达式节点判定
    表达式键,#配置表达式的键名
)
from .cordis import 服务#服务标记
from .cosmokit import 克隆#深克隆条目列表

js标签='tag:yaml.org,2002:js'#YAML !!js 的完整标签
扩展名到媒体类型={'.json':'application/json','.yaml':'application/yaml','.yml':'application/yaml'}#可写扩展名
写入重试上限=10#改名失败的重试次数
写入重试间隔毫秒=50#重试退避的基础间隔

def 路径转文件网址(路径):
    """把文件系统路径收成 file 网址。"""
    编码=路径转网址片段(os.path.abspath(路径))#绝对路径按百分号编码
    if not 编码.startswith('/'):
        编码='/'+编码#补上根斜杠
    return 'file://'+编码#三斜杠 file 网址

def 文件网址转路径(网址):
    """把 file 网址收成文件系统路径。"""
    解析=解析网址(网址)#拆出主机与路径
    if 解析.netloc:
        return 网址片段转路径(解百分号('//'+解析.netloc+解析.path))#UNC 路径
    return 网址片段转路径(解百分号(解析.path))#本地路径

def 解析配置文件路径(相对路径,基准网址):
    """按基准网址把配置文件说明符解析成本地路径。"""
    片段=相对路径.replace('\\','/')#反斜杠收成网址分隔符
    合并=拼接网址(基准网址,片段) if 基准网址 else 片段#相对基准拼接
    解析=解析网址(合并)#检查方案
    if not 解析.scheme:
        raise ValueError('相对路径缺少基准网址：'+合并)#没有基准就解析不出来
    if 解析.scheme!='file':
        raise ValueError('配置文件只能是 file 方案：'+合并)#只接受本地文件
    return 文件网址转路径(合并)#本地路径

class 条目列表读取器(yaml.SafeLoader):
    """认得 !!js 标量的 YAML 读取器。"""

class 条目列表写出器(yaml.SafeDumper):
    """把表达式节点写回 !!js 标量的 YAML 写出器。"""

def _限定为json方言(解析类):
    """只按 JSON 认得的形态解析裸标量：yes、on、12:30 与 2020-01-01 都是字符串。"""
    解析类.yaml_implicit_resolvers={}#丢掉 YAML 1.1 的布尔别名、六十进制与时间戳
    解析类.add_implicit_resolver('tag:yaml.org,2002:null',re.compile(r'^(?:~|null|Null|NULL|)$'),['~','n','N',''])#空值
    解析类.add_implicit_resolver('tag:yaml.org,2002:bool',re.compile(r'^(?:true|True|TRUE|false|False|FALSE)$'),list('tTfF'))#布尔
    解析类.add_implicit_resolver('tag:yaml.org,2002:int',re.compile(r'^-?(?:0|[1-9][0-9]*)$'),list('-0123456789'))#整数
    解析类.add_implicit_resolver('tag:yaml.org,2002:float',re.compile(r'^-?(?:0|[1-9][0-9]*)(?:\.[0-9]*)?(?:[eE][-+]?[0-9]+)?$'),list('-0123456789'))#浮点

_限定为json方言(条目列表读取器)#读取按 JSON 方言
_限定为json方言(条目列表写出器)#写出用同一套方言，裸标量才能原样读回

def _构造表达式节点(读取器,节点):
    """把 !!js 标量收成表达式节点。"""
    return {表达式键:读取器.construct_scalar(节点)}#表达式节点

def _写出映射(写出器,数据):
    """表达式节点写成 !!js 标量，其余按普通映射写出。"""
    if 是否表达式节点(数据):
        return 写出器.represent_scalar(js标签,数据[表达式键])#!!js 标量
    return yaml.SafeDumper.represent_dict(写出器,数据)#普通映射

条目列表读取器.add_constructor(js标签,_构造表达式节点)#登记 !!js 读取
条目列表写出器.add_representer(dict,_写出映射)#登记映射写出

class 配置文件错误(Exception):
    """读、解析或校验配置文件失败。"""
    def __init__(自身,阶段,路径,原因):
        """记下失败阶段并挂上原错误。"""
        super().__init__(f'配置文件{阶段}失败：{路径}')#带阶段的消息
        自身.阶段=阶段#读取、解析或校验
        自身.路径=路径#配置文件路径
        自身.__cause__=原因#原错误

def 应用条目补丁(数据,补丁列表,警告):
    """按补丁列表改写条目列表，返回一份脱离原输入的新列表。"""
    数据=克隆(数据)#先脱离原对象，热重载才不会把旧补丁烤进缓存
    if not 补丁列表:
        return 数据#没有补丁
    条目表={}#编号到条目
    def 建表(条目们):
        """按编号索引本层以及组内的条目。"""
        for 条目 in 条目们:
            编号=条目.get('id')#条目编号
            if 编号:
                条目表[编号]=条目#登记
            if 条目.get('group') and isinstance(条目.get('config'),list):
                建表(条目.get('config'))#递归进组
    建表(数据)#索引现有条目
    for 补丁 in 补丁列表:
        编号=补丁.get('id')#目标编号
        插入列表=补丁.get('insert')#要插入的条目
        if 插入列表 is not None:
            if _插入条目(数据,条目表,编号,插入列表,警告):
                建表(插入列表)#插进去了，后续补丁才能改到这些条目
            continue#本条补丁结束
        if not 编号:
            警告('补丁缺少 id：只有插入型补丁可以省略 id')#非插入必须有编号
            continue#跳过
        目标=条目表.get(编号)#覆盖目标
        if 目标 is None:
            警告('补丁跳过：找不到条目 %C',编号)#找不到
            continue#跳过
        名称=补丁.get('name')#期望的插件名
        if 名称 and 名称!=目标.get('name'):
            警告('补丁跳过：条目 %C 的插件名是 %C，补丁写的是 %C',编号,目标.get('name'),名称)#名字不符
            continue#跳过
        for 键 in 补丁:
            if 键 in ('id','insert','name'):
                continue#已经单独处理过的字段
            目标[键]=补丁[键]#写入覆盖
    return 数据#打过补丁的新列表

def _插入条目(数据,条目表,编号,插入列表,警告):
    """把条目插到根列表或某个组的配置里，返回是否真的插进去了。"""
    if not 编号:
        数据.extend(插入列表)#插到根列表
        return True#插入成功
    目标=条目表.get(编号)#目标组
    if 目标 is None:
        警告('插入补丁跳过：找不到条目 %C',编号)#找不到
        return False#没插进去
    if not 目标.get('group'):
        警告('插入补丁跳过：条目 %C 不是组',编号)#不是组
        return False#没插进去
    if not isinstance(目标.get('config'),list):
        目标['config']=[]#组的配置补成列表
    目标['config'].extend(插入列表)#插到组里
    return True#插入成功

class 包含(条目树):
    """由 YAML 或 JSON 文件支撑的加载器条目树。"""
    依赖声明=['加载器']#需要加载器服务

    def __init__(自身,上下文,配置):
        """解析配置文件路径，并把子树的基准网址切到该文件所在目录。"""
        条目树.__init__(自身,上下文)#先建根组
        自身.配置=配置#插件配置
        自身.启用日志=_解析日志开关(配置,上下文)#树日志开关
        自身.文件名=解析配置文件路径(配置['path'],自身.所属上下文.基准网址)#配置文件路径
        扩展名=os.path.splitext(自身.文件名)[1]#扩展名
        if 扩展名 not in 扩展名到媒体类型:
            raise ValueError(f'不支持的配置文件扩展名 "{扩展名}"')#只认 json 与 yaml
        自身.媒体类型=扩展名到媒体类型[扩展名]#媒体类型
        自身.只读=False#文件不可写时置真
        目录网址=路径转文件网址(os.path.dirname(自身.文件名))#文件所在目录
        if not 目录网址.endswith('/'):
            目录网址+='/'#目录网址必须带尾斜杠
        自身.所属上下文.__dict__['基准网址']=目录网址#子树的相对路径以该目录为基准
        自身.内容=None#上次读到的文本
        自身.数据=None#还没打补丁的解析结果
        自身.写出定时器=None#合并同拍写出的定时器
        自身.待写出=None#合并后的待写数据
        自身.更新锁=threading.Lock()#子树更新串行锁
        自身.待写锁=threading.Lock()#只保护待写数据与定时器
        自身.写出锁=threading.Lock()#写文件串行锁
        自身.__dict__[服务.初始化]=自身._初始化#依赖就绪后再读文件
        def 处理更新(纤程,新配置,不保存,续体):
            """路径没变就只重打补丁，不重启本插件。"""
            if 新配置.get('path')!=自身.配置.get('path'):
                return 续体()#路径变了才重启
            def 任务():
                """用新补丁刷新子条目。"""
                自身.根组.更新(自身.应用补丁(自身.数据,新配置.get('patches')))#事务更新
                自身.配置=新配置#保存新配置
            自身.串行执行(任务)#串行执行
        上下文.监听('internal/update',处理更新)#挂到本纤程的更新钩子

    #============================== 读取与提交 ==============================
    def 串行执行(自身,任务):
        """串行执行子树更新，前一次失败不挡住后一次。"""
        with 自身.更新锁:
            return 任务()#执行本任务

    def 检查可写(自身):
        """文件不可写时把本树标成只读。"""
        自身.只读=not os.access(自身.文件名,os.W_OK)#按文件权限

    def 读取(自身,强制=False):
        """读文件并解析成条目列表。文本没变时给出空值。"""
        try:
            with open(自身.文件名,'r',encoding='utf-8',errors='replace') as 文件:
                内容=文件.read()#读全部文本
        except OSError as 错误:
            raise 配置文件错误('读取',自身.文件名,错误)#读失败
        if not 强制 and 自身.内容==内容:
            return None#内容没变
        try:
            if 自身.媒体类型=='application/yaml':
                数据=yaml.load(内容,Loader=条目列表读取器)#YAML 方言
            else:
                数据=json.loads(内容)#JSON
        except Exception as 错误:
            raise 配置文件错误('解析',自身.文件名,错误)#解析失败
        if not isinstance(数据,list):
            raise 配置文件错误('校验',自身.文件名,TypeError('配置文件的顶层必须是数组'))#形态非法
        return {'内容':内容,'数据':数据}#候选

    def 应用补丁(自身,数据,补丁列表=None):
        """用加载器日志器打补丁，跳过的补丁记成警告。"""
        def 警告(消息,*参数):
            """把跳过的补丁打到加载器日志。"""
            自身.所属上下文.根.日志('加载器').警告(消息,*参数)#警告
        return 应用条目补丁(数据,补丁列表,警告)#打补丁

    def _初始化(自身):
        """读取配置文件并挂上子条目。"""
        候选=自身._首次读取()#读文件，必要时先写出初值
        yield 自身.停止#卸载时停子树并冲刷写出
        自身.提交(候选)#提交条目

    def _首次读取(自身):
        """首次读取。文件缺失且配置给了初值时先把初值写出去。"""
        try:
            return 自身.读取(True)#强制读
        except 配置文件错误 as 错误:
            if 错误.阶段!='读取' or getattr(错误.__cause__,'errno',None)!=errno.ENOENT:
                raise#不是文件缺失
            初值=自身.配置.get('initial')#配置里给的初值
            if 初值 is None:
                raise FileNotFoundError('找不到配置文件：'+自身.文件名)#没有初值可写
            自身._写文件(初值)#写出初值
            return 自身.读取(True)#再读一次

    def 停止(自身):
        """停掉子条目并冲刷还没写出的配置。"""
        自身.根组.停止()#停根组
        自身.冲刷写出()#写出残留

    def 刷新(自身):
        """文件内容变化时事务性刷新子条目。"""
        def 任务():
            """在队列里读，才能跟已提交状态比内容。"""
            候选=自身.读取()#读文件
            if 候选 is not None:
                自身._提交(候选)#提交
        自身.串行执行(任务)#串行执行

    def 提交(自身,候选):
        """把候选入队后提交。"""
        def 任务():
            """提交候选。"""
            自身._提交(候选)#实际提交
        return 自身.串行执行(任务)#串行执行

    def _提交(自身,候选):
        """打补丁、更新根组并记下原文。"""
        自身.根组.更新(自身.应用补丁(候选['数据'],自身.配置.get('patches')))#事务更新
        自身.内容=候选['内容']#记下原文
        自身.数据=候选['数据']#记下还没打补丁的解析结果
        自身.检查可写()#更新只读标记

    #============================== 写出 ==============================
    def _写文件(自身,配置):
        """序列化后经临时文件改名写出。"""
        if 自身.只读:
            raise PermissionError('配置文件只读，不能覆盖：'+自身.文件名)#只读拒绝
        if 自身.媒体类型=='application/yaml':
            自身.内容=yaml.dump(配置,Dumper=条目列表写出器,allow_unicode=True,sort_keys=False,default_flow_style=False)#YAML
        else:
            自身.内容=json.dumps(配置,indent=2,ensure_ascii=False)#JSON
        临时文件名=自身.文件名+'.tmp'#临时文件
        with open(临时文件名,'w',encoding='utf-8') as 文件:
            文件.write(自身.内容)#写入文本
        自身._改名覆盖(临时文件名)#原子替换

    def _改名覆盖(自身,临时文件名):
        """把临时文件原子改名成目标文件，占用类错误退避重试。"""
        重试=0#已重试次数
        while True:
            try:
                os.replace(临时文件名,自身.文件名)#原子改名覆盖
                return#成功
            except OSError as 错误:
                if 错误.errno not in (errno.EACCES,errno.EBUSY,errno.EPERM) or 重试>=写入重试上限:
                    raise#不可重试，或次数已用尽
                time.sleep((重试+1)*写入重试间隔毫秒/1000)#退避
                重试+=1#下一次

    def 调度写出(自身,配置):
        """合并同一拍里的多次写出，延迟到定时器触发。写文件不在这里发生。"""
        with 自身.待写锁:
            if 自身.写出定时器 is not None:
                自身.写出定时器.cancel()#取消还没触发的写出
            自身.待写出=配置#记下最新数据
            自身.写出定时器=threading.Timer(0,自身._定时写出)#零延迟定时器
            自身.写出定时器.start()#启动

    def _定时写出(自身):
        """定时器线程里的写出。这里抛错没人接得住，只记日志。"""
        try:
            自身.冲刷写出()#实际写出
        except Exception as 错误:
            日志=自身.所属上下文.根.日志('加载器')#加载器日志门面
            日志.警告('写出配置文件失败 %C',自身.文件名)#写出失败
            日志.警告(错误)#失败详情

    def 冲刷写出(自身):
        """立刻写出待写数据。没有待写数据时是空操作。"""
        with 自身.待写锁:
            if 自身.写出定时器 is not None:
                自身.写出定时器.cancel()#取消定时器
                自身.写出定时器=None#清空
            配置=自身.待写出#取出待写数据
            自身.待写出=None#清空
        if 配置 is None:
            return#没有待写数据
        with 自身.写出锁:
            自身._写文件(配置)#实际写出

    def 写入(自身):
        """把当前根条目数据安排写出。"""
        自身.所属上下文.广播('loader/config-update')#通知配置更新
        自身.调度写出(自身.根组.子条目选项)#安排写出

def _解析日志开关(配置,上下文):
    """显式配置优先，其次继承父树，都没有则关闭。"""
    启用=配置.get('enableLogs')#显式开关
    if 启用 is not None:
        return 启用#显式配置
    条目对象=上下文.纤程.条目#所属条目
    if 条目对象 is not None:
        return bool(条目对象.父组.所属树.启用日志)#继承父树
    return False#默认关闭

标记为组插件(包含)#树载体：它的配置是条目列表，保持字面量

默认=包含#模块的默认插件导出
