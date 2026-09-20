import posixpath#远端 POSIX 相对路径
from ...依赖.工具 import 路径转文件url,二进制#file URL 与 base64
from ...工具.超时 import 若已中止则抛出,已中止#中止
from ...文件系统.文件系统 import 文件系统,文件系统错误#文件系统缝
from ..ssh.模式 import (#辅助 JSON 模式
    目标模式,#目标
    信息可空模式,#stat
    路径信息可空模式,#lstat
    文本流标识模式,#流 id
    目录项模式,#列举
    写结果模式,#写
    编辑结果模式,#编辑
)#模式结束
from ..ssh.协议 import 远程操作错误,ssh错误

__all__=['ssh文件系统','依赖']

依赖=['ssh','sandboxPolicy']

错误码表={#可提升为文件系统错误的码
    'FS_NOT_FOUND':True,'FS_NOT_DIRECTORY':True,'FS_NOT_TEXT':True,'FS_NOT_REGULAR_FILE':True,
    'FS_TOO_LARGE':True,'FS_PERMISSION_DENIED':True,'FS_SANDBOX_DENIED':True,'FS_IO_ERROR':True,
    'FS_STALE_VERSION':True,'FS_NOT_OBSERVED':True,'FS_AMBIGUOUS_EDIT':True,'FS_EDIT_NOT_FOUND':True,'FS_ABORTED':True,
}#码表结束

