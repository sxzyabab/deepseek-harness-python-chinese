"""受限令牌构造：打开当前进程令牌，抽出其登录 SID，构建众所周知 SID，并用限制 SID 允许列表调用 CreateRestrictedToken。每次 API 调用都检查；任何失败都带 API 名与精确 Win32 码抛出。"""
import os,ctypes#取pid与缓冲视图
from .ffi import (
    分配字节,#缓冲分配
    分配指针槽,#指针槽
    分配无符号32,#DWORD槽
    解码指针,#解码指针
    解码缓冲内指针,#缓冲内指针
    解码无符号32,#解码DWORD
    编码无符号32,#编码DWORD
    是否空指针,#空指针判定
    指针地址,#地址
    抛上次错误,#BOOL失败
    抛Win32,#ERROR_*失败
)#导入FFI辅助
from .acl import 构建显式访问#显式访问条目打包
from . import win32_abi as abi#ABI常量

def 打开当前进程令牌(接口):#打开当前进程令牌
    """以 CreateRestrictedToken 所需权限打开当前进程的访问令牌。"""
    进程句柄=接口.openProcess(abi.进程查询信息,0,os.getpid())#打开本进程
    if 是否空指针(进程句柄):#打开失败
        抛上次错误(接口,'OpenProcess','pid '+str(os.getpid()))#抛出
    令牌槽=分配指针槽()#接收令牌句柄的槽
    已打开=接口.openProcessToken(进程句柄,abi.令牌查询|abi.令牌复制|abi.令牌调整默认|abi.令牌指派主,令牌槽)#打开令牌
    if 已打开==0:#打开失败
        win32码=接口.getLastError()#先记下码
        接口.closeHandle(进程句柄)#错误路径上尽力关闭
        抛Win32(接口,'OpenProcessToken',win32码,'pid '+str(os.getpid()))#带码抛出
    if 接口.closeHandle(进程句柄)==0:#关掉进程句柄
        抛上次错误(接口,'CloseHandle','OpenProcess process handle')#抛出
    令牌=解码指针(令牌槽)#取出令牌
    if 令牌 is None:#空句柄
        抛Win32(接口,'OpenProcessToken',接口.getLastError(),'null token handle')#空句柄
    return 令牌#已打开令牌

def 查找登录SID(接口,令牌):#抽出登录SID
    """查找并复制令牌的登录会话 SID（SE_GROUP_LOGON_ID）。"""
    所需槽=分配无符号32()#接收所需大小
    接口.getTokenInformation(令牌,abi.令牌组信息,None,0,所需槽)#预期以ERROR_INSUFFICIENT_BUFFER失败
    所需=解码无符号32(所需槽)#所需字节
    if 所需==0:#大小查询失败
        抛上次错误(接口,'GetTokenInformation','TokenGroups size query')#抛出
    if 所需<abi.令牌组偏移:#大小不可信
        抛Win32(接口,'GetTokenInformation',接口.getLastError(),'implausible TokenGroups size '+str(所需))#抛出
    组们=bytearray(所需)#组缓冲
    组缓冲=(ctypes.c_ubyte*所需).from_buffer(组们)#可写ctypes视图
    if 接口.getTokenInformation(令牌,abi.令牌组信息,组缓冲,所需,所需槽)==0:#真正读取失败
        抛上次错误(接口,'GetTokenInformation','TokenGroups')#带码抛出
    组数=int.from_bytes(组们[0:4],'little')#组数
    for 下标 in range(组数):#逐组
        基=abi.令牌组偏移+下标*abi.SID与属性大小#本组偏移
        sid指针=解码缓冲内指针(组们,基)#本组SID
        属性=int.from_bytes(组们[基+8:基+12],'little')#本组属性
        是登录=((属性&abi.组登录标识)&0xFFFFFFFF)==(abi.组登录标识&0xFFFFFFFF)#是否登录SID
        if sid指针 is None or not 是登录:#不是则跳过
            continue#下组
        sid长度=接口.getLengthSid(sid指针)#SID字节长
        if sid长度==0:#长度失败
            抛上次错误(接口,'GetLengthSid','logon SID group '+str(下标))#抛出
        副本=接口.localAlloc(0x40,sid长度)#LMEM_ZEROINIT，供后续LocalFree
        if 是否空指针(副本):#分配失败
            抛上次错误(接口,'LocalAlloc','logon SID group '+str(下标))#抛出
        if 接口.copySid(sid长度,副本,sid指针)==0:#复制失败
            接口.localFree(副本)#释放失败副本
            抛上次错误(接口,'CopySid','logon SID group '+str(下标))#抛出
        return 副本#登录SID副本
    raise Exception('CreateRestrictedToken prerequisite failed: no logon SID found among '+str(组数)+' token groups')#没有登录SID

