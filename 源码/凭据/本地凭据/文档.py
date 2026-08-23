"""凭证 YAML 文档的解析、渲染与仅所有者权限检查。"""
import os,errno,io#路径、错误码与文本流
from ...依赖 import ruamel_yaml#外部依赖胶水（ruamel.yaml）
YAML解析器=ruamel_yaml.YAML#可保留注释的 YAML 往返
带注释映射=ruamel_yaml.comments.CommentedMap#带注释的映射根
YAML错误=ruamel_yaml.error.YAMLError#解析失败
from ..凭据 import 凭证引用#凭证引用校验
from ...工具.工作区路径 import 规范化监视路径#监视路径规范化

凭证文件名='.credentials.yaml'#harness 主目录内凭证文档的基名
组其他人位=0o077#所有者以外的权限位；凭证文档不得带其中任何一位（0600 创建/替换后仍须拒绝 umask 放宽）
字符串流=io.StringIO#把文档序列化进内存

def 补错误码(错误):#给 OSError 补上 Node 风格 code
    """给逃出的 OSError 补上 Node 风格 `code`。"""
    if isinstance(错误,OSError) and getattr(错误,'code',None) is None:#尚无 code
        表={
            errno.ENOENT:'ENOENT',#缺席
            errno.ENOTDIR:'ENOTDIR',#父段不是目录
            errno.EISDIR:'EISDIR',#目标是目录
            errno.EACCES:'EACCES',#拒绝访问
            errno.EPERM:'EPERM',#操作不允许
        }#常见映射
        错误.code=表.get(错误.errno) or errno.errorcode.get(错误.errno) or 'EIO'#写入 code
    return 错误#原错误

def 是否缺席(错误):#文件系统错误是否表示缺席
    """判定缺席错误；每一个非 ENOENT 失败都必须浮出。"""
    if getattr(错误,'code',None)=='ENOENT':#已带缺席码
        return True#缺席
    return isinstance(错误,OSError) and 错误.errno==errno.ENOENT#按 errno 判定

def 断言无空字节(文件名):#拒绝路径里的空字节
    """空字节在到达操作系统之前拒绝，错误码对齐 Node `ERR_INVALID_ARG_VALUE`。"""
    if '\0' in 文件名:#路径含空字节
        错误=ValueError("The argument 'path' must be a string or Uint8Array without null bytes. Received "+repr(文件名))#对齐 Node 非法路径
        错误.code='ERR_INVALID_ARG_VALUE'#Node 非法参数码
        raise 错误#抛出

def 建解析器():#构造往返 YAML 解析器
    """构造保留注释与引号、拒绝重复键的往返解析器。"""
    解析器=YAML解析器(typ='rt')#往返模式
    解析器.allow_duplicate_keys=False#重复键以解析错误浮出
    解析器.preserve_quotes=True#保留原引号样式
    解析器.width=4096#避免把长标量折行
    解析器.explicit_start=False#不要写出文档起始标记
    解析器.explicit_end=False#不要写出文档结束标记
    解析器.default_flow_style=False#块状映射
    解析器.version=(1,2)#YAML 1.2
    return 解析器#解析器

def 描述yaml错误(错误):#把 YAML 错误收成无密钥诊断
    """描述一次 YAML 解析失败，且不引用源文。解析器自己的 message 会嵌进出错行，而这里那一行就是密钥。"""
    标记=getattr(错误,'problem_mark',None)#行列位置
    if 标记 is None:#没有行列
        位置=''#空位置
    else:
        位置=' at line '+str(标记.line+1)+', column '+str(标记.column+1)#1 起算行列
    码=getattr(错误,'code',None)#机器码
    if 码 is None:#没有码则用类型名
        码=type(错误).__name__#类型名
    return str(码)+位置#只返回码与位置

