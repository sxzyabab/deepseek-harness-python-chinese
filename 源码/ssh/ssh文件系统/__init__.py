import posixpath#远端 POSIX 相对路径
from ...依赖.工具 import 路径转文件url,二进制#file URL 与 base64
from ...基础设施.js特性 import PromiseEX as 期约#流文本迭代器返回的期约
from ...文件系统.文件系统 import 文件系统#文件系统缝
from ...文件系统.文件系统.异常 import 文件系统错误#文件系统缝
from ..ssh.模式 import (#辅助 JSON 模式
    目标模式,#目标
    信息可空模式,#stat
    路径信息可空模式,#lstat
    文本流标识模式,#流 id
    目录项模式,#列举
    写结果模式,#写
    编辑结果模式,#编辑
)#模式结束
from ..ssh.异常 import 远程操作错误,ssh错误#基类与带码远端错误

__all__=['ssh文件系统','依赖']

依赖=['ssh','sandboxPolicy']

错误码表={#可提升为文件系统错误的码
    'FS_NOT_FOUND':True,'FS_NOT_DIRECTORY':True,'FS_NOT_TEXT':True,'FS_NOT_REGULAR_FILE':True,
    'FS_TOO_LARGE':True,'FS_PERMISSION_DENIED':True,'FS_SANDBOX_DENIED':True,'FS_IO_ERROR':True,
    'FS_STALE_VERSION':True,'FS_NOT_OBSERVED':True,'FS_AMBIGUOUS_EDIT':True,'FS_EDIT_NOT_FOUND':True,'FS_ABORTED':True,
}#码表结束

