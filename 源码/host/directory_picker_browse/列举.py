"""browse 后端的列举辅助：完全限定围栏、有界窗口、中止竞速、面包屑与可进入行。

对齐上游 `directory-picker-browse/src/index.ts` 中的辅助函数。公开面仅中文名。
"""
import os,re,sys#路径、正则、平台

__all__=['完全限定','有界插入','竞速中止','祖先面包屑','目录行','列举候选']#仅中文公开名

def _是否thenable(值):#判定可等待对象
    if 值 is None:#空不是
        return False#不是
    if callable(getattr(值,'wait',None)):#Future 风格
        return True#可等待
    return callable(getattr(值,'等待',None))#外来 thenable

def _等待(值):#统一阻塞到结算
    if callable(getattr(值,'wait',None)):#Future 风格
        return 值.wait()#等待
    return 值.等待()#外来 thenable

def 解开(值):#可等待则等待否则原样
    """可等待则等待，否则原样返回。"""
    if _是否thenable(值):#可等待
        return _等待(值)#等待
    return 值#同步值

列举候选=dict#流式候选映射形状

def 完全限定(路径,平台=None):#路径是否完全限定
    """路径是否命名了一个不依赖进程状态的固定文件系统位置。"""
    if 平台 is None:#缺省当前平台
        平台=sys.platform#进程平台
    if 平台=='win32':#Windows：盘符或完整 UNC
        if not os.path.isabs(路径):#非绝对
            return False#未限定
        return re.match(r'^(?:[A-Za-z]:[\\/]|[\\/]{2}[^\\/]+[\\/]+[^\\/]+)',路径) is not None#盘符或完整 UNC
    return os.path.isabs(路径)#POSIX 绝对

def 有界插入(窗口,候选,保留):#把候选插入名称有序窗口
    """把一条流式候选插入按名称排序的有界窗口；超限驱逐名称最大者。返回是否发生过驱逐。"""
    名=候选['name']#候选基名
    if len(窗口)==保留 and _比较名(名,窗口[-1]['name'])>=0:#已满且不小于尾部
        return True#驱逐发生、不插入
    左=0#插入区间左
    右=len(窗口)#右（不含）
    while 左<右:#二分
        中=(左+右)//2#中点
        if _比较名(名,窗口[中]['name'])<0:#候选更小
            右=中#收缩右
        else:#更大或相等
            左=中+1#收缩左
    窗口.insert(左,候选)#插入保持升序
    if len(窗口)<=保留:#未超限
        return False#无驱逐
    窗口.pop()#丢掉尾部
    return True#发生驱逐

def 竞速中止(操作,信号):#文件系统步骤与中止信号竞速
    """等待操作，但信号一中止就用其中止原因拒绝。"""
    if 信号 is None:#无信号
        return 解开(操作)#直接等
    if getattr(信号,'aborted',False):#已中止
        raise 收成错误(getattr(信号,'reason',None) or Exception('aborted'))#立刻拒绝
    return 解开(操作)#同步文件系统步骤；中止由调用方在循环中检查

def 祖先面包屑(目标):#从根到目标的祖先链
    """从文件系统根到 target（含）的祖先链——每块都是跳转目标。"""
    屑们=[]#由叶向根填
    当前=目标#当前路径
    while True:#沿 dirname 走到根
        父=os.path.dirname(当前)#上一层
        名=当前 if 父==当前 else os.path.basename(当前)#根用完整路径
        屑们.insert(0,{'name':名,'path':当前,'hidden':False})#面包屑 hidden 恒 false
        if 父==当前:#已到根
            return 屑们#整条链
        当前=父#继续向上

def 目录行(父,名称,是目录,是符号链接,信号):#一条可进入列举行
    """跟随指向目录的符号链接；非目录以及损坏/成环链接为 None。"""
    路径=os.path.join(父,名称)#绝对路径
    可进入=是目录#dirent 标明目录
    if (not 可进入) and 是符号链接:#可能是指向目录的链接
        try:#stat 探测
            if 信号 is not None and getattr(信号,'aborted',False):#中止
                raise 收成错误(getattr(信号,'reason',None) or Exception('aborted'))#抛中止
            可进入=os.path.isdir(路径)#目标是否目录
        except BaseException:#stat 失败
            if 信号 is not None and getattr(信号,'aborted',False):#中止
                raise 收成错误(getattr(信号,'reason',None) or Exception('aborted'))#抛中止
            return None#不可进入
    if not 可进入:#非目录
        return None#跳过
    return {'name':名称,'path':路径,'hidden':名称.startswith('.')}#点前缀视为隐藏

def _比较名(甲,乙):#名称比较
    """按字符串比较名称。"""
    if 甲<乙:#更小
        return -1#负
    if 甲>乙:#更大
        return 1#正
    return 0#相等

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

def 收成错误(值):#规范未知抛出
    """把未知抛出值强制成 Exception。"""
    if isinstance(值,BaseException):#已是
        return 值#原样
    return Exception(str(值))#包装
