"""宿主文件系统实现。由 realpath 推导的目标身份让别名共享过期守卫，经符号链接的写入更新其目标而不替换链接本身。"""
import os#工作目录与路径判定
import threading#每目标键互斥
from urllib.request import pathname2url#路径转 file URL
from ...依赖.schemastery import 字符串字段,数字字段#配置字段
from .. import 文件系统 as fs#文件系统服务定义与错误
from . import 文件读写#本地 IO 实现

默认diff基准最大字节=10*1024*1024#diff 基准默认 10MiB
缓冲区最大长度=4294967295#Node 64 位 buffer.constants.MAX_LENGTH
字符串最大长度=536870888#Node 64 位 buffer.constants.MAX_STRING_LENGTH
最大diff基准字节=min(缓冲区最大长度,字符串最大长度)#diff 基准不可超过的运行时上限
配置模式={#schemastery 配置模式
    'cwd':字符串字段(默认值=os.getcwd()),#相对路径基准目录，默认进程 cwd
    'diffBasisMaxBytes':数字字段(默认值=默认diff基准最大字节),#diff 基准每侧字节上限
}#Config 模式结束

__all__=['本地文件系统','配置模式','应用','本地文件系统错误']#仅中文公开名；Cordis 槽英文别名不入表

class 已解析配置:#缺省已填满的配置
    """已校验配置（构造前 schemastery 已套用默认值）。"""
    def __init__(自身,工作目录,diff基准最大字节):#保存已解析配置
        """保存已解析配置。"""
        自身.cwd=工作目录#相对路径基准目录
        自身.diffBasisMaxBytes=diff基准最大字节#diff 基准字节上限

class 内部钩子:#本地 IO 测试钩子
    """转发给文件读写的测试钩子，用于原子发布边界。"""

