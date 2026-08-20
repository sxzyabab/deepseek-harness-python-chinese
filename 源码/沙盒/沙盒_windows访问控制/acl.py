"""ACL 编辑辅助：经 SetEntriesInAclW + SetNamedSecurityInfoW 在目录上授予/撤销能力 SID（POC 用的同一组调用，外加 POC 缺少的失败处理）。每次 API 调用都检查，每次失败都带 API 名、精确 Win32 码、格式化系统文本与受影响路径报告。

并发：授权是针对目录当前 DACL 的读-合并-写，整段 get-merge-set 序列跑在按路径的独占 LockFileEx 锁下（见 withPathLock / 持路径锁），因此并发沙箱实例不能互相踩 ACE。
"""
import hashlib,os#哈希与路径
from .ffi import (
    分配重叠结构,#重叠结构
    分配指针槽,#指针槽
    解码指针,#解码指针
    解码偏移无符号8,#读一字节
    解码偏移无符号16,#读WORD
    解码偏移无符号32,#读DWORD
    取临时路径,#临时路径
    是否无效句柄,#无效句柄
    是否空指针,#空指针
    指针地址,#取地址
    同SID于,#SID比较
    抛上次错误,#BOOL失败
    抛Win32,#ERROR_*失败
)#导入FFI辅助
from . import win32_abi as abi#ABI常量

def 构建显式访问(sid指针,模式,权限):#打包显式访问条目
    """打包一条 EXPLICIT_ACCESS_W（48 字节）。"""
    条目=bytearray(abi.显式访问W大小)#48字节条目
    条目[0:4]=权限.to_bytes(4,'little')#grfAccessPermissions
    条目[4:8]=模式.to_bytes(4,'little')#grfAccessMode
    条目[8:12]=abi.子容器与对象继承.to_bytes(4,'little')#grfInheritance:OI|CI
    条目[24:28]=abi.无多重受托人.to_bytes(4,'little')#Trustee.MultipleTrusteeOperation
    条目[28:32]=abi.受托人是SID.to_bytes(4,'little')#Trustee.TrusteeForm
    条目[32:36]=abi.受托人未知.to_bytes(4,'little')#Trustee.TrusteeType
    条目[40:48]=指针地址(sid指针).to_bytes(8,'little')#Trustee.ptstrName=能力SID
    return 条目#已打包条目

def 锁文件路径(接口,路径):#锁文件路径
    """每个受保护路径一个锁文件：`<GetTempPathW()>\\dsh-acl-locks\\<sha256前16位>.lock`。"""
    摘要=hashlib.sha256(路径.lower().encode('utf-8')).hexdigest()[:16]#小写路径哈希前16位
    return os.path.join(取临时路径(接口),'dsh-acl-locks',摘要+'.lock')#临时根下的锁文件

def 持路径锁(接口,路径,动作):#持锁跑动作
    """持有按路径独占锁时跑 `动作`。"""
    锁路径=锁文件路径(接口,路径)#本路径的锁文件
    os.makedirs(os.path.dirname(锁路径),exist_ok=True)#确保锁目录存在
    句柄=接口.createFileW(锁路径,abi.通用读|abi.通用写,abi.共享读|abi.共享写,None,abi.始终打开,0,None)#打开或创建锁文件
    if 是否无效句柄(句柄):#打开失败
        抛上次错误(接口,'CreateFileW',锁路径)#抛出
    重叠=分配重叠结构()#保持清零：偏移0，hEvent NULL
    if 接口.lockFileEx(句柄,abi.独占锁,0,1,0,重叠)==0:#加独占锁失败
        win32码=接口.getLastError()#先记下码
        接口.closeHandle(句柄)#加锁失败路径上尽力关闭
        抛Win32(接口,'LockFileEx',win32码,锁路径)#带码抛出
    try:#跑动作
        结果=动作()#get-merge-set
    except BaseException as 错误:#动作失败
        接口.unlockFileEx(句柄,0,1,0,重叠)#尽力解锁
        接口.closeHandle(句柄)#尽力关闭
        raise 错误#再抛原错误
    if 接口.unlockFileEx(句柄,0,1,0,重叠)==0:#解锁失败
        win32码=接口.getLastError()#先记下码
        接口.closeHandle(句柄)#解锁失败路径上尽力关闭
        抛Win32(接口,'UnlockFileEx',win32码,锁路径)#带码抛出
    if 接口.closeHandle(句柄)==0:#关闭失败
        抛上次错误(接口,'CloseHandle','lock file '+锁路径)#抛出
    return 结果#动作结果

def 读当前DACL(接口,路径):#读当前显式DACL
    """经 GetNamedSecurityInfoW 读目录当前显式 DACL。"""
    所有者槽=分配指针槽()#所有者槽（忽略）
    组槽=分配指针槽()#组槽（忽略）
    dacl槽=分配指针槽()#DACL槽
    sacl槽=分配指针槽()#SACL槽（忽略）
    描述符槽=分配指针槽()#描述符槽
    读结果=接口.getNamedSecurityInfoW(路径,abi.文件对象类型,abi.DACL安全信息,所有者槽,组槽,dacl槽,sacl槽,描述符槽)#读DACL
    if 读结果!=abi.错误成功:#读取失败
        抛Win32(接口,'GetNamedSecurityInfoW',读结果,路径)#抛出
    return {'oldAcl':解码指针(dacl槽),'descriptor':解码指针(描述符槽)}#DACL与所属描述符

