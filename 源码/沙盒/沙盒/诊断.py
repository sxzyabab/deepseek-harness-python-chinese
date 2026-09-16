"""把观察到的沙箱运行器失败与文件效果拒绝分类。"""
import os,stat#工作目录可进入性与目录判定
from errno import EACCES as 权限拒绝,ENOENT as 不存在#可执行解析/权限失败码

__all__=('是否运行器派生失败','分类运行器失败','匹配签名')#仅中文公开名

可执行派生码=frozenset(('EACCES','ENOENT',权限拒绝,不存在))#可执行解析或权限失败

def 可进入工作目录(路径):#调用方拥有的 cwd 能否进入
    """调用方拥有的派生工作目录是否可进入。"""
    try:#独立检查，不与 spawn 原子
        信息=os.stat(路径)#取元数据
        if not stat.S_ISDIR(信息.st_mode):#不是目录
            return False#不可用
        return os.access(路径,os.X_OK)#进入位成立才可用
    except OSError:#缺失或无权
        return False#不可用

def 是否运行器派生失败(错误,运行器程序,工作目录):#是否运行器 spawn 失败
    """仅在可进入 cwd 下把 ENOENT/EACCES 归到 argv[0] 运行器。"""
    if 运行器程序 is None or not 可进入工作目录(工作目录):#无程序或 cwd 不可用
        return False#证据不足
    if not isinstance(错误,OSError):#非 OS 错误
        return False#不是派生失败
    码=错误.errno#数值码
    名=getattr(错误,'winerror',None)#Windows 码不参与
    码名=errno名(码)#EACCES/ENOENT 名
    if 码 not in 可执行派生码 and 码名 not in 可执行派生码:#不是那两个码
        return False#不是
    系统调用=getattr(错误,'syscall',None)#系统调用名
    if not isinstance(系统调用,str):#无线程级 syscall 字段时用 errno 形态
        系统调用=None#下面按路径判定
    错误路径=getattr(错误,'filename',None)#错误路径
    精确='spawn '+运行器程序#精确 syscall 文案
    if 错误路径 is None:#无路径则要求 syscall 精确
        return 系统调用==精确#精确匹配
    if not isinstance(错误路径,str) or len(错误路径)==0 or 错误路径!=运行器程序:#路径必须就是运行器
        return False#不是运行器
    return 系统调用 is None or 系统调用=='spawn' or 系统调用==精确#路径命中

def errno名(码):#errno 到名
    """把 errno 整数映射成 EACCES/ENOENT 名。"""
    if 码==权限拒绝:#EACCES
        return 'EACCES'#名
    if 码==不存在:#ENOENT
        return 'ENOENT'#名
    return ''#其它

def 分类运行器失败(退出码,标准错误,规则表):#按规则分类
    """按选定后端的结构化运行器失败规则分类一次已结算进程。"""
    if 退出码 is None or 退出码==0:#信号终止或成功
        return None#证据不足
    行列表=标准错误.split('\n')#按 LF 拆
    规范化=[]#去掉 CR
    for 行 in 行列表:#逐行
        if 行.endswith('\r'):#CRLF
            规范化.append(行[:-1])#去 CR
        else:#LF
            规范化.append(行)#原行
    for 规则 in 规则表:#逐条规则
        if 'allowedExitCodes' in 规则 and 退出码 not in 规则['allowedExitCodes']:#退出码门
            continue#跳过
        信息行=set()#应排除的信息行
        if 'informationalLines' in 规则 and 规则['informationalLines'] is not None:#有信息行
            for 项 in 规则['informationalLines']:#逐条
                信息行.add(项.lower())#大小写不敏感精确相等
        致命=[]#有效致命签名
        for 签名 in 规则['fatalSignatures']:#逐签名
            if len(签名.strip())>0:#空白不算证据
                致命.append(签名.lower())#小写
        for 行 in 规范化:#逐行
            小写=行.lower()#小写
            if 小写 in 信息行:#信息行排除
                continue#跳过
            for 签名 in 致命:#致命子串
                if 签名 in 小写:#命中
                    return {'detail':行}#原行
    return None#未命中

def 匹配签名(退出码,标准错误,签名表):#大小写不敏感子串
    """非零退出且 stderr 命中任一签名。"""
    if 退出码 is None or 退出码==0:#成功或信号
        return False#否
    小写=标准错误.lower()#小写
    for 签名 in 签名表:#逐签名
        if 签名.lower() in 小写:#命中
            return True#是
    return False#否
