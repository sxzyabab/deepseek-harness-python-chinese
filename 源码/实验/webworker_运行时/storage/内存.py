from ..node.未实现失败 import 运行时错误#本包错误
import time#mtime
from ..module_system.posix路径 import 目录名,拼接,规范化,解析,分隔符#路径工具
from ..镜像布局 import 镜像覆盖目录列表#覆盖层目录白名单
from .tar import 解析tar#tar解析

__all__=['内存vfs','加载vfs镜像','加载vfs覆盖层']#仅中文公开名

默认文件权限=0o644#默认文件权限
默认目录权限=0o755#默认目录权限

def 失败(码,系统调用,路径,细节=None):#抛VFS错误
    """构造并抛出带 code/path/syscall 的错误。"""
    错误=运行时错误(f"{码}: {细节 if 细节 is not None else 系统调用} failed, {系统调用} '{路径}'")#构造消息，??系统调用，空串合法
    错误.code=码#挂错误码
    错误.path=路径#挂路径
    错误.syscall=系统调用#挂系统调用
    raise 错误#抛出

def 解析编码(选项):#解析读编码
    """从读选项取出编码。"""
    if 选项 is None:#无选项
        return None#无
    if isinstance(选项,str):#直接编码串
        return 选项#编码
    return 选项.get('encoding')#对象内编码

def _恒假():#Stats恒假谓词
    """Node Stats 上恒假的类型谓词。"""
    return False#否

def _构造是文件(是目录):#isFile 闭包
    """构造 isFile。"""
    def 是文件():#是否普通文件
        """是否普通文件。"""
        return not 是目录#非目录即文件
    return 是文件#谓词

def _构造是目录(是目录):#isDirectory 闭包
    """构造 isDirectory。"""
    def 是目录面():#是否目录
        """是否目录。"""
        return 是目录#目录否
    return 是目录面#谓词

def 普通统计(大小,mtime毫秒,是目录,inode,权限):#普通Stats
    """组装名册读取的 fs.Stats 子集。"""
    return {#组装
        'size':大小,#字节大小
        'ino':int(inode),#inode转number
        'mtimeMs':mtime毫秒,#修改时间
        'ctimeMs':mtime毫秒,#状态变更同mtime
        'atimeMs':mtime毫秒,#访问同mtime
        'birthtimeMs':mtime毫秒,#创建同mtime
        'mtime':mtime毫秒,#Date形态（毫秒）
        'mode':(0o040000 if 是目录 else 0o100000)|(权限&0o777),#类型位加权限
        'isFile':_构造是文件(是目录),#是否文件
        'isDirectory':_构造是目录(是目录),#是否目录
        'isSymbolicLink':_恒假,#无符号链接
        'isFIFO':_恒假,#非FIFO
        'isSocket':_恒假,#非套接字
        'isBlockDevice':_恒假,#非块设备
        'isCharacterDevice':_恒假,#非字符设备
    }#return结束

def 大整数统计(大小,mtime毫秒,是目录,inode,权限,链接数=1):#BigInt Stats
    """与普通统计同一条目，整数形态。"""
    毫秒=int(mtime毫秒)#毫秒
    纳秒=毫秒*1_000_000#纳秒
    return {#组装
        'size':大小,'mode':(0o040000 if 是目录 else 0o100000)|(权限&0o777),#大小模式
        'dev':1,'ino':inode,'nlink':链接数,#身份
        'mtimeMs':毫秒,'mtimeNs':纳秒,'ctimeMs':毫秒,'ctimeNs':纳秒,#时间
        'atimeMs':毫秒,'atimeNs':纳秒,'birthtimeMs':毫秒,'birthtimeNs':纳秒,#访问创建
        'mtime':毫秒,'ctime':毫秒,'atime':毫秒,'birthtime':毫秒,#Date
        'isFile':_构造是文件(是目录),'isDirectory':_构造是目录(是目录),#类型
        'isSymbolicLink':_恒假,'isFIFO':_恒假,'isSocket':_恒假,#其余
        'isBlockDevice':_恒假,'isCharacterDevice':_恒假,#设备
    }#return结束

def 打开模式(标志):#解析打开标志
    """解析兼容文件系统支持的 Node 字符串标志。"""
    基=标志[0] if 标志 else ''#首字母
    后缀=list(标志[1:])#后缀字符
    合法后缀=all(后缀字符 in ('+','x','s') for 后缀字符 in 后缀)#后缀合法
    唯一后缀=len(set(后缀))==len(后缀)#后缀无重复
    if 基 not in ('r','w','a') or not 合法后缀 or not 唯一后缀 or (基=='r' and 'x' in 标志):#非法标志
        错误=TypeError(f"The argument 'flags' is invalid. Received '{标志}'")#类型错误
        错误.code='ERR_INVALID_ARG_VALUE'#错误码
        raise 错误#抛出
    return {#组装模式
        'readable':基=='r' or '+' in 标志,#可读
        'writable':基!='r' or '+' in 标志,#可写
        'append':基=='a',#追加
        'create':基 in ('w','a'),#可创建
        'truncate':基=='w',#截断
        'exclusive':'x' in 标志,#排他
    }#return结束