def 解析凭证文档(文本,文件名):#把凭证文档解析成条目
    """把一份凭证文档解析成条目。文档是严格的 CredentialRef 到非空字符串映射：非映射根、非 POSIX 标识符键、非字符串值、空字符串全部拒绝而不是跳过，因为本文件只装凭证，静默忽略一条会读成“我存的键没有效果”。重复键以解析器错误浮出。空文档就是空存储。"""
    # prettyErrors 只为拿行列；从不使用 error.message，因为解析器会引用出错源码行，而本文件里那一行就是密钥。只有错误码和位置离开本函数；本文件所有诊断都遵守同一规则——键名可打印，值不可。
    解析器=建解析器()#往返解析器（拒绝重复键）
    try:#严格唯一键解析
        根=解析器.load(文本)#解析
    except YAML错误 as 错误:#有解析错误
        raise Exception('credentials-local: invalid document at '+文件名+': '+描述yaml错误(错误))#拼无密钥诊断后抛出
    if 根 is None:#空文档当空对象
        根={}#空映射
    if not isinstance(根,dict) or isinstance(根,list):#根必须是映射
        raise TypeError('credentials-local: '+文件名+' must be a mapping of credential reference to value')#拒绝非映射根
    条目={}#收集合法条目
    for 键,值 in 根.items():#逐条检查
        文字键=键 if isinstance(键,str) else str(键)#Object.entries 会把键收成字符串
        # credentialRef 对非 POSIX 标识符抛错，而这正是已存引用要能经能力缝寻址所必须满足的约束。
        凭证引用(文字键)#校验键为合法引用
        # 引用的是键名，从不引用值：类型错误的条目仍是用户想存的密钥。
        if not isinstance(值,str):#值必须是字符串
            raise TypeError('credentials-local: the value for "'+文字键+'" in '+文件名+' must be a string')#拒绝非字符串值
        if len(值)==0:#空值算缺席，不得存
            raise Exception('credentials-local: the value for "'+文字键+'" in '+文件名+' is empty; remove the key instead')#拒绝空串
        条目[文字键]=值#收下合法条目
    return 条目#返回解析结果

def 渲染文档(文本,引用,值):#按条渲染下一份文档
    """渲染下一份文档文本：设置或删除一条引用。编辑已解析文档而不是重建，以保留注释和所有未触碰条目的格式；缺席文档则新开一份。"""
    解析器=建解析器()#往返解析器
    # text 只缓存曾经解析成功的内容，因此这次为可保留注释的可变树再解析不会失败。
    if 文本 is None:#缺席则新文档
        文档=带注释映射()#空映射
    else:
        文档=解析器.load(文本)#再解析可保留注释的树
        if 文档 is None:#空文档
            文档=带注释映射()#空映射
    if 值 is None:#无值则删键
        if 引用 in 文档:#键存在才删
            del 文档[引用]#删键及其注解
    else:
        文档[引用]=值#有值则写入该键
    if len(文档)==0:#空存储写成流式空映射
        return '{}\n'#空映射文本
    流=字符串流()#内存流
    解析器.dump(文档,流)#序列化为文本
    结果=流.getvalue()#取出文本
    if not 结果.endswith('\n'):#文档必须以换行结束
        结果=结果+'\n'#补换行
    return 结果#要持久化的文本

def 读文档文本(文件名):#按 utf8 读文档
    """按 utf8 读取凭证文档全文。"""
    断言无空字节(文件名)#先拒绝空字节
    try:#读文件
        with open(文件名,'r',encoding='utf-8',newline='') as 文件:#按 utf8 打开且不翻译换行
            return 文件.read()#读出全文
    except OSError as 错误:#读失败
        raise 补错误码(错误)#非缺席码必须浮出

def 断言仅所有者(文件名):#断言仅所有者可读
    """在读取内容之前，拒绝其他 OS 用户也能读的凭证文档。提供方以 `0600` 创建和替换该文件，但手写或外部生成的文件带着当时 umask 给的模式；若静默从全局可读文件里提供密钥，提供方承诺的模式就毫无意义。

    仅 POSIX：Windows 没有可检查的 mode——其 ACL 无法在此表达——所以跳过检查而不是伪造；那边的保护就是创建与替换 API 所表达的那套。
    """
    断言无空字节(文件名)#先拒绝空字节
    try:
        模式=os.stat(文件名).st_mode#取出 mode
    except OSError as 错误:
        补错误码(错误)#补 code
        if not 是否缺席(错误):#非缺席则原样抛出
            raise 错误#原样抛出
        规范化监视路径(文件名)#缺席时仍规范化监视路径
        return#无文件则通过（缺席不是越权）
    if os.name=='nt':#Windows 无 POSIX mode 可检
        return#跳过：不伪造 ACL；保护靠创建/替换 API 的 0600
    越权=模式&组其他人位#组/其他人权限位（相对 0600 的 umask 放宽）
    if 越权==0:#没有越权位则通过
        return#通过
    八进制=format(模式&0o777,'o')#权限八进制
    raise Exception('credentials-local: '+文件名+' is readable beyond its owner (mode '+八进制+'); run "chmod 600 '+文件名+'" before starting again')#越权则大声失败