class 本地文件系统错误(Exception):#本包配置非法
    """本地文件系统配置非法；详情保持英文线协议原文。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

def 路径转文件网址(路径):
    """把进程路径编成 file URL。"""
    绝对=os.path.abspath(路径)#绝对路径
    网址路径=pathname2url(绝对)#编成 URL 路径
    if 网址路径.startswith('//'):#UNC 风格
        return 'file:'+网址路径#file: 加双斜杠路径
    return 'file://'+网址路径#普通 file:// URL

class 本地文件系统(fs.文件系统):#本地文件系统后端
    """宿主文件系统后端。读取相对路径从配置 cwd 解析；这是解析默认值，不是包含边界。"""
    Config=配置模式#schemastery 配置模式
    def __init__(自身,ctx,配置):#用上下文与配置构造本地文件系统
        """用上下文与配置构造本地文件系统。"""
        super().__init__(ctx)#注册为文件系统服务
        工作目录=配置['cwd']#基准目录
        上限=配置['diffBasisMaxBytes']#diff 上限
        if isinstance(上限,bool):#布尔不是整数
            raise 本地文件系统错误('fs-local: diffBasisMaxBytes must be a positive safe integer no greater than '+str(最大diff基准字节))#配置非法则加载失败
        if isinstance(上限,float) and 上限.is_integer():#配置入口整值浮点
            上限=int(上限)#收成int
        if not isinstance(上限,int) or 上限<=0 or 上限>9007199254740991 or 上限>最大diff基准字节:#非法上限
            raise 本地文件系统错误('fs-local: diffBasisMaxBytes must be a positive safe integer no greater than '+str(最大diff基准字节))#配置非法则加载失败
        自身.配置=已解析配置(工作目录,上限)#保存已解析配置
        自身.内部=内部钩子()#测试用 IO 钩子
        自身.锁表={}#每目标键的互斥条目
        自身.锁表锁=threading.Lock()#保护锁表本身

    def 带锁(自身,目标键,操作):#按目标键串行执行
        """对 `targetKey` 独占运行操作（每键 FIFO）。"""
        with 自身.锁表锁:#拿锁表互斥
            条目=自身.锁表[目标键] if 目标键 in 自身.锁表 else None#取出该键条目
            if 条目 is None:#尚无条目
                条目={'锁':threading.Lock(),'等待':0}#新建互斥与等待计数
                自身.锁表[目标键]=条目#挂进锁表
            条目['等待']+=1#登记一位等待者
            互斥=条目['锁']#取出该键互斥
        互斥.acquire()#进入该键临界区
        try:#执行本次操作
            return 操作()#返回本次结果或抛出本次错误
        finally:#无论成败都释放并可能摘链
            互斥.release()#离开临界区
            with 自身.锁表锁:#再拿锁表互斥
                条目['等待']-=1#少一位等待者
                if 条目['等待']==0 and 目标键 in 自身.锁表 and 自身.锁表[目标键] is 条目:#没有后来者且仍是自己的条目
                    del 自身.锁表[目标键]#删除锁条目

    def 解析(自身,路径,选项=None):#解析路径为稳定目标
        """解析路径为稳定目标。"""
        if 文件读写.已中止(选项['signal'] if 选项 is not None and 'signal' in 选项 else None):#已中止则拒绝
            raise fs.文件系统错误('resolve aborted','FS_ABORTED')#结构化中止
        工作目录=选项['cwd'] if 选项 is not None and 'cwd' in 选项 else None#可选覆盖 cwd
        if 工作目录 is None:#未覆盖
            工作目录=自身.配置.cwd#用配置 cwd
        本地=文件读写.解析本地目标(工作目录,路径)#相对 cwd 解析本地目标
        if 文件读写.已中止(选项['signal'] if 选项 is not None and 'signal' in 选项 else None):#解析后再查中止
            raise fs.文件系统错误('resolve aborted','FS_ABORTED')#结构化中止
        return {'targetKey':本地['targetKey'],'displayPath':本地['displayPath']}#返回稳定目标

    def 进程路径(自身,目标):#返回执行世界进程路径
        """返回执行世界进程路径。"""
        return str(目标['targetKey'])#本地后端目标键就是 realpath

    def 宿主路径转进程路径(自身,宿主路径):#本地世界把绝对宿主路径收成进程路径
        """本地世界：绝对路径经规范后即进程路径；相对路径无映射。"""
        if not os.path.isabs(宿主路径):#相对路径
            return None#无映射
        return os.path.abspath(宿主路径)#规范绝对路径

    def 文件网址(自身,目标):#返回规范 file URI
        """返回规范 file URI。"""
        return 路径转文件网址(自身.进程路径(目标))#把进程路径编成 file URL

    def 包含(自身,父目标,子目标):#判断 child 是否位于 parent 下
        """判断子目标是否位于父目标之下。"""
        父路径=自身.进程路径(父目标)#父进程路径
        子路径=自身.进程路径(子目标)#子进程路径
        try:#计算相对路径
            相对=os.path.relpath(子路径,父路径)#相对父目录
        except ValueError:#跨盘等无法相对
            return False#不包含
        if 相对=='' or 相对=='.':#同一路径
            return True#包含自身
        return 相对!='..' and not 相对.startswith('..'+os.sep) and not os.path.isabs(相对)#未逃出父目录

    def 状态(自身,目标,信号=None):#读取目标元数据
        """读取目标元数据；不存在时为 None。"""
        if 文件读写.已中止(信号):#已中止则拒绝
            raise fs.文件系统错误('stat aborted','FS_ABORTED')#结构化中止
        信息=文件读写.探测(目标['targetKey'])#跟随链接探测
        if 文件读写.已中止(信号):#探测后再查中止
            raise fs.文件系统错误('stat aborted','FS_ABORTED')#结构化中止
        if 信息 is None:#不存在
            return None#缺失
        return {'version':信息['version'],'type':信息['type'],'size':信息['size']}#返回元数据

    def 链接状态(自身,路径,选项=None,信号=None):#不跟随末段链接的路径元数据
        """不跟随末段链接的路径元数据。"""
        if 文件读写.已中止(信号):#已中止则拒绝
            raise fs.文件系统错误('lstat aborted','FS_ABORTED')#结构化中止
        if len(路径.strip())==0:#空路径视为未找到
            raise fs.文件系统错误('file_path must be a non-empty string','FS_NOT_FOUND')#空路径
        工作目录=选项['cwd'] if 选项 is not None and 'cwd' in 选项 else None#可选覆盖 cwd
        if 工作目录 is None:#未覆盖
            工作目录=自身.配置.cwd#用配置 cwd
        信息=文件读写.不跟随探测(os.path.abspath(os.path.join(工作目录,路径)))#相对 cwd 解析后 lstat
        if 文件读写.已中止(信号):#探测后再查中止
            raise fs.文件系统错误('lstat aborted','FS_ABORTED')#结构化中止
        if 信息 is None:#不存在
            return None#缺失
        return {'version':信息['version'],'type':信息['type'],'size':信息['size']}#返回路径级元数据

    def 读文本(自身,目标,信号=None):#读取整个文本文件
        """读取整个文本文件。"""
        return 文件读写.读整文件文本({'displayPath':目标['displayPath'],'targetKey':目标['targetKey']},信号)#委托文件读写

    def 流文本(自身,目标,信号=None):#流式读取文本
        """流式读取文本。"""
        return 文件读写.流整文件文本({'displayPath':目标['displayPath'],'targetKey':目标['targetKey']},信号)#委托文件读写

    def 读字节(自身,目标,信号,最大字节):#按字节上限读取原始内容
        """按字节上限读取原始内容。"""
        return 文件读写.读整文件字节({'displayPath':目标['displayPath'],'targetKey':目标['targetKey']},信号,最大字节,自身.内部)#委托并传入测试钩子

    def 列目录(自身,目标,信号=None):#列举目录直接子项
        """列举目录直接子项。"""
        条目列表=文件读写.列目录({'displayPath':目标['displayPath'],'targetKey':目标['targetKey']},信号)#委托文件读写列举
        结果=[]#收集目录条目
        for 条目 in 条目列表:#逐项映射
            映射={'name':条目['name'],'type':条目['type'],'target':{'targetKey':条目['target']['targetKey'],'displayPath':条目['target']['displayPath']}}#基础字段
            if 'version' in 条目:#有版本则带上
                映射['version']=条目['version']#版本令牌
            if 'size' in 条目:#有大小则带上
                映射['size']=条目['size']#字节大小
            结果.append(映射)#收入结果
        return 结果#返回目录条目列表

    def 写文本(自身,目标,内容,期望=None,信号=None,沙箱政策=None):#原子写入整文件
        """原子写入整文件。裸后端忽略沙箱政策。"""
        目标键=目标['targetKey']#稳定目标键
        展示路径=目标['displayPath']#面向调用方的路径
        def 操作():#在该目标锁内执行写入
            """在该目标锁内执行写入。"""
            已有=文件读写.探测(目标键)#探测当前是否存在
            if 已有 is not None and 已有['type']!='file':#存在但不是普通文件
                raise fs.文件系统错误(f'cannot write "{展示路径}": not a regular file','FS_NOT_REGULAR_FILE')#拒绝写入非普通文件
            种类=期望['kind'] if 期望 is not None and 'kind' in 期望 else None#写意图种类
            if 种类=='replaceIfVersion':#按版本替换
                if 已有 is None:#已消失视为过期
                    raise fs.文件系统错误(f'cannot write "{展示路径}": file no longer exists','FS_STALE_VERSION')#过期
                if 已有['version']!=期望['version']:#版本不匹配
                    raise fs.文件系统错误(f'cannot write "{展示路径}": file changed since it was read','FS_STALE_VERSION')#内容已变视为过期
            elif 种类=='createIfAbsent' and 已有 is not None:#要创建但已经存在
                raise fs.文件系统错误(f'cannot overwrite existing "{展示路径}" without reading it first','FS_NOT_OBSERVED')#未经观察不得覆盖
            可diff=已有 is not None and len(内容.encode('utf-8'))<自身.配置.diffBasisMaxBytes#值得抓 diff 基准
            之前=文件读写.为diff读文本(目标键,自身.配置.diffBasisMaxBytes,信号) if 可diff else None#尽力读取旧文本或 None
            文件读写.原子写文件(目标键,内容,已有['mode'] if 已有 is not None else None,信号,自身.内部,{'displayPath':展示路径} if 种类=='createIfAbsent' else None)#原子发布
            之后=文件读写.探测(目标键)#写入后再探测版本
            return {#组装写入结果
                'operation':'update' if 已有 is not None else 'create',#已存在则更新否则创建
                'version':自身.写后版本(之后,目标),#写入后版本
                'before':之前,#写入前文本或 None
                'after':文件读写.规范行尾(内容),#写入后文本（LF）
            }#结果结束
        return 自身.带锁(目标键,操作)#在该目标锁内执行

    def 编辑文本(自身,目标,编辑,期望=None,信号=None,沙箱政策=None):#原子字面量编辑
        """原子字面量编辑。裸后端忽略沙箱政策。"""
        目标键=目标['targetKey']#稳定目标键
        展示路径=目标['displayPath']#面向调用方的路径
        def 操作():#在该目标锁内执行编辑
            """在该目标锁内执行编辑。"""
            已有=文件读写.探测(目标键)#探测当前文件
            if 已有 is None:#不存在视为过期
                raise fs.文件系统错误(f'cannot edit "{展示路径}": file changed since it was read','FS_STALE_VERSION')#过期
            if 已有['type']!='file':#非普通文件不可编辑
                raise fs.文件系统错误(f'cannot edit "{展示路径}": not a regular file','FS_NOT_REGULAR_FILE')#非普通文件
            if 期望 is not None and 已有['version']!=期望['version']:#提供了版本但已不匹配
                raise fs.文件系统错误(f'cannot edit "{展示路径}": file changed since it was read','FS_STALE_VERSION')#视为过期
            原始=文件读写.为编辑读取(目标键,展示路径,信号)#读取并做 LF 规范化
            全替换=False#默认只换一处
            if 'replaceAll' in 编辑 and 编辑['replaceAll']:#请求全量替换
                全替换=True#全量
            已编=文件读写.应用字面量编辑(原始['content'],编辑['oldString'],编辑['newString'],全替换,展示路径)#应用字面量替换
            内容=文件读写.恢复行尾(已编['content'],原始['lineEndings'])#写回前恢复原行尾
            文件读写.原子写文件(目标键,内容,已有['mode'],信号,自身.内部)#原子发布编辑后内容
            之后=文件读写.探测(目标键)#编辑后再探测版本
            return {#组装编辑结果
                'version':自身.写后版本(之后,目标),#编辑后版本
                'before':原始['content'],#编辑前 LF 文本
                'after':已编['content'],#编辑后 LF 文本
            }#结果结束
        return 自身.带锁(目标键,操作)#在该目标锁内执行

    def 写后版本(自身,之后,目标):#写入后取版本，缺失则哨兵
        """写入后取版本，缺失则哨兵。"""
        if 之后 is not None:#探测成功
            return 之后['version']#用真实版本
        return fs.版本令牌('missing:'+目标['targetKey'])#否则用缺失哨兵版本

Config=配置模式#Cordis 配置模式
default=本地文件系统#框架槽