class ssh文件系统(文件系统):#远端文件系统
    '与 SSH 子进程和沙箱提供方配对'
    inject=依赖
    def 沙箱模式(自身):#部署默认
        '读 sandboxPolicy.defaultMode'
        return 自身.所属上下文.sandboxPolicy.defaultMode#默认模式
    def 解析(自身,路径,选项=None):#远端规范化
        工作目录=选项['cwd'] if 选项 is not None and 'cwd' in 选项 else None#cwd
        信号=选项['signal'] if 选项 is not None and 'signal' in 选项 else None#信号
        参数={'path':路径}#请求
        if 工作目录 is not None:#有 cwd
            参数['cwd']=工作目录#cwd
        return 自身.调用('fs.resolve',参数,目标模式,信号)#目标
    def 进程路径(自身,目标):#远端进程路径
        'targetKey 字符串'
        return str(目标['targetKey'])#路径
    def 文件网址(自身,目标):#file URI
        '同一远端命名空间'
        return 路径转文件url(自身.进程路径(目标))#URI
    def 包含(自身,父目标,子目标):#规范包含
        'POSIX 相对路径判定'
        路径=posixpath.relpath(自身.进程路径(子目标),自身.进程路径(父目标))#相对
        if 路径=='.':#自身
            路径=''#空
        return 路径=='' or (not 路径.startswith('../') and 路径!='..' and not posixpath.isabs(路径))#包含
    def 状态(自身,目标,信号=None):#stat
        '缺失则空'
        return 自身.调用('fs.stat',{'target':目标},信息可空模式,信号)#信息
    def 链接状态(自身,路径,选项=None,信号=None):#lstat
        '不跟随末段链接'
        工作目录=选项['cwd'] if 选项 is not None and 'cwd' in 选项 else None#cwd
        参数={'path':路径}#请求
        if 工作目录 is not None:#有 cwd
            参数['cwd']=工作目录#cwd
        return 自身.调用('fs.lstat',参数,路径信息可空模式,信号)#路径信息
    def 读文本(自身,目标,信号=None):#整文件文本
        def 字符串(值):#z.string
            '须为字符串'
            if not isinstance(值,str):#非法
                raise ssh错误('expected string')#失败
            return 值#文本
        return 自身.调用('fs.readText',{'target':目标},字符串,信号)#文本
    def 流文本(自身,目标,信号=None):#分块文本
        """有界拉取；提前停止关远端迭代器。
        返回期约，兑现异步迭代器：下一个() 返回期约，兑现下一块文本，流结束时兑现 None；
        返回() 在流未自然结束时关远端迭代器，返回期约
        """
        def 空(值):#z.null
            '须为空'
            return 值#空
        def 建迭代器(标识):
            'fs.stream 兑现后，用远端流 id 组装迭代器'
            已结束=False#是否自然结束
            def 下一块(值):#done/value
                '严格两字段'
                if not isinstance(值,dict) or 'done' not in 值 or 'value' not in 值:#缺
                    raise ssh错误('expected stream chunk')#失败
                if not isinstance(值['done'],bool) or not isinstance(值['value'],str):#类型
                    raise ssh错误('expected stream chunk fields')#失败
                return 值#块
            def 下一个():
                '拉取下一块非空文本；远端 done 后兑现 None'
                nonlocal 已结束#改外层
                拉取结果=期约()#本次拉取
                if 已结束:#已自然结束
                    拉取结果.解决(None)#没有更多
                    return 拉取结果#已落定
                try:#中止检查
                    若已中止则抛出(信号)#中止
                except Exception as 错误:#已中止
                    拉取结果.拒绝(错误)#拒绝
                    return 拉取结果#已落定
                def 收到块(下):
                    '远端块兑现：记结束；空块（含最后一块）继续拉，非空块交出'
                    nonlocal 已结束#改外层
                    已结束=下['done']#结束?
                    if len(下['value'])>0:#有内容
                        拉取结果.解决(下['value'])#块
                        return#已落定
                    if 已结束:#结束且无内容
                        拉取结果.解决(None)#没有更多
                        return#已落定
                    下一个().然后(拉取结果.解决,拉取结果.拒绝)#跳过空块继续拉
                自身.调用('fs.next',{'id':标识},下一块,信号).然后(收到块,拉取结果.拒绝)#下一块
                return 拉取结果#期约
            def 返回():
                '消费方提前停止：流未自然结束则关远端迭代器，关失败不影响调用方'
                关闭结果=期约()#关流结果
                if 已结束:#已自然结束
                    关闭结果.解决(None)#无需关
                    return 关闭结果#已落定
                def 关流已结算(落定值):
                    '关流不论成败都算结束，上游同样吞掉失败'
                    关闭结果.解决(None)#完
                自身.调用('fs.streamClose',{'id':标识},空).然后(关流已结算,关流已结算)#关
                return 关闭结果#期约
            return type('文本流迭代器',(),{'下一个':staticmethod(下一个),'返回':staticmethod(返回)})()#异步迭代器
        return 自身.调用('fs.stream',{'target':目标},文本流标识模式,信号).然后(建迭代器)#流 id
    def 读字节(自身,目标,信号,最大字节):#原始字节
        'base64 解码，返回期约，兑现字节'
        def base64值(值):#z.base64
            '规范 base64'
            if not isinstance(值,str):#非法
                raise ssh错误('expected base64')#失败
            return 值#文本
        return 自身.调用('fs.readBytes',{'target':目标,'maxBytes':最大字节},base64值,信号).然后(二进制.从base64)#字节
    def 读字节范围(自身,目标,范围,信号=None):#窗口
        'offset/length，返回期约，兑现字节'
        def base64值(值):#z.base64
            '规范 base64'
            if not isinstance(值,str):#非法
                raise ssh错误('expected base64')#失败
            return 值#文本
        参数={'target':目标,'offset':范围['offset'],'length':范围['length']}#请求
        return 自身.调用('fs.readRange',参数,base64值,信号).然后(二进制.从base64)#字节
    def 列目录(自身,目标,信号=None):#列举
        return 自身.调用('fs.list',{'target':目标},目录项模式,信号)#项
    def 写文本(自身,目标,内容,期望=None,信号=None,沙箱政策=None):#原子写
        '把已解析政策发给辅助程序'
        政策=沙箱政策 if 沙箱政策 is not None else 自身.所属上下文.sandboxPolicy.解析()#政策
        参数={'target':目标,'content':内容,'policy':政策}#请求
        if 期望 is not None:#意图
            参数['expected']=期望#守卫
        return 自身.调用('fs.write',参数,写结果模式,信号)#结果
    def 编辑文本(自身,目标,编辑,期望=None,信号=None,沙箱政策=None):#原子编辑
        '字面量编辑'
        政策=沙箱政策 if 沙箱政策 is not None else 自身.所属上下文.sandboxPolicy.解析()#政策
        参数={'target':目标,'edit':编辑,'policy':政策}#请求
        if 期望 is not None:#版本
            参数['expected']=期望#守卫
        return 自身.调用('fs.edit',参数,编辑结果模式,信号)#结果
    def 调用(自身,方法,参数,模式,信号=None):#包装 ssh.请求
        '返回期约，兑现经模式校验的结果；远端操作错误拒绝为文件系统错误'
        def 提升错误(错误):
            '带码远端错误提升为文件系统错误，其余 SSH 错误按中止与否包装，别的错误原样'
            if isinstance(错误,远程操作错误):#带码
                if 错误.code is not None and 错误.code in 错误码表:#已知码
                    raise 文件系统错误(str(错误),错误.code,{'cause':错误})#提升
                码='FS_ABORTED' if 已中止(信号) else 'FS_IO_ERROR'#回落码
                raise 文件系统错误(str(错误),码,{'cause':错误})#包装
            if isinstance(错误,ssh错误):#传输或校验失败
                码='FS_ABORTED' if 已中止(信号) else 'FS_IO_ERROR'#回落码
                raise 文件系统错误(str(错误),码,{'cause':错误})#包装
            raise 错误#原样
        return 自身.所属上下文.ssh.请求(方法,参数,模式,信号).捕获(提升错误)#请求

inject=依赖
default=ssh文件系统