def 制作众所周知SID(接口,类型):#创建众所周知SID
    """创建一个众所周知 SID（68 字节缓冲）并断言其有效。"""
    sid=接口.localAlloc(0x40,abi.安全最大SID大小)#LMEM_ZEROINIT，供后续LocalFree
    if 是否空指针(sid):#分配失败
        抛上次错误(接口,'LocalAlloc','CreateWellKnownSid type '+str(类型))#抛出
    大小槽=分配无符号32()#进出大小
    编码无符号32(大小槽,abi.安全最大SID大小)#写入容量
    if 接口.createWellKnownSid(类型,None,sid,大小槽)==0:#创建失败
        接口.localFree(sid)#释放失败缓冲
        抛上次错误(接口,'CreateWellKnownSid','type '+str(类型))#带类型抛出
    if 接口.isValidSid(sid)==0:#无效SID
        接口.localFree(sid)#释放无效缓冲
        抛上次错误(接口,'IsValidSid','CreateWellKnownSid type '+str(类型))#抛出
    return sid#有效SID

def 设令牌默认DACL授予(接口,令牌,sid指针):#合并默认DACL授权
    """把 sid 的一条完全访问允许 ACE 合并进令牌的默认 DACL。"""
    所需槽=分配无符号32()#接收所需大小
    接口.getTokenInformation(令牌,abi.令牌默认DACL,None,0,所需槽)#预期以ERROR_INSUFFICIENT_BUFFER失败
    所需=解码无符号32(所需槽)#所需字节
    if 所需==0:#大小查询失败
        抛上次错误(接口,'GetTokenInformation','TokenDefaultDacl size query')#抛出
    缓冲=bytearray(所需)#DACL缓冲
    缓冲视图=(ctypes.c_ubyte*所需).from_buffer(缓冲)#可写视图
    if 接口.getTokenInformation(令牌,abi.令牌默认DACL,缓冲视图,所需,所需槽)==0:#真正读取失败
        抛上次错误(接口,'GetTokenInformation','TokenDefaultDacl')#带码抛出
    当前DACL=解码缓冲内指针(缓冲,0)#当前默认DACL
    if 当前DACL is None:#没有默认DACL
        raise Exception('setTokenDefaultDaclGrant: the token carries no default DACL to extend')#无法扩展
    新DACL槽=分配指针槽()#接收合并后DACL
    结果=接口.setEntriesInAclW(1,构建显式访问(sid指针,abi.授予访问,abi.文件全访问),当前DACL,新DACL槽)#合并一条授权
    if 结果!=abi.错误成功:#合并失败
        抛Win32(接口,'SetEntriesInAclW',结果,'default DACL merge')#抛出
    新DACL=解码指针(新DACL槽)#取出新DACL
    if 新DACL is None:#空指针
        抛Win32(接口,'SetEntriesInAclW',结果,'null merged default DACL')#空指针
    信息=bytearray(8)#指针结构
    信息[0:8]=指针地址(新DACL).to_bytes(8,'little')#写入新DACL指针
    信息视图=(ctypes.c_ubyte*8).from_buffer(信息)#可写视图
    if 接口.setTokenInformation(令牌,abi.令牌默认DACL,信息视图,8)==0:#写入失败
        win32码=接口.getLastError()#先记下码
        接口.localFree(新DACL)#释放合并结果
        抛Win32(接口,'SetTokenInformation',win32码,'TokenDefaultDacl')#带码抛出
    接口.localFree(新DACL)#释放合并结果

def 构建限制SID们(sid们):#打包限制SID数组
    """打包 `SID_AND_ATTRIBUTES[count]`（Attributes 保持 0）。"""
    缓冲=bytearray(abi.SID与属性大小*len(sid们))#数组缓冲
    for 下标,sid in enumerate(sid们):#逐个SID
        偏移=abi.SID与属性大小*下标#条目偏移
        缓冲[偏移:偏移+8]=指针地址(sid).to_bytes(8,'little')#写入SID指针
    return 缓冲#已打包数组

def 创建受限令牌(接口,当前令牌,登录SID,写入SID们,已知,模式):#创建写入受限令牌
    """用按模式选择的限制列表创建写入受限令牌。"""
    if 模式=='read-only':#只读
        限制列表=[登录SID,已知['world']]#保活组
    elif len(写入SID们)==0:#工作区可写却没有写入SID
        raise Exception('createRestrictedToken: workspace-write restricting list requires at least one write SID')#必须至少一条
    else:#workspace-write
        限制列表=[登录SID,已知['world'],*写入SID们]#保活组加能力SID
    限制缓冲=构建限制SID们(限制列表)#打包
    限制视图=(ctypes.c_ubyte*len(限制缓冲)).from_buffer(限制缓冲)#可写视图
    令牌槽=分配指针槽()#接收受限令牌
    已创建=接口.createRestrictedToken(当前令牌,abi.禁用最大特权|abi.受限用户令牌|abi.写入受限,0,None,0,None,len(限制列表),限制视图,令牌槽)#创建受限令牌
    if 已创建==0:#创建失败
        抛上次错误(接口,'CreateRestrictedToken','restricting SIDs: '+str(len(限制列表)))#创建失败
    令牌=解码指针(令牌槽)#取出令牌
    if 令牌 is None:#空句柄
        抛Win32(接口,'CreateRestrictedToken',接口.getLastError(),'null token handle')#空句柄
    return 令牌#受限令牌
