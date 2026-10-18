'目录选择缝的浏览后端：一层目录列表和创建子目录，不在宿主屏幕上画任何东西'
import os,sys,re,stat#路径、平台、完全限定与目录探测
from ..目录选择器 import 目录选择器,浏览目录选择能力#缝与浏览能力形状
from ..目录选择器.异常 import 目录选择器错误#带码失败
from ...依赖.schemastery import 自然数字段#maxEntries 的最小与默认
from . import 异常#中止与失败文本

__all__=['完全限定','有界插入','竞争中止','浏览目录选择器','配置','异常']#同目录公开名

# 至少 1，默认 1000。只读字段上的最小和默认，不调用它的校验数据
条目上限字段=自然数字段(最小=1,默认值=1000)#一层子目录行数上限


def 完全限定(路径,平台=None):
    'Windows 只认盘符绝对或完整 UNC。其余平台只认 POSIX 绝对。无盘符有根和不完整 UNC 不算'
    if 平台 is None:#未指定
        平台=sys.platform#当前平台
    if 平台!='win32':#POSIX
        return 路径.startswith('/')#以斜杠开头
    if 路径=='':#空路径
        return False#不是绝对
    首=路径[0]#第一个字符
    是根斜杠=首=='/' or 首=='\\'#以斜杠开头
    是盘符=('A'<=首<='Z' or 'a'<=首<='z') and len(路径)>2 and (路径[2]=='/' or 路径[2]=='\\')#盘符加分隔符
    if not (是根斜杠 or 是盘符):#win32 不绝对
        return False#拒绝
    完全=re.match(r'^(?:[A-Za-z]:[\\/]|[\\/]{2}[^\\/]+[\\/]+[^\\/]+)',路径)#盘符或完整 UNC
    return 完全 is not None#是否匹配


def 有界插入(窗口,候选,保留数):
    '窗口按名升序。满了且候选名不小于队尾则拒绝并记驱逐，否则二分插入，超出则丢掉名最大的'
    if len(窗口)==保留数 and 候选['name']>=窗口[-1]['name']:#不进窗口
        return True#发生驱逐
    下界=0#左端
    上界=len(窗口)#右端
    while 下界<上界:#二分
        中点=(下界+上界)//2#中点
        if 候选['name']<窗口[中点]['name']:#靠前
            上界=中点#收左
        else:#靠后或同名
            下界=中点+1#收右
    窗口.insert(下界,候选)#插入
    if len(窗口)<=保留数:#未超
        return False#无驱逐
    窗口.pop()#丢掉名最大
    return True#发生驱逐


def 吞掉关闭失败(原因=None):
    '调用方已经离开，关闭失败没有接收者'
    return None#不把关闭失败再抛出去


def 竞争中止(操作,信号=None):
    '同步执行操作。没有信号就返回结果。信号已中止时仍执行一次，吞掉操作失败，再抛出中止原因'
    if 信号 is None:#没有寿命
        return 操作()#直接执行
    事先已中止=异常.已中止(信号)#调用前已离开
    try:#执行这一步
        结果=操作()#文件系统步骤
    except Exception as 原因:#步骤失败
        if 事先已中止 or 异常.已中止(信号):#中止不是步骤失败
            raise 异常.作为错误(getattr(信号,'reason',None)) from None#中止原因
        raise 异常.作为错误(原因) from None#步骤自己的错误
    if 事先已中止 or 异常.已中止(信号):#步骤成功但调用方已离开
        raise 异常.作为错误(getattr(信号,'reason',None))#丢掉结果
    return 结果#步骤的值


class 配置模式:
    '一层完整列表最多放上线路的子目录行数'
    def 校验数据(自身,数据=None):
        '缺省 maxEntries 为字段默认值。写出的值必须是大于等于最小的整数，布尔不算'
        if 数据 is None:#没传配置
            数据={}#按缺省
        if not isinstance(数据,dict):#必须是对象
            raise TypeError('directory-picker-browse: 配置必须是对象')#拒绝
        if 'maxEntries' not in 数据:#没写
            值=条目上限字段.默认值#1000
        else:#写了
            值=数据['maxEntries']#原值
        if type(值) is not int or 值<条目上限字段.最小:#不是范围内的整数
            raise TypeError('maxEntries 必须是大于等于 '+str(条目上限字段.最小)+' 的整数')#拒绝
        return {'maxEntries':值}#只留这个键


配置=配置模式()#加载器与类上的 Config 是同一份