class ssh文件系统(文件系统):#远端文件系统
    """与 SSH 子进程和沙箱提供方配对。"""
    inject=依赖
    def 沙箱模式(自身):#部署默认
        """读 sandboxPolicy.defaultMode。"""
        return 自身.所属上下文.sandboxPolicy.defaultMode#默认模式
    def 解析(自身,路径,选项=None):#远端规范化
        """fs.resolve。"""
        工作目录=选项['cwd'] if 选项 is not None and 'cwd' in 选项 else None#cwd
        信号=选项['signal'] if 选项 is not None and 'signal' in 选项 else None#信号
        参数={'path':路径}#请求
        if 工作目录 is not None:#有 cwd
            参数['cwd']=工作目录#cwd
        return 自身.调用('fs.resolve',参数,目标模式,信号)#目标
    def 进程路径(自身,目标):#远端进程路径
        """targetKey 字符串。"""
        return str(目标['targetKey'])#路径
    def 文件网址(自身,目标):#file URI
        """同一远端命名空间。"""
        return 路径转文件url(自身.进程路径(目标))#URI
    def 包含(自身,父目标,子目标):#规范包含
        """POSIX 相对路径判定。"""
        路径=posixpath.relpath(自身.进程路径(子目标),自身.进程路径(父目标))#相对
        if 路径=='.':#自身
            路径=''#空
        return 路径=='' or (not 路径.startswith('../') and 路径!='..' and not posixpath.isabs(路径))#包含
    def 状态(自身,目标,信号=None):#stat
        """缺失则空。"""
        return 自身.调用('fs.stat',{'target':目标},信息可空模式,信号)#信息
    def 链接状态(自身,路径,选项=None,信号=None):#lstat
        """不跟随末段链接。"""
        工作目录=选项['cwd'] if 选项 is not None and 'cwd' in 选项 else None#cwd
        参数={'path':路径}#请求
        if 工作目录 is not None:#有 cwd
            参数['cwd']=工作目录#cwd
        return 自身.调用('fs.lstat',参数,路径信息可空模式,信号)#路径信息
    def 读文本(自身,目标,信号=None):#整文件文本
        """fs.readText。"""
        def 字符串(值):#z.string
            """须为字符串。"""
            if not isinstance(值,str):#非法
                raise ssh错误('expected string')#失败
            return 值#文本
        return 自身.调用('fs.readText',{'target':目标},字符串,信号)#文本
    def 流文本(自身,目标,信号=None):#分块文本
        """有界拉取；提前停止关远端迭代器。"""
        标识=自身.调用('fs.stream',{'target':目标},文本流标识模式,信号)#流 id
        def 迭代():#生成器
            """fs.next 直到 done。"""
            已结束=False#是否自然结束
            try:#拉取
                while not 已结束:#未结束
                    若已中止则抛出(信号)#中止
                    def 下一块(值):#done/value
                        """严格两字段。"""
                        if not isinstance(值,dict) or 'done' not in 值 or 'value' not in 值:#缺
                            raise ssh错误('expected stream chunk')#失败
                        if not isinstance(值['done'],bool) or not isinstance(值['value'],str):#类型
                            raise ssh错误('expected stream chunk fields')#失败
                        return 值#块
                    下=自身.调用('fs.next',{'id':标识},下一块,信号)#下一块
                    已结束=下['done']#结束?
                    if len(下['value'])>0:#有内容
                        yield 下['value']#块
            finally:#未结束则关
                if not 已结束:#消费方停
                    def 空(值):#z.null
                        """须为空。"""
                        return 值#空
                    try:#关流
                        自身.调用('fs.streamClose',{'id':标识},空)#关
                    except (远程操作错误,ssh错误,OSError):
                        pass
            return
        return 迭代()#迭代器
    def 读字节(自身,目标,信号,最大字节):#原始字节
        """base64 解码。"""
        def base64值(值):#z.base64
            """规范 base64。"""
            if not isinstance(值,str):#非法
                raise ssh错误('expected base64')#失败
            return 值#文本
        return 二进制.从base64(自身.调用('fs.readBytes',{'target':目标,'maxBytes':最大字节},base64值,信号))#字节
    def 读字节范围(自身,目标,范围,信号=None):#窗口
        """offset/length。"""
        def base64值(值):#z.base64
            """规范 base64。"""
            if not isinstance(值,str):#非法
                raise ssh错误('expected base64')#失败
            return 值#文本
        参数={'target':目标,'offset':范围['offset'],'length':范围['length']}#请求
        return 二进制.从base64(自身.调用('fs.readRange',参数,base64值,信号))#字节
    def 列目录(自身,目标,信号=None):#列举
        """fs.list。"""
        return 自身.调用('fs.list',{'target':目标},目录项模式,信号)#项
    def 写文本(自身,目标,内容,期望=None,信号=None,沙箱政策=None):#原子写
        """把已解析政策发给辅助程序。"""
        政策=沙箱政策 if 沙箱政策 is not None else 自身.所属上下文.sandboxPolicy.解析()#政策
        参数={'target':目标,'content':内容,'policy':政策}#请求
        if 期望 is not None:#意图
            参数['expected']=期望#守卫
        return 自身.调用('fs.write',参数,写结果模式,信号)#结果
    def 编辑文本(自身,目标,编辑,期望=None,信号=None,沙箱政策=None):#原子编辑
        """字面量编辑。"""
        政策=沙箱政策 if 沙箱政策 is not None else 自身.所属上下文.sandboxPolicy.解析()#政策
        参数={'target':目标,'edit':编辑,'policy':政策}#请求
        if 期望 is not None:#版本
            参数['expected']=期望#守卫
        return 自身.调用('fs.edit',参数,编辑结果模式,信号)#结果
    def 调用(自身,方法,参数,模式,信号=None):#包装 ssh.请求
        """远端操作错误提升为文件系统错误。"""
        try:#请求
            return 自身.所属上下文.ssh.请求(方法,参数,模式,信号)#请求
        except 远程操作错误 as 错误:#带码
            if 错误.code is not None and 错误.code in 错误码表:#已知码
                raise 文件系统错误(str(错误),错误.code,{'cause':错误})#提升
            码='FS_ABORTED' if 已中止(信号) else 'FS_IO_ERROR'#回落码
            raise 文件系统错误(str(错误),码,{'cause':错误})#包装
        except ssh错误 as 错误:
            码='FS_ABORTED' if 已中止(信号) else 'FS_IO_ERROR'
            raise 文件系统错误(str(错误),码,{'cause':错误})

inject=依赖
default=ssh文件系统
