"""内部沙箱结果分类辅助。

对齐上游 `@deepseek-ai/dsh-bash-sandbox/helpers`。包内细节，不经包根再导出；公开面仅中文名。
"""
import os,stat,re#目录探测、文件类型与按行拆分

__all__=(#仅中文名（供本包与测试直接引用；包根不 re-export）
    '是否启动器拉起失败',#spawn 阶段运行器证据
    '分类拒绝',#政策拒绝
    '分类启动器失败',#已结算运行器失败
    '匹配特征',#stderr 签名匹配
)#公开面结束

可执行拉起码=set(('EACCES','ENOENT'))#已证明标识可执行解析或权限失败的 Node 本地 spawn 码

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 工作目录可用(路径):#工作目录是否可进入
    """调用方拥有的 spawn cwd 是否可以进入。"""
    try:#stat/access 可能因缺失或无权限失败
        if not stat.S_ISDIR(os.stat(路径).st_mode):#不是目录
            return False#不是目录
        if not os.access(路径,os.X_OK):#需要执行许可才能进入
            return False#不可进入
        return True#可进入
    except Exception:#缺失、不是目录或不可进入；只有这类抛出能到这里
        return False#不可用

def 是否启动器拉起失败(错误,运行器程序,工作目录):#是否运行器 spawn 失败
    """只把在独立排除调用方拥有 cwd 之后、错误路径等于 argv[0] 的 Node ENOENT/EACCES 失败归给运行器。

    提供的错误路径必须精确标识运行器；没有路径时系统调用必须标识。cwd 可用时，这些码描述对该 argv[0] 或其 shebang 解释器的解析或执行许可。
    工作目录在分类时检查，不是与 spawn 原子；并发路径替换可能改变归属，但不能允许未隔离执行。
    """
    if 运行器程序 is None or not 工作目录可用(工作目录):#没有运行器或 cwd 不可用
        return False#没有运行器证据
    if 错误 is None or isinstance(错误,(str,bytes,int,float,bool)):#不是对象错误
        return False#不是对象错误
    码=取字段(错误,'code')#错误码
    系统调用=取字段(错误,'syscall')#系统调用名
    if isinstance(错误,dict):#映射错误
        有路径='path' in 错误#是否带着 path
        路径=错误.get('path')#错误路径
    else:#对象错误
        有路径=hasattr(错误,'path')#是否带着 path
        路径=getattr(错误,'path',None)#错误路径
    if not isinstance(码,str) or 码 not in 可执行拉起码:#不是 ENOENT/EACCES
        return False#不是可执行失败码
    if not isinstance(系统调用,str):#没有系统调用名
        return False#没有系统调用名
    精确调用='spawn '+运行器程序#精确 spawn 运行器
    if not 有路径:#无路径则系统调用必须点名运行器
        return 系统调用==精确调用#系统调用必须点名运行器
    if not isinstance(路径,str) or len(路径)==0 or 路径!=运行器程序:#路径必须等于运行器
        return False#路径对不上运行器
    return 系统调用=='spawn' or 系统调用==精确调用#系统调用是 spawn 或其精确形式

def 分类拒绝(结果,特征们):#是否政策拒绝
    """对照所选后端的拒绝方言分类一次失败运行。"""
    return 匹配特征(取字段(结果,'exitCode'),取字段(取字段(结果,'stderr'),'text'),特征们)#按退出码与 stderr 签名匹配

def 分类启动器失败(退出码,标准误,规则们):#分类运行器失败
    """对照所选后端的结构化运行器失败规则分类一次已结算进程。

    每条规则要求非零退出、其可选退出码门，以及去掉精确信息行之后一条 stderr 行上的致命签名。
    """
    if 退出码 is None or 退出码==0:#零退出或信号不算运行器失败
        return None#证据不足
    行们=re.split(r'\r?\n',标准误)#按行拆 stderr
    for 规则 in 规则们:#逐规则
        允许退出码=取字段(规则,'allowedExitCodes')#可选退出码门
        if 允许退出码 is not None and 退出码 not in 允许退出码:#退出码门不匹配
            continue#下一条规则
        信息行=取字段(规则,'informationalLines')#信息行
        if 信息行 is None:#没有信息行
            信息行=[]#空表
        信息行集合=set(行.lower() for 行 in 信息行)#信息行小写集
        #空或仅空白的子串不是有意义的运行器证据
        致命特征=[签名.lower() for 签名 in 取字段(规则,'fatalSignatures') if len(签名.strip())>0]#去掉空白签名并小写
        for 行 in 行们:#逐行
            小写=行.lower()#小写行
            if 小写 in 信息行集合:#信息行跳过
                continue#下一条行
            if any(签名 in 小写 for 签名 in 致命特征):#命中致命签名
                return {'detail':行}#匹配到的致命行
    return None#没有足够证据

def 匹配特征(退出码,标准误,特征们):#匹配拒绝签名
    """把非零退出对照大小写不敏感的 stderr 签名匹配。"""
    if 退出码 is None or 退出码==0:#零退出或信号不算
        return False#不算拒绝
    小写=标准误.lower()#stderr 小写
    return any(签名.lower() in 小写 for 签名 in 特征们)#任一签名命中