class 浏览能力(浏览目录选择能力):
    '这一服务存活期间的稳定 browse 能力。list 与 createDirectory 用所属服务的配置'
    def __init__(自身,服务):
        '记下所属浏览实现'
        自身.服务=服务#配置与身份

    def list(自身,路径=None,信号=None):
        '流式读一层，只保留按名排序的前 maxEntries+1 个目录或符号链接候选'
        家=os.path.expanduser('~')#宿主家目录
        if 路径 is not None and not 完全限定(路径):#不是完全限定
            说明='cannot list "'+路径+'": not a fully qualified path'#拒绝说明
            raise 目录选择器错误('directory-unreadable',路径,说明)#不改基到当前目录
        if 路径 is None:#省略路径
            待解析=家#列家目录
        else:#调用方给了路径
            待解析=路径#已通过完全限定
        目标=os.path.abspath(待解析)#绝对且规范化
        保留=自身.服务.配置['maxEntries']+1#多留一格证明被截断
        窗口=[]#按名窗口
        已驱逐=False#窗口外还有候选
        try:#打开并读完这一层
            句柄={'目录流':None}#打开成功后留下，便于中止时关闭
            def 打开():
                '打开这一层的目录流'
                目录流=os.scandir(目标)#一层
                句柄['目录流']=目录流#交给外层关闭
                return 目录流#句柄
            try:#打开这一步
                层=竞争中止(打开,信号)#已中止则抛中止原因
            except Exception:#打开失败或已中止
                目录流=句柄['目录流']#可能已经打开
                if 目录流 is not None:#放弃的打开还要关
                    try:#关闭
                        目录流.close()#释放
                    except Exception:#关闭失败没有接收者
                        吞掉关闭失败()#吞掉
                raise#原样
            def 读一项():
                '读下一个目录项。这一层读完返回 None'
                try:#下一项
                    return next(层)#目录项
                except StopIteration:#没有更多
                    return None#结束
            try:#逐项读
                while True:#直到读完
                    项=竞争中止(读一项,信号)#已中止则抛
                    if 项 is None:#这一层结束
                        break#停
                    是目录=项.is_dir(follow_symlinks=False)#不跟随
                    是链接=项.is_symlink()#符号链接
                    if (not 是目录) and (not 是链接):#进不去
                        continue#跳过
                    候选={'name':项.name,'isDirectory':是目录,'isSymbolicLink':是链接}#候选
                    if 有界插入(窗口,候选,保留):#放进窗口
                        已驱逐=True#窗外还有
            finally:#无论怎样都关闭
                if 异常.已中止(信号):#已离开则不等关闭失败
                    try:#关闭
                        层.close()#释放
                    except Exception:#没有接收者
                        吞掉关闭失败()#吞掉
                else:#还在
                    层.close()#失败要冒出来
        except Exception as 错误:#文件系统失败
            异常.若中止则抛(信号)#中止不是不可读
            说明='cannot list '+目标+': '+异常.失败文本(错误)#步骤消息
            raise 目录选择器错误('directory-unreadable',目标,说明)#不可读
        条目=[]#可进入行
        截断=已驱逐#已被窗口丢掉则截断
        for 候选 in 窗口:#按名从头到尾
            异常.若中止则抛(信号)#探测前已离开
            名=候选['name']#基名
            子路径=os.path.join(目标,名)#子路径
            可进入=候选['isDirectory']#目录不用再探
            if (not 可进入) and 候选['isSymbolicLink']:#链接要看目标
                def 探测():
                    '跟随符号链接，看目标是不是目录'
                    状态=os.stat(子路径)#跟随链接
                    return stat.S_ISDIR(状态.st_mode)#目标是目录
                try:#探测
                    可进入=竞争中止(探测,信号)#已中止则抛
                except Exception:#坏链接、环或其它失败
                    if 异常.已中止(信号):#探测时已离开
                        异常.若中止则抛(信号)#中止原因
                    可进入=False#不可进入
            if not 可进入:#不是目录
                continue#跳过，不从窗口外回填
            if len(条目)==自身.服务.配置['maxEntries']:#满了
                截断=True#截断
                break#停
            条目.append({'name':名,'path':子路径,'hidden':名.startswith('.')})#POSIX 隐藏惯例
        屑=[]#从根到目标
        当前=目标#游标
        while True:#直到根
            父=os.path.dirname(当前)#父
            if 父==当前:#到根
                名=当前#根屑用完整路径
            else:#普通一截
                名=os.path.basename(当前)#基名
            屑.insert(0,{'name':名,'path':当前,'hidden':False})#前插
            if 父==当前:#根已经记下
                break#停
            当前=父#上移
        return {'path':目标,'home':家,'crumbs':屑,'entries':条目,'truncated':截断}#一层

    def createDirectory(自身,路径,名称):
        '父目录必须完全限定，名字必须是单个路径段。不递归创建'
        if not 完全限定(路径):#父不合法
            说明='cannot create under "'+路径+'": not a fully qualified parent path'#拒绝说明
            raise 目录选择器错误('directory-create-failed',路径,说明)#不改基到当前目录
        父=os.path.abspath(路径)#父的绝对路径
        空白=名称.strip()==''#去掉空白后是空的
        是点=名称=='.' or 名称=='..'#当前或上一级
        有分隔=re.search(r'[/\\]',名称) is not None#含斜杠
        if 空白 or 是点 or 有分隔:#不是单段
            if 空白:#空白段保留原文，避免规范化吃掉末尾空白
                失败路径=os.path.join(父,名称)#说明所关于的路径
            else:#. .. 和带斜杠的段消掉 . 与 ..
                失败路径=os.path.normpath(os.path.join(父,名称))#与 path.join 相同
            说明='"'+名称+'" is not a single path segment'#拒绝说明
            raise 目录选择器错误('directory-create-failed',失败路径,说明)#拒绝
        目标=os.path.join(父,名称)#子目录
        try:#创建
            os.mkdir(目标)#不递归。父目录不存在就是失败
            return 目标#新目录绝对路径
        except FileExistsError:#已存在
            说明=目标+' already exists'#已存在
            raise 目录选择器错误('directory-exists',目标,说明)#已存在
        except OSError as 错误:#其它失败
            说明='cannot create '+目标+': '+异常.失败文本(错误)#步骤消息
            raise 目录选择器错误('directory-create-failed',目标,说明)#创建失败


class 浏览目录选择器(目录选择器):
    'maxEntries 限制单次 list 放上线路的子目录行数，默认 1000'
    Config=配置#插件配置
    def __init__(自身,上下文,配置值):
        '登记 directoryPicker，并留下稳定的 browse 能力对象'
        super().__init__(上下文)#一个上下文只能有一个
        自身.配置=配置值#已校验的 maxEntries
        自身.浏览能力=浏览能力(自身)#稳定能力

    def capability(自身):
        '返回稳定的 browse 能力对象'
        return 自身.浏览能力#同一对象


Config=配置#框架槽
default=浏览目录选择器#类插件
