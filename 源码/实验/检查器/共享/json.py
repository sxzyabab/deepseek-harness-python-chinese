import json#序列化
from threading import Event as 事件,Lock as 锁,Thread as 线程#完成门、结算互斥、工作线程

__all__=[#仅中文公开名
    '检查器json标量','检查器json值','检查器json对象',
    '是否json值','要求json对象','json字节长度','是否普通对象',
    '检查器错误','操作任务','在线程执行','已中止','若已中止则抛出',
]#公开面结束

检查器json标量=type(None)|bool|int|float|str#JSON标量

class 检查器错误(Exception):#检查器错误基类
    """检查器包内错误基类。"""
    def __init__(自身,消息):#构造
        """记下英文诊断。"""
        super().__init__(消息)#基类
        自身.消息=消息#诊断

class 操作任务:#单次操作结果
    """单次操作结果，只暴露兑现、拒绝、等待。"""
    def __init__(自身):#构造未决任务
        """构造未决任务。"""
        自身._门=事件()#完成门
        自身._锁=锁()#结算互斥
        自身._值=None#成功值
        自身._错误=None#失败异常
        自身._已结算=False#是否已结算

    def 兑现(自身,值=None):#成功结算
        """成功结算。"""
        with 自身._锁:#竞态
            if 自身._已结算:#已结算
                return 值#忽略
            自身._已结算=True#标记
            自身._值=值#写入结果
        自身._门.set()#放行
        return 值#返回兑现值

    def 拒绝(自身,错误):#失败结算
        """失败结算。"""
        with 自身._锁:#竞态
            if 自身._已结算:#已结算
                return#忽略
            自身._已结算=True#标记
            if isinstance(错误,BaseException):#已是异常
                自身._错误=错误#原样
            else:#非异常
                自身._错误=Exception(str(错误))#包装
        自身._门.set()#放行

    def 等待(自身,超时=None):#阻塞等待
        """阻塞等到结算。"""
        if not 自身._门.wait(超时):#超时未完成
            raise TimeoutError()#超时
        if 自身._错误 is not None:#失败
            raise 自身._错误#原样抛
        return 自身._值#成功值

def 在线程执行(函数):#在工作线程执行
    """在工作线程执行并返回操作任务。"""
    任务=操作任务()#本次任务
    def 执行并结算():#执行函数并结算
        """执行函数并结算。"""
        try:#执行
            任务.兑现(函数())#兑现
        except Exception as 错误:#结算路径上的回调什么都可能抛，契约未定所以收不窄
            任务.拒绝(错误)#拒绝
    工作=线程(target=执行并结算,daemon=True)#工作线程
    工作.start()#启动
    return 任务#操作任务

def 已中止(信号):#信号是否已中止
    """信号是否已中止；信号是 threading.Event。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#事件置位

def 若已中止则抛出(信号):#已中止则抛
    """已中止则抛出检查器错误。"""
    if 已中止(信号):#已置位
        raise 检查器错误('The operation was aborted')#取消

class 检查器json对象(dict):#JSON对象面
    """检查器传输接受的 JSON 兼容对象。"""

检查器json值=检查器json标量|list|检查器json对象#JSON兼容值

def 是否普通对象(值):#是否为普通对象
    """检验是否为带字符串自有键的普通对象。"""
    if not isinstance(值,dict) or isinstance(值,检查器json对象) is False and type(值) is not dict:#非dict
        if not isinstance(值,dict):#非映射
            return False#否
    if isinstance(值,list):#数组
        return False#否
    return isinstance(值,dict)#普通dict

def 访问json(值,祖先):#递归访问JSON形状
    """带祖先集合递归访问。"""
    if 值 is None or isinstance(值,(str,bool)):#标量真
        return True#真
    if isinstance(值,(int,float)):#数
        if isinstance(值,bool):#bool是int子类
            return True#已在上
        if not (值==值 and 值 not in (float('inf'),float('-inf'))):#非有限
            return False#否
        if 值==0 and str(值)=='-0':#负零
            return False#否
        return True#有限数
    if not isinstance(值,(dict,list)) or id(值) in 祖先:#非对象或环
        return False#否
    祖先.add(id(值))#记入祖先
    try:#访问子项
        if isinstance(值,list):#数组分支
            return all(访问json(项,祖先) for 项 in 值)#逐项
        if not 是否普通对象(值):#非普通对象
            return False#否
        for 键,子 in 值.items():#逐键
            if not isinstance(键,str):#仅字符串键
                return False#否
            if not 访问json(子,祖先):#值非法
                return False#否
        return True#对象合法
    finally:#无论成败
        祖先.discard(id(值))#退出祖先

def 是否json值(值):#是否为可过线JSON值
    """检验能否无损穿过 MessagePort 与 JSON WebSocket。"""
    return 访问json(值,set())#带祖先集合

def 要求json对象(值,标签):#要求普通JSON对象
    """要求普通 JSON 对象并以收窄后类型返回。"""
    if not 是否普通对象(值) or not 是否json值(值):#非普通或非JSON
        raise 检查器错误(f'inspector protocol: {标签} must be a JSON object')#英文诊断
    return 值#已收窄

def json字节长度(值):#JSON线上字节长度
    """计算 JSON 线上值的 UTF-8 字节长度。"""
    return len(json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8'))#序列化后量