def 合并并应用(接口,路径,条目,旧ACL,描述符,标签):#合并并应用DACL
    """把条目合并进旧 ACL，应用后释放分配。"""
    新ACL槽=分配指针槽()#接收合并后ACL
    合并结果=接口.setEntriesInAclW(1,条目,旧ACL,新ACL槽)#合并一条
    if 合并结果!=abi.错误成功:#合并失败
        if 描述符 is not None:#有描述符
            接口.localFree(描述符)#也释放ACL块
        抛Win32(接口,'SetEntriesInAclW',合并结果,标签+'('+路径+')')#带标签抛出
    新ACL=解码指针(新ACL槽)#取出新ACL
    if 新ACL is None:#空指针
        if 描述符 is not None:#有描述符
            接口.localFree(描述符)#释放描述符
        抛Win32(接口,'SetEntriesInAclW',接口.getLastError(),标签+'('+路径+'): null new ACL')#空ACL
    释放描述符=接口.localFree(描述符) if 描述符 is not None else None#释放旧描述符
    应用结果=接口.setNamedSecurityInfoW(路径,abi.文件对象类型,abi.DACL安全信息,None,None,新ACL,None)#应用新DACL
    释放新=接口.localFree(新ACL)#释放合并结果
    if 应用结果!=abi.错误成功:#应用失败
        抛Win32(接口,'SetNamedSecurityInfoW',应用结果,标签+'('+路径+')')#抛出
    if 释放描述符 is not None and not 是否空指针(释放描述符):#释放描述符失败
        抛上次错误(接口,'LocalFree',标签+'('+路径+') descriptor')#抛出
    if not 是否空指针(释放新):#释放新ACL失败
        抛上次错误(接口,'LocalFree',标签+'('+路径+') new ACL')#抛出

def 有精确授予(旧ACL,sid指针):#是否已有精确授权ACE
    """显式 DACL 是否已经携带本模块会加上的那条精确写入授权。"""
    acl大小=解码偏移无符号16(旧ACL,2)#ACL字节大小
    ace条数=解码偏移无符号16(旧ACL,4)#ACE条数
    if acl大小<8 or acl大小>1048576:#不可信：回落到合并路径
        return False#不可信
    偏移=8#第一条ACE跟在8字节ACL头之后
    for _ in range(ace条数):#逐条ACE
        ace大小=解码偏移无符号16(旧ACL,偏移+2)#本ACE大小
        if ace大小<8 or 偏移+ace大小>acl大小:#不可信
            return False#回落到合并路径
        精确=(解码偏移无符号8(旧ACL,偏移)==abi.允许ACE类型#允许ACE
            and 解码偏移无符号8(旧ACL,偏移+1)==abi.子容器与对象继承#OI|CI继承
            and 解码偏移无符号32(旧ACL,偏移+4)==abi.授予掩码)#精确掩码
        if 精确 and 同SID于(旧ACL,偏移+8,sid指针,0):#SID也匹配
            return True#已有
        偏移+=ace大小#下一条
    return False#没有精确匹配

def 授予写入(接口,路径,sid指针):#授予写入ACE
    """在路径上把 GRANT_MASK 授给能力 SID，幂等跳过已常驻精确 ACE。"""
    def 动作():#持锁动作
        当前=读当前DACL(接口,路径)#读当前DACL
        旧ACL=当前['oldAcl']#当前DACL
        描述符=当前['descriptor']#所属描述符
        if 旧ACL is not None and 有精确授予(旧ACL,sid指针):#精确ACE已常驻
            if 描述符 is not None:#有描述符
                释放=接口.localFree(描述符)#只释放描述符
                if not 是否空指针(释放):#释放失败
                    抛上次错误(接口,'LocalFree','grantWrite('+路径+') descriptor')#抛出
            return#跳过再传播
        合并并应用(接口,路径,构建显式访问(sid指针,abi.授予访问,abi.授予掩码),旧ACL,描述符,'grantWrite')#合并授予
    持路径锁(接口,路径,动作)#持锁

def 撤销写入(接口,路径,sid指针):#撤销写入ACE
    """从目录 DACL 去掉能力 SID 的每条 ACE。"""
    def 动作():#持锁动作
        当前=读当前DACL(接口,路径)#读当前DACL
        旧ACL=当前['oldAcl']#当前DACL
        描述符=当前['descriptor']#所属描述符
        if 旧ACL is None:#没有显式DACL
            if 描述符 is not None:#仍可能有描述符
                释放=接口.localFree(描述符)#释放描述符
                if not 是否空指针(释放):#释放失败
                    抛上次错误(接口,'LocalFree','revokeWrite('+路径+') descriptor')#抛出
            return False#未尝试移除
        合并并应用(接口,路径,构建显式访问(sid指针,abi.撤销访问,0),旧ACL,描述符,'revokeWrite')#合并撤销
        return True#已尝试移除
    return 持路径锁(接口,路径,动作)#持锁
