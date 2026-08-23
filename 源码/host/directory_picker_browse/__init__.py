"""目录选择缝的 browse 后端：把 `ctx.directoryPicker` 登记为 `browse` 能力。

对齐上游 `@deepseek-ai/dsh-host-directory-picker-browse`。公开面仅中文名。经标准库在宿主文件系统上做一层目录列举与子目录创建。宿主显示器上不渲染任何内容。本包默认导出服务类。
"""
import os,re,sys#路径、正则、平台
from ...依赖 import schemastery#外部依赖胶水
模式=schemastery.模式#配置模式
from ..directory_picker import 目录选择器,目录选择错误#缝定义与业务失败
from .列举 import (
    完全限定,#路径围栏
    有界插入,#有界窗口
    竞速中止,#中止竞速
    祖先面包屑,#面包屑
    目录行,#可进入行
    列举候选,#候选形状
)#列举辅助

__all__=['浏览目录选择器','完全限定','有界插入','竞速中止','列举候选']#仅中文公开名

配置=模式.对象({#插件配置模式
    'maxEntries':模式.自然数().最小(1).默认(1000),#完整结果上限，默认 1000
})#配置结束

class 浏览目录选择器(目录选择器):#browse 后端
    """`ctx.directoryPicker` 的 browse 实现（服务生命周期内能力对象稳定）。"""
    Config=配置#Cordis 配置模式
    配置=配置#中文别名

    def __init__(自身,上下文,配置值):#按上下文与已校验配置构造
        """登记为 ctx.directoryPicker 并钉住稳定 browse 能力。"""
        super().__init__(上下文)#登记服务
        自身.配置值=配置值#已校验配置
        def 列举(路径=None,信号=None):#列举一层
            """转给实例列举。"""
            return 自身.列举(路径,信号)#实例方法
        def 创建目录(路径,名称):#创建子目录
            """转给实例创建。"""
            return 自身.创建目录(路径,名称)#实例方法
        自身.浏览能力={'kind':'browse','list':列举,'createDirectory':创建目录}#稳定能力对象

    def capability(自身):#browse 交互能力
        """返回稳定的 browse 能力对象。"""
        return 自身.浏览能力#同一对象

    def 列举(自身,路径=None,信号=None):#列举一层目录；缺省列举主目录
        """列举一层目录；缺省列举主目录。拒绝未完全限定路径。"""
        主目录=os.path.expanduser('~')#宿主账户主目录
        if 路径 is not None and not 完全限定(路径):#未完全限定
            raise 目录选择错误('directory-unreadable',路径,'cannot list "'+路径+'": not a fully qualified path')#拒绝
        目标=os.path.abspath(路径 if 路径 is not None else 主目录)#规范化目标
        保留=取字段(自身.配置值,'maxEntries')+1#窗口容量：完整上限再加一格
        窗口=[]#名称升序的有界候选窗
        已驱逐=False#是否有候选被挤出
        try:#打开目录、读完、关闭
            打开=竞速中止(_打开目录(目标),信号)#打开与中止竞速
            try:#逐条读
                for 项 in 打开:#逐条目
                    if 信号 is not None and getattr(信号,'aborted',False):#已中止
                        raise 收成错误(getattr(信号,'reason',None) or Exception('aborted'))#抛中止
                    是目录=项.is_dir(follow_symlinks=False) if hasattr(项,'is_dir') else False#dirent 目录
                    是链接=项.is_symlink() if hasattr(项,'is_symlink') else os.path.islink(os.path.join(目标,项.name))#符号链接
                    if (not 是目录) and (not 是链接):#不可进入候选
                        continue#跳过文件
                    候选={'name':项.name,'isDirectory':是目录,'isSymbolicLink':是链接}#窗口所需事实
                    if 有界插入(窗口,候选,保留):#插入；驱逐则截断
                        已驱逐=True#标记
            finally:#关句柄
                if hasattr(打开,'close'):#可关闭
                    打开.close()#关闭
        except BaseException as 错误:#打开或读取失败
            if 信号 is not None and getattr(信号,'aborted',False):#中止
                raise 收成错误(getattr(信号,'reason',None) or 错误)#中止原因
            raise 目录选择错误('directory-unreadable',目标,'cannot list '+目标+': '+说明(错误))#不可列举
        条目们=[]#最终上线行
        截断=已驱逐#窗外驱逐则截断
        上限=取字段(自身.配置值,'maxEntries')#完整上限
        for 候选 in 窗口:#按名称探测
            if 信号 is not None and getattr(信号,'aborted',False):#探测前中止
                raise 收成错误(getattr(信号,'reason',None) or Exception('aborted'))#抛中止
            行=目录行(目标,候选['name'],候选['isDirectory'],候选['isSymbolicLink'],信号)#跟随链接
            if 行 is None:#不可进入
                continue#跳过
            if len(条目们)==上限:#已达上限
                截断=True#标记截断
                break#停
            条目们.append(行)#收下
        return {'path':目标,'home':主目录,'crumbs':祖先面包屑(目标),'entries':条目们,'truncated':截断}#列举结果

    def 创建目录(自身,路径,名称):#在已存在父目录下创建一层子目录
        """非递归创建；拒绝未完全限定父路径与非法段名。"""
        if not 完全限定(路径):#父路径未限定
            raise 目录选择错误('directory-create-failed',路径,'cannot create under "'+路径+'": not a fully qualified parent path')#拒绝
        父=os.path.abspath(路径)#规范化父路径
        if 名称.strip()=='' or 名称=='.' or 名称=='..' or re.search(r'[/\\]',名称):#非法段
            raise 目录选择错误('directory-create-failed',os.path.join(父,名称),'"'+名称+'" is not a single path segment')#拒绝
        目标=os.path.join(父,名称)#将创建路径
        try:#非递归创建
            os.mkdir(目标)#只创建这一层
            return 目标#返回绝对路径
        except FileExistsError:#已存在
            raise 目录选择错误('directory-exists',目标,目标+' already exists')#业务码
        except BaseException as 错误:#其它失败
            raise 目录选择错误('directory-create-failed',目标,'cannot create '+目标+': '+说明(错误))#包装

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#值
        return 缺省#缺席
    return getattr(对象,键,缺省)#属性

def 说明(错误):#未知失败说明文本
    """从未知失败取出说明文本。"""
    if isinstance(错误,BaseException):#异常
        return str(错误) or type(错误).__name__#消息或类型名
    return str(错误)#其它

def 收成错误(值):#规范未知抛出
    """把未知抛出值强制成 Exception。"""
    if isinstance(值,BaseException):#已是
        return 值#原样
    return Exception(str(值))#包装

def _打开目录(目标):#打开目录迭代器
    """打开目录条目迭代器。"""
    return os.scandir(目标)#scandir
