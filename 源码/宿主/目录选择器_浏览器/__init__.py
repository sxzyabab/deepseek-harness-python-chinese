'目录选择缝的浏览后端：一层列表与创建子目录，不在宿主屏幕上画任何东西'
import os,sys,re#路径、平台与完全限定判定
from ..目录选择器 import 目录选择器,目录选择器错误#缝与失败
from ...依赖.schemastery import 自然数字段#配置字段
__all__=['名称','配置','浏览目录选择器','完全限定','有界插入']#仅中文公开名

名称='directory-picker-browse'#插件名
配置={#插件配置
    'maxEntries':自然数字段(最小=1,默认值=1000),#一层最多子目录行数
}#配置结束

def 完全限定(路径,平台=None):#路径是否不依赖进程状态就指向固定位置
    'Windows 只要盘符绝对或完整 UNC；其余平台要 POSIX 绝对'
    if 平台 is None:#未指定
        平台=sys.platform#当前平台
    if 平台=='win32':#Windows
        return re.match(r'^(?:[A-Za-z]:[\\/]|[\\/]{2}[^\\/]+[\\/]+[^\\/]+)',路径) is not None#盘符或 UNC
    return 路径.startswith('/')#POSIX 绝对

def 有界插入(窗口,候选,保留数):#按名插入有界窗口，超出则丢掉名最大的
    '窗口满且候选名不小于队尾时直接拒绝；否则二分插入'
    if len(窗口)==保留数 and 候选['name']>=窗口[-1]['name']:#不进窗口
        return True#发生驱逐
    低=0#下界
    高=len(窗口)#上界
    while 低<高:#二分
        中=(低+高)//2#中点
        if 候选['name']<窗口[中]['name']:#靠前
            高=中#收左
        else:#靠后
            低=中+1#收右
    窗口.insert(低,候选)#插入
    if len(窗口)<=保留数:#未超
        return False#无驱逐
    窗口.pop()#丢掉名最大
    return True#发生驱逐

def 祖先屑(目标):#从文件系统根到目标的面包屑
    '根屑的名字用完整路径'
    屑=[]#面包屑
    当前=目标#游标
    while True:#直到根
        父=os.path.dirname(当前)#父
        名=当前 if 父==当前 or os.path.basename(当前)=='' else os.path.basename(当前)#根用全路径
        屑.insert(0,{'name':名,'path':当前,'hidden':False})#前插
        if 父==当前:#到根
            return 屑#结束
        当前=父#上移

def 消息(错误):#未知抛出的文本
    '取异常消息'
    return str(错误)#消息

class 浏览能力:#稳定的 browse 能力对象
    'list 与 createDirectory 转到所属服务'
    kind='browse'#能力种类
    def __init__(自身,服务):#记下服务
        '能力对象在服务存活期间保持同一身份'
        自身.服务=服务#所属实现

    def list(自身,路径=None,信号=None):#列一层
        '列一层目录'
        return 自身.服务.列出(路径,信号)#转发

    def createDirectory(自身,路径,名称):#建子目录
        '创建单段子目录'
        return 自身.服务.创建目录(路径,名称)#转发