def 调整大小(字节序列,长度):#调整字节长度
    """精确调整字节大小，保留前缀，增长时填零。"""
    if not isinstance(长度,int) or 长度<0 or isinstance(长度,bool):#非法长度
        错误=ValueError(f'The value of "len" is out of range. It must be >= 0. Received {长度}')#范围错
        错误.code='ERR_OUT_OF_RANGE'#错误码
        raise 错误#抛出
    return bytes(字节序列[:长度])+bytes(max(0,长度-len(字节序列)))#拷前缀填零

class 内存vfs:#内存VFS
    """用两张映射持有的文件系统：一张文件字节，一张目录。"""

    def __init__(自身,选项=None):#构造
        """构建同步文件系统权威。"""
        if 选项 is None:#缺省
            选项={}#空
        自身._文件表={}#文件映射 path->node
        自身._目录集={分隔符}#目录集含根
        自身._目录权限={}#目录权限
        自身._目录mtime={}#目录mtime
        自身._变更监听=set()#变更监听
        自身._汇=选项.get('sink')#持久sink
        自身._临时序号=0#临时目录序号
        自身._身份表={}#路径身份
        自身._上一身份=0#上一身份
        自身.promises={#promise面——委托同步
            'readFile':自身.读取文件同步,'writeFile':自身._异步写文件,#读写
            'appendFile':自身.追加文件同步,'mkdir':自身.建目录同步,#追加建目录
            'readdir':自身.读目录同步,'stat':自身.统计同步,'lstat':自身.统计同步,#列stat
            'realpath':自身.真实路径同步,'rename':自身.重命名同步,'unlink':自身.取消链接同步,#路径操作
            'rm':自身.移除同步,'mkdtemp':自身.建临时目录同步,'link':自身.硬链接同步,#移除临时链接
            'truncate':自身.截断同步,'chmod':自身.改权限同步,#截断权限
            'opendir':自身.打开目录,'open':自身.打开,'access':自身._访问,#打开访问
        }#promises结束

    def _异步写文件(自身,路径,数据,选项=None):#异步写委托
        """委托同步写。"""
        自身.写入文件同步(路径,数据,选项)#委托

    def _访问(自身,路径):#异步access
        """对任何已存在路径解析。"""
        目标=规范化(解析(路径))#规范化
        if 目标 not in 自身._文件表 and 目标 not in 自身._目录集:#不存在
            失败('ENOENT','access',目标)#报错

    def 刷新(自身):#刷新sink
        """结算持久 sink，不改变内存侧成功。"""
        if 自身._汇 is not None and hasattr(自身._汇,'flush'):#有汇
            自身._汇.flush()#等待持久

    def 订阅(自身,监听器):#订阅变更
        """观察已提交的运行时变更。"""
        自身._变更监听.add(监听器)#加入
        def 拆除():#拆除器
            """阻止未来调用。"""
            自身._变更监听.discard(监听器)#移除
        return 拆除#拆除器

    def _发布(自身,变更):#发布变更
        """状态变更后发布；一个故障观察者不能回滚一次写。"""
        观察者列表=[]#观察者列表
        if 自身._汇 is not None:#有sink
            def 记汇(改,汇=自身._汇):#sink记录
                """记录到汇。"""
                汇.record(改)#记录
            观察者列表.append(记汇)#加入
        观察者列表.extend(自身._变更监听)#监听器
        for 监听器 in 观察者列表:#逐个通知
            try:#隔离失败
                监听器(变更)#回调
            except Exception as 错误:#变更观察者是被模拟回调，什么都可能抛，收不窄
                print('webworker vfs: mutation observer failed',错误)#记日志

    def _键(自身,路径):#规范化键
        """返回无尾分隔符的绝对路径。"""
        绝对=规范化(解析(路径))#绝对规范化
        return 绝对[:-1] if len(绝对)>1 and 绝对.endswith(分隔符) else 绝对#去尾分隔

    def 读取文件同步(自身,路径,选项=None):#同步读文件
        """读文件；省略编码则取字节。"""
        目标=自身._键(路径)#规范化
        节点=自身._文件表.get(目标)#取节点
        if 节点 is None:#无文件
            if 目标 in 自身._目录集:#是目录
                失败('EISDIR','read',目标)#报错
            失败('ENOENT','open',目标)#不存在
        return 节点['bytes'] if 解析编码(选项) is None else 节点['bytes'].decode('utf-8')#字节或文本

    def 存在同步(自身,路径):#路径是否存在
        """报告路径是否存在。"""
        目标=自身._键(路径)#规范化
        return 目标 in 自身._文件表 or 目标 in 自身._目录集#文件或目录

    def 统计同步(自身,路径,选项=None):#同步stat
        """Stat 路径。"""
        目标=自身._键(路径)#规范化
        节点=自身._文件表.get(目标)#文件节点
        if 节点 is not None:#有文件
            大小,mtime毫秒,是目录,权限=len(节点['bytes']),节点['mtimeMs'],False,节点['mode']#文件字段
        elif 目标 in 自身._目录集:#有目录
            大小,mtime毫秒,是目录,权限=0,自身._目录mtime.get(目标,0),True,自身._目录权限.get(目标,默认目录权限)#目录字段
        else:#不存在
            失败('ENOENT','stat',目标)#报错
        身份=自身._路径身份(目标) if 节点 is None else 自身._文件身份(节点)#身份
        if 选项 is not None and 选项.get('bigint') is True:#BigInt形态，空字典不走
            return 大整数统计(大小,mtime毫秒,是目录,身份,权限,1 if 节点 is None else 自身._文件链接数(节点))#BigInt
        return 普通统计(大小,mtime毫秒,是目录,身份,权限)#普通

    def _路径身份(自身,目标):#路径身份
        """已存在路径的稳定身份，首次观察时分配。"""
        已有=自身._身份表.get(目标)#已有
        if 已有 is not None:#复用
            return 已有#返回
        自身._上一身份+=1#分配新
        自身._身份表[目标]=自身._上一身份#登记
        return 自身._上一身份#返回

    def _文件身份(自身,节点):#文件节点身份
        """文件节点跨名称保留的 inode 类身份。"""
        if 节点.get('identity') is not None:#已有
            return 节点['identity']#返回
        自身._上一身份+=1#分配
        节点['identity']=自身._上一身份#写入节点
        return 节点['identity']#返回

    def _文件链接数(自身,节点):#硬链接数
        """当前链到一个文件节点的名称数。"""
        路径索引=节点.get('paths')#路径索引
        if isinstance(路径索引,str):#字符串为一
            return 1#一
        return len(路径索引) if 路径索引 is not None else 0#集合大小

    def _加文件路径(自身,节点,路径):#添加路径索引
        """添加一个映射名，把罕见硬链接情况提升为集合。"""
        if 'paths' not in 节点:#空
            节点['paths']=路径#单路径
        elif isinstance(节点['paths'],str):#已有单路径
            节点['paths']={节点['paths'],路径}#升为集合
        else:#已是集合
            节点['paths'].add(路径)#加入

    def _删文件路径(自身,节点,路径):#移除路径索引
        """移除一个映射名，把剩余单链接收拢回字符串。"""
        路径索引=节点.get('paths')#当前
        if isinstance(路径索引,str):#单路径
            节点['paths']=None#清空
            return
        if 路径索引 is None:#已空
            return
        路径索引.discard(路径)#从集合删
        if len(路径索引)==1:#剩一个
            节点['paths']=next(iter(路径索引))#收拢为字符串

    def _设文件(自身,路径,节点):#设置文件映射
        """设置一个文件映射条目，同时维护两节点的反向路径索引。"""
        旧=自身._文件表.get(路径)#旧节点
        if 旧 is 节点:#同节点无需
            return
        if 旧 is not None:#卸旧索引
            自身._删文件路径(旧,路径)#卸旧
        自身._文件表[路径]=节点#写入映射
        自身._加文件路径(节点,路径)#挂新索引

    def _删文件(自身,路径):#删文件映射
        """删除一个文件映射条目。"""
        节点=自身._文件表.pop(路径,None)#取并删
        if 节点 is None:#无则空
            return None#空
        自身._删文件路径(节点,路径)#卸索引
        return 节点#返回节点

    def _发布文件路径(自身,节点,路径,追加起点=None):#按路径发布写
        """内容或元数据写后发布一个链接名。"""
        变更={'kind':'write','path':路径,'bytes':节点['bytes'],'mode':节点['mode'],'entryChanged':False}#写变更
        if 追加起点 is not None:#可选追加起点
            变更['appendedFrom']=追加起点#追加
        自身._发布(变更)#发布

    def _发布文件(自身,节点,追加起点=None):#按节点发布写
        """对一个节点的每个硬链接发布内容或元数据写。"""
        路径索引=节点.get('paths')#路径
        if isinstance(路径索引,str):#单名
            自身._发布文件路径(节点,路径索引,追加起点)#发布一名
            return
        if 路径索引 is None:#无名
            return
        for 路径 in list(路径索引):#逐名发布
            自身._发布文件路径(节点,路径,追加起点)#发布

    def _替换文件(自身,节点,字节序列,追加起点=None):#替换字节
        """替换一个文件身份上的字节并通知所有链接路径。"""
        节点['bytes']=字节序列#写入字节
        节点['mtimeMs']=自身._触碰节点(节点)#推进mtime
        自身._发布文件(节点,追加起点)#通知链接

    def _写文件节点(自身,节点,位置,数据):#节点写
        """在一个偏移写入，空隙填零。"""
        偏移=max(0,位置)#非负偏移
        旧长=len(节点['bytes'])#旧长度
        字节=bytearray(max(旧长,偏移+len(数据)))#扩容缓冲
        字节[0:旧长]=节点['bytes']#拷旧
        字节[偏移:偏移+len(数据)]=数据#写入
        自身._替换文件(节点,bytes(字节),旧长 if 偏移==旧长 else None)#替换并可选追加
        return len(数据)#写入字节数

    def _截断文件(自身,节点,长度):#截断节点
        """调整一个文件身份大小并通知所有链接路径。"""
        自身._替换文件(节点,调整大小(节点['bytes'],长度))#调整大小

    def _触碰节点(自身,节点=None):#节点触碰时间
        """严格新于一个文件节点当前值的修改时间。"""
        先前=None if 节点 is None else 节点.get('mtimeMs')#先前
        现在=int(time.time()*1000)#现在毫秒
        return 现在 if 先前 is None else max(现在,先前+1)#严格递增

    def _触碰目录(自身,目标):#推进目录mtime
        """直接子项变化后推进目录的 mtime。"""
        先前=自身._目录mtime.get(目标)#先前
        现在=int(time.time()*1000)#现在
        自身._目录mtime[目标]=现在 if 先前 is None else max(现在,先前+1)#严格递增

    def _忘身份(自身,目标):#忘记身份
        """忘记已移除目录的身份。"""
        自身._身份表.pop(目标,None)#删自身
        前缀=f'{目标}{分隔符}'#子路径前缀
        for 已知 in list(自身._身份表.keys()):#扫已知
            if 已知.startswith(前缀):#后代
                自身._身份表.pop(已知,None)#删后代

    def 读目录同步(自身,路径,选项=None):#同步列目录
        """列出目录。"""
        目标=自身._键(路径)#规范化
        if 目标 not in 自身._目录集:#非目录
            if 目标 in 自身._文件表:#是文件
                失败('ENOTDIR','scandir',目标)#报错
            失败('ENOENT','scandir',目标)#不存在
        前缀=分隔符 if 目标==分隔符 else f'{目标}{分隔符}'#子项前缀
        名称集合=set()#直接子名
        for 候选 in list(自身._文件表.keys())+list(自身._目录集):#扫全部路径
            if not 候选.startswith(前缀) or 候选==目标:#非后代
                continue#跳过
            剩余=候选[len(前缀):]#相对剩余
            if 剩余=='':#空则跳
                continue#跳过
            头=剩余.split(分隔符)[0]#直接子名
            名称集合.add(头)#收录
        已排序=sorted(名称集合)#排序
        if 选项 is None or 选项.get('withFileTypes') is not True:#仅名，缺席或非 True，空字典走仅名
            return 已排序#名列表
        return [自身._目录项(目标,名) for 名 in 已排序]#目录项

    def _目录项(自身,目录,名称):#构建目录项
        """directory 的一个子项的目录项。"""
        统计=自身.统计同步(拼接(目录,名称))#子项统计
        return {#组装
            'name':名称,'parentPath':目录,#名与父
            'isFile':统计['isFile'],'isDirectory':统计['isDirectory'],#类型
            'isSymbolicLink':_恒假,#无符号链接
        }#return结束

    def 真实路径同步(自身,路径):#同步真实路径
        """解析路径；VFS 无符号链接，故仅规范化。"""
        目标=自身._键(路径)#规范化
        if not 自身.存在同步(目标):#不存在
            失败('ENOENT','realpath',目标)#报错
        return 目标#返回

    def 建目录同步(自身,路径,选项=None):#同步建目录
        """创建目录。"""
        if 选项 is None:#缺省
            选项={}#空
        目标=自身._键(路径)#规范化
        if 目标 in 自身._文件表:#与文件冲突
            失败('EEXIST','mkdir',目标)#报错
        if 目标 in 自身._目录集:#已存在目录
            if 选项.get('recursive') is True:#递归容忍
                return None#无事
            失败('EEXIST','mkdir',目标)#非递归拒绝
        父=目录名(目标)#父路径
        if 父 not in 自身._目录集:#缺父
            if 选项.get('recursive') is not True:#非递归失败
                失败('ENOENT','mkdir',目标)#报错
            自身.建目录同步(父,选项)#递归建父
        自身._目录集.add(目标)#登记目录
        自身._触碰目录(目标)#新目录mtime
        自身._触碰目录(父)#父mtime
        if 'mode' not in 选项: 权限位=默认目录权限#??默认目录权限，mode=0 合法
        else: 权限位=选项['mode']#目录权限
        权限=权限位&0o777#权限位
        if 权限!=默认目录权限:#非默认则记
            自身._目录权限[目标]=权限#记下
        自身._发布({'kind':'mkdir','path':目标,'mode':权限})#发布
        return 目标#返回路径

    def 写入文件同步(自身,路径,数据,选项=None):#同步写文件
        """写文件，替换已有内容。"""
        if 选项 is None:#缺省
            选项={}#空
        目标=自身._键(路径)#规范化
        if 目标 in 自身._目录集:#是目录
            失败('EISDIR','open',目标)#报错
        if 目录名(目标) not in 自身._目录集:#缺父
            失败('ENOENT','open',目标)#报错
        if 'flag' not in 选项: 标志='w'#??w，空串合法
        else: 标志=选项['flag']#打开标志
        if 标志.startswith('wx') and 目标 in 自身._文件表:#排他创建
            失败('EEXIST','open',目标)#报错
        if 标志.startswith('a'):#追加路径
            自身.追加文件同步(目标,数据)#追加
            return
        先前=自身._文件表.get(目标)#已有节点
        if 先前 is not None:#已存在
            权限=先前['mode']#保留权限
        elif 选项.get('mode') is not None:#创建权限
            权限=选项['mode']&0o777#掩码
        else:#默认
            权限=默认文件权限#默认
        字节=数据.encode('utf-8') if isinstance(数据,str) else bytes(数据)#编码或原字节
        if 先前 is not None:#已存在
            自身._替换文件(先前,字节)#替换内容
            return
        节点={'bytes':字节,'mtimeMs':自身._触碰节点(),'mode':权限,'paths':None}#新节点
        自身._设文件(目标,节点)#挂映射
        自身._触碰目录(目录名(目标))#父mtime
        自身._发布({'kind':'write','path':目标,'bytes':字节,'mode':权限,'entryChanged':True})#新条目写

    def 追加文件同步(自身,路径,数据):#同步追加
        """追加到文件，不存在则创建。"""
        目标=自身._键(路径)#规范化
        已有=自身._文件表.get(目标)#已有节点
        追加=数据.encode('utf-8') if isinstance(数据,str) else bytes(数据)#追加字节
        if 已有 is None:#不存在则创建
            自身.写入文件同步(目标,追加)#创建
            return
        自身._写文件节点(已有,len(已有['bytes']),追加)#末尾写

    def 注水(自身,路径,数据,选项=None):#注水文件
        """注水文件及其父目录，供镜像加载与测试。"""
        if 选项 is None:#缺省
            选项={}#空
        目标=自身._键(路径)#规范化
        自身.注水目录(目录名(目标))#确保父目录
        字节=数据.encode('utf-8') if isinstance(数据,str) else bytes(数据)#内容
        自身._设文件(目标,{#挂文件节点
            'bytes':字节,#内容
            'mtimeMs':选项.get('mtimeMs') if 选项.get('mtimeMs') is not None else 自身._触碰节点(),#mtime
            'mode':(默认文件权限 if 'mode' not in 选项 else 选项['mode'])&0o777,#??默认文件权限，mode=0 合法
            'paths':None,#尚无反向索引
        })#setFile结束
        自身._触碰目录(目录名(目标))#父mtime

    def 注水目录(自身,路径,选项=None):#注水目录
        """创建目录及其父级。"""
        if 选项 is None:#缺省
            选项={}#空
        目标=自身._键(路径)#规范化
        if 目标 not in 自身._目录集:#尚无
            父=目录名(目标)#父
            if 父!=目标:#递归父
                自身.注水目录(父)#递归
            if 目标 in 自身._文件表:#与文件冲突
                失败('EEXIST','mkdir',目标)#报错
            自身._目录集.add(目标)#登记
            自身._目录mtime[目标]=选项.get('mtimeMs') if 选项.get('mtimeMs') is not None else int(time.time()*1000)#mtime
            自身._触碰目录(父)#父mtime
        if 选项.get('mode') is not None:#可选权限
            自身._目录权限[目标]=选项['mode']&0o777#记下
        if 选项.get('mtimeMs') is not None:#可选mtime
            自身._目录mtime[目标]=选项['mtimeMs']#记下

    def 用量(自身):#用量统计
        """报告本文件系统所持。"""
        字节=0#总字节
        for 节点 in 自身._文件表.values():#累加
            字节+=len(节点['bytes'])#累加
        return {'files':len(自身._文件表),'directories':len(自身._目录集),'bytes':字节}#报告

    def 重命名同步(自身,源路径,目标路径):#同步重命名
        """移动文件或目录子树。"""
        源=自身._键(源路径)#源键
        目标=自身._键(目标路径)#目标键
        if 源==目标:#同路径无事
            return
        节点=自身._文件表.get(源)#文件节点
        if 节点 is not None:#移动文件
            if 目标 in 自身._目录集:#目标是目录
                失败('EISDIR','rename',目标)#报错
            if 目录名(目标) not in 自身._目录集:#缺父
                失败('ENOENT','rename',目标)#报错
            if 自身._文件表.get(目标) is 节点:#硬链接自移
                return
            自身._删文件(源)#卸源名
            自身._设文件(目标,节点)#挂目标名
            自身._忘身份(源)#忘源身份
            自身._忘身份(目标)#忘目标身份
            自身._触碰目录(目录名(源))#源父mtime
            自身._触碰目录(目录名(目标))#目标父mtime
            自身._发布({'kind':'remove','path':源})#发移除
            自身._发布({'kind':'write','path':目标,'bytes':节点['bytes'],'mode':节点['mode'],'entryChanged':True})#发写入
            return#文件路径结束
        if 源 not in 自身._目录集:#源不存在
            失败('ENOENT','rename',源)#报错
        if 目标 in 自身._文件表:#目标是文件
            失败('ENOTDIR','rename',目标)#报错
        if 目录名(目标) not in 自身._目录集:#缺父
            失败('ENOENT','rename',目标)#报错
        if 目标 in 自身._目录集:#目标目录已存在
            if len(自身.读目录同步(目标))>0:#非空
                失败('ENOTEMPTY','rename',目标)#报错
            自身._目录集.discard(目标)#删空目标
            自身._目录权限.pop(目标,None)#清权限
            自身._目录mtime.pop(目标,None)#清mtime
        前缀=f'{源}{分隔符}'#子树前缀
        已移文件=[]#已移文件
        for 候选,值 in list(自身._文件表.items()):#扫文件
            if not 候选.startswith(前缀):#非子树
                continue#跳过
            自身._删文件(候选)#卸旧名
            新路径=拼接(目标,候选[len(前缀):])#新路径
            自身._设文件(新路径,值)#挂新名
            已移文件.append({'path':新路径,'bytes':值['bytes'],'mode':值['mode']})#记录
        已移目录=[]#已移目录
        for 候选 in list(自身._目录集):#扫目录
            if not 候选.startswith(前缀) and 候选!=源:#非本树
                continue#跳过
            移到=目标 if 候选==源 else 拼接(目标,候选[len(前缀):])#新路径
            自身._目录集.discard(候选)#卸旧
            自身._目录集.add(移到)#挂新
            位=自身._目录权限.pop(候选,None)#权限
            if 位 is not None:#移权限
                自身._目录权限[移到]=位#记下
            已移目录.append({'path':移到,'mode':默认目录权限 if 位 is None else 位})#记录
            时=自身._目录mtime.pop(候选,None)#mtime
            if 时 is not None:#移mtime
                自身._目录mtime[移到]=时#记下
        自身._忘身份(源)#忘源
        自身._忘身份(目标)#忘目标
        自身._触碰目录(目录名(源))#源父
        自身._触碰目录(目录名(目标))#目标父
        自身._发布({'kind':'remove','path':源})#发源移除
        for 目录 in 已移目录:#重发目录
            自身._发布({'kind':'mkdir','path':目录['path'],'mode':目录['mode']})#mkdir
        for 条目 in 已移文件:#重发文件
            自身._发布({'kind':'write','path':条目['path'],'bytes':条目['bytes'],'mode':条目['mode'],'entryChanged':True})#写变更

    def 硬链接同步(自身,已有,下一):#同步硬链接
        """给已有字节第二个名字。"""
        源=自身._键(已有)#源键
        目标=自身._键(下一)#新名
        节点=自身._文件表.get(源)#节点
        if 节点 is None:#源无
            失败('ENOENT','link',源)#报错
        if 目标 in 自身._文件表 or 目标 in 自身._目录集:#目标占用
            失败('EEXIST','link',目标)#报错
        if 目录名(目标) not in 自身._目录集:#缺父
            失败('ENOENT','link',目标)#报错
        自身._设文件(目标,节点)#挂第二名
        自身._触碰目录(目录名(目标))#父mtime
        自身._发布({'kind':'write','path':目标,'bytes':节点['bytes'],'mode':节点['mode'],'entryChanged':True})#发新名

    def 截断同步(自身,路径,长度=0):#同步截断
        """缩短文件。"""
        目标=自身._键(路径)#规范化
        节点=自身._文件表.get(目标)#节点
        if 节点 is None:#不存在
            失败('ENOENT','truncate',目标)#报错
        自身._截断文件(节点,长度)#截断

    def 改权限同步(自身,路径,权限):#同步改权限
        """更改条目的权限位。"""
        目标=自身._键(路径)#规范化
        节点=自身._文件表.get(目标)#文件节点
        if 节点 is not None:#文件
            节点['mode']=权限&0o777#掩码权限
            路径索引=节点.get('paths')#路径
            if isinstance(路径索引,str):#单名
                自身._发布({'kind':'chmod','path':路径索引,'mode':节点['mode']})#发chmod
            elif 路径索引 is not None:#多名
                for 名 in list(路径索引):#逐名发
                    自身._发布({'kind':'chmod','path':名,'mode':节点['mode']})#发chmod
            return
        if 目标 in 自身._目录集:#目录
            位=权限&0o777#掩码
            自身._目录权限[目标]=位#记下
            自身._发布({'kind':'chmod','path':目标,'mode':位})#发chmod
            return
        失败('ENOENT','chmod',目标)#不存在

    def 取消链接同步(自身,路径):#同步删文件
        """移除文件。"""
        目标=自身._键(路径)#规范化
        if 自身._删文件(目标) is None:#不存在
            失败('ENOENT','unlink',目标)#报错
        自身._忘身份(目标)#忘身份
        自身._触碰目录(目录名(目标))#父mtime
        自身._发布({'kind':'remove','path':目标})#发移除

    def 移除同步(自身,路径,选项=None):#同步移除
        """移除文件或目录。"""
        if 选项 is None:#缺省
            选项={}#空
        目标=自身._键(路径)#规范化
        if 自身._删文件(目标) is not None:#是文件
            自身._忘身份(目标)#忘身份
            自身._触碰目录(目录名(目标))#父mtime
            自身._发布({'kind':'remove','path':目标})#发移除
            return
        if 目标 in 自身._目录集:#是目录
            if 选项.get('recursive') is not True:#须递归
                失败('ERR_FS_EISDIR','rm',目标)#报错
            前缀=f'{目标}{分隔符}'#子树前缀
            for 候选 in list(自身._文件表.keys()):#删子文件
                if 候选.startswith(前缀):#子
                    自身._删文件(候选)#删
            for 候选 in list(自身._目录集):#扫子目录
                if not 候选.startswith(前缀):#非子
                    continue#跳过
                自身._目录集.discard(候选)#删目录
                自身._目录权限.pop(候选,None)#清权限
                自身._目录mtime.pop(候选,None)#清mtime
            自身._目录集.discard(目标)#删自身
            自身._目录权限.pop(目标,None)#清权限
            自身._目录mtime.pop(目标,None)#清mtime
            自身._忘身份(目标)#忘身份
            自身._触碰目录(目录名(目标))#父mtime
            自身._发布({'kind':'remove','path':目标})#发移除
            return
        if 选项.get('force') is not True:#非强制则报错
            失败('ENOENT','rm',目标)#报错

    def 建临时目录同步(自身,前缀):#同步临时目录
        """在 prefix 旁创建唯一命名目录。"""
        自身._临时序号+=1#序号
        目标=f'{前缀}{int(time.time()*1000):x}{自身._临时序号:x}'#唯一路径
        自身.建目录同步(目标,{'recursive':True})#创建
        return 自身._键(目标)#返回规范化

    def 打开目录(自身,路径):#打开目录
        """打开目录；消费者枚举条目。"""
        目标=自身._键(路径)#规范化
        名称列表=自身.读目录同步(目标)#快照名列表
        游标=[0]#读游标
        def 关闭():#无操作关闭
            """关闭句柄。"""
            return None#无事
        def 读():#读下一项
            """读下一项。"""
            if 游标[0]>=len(名称列表):#空
                return None#空
            名=名称列表[游标[0]]#当前名
            游标[0]+=1#推进
            return 自身._目录项(目标,名)#目录项
        def 迭代():#异步迭代
            """逐项产出。"""
            for 名 in 名称列表:#逐项
                yield 自身._目录项(目标,名)#产出
        return {'path':目标,'close':关闭,'read':读,'__iter__':迭代}#句柄

    def 打开文件同步(自身,路径,标志='r',权限=None):#同步打开身份
        """在稳定文件身份上打开一个同步描述符。"""
        目标=自身._键(路径)#规范化
        访问=打开模式(标志)#解析标志
        已有=自身._文件表.get(目标)#已有节点
        if 目标 in 自身._目录集:#是目录
            失败('EISDIR','open',目标)#报错
        if 访问['exclusive'] and 已有 is not None:#排他冲突
            失败('EEXIST','open',目标)#报错
        if not 访问['create'] and 已有 is None:#须存在
            失败('ENOENT','open',目标)#报错
        if 访问['create'] and 已有 is None:#需创建
            自身.写入文件同步(目标,b'',None if 权限 is None else {'mode':权限})#建空文件
        elif 访问['truncate'] and 已有 is not None:#需截断
            自身._截断文件(已有,0)#截零
        节点=自身._文件表.get(目标)#取节点
        if 节点 is None:#仍无
            失败('ENOENT','open',目标)#报错
        def 读(位置,长度):#读
            """按偏移读。"""
            if not 访问['readable']:#不可读
                失败('EBADF','read',目标)#报错
            return 节点['bytes'][位置:位置+长度]#视图
        def 写(位置,数据):#写
            """按偏移写。"""
            if not 访问['writable']:#不可写
                失败('EBADF','write',目标)#报错
            return 自身._写文件节点(节点,len(节点['bytes']) if 访问['append'] else 位置,数据)#委托写
        def 截断(长度):#截断
            """截断。"""
            if not 访问['writable']:#不可写
                失败('EINVAL','ftruncate',目标)#报错
            自身._截断文件(节点,长度)#委托
        def 统计():#统计
            """打开文件Stats。"""
            return 普通统计(len(节点['bytes']),节点['mtimeMs'],False,自身._文件身份(节点),节点['mode'])#组装
        return {'readable':访问['readable'],'writable':访问['writable'],'append':访问['append'],'read':读,'write':写,'truncate':截断,'stat':统计}#打开身份

    def 打开(自身,路径,标志='r',权限=None):#打开文件句柄
        """打开文件句柄。"""
        目标=自身._键(路径)#规范化
        if 目标 in 自身._目录集:#是目录
            if not 标志.startswith('r'):#非只读拒
                失败('EISDIR','open',目标)#报错
            def 拒写(*位置参数,**关键字参数):#拒写
                """目录拒写。"""
                失败('EISDIR','write',目标)#报错
            def 拒读(*位置参数,**关键字参数):#拒读
                """目录拒读。"""
                失败('EISDIR','read',目标)#报错
            def 拒截(*位置参数,**关键字参数):#拒截断
                """目录拒截断。"""
                失败('EISDIR','ftruncate',目标)#报错
            def 统计():#stat
                """目录统计。"""
                return 自身.统计同步(目标)#统计
            def 同步():#sync
                """刷新。"""
                自身.刷新()#刷新
            def 关闭():#关闭
                """空关闭。"""
                return None#无事
            return {'write':拒写,'writeFile':拒写,'readFile':拒读,'truncate':拒截,'stat':统计,'sync':同步,'datasync':同步,'close':关闭}#目录句柄
        文件=自身.打开文件同步(目标,标志,权限)#打开身份
        位置=[0]#当前位置
        已关闭=[False]#是否关闭
        def 当前(系统调用):#取当前描述符
            """取当前描述符。"""
            if 已关闭[0]:#已关闭
                失败('EBADF',系统调用,目标)#报错
            return 文件#返回
        def 写(数据):#写
            """写。"""
            字节=数据.encode('utf-8') if isinstance(数据,str) else bytes(数据)#编码
            描述符=当前('write')#取描述符
            偏移=描述符['stat']()['size'] if 描述符['append'] else 位置[0]#偏移
            已写=描述符['write'](偏移,字节)#写入
            位置[0]=偏移+已写#推进
            return {'bytesWritten':已写}#已写数
        def 整写(数据):#整写
            """整文件写。"""
            写(数据)#委托
        def 读文件(选项=None):#读剩余
            """读剩余。"""
            描述符=当前('read')#取描述符
            字节=描述符['read'](位置[0],max(0,描述符['stat']()['size']-位置[0]))#读
            位置[0]+=len(字节)#推进
            return 字节 if 解析编码(选项) is None else 字节.decode('utf-8')#字节或文本
        def 截断(长度=0):#截断
            """截断。"""
            当前('ftruncate')['truncate'](长度)#委托
        def 统计():#fstat
            """fstat。"""
            return 当前('fstat')['stat']()#统计
        def 同步():#fsync
            """fsync。"""
            当前('fsync')#取
            自身.刷新()#刷新
        def 关闭():#关闭
            """关闭。"""
            已关闭[0]=True#关闭
        return {'write':写,'writeFile':整写,'readFile':读文件,'truncate':截断,'stat':统计,'sync':同步,'datasync':同步,'close':关闭}#文件句柄