class 浏览目录选择器(目录选择器):#ctx.directoryPicker 的浏览实现
    'maxEntries 限制单次 list 放上线路的子目录行数，默认 1000'
    Config=配置#插件配置
    def __init__(自身,上下文,配置=None):#构造
        '登记服务并留下稳定能力对象'
        super().__init__(上下文)#登记 directoryPicker
        上限=None if 配置 is None else 配置.get('maxEntries')#配置上限
        自身.最大条目=1000 if 上限 is None else 上限#默认一千
        自身.浏览能力=浏览能力(自身)#稳定能力

    def capability(自身):#浏览能力
        '返回稳定的 browse 能力对象'
        return 自身.浏览能力#同一对象

    def 列出(自身,路径=None,信号=None):#列一层
        '流式读目录，只保留按名排序的前 maxEntries+1 个可进入候选'
        家=os.path.expanduser('~')#家目录
        if 路径 is not None and not 完全限定(路径):#不是完全限定
            raise 目录选择器错误('directory-unreadable',路径,'cannot list "'+路径+'": not a fully qualified path')#拒绝
        目标=os.path.abspath(路径 if 路径 is not None else 家)#目标
        保留=自身.最大条目+1#多留一格证明被截断
        窗口=[]#按名窗口
        已驱逐=False#窗口外还有候选
        try:#打开并读
            if 已中止(信号):#调用前已取消
                raise OSError('directory listing was aborted')#中止
            with os.scandir(目标) as 层:#一层
                for 项 in 层:#逐项
                    if 已中止(信号):#读之间取消
                        raise OSError('directory listing was aborted')#中止
                    是目录=项.is_dir(follow_symlinks=False)#目录
                    是链接=项.is_symlink()#符号链接
                    if (not 是目录) and (not 是链接):#进不去
                        continue#跳过
                    候选={'name':项.name,'isDirectory':是目录,'isSymbolicLink':是链接}#候选
                    if 有界插入(窗口,候选,保留):#放进窗口
                        已驱逐=True#窗外还有
        except 目录选择器错误:#业务失败原样
            raise#原样
        except OSError as 错误:#打不开
            if 已中止(信号):#中止不是不可读
                raise#原样
            raise 目录选择器错误('directory-unreadable',目标,'cannot list '+目标+': '+消息(错误))#不可读
        条目=[]#可进入行
        截断=已驱逐#已被窗口丢掉则截断
        for 候选 in 窗口:#逐候选
            if 已中止(信号):#探测前取消
                raise OSError('directory listing was aborted')#中止
            行=目录行(目标,候选['name'],候选['isDirectory'],候选['isSymbolicLink'])#行
            if 行 is None:#不可进入
                continue#跳过
            if len(条目)==自身.最大条目:#满了
                截断=True#截断
                break#停
            条目.append(行)#收下
        return {'path':目标,'home':家,'crumbs':祖先屑(目标),'entries':条目,'truncated':截断}#一层

    def 创建目录(自身,路径,名称):#建子目录
        '父目录必须完全限定，名字必须是单段'
        if not 完全限定(路径):#父不合法
            raise 目录选择器错误('directory-create-failed',路径,'cannot create under "'+路径+'": not a fully qualified parent path')#拒绝
        父=os.path.abspath(路径)#父
        if 名称.strip()=='' or 名称=='.' or 名称=='..' or re.search(r'[/\\]',名称) is not None:#非法段
            raise 目录选择器错误('directory-create-failed',os.path.join(父,名称),'"'+名称+'" is not a single path segment')#拒绝
        目标=os.path.join(父,名称)#子路径
        try:#创建
            os.mkdir(目标)#不递归
            return 目标#绝对路径
        except FileExistsError:#已存在
            raise 目录选择器错误('directory-exists',目标,目标+' already exists')#已存在
        except OSError as 错误:#其它失败
            raise 目录选择器错误('directory-create-failed',目标,'cannot create '+目标+': '+消息(错误))#失败

def 目录行(父,名,是目录,是链接):#一个子项能不能进入
    '普通目录直接进入；符号链接要 stat 到目录；坏链接跳过'
    路径=os.path.join(父,名)#子路径
    可进入=是目录#目录不用再探
    if (not 可进入) and 是链接:#链接要看目标
        try:#stat
            可进入=os.path.isdir(路径)#目标是目录
        except OSError:#坏或环
            return None#跳过
    if not 可进入:#不是目录
        return None#跳过
    return {'name':名,'path':路径,'hidden':名.startswith('.')}#POSIX 隐藏惯例

name=名称#框架槽
Config=配置#框架槽
default=浏览目录选择器#类插件