def 加载vfs镜像(镜像,根='/dsh',文件系统=None):#加载基础镜像
    """挂载构建时收集器产出的 tar 镜像。"""
    if 文件系统 is None:#默认新建
        文件系统=内存vfs()#新建
    文件系统.注水目录(根)#确保根
    for 条目 in 解析tar(镜像):#逐条目
        相对名=条目['name'][2:] if 条目['name'].startswith('./') else 条目['name']#去点斜杠
        if 相对名.startswith(分隔符):#绝对名非法
            raise 运行时错误(f'webworker vfs: image entry must be relative to {根}, received "{条目["name"]}"')#拒绝
        目标=拼接(根,相对名)#目标路径
        if 条目['directory']:#目录
            文件系统.注水目录(目标,{'mode':条目['mode']})#注水目录
            continue#下一
        文件系统.注水(目标,条目['bytes'],{'mode':条目['mode']})#注水文件
    return 文件系统#返回

def 加载vfs覆盖层(镜像,根,文件系统):#加载覆盖层
    """对已挂载的基础镜像应用一个有序数据覆盖层。"""
    for 条目 in 解析tar(镜像):#逐条目
        相对名=条目['name'][2:] if 条目['name'].startswith('./') else 条目['name']#去点斜杠
        路径=相对名[:-1] if 相对名.endswith('/') else 相对名#去尾斜杠
        段列表=路径.split('/')#路径段
        if (路径=='' or 相对名.startswith(分隔符)#空或绝对
            or any(段=='' or 段=='.' or 段=='..' for 段 in 段列表)#遍历段
            or (段列表[0] if 段列表 else '') not in 镜像覆盖目录列表):#不在白名单
            raise 运行时错误(f'webworker vfs: overlay entry must stay under {"/ or ".join(镜像覆盖目录列表)}, received "{条目["name"]}"')#拒绝
        目标=拼接(根,路径)#目标路径
        if 条目['directory']:#目录
            文件系统.注水目录(目标,{'mode':条目['mode']})#注水目录
            continue#下一
        if 文件系统.存在同步(目标) and 文件系统.统计同步(目标)['isDirectory']():#文件打目录
            raise 运行时错误(f'webworker vfs: overlay file cannot replace directory "{目标}"')#类型冲突
        文件系统.注水(目标,条目['bytes'],{'mode':条目['mode']})#注水文件
    return 文件系统#返回
