"""检查器跨界消息一律承认的 JSON 值。

对齐上游 `shared/json.ts`。公开面仅中文名。
本包并发原语也落在此文件。
"""
import json,threading#序列化与后台线程
from concurrent.futures import Future as 原生结果#单次操作结果

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
    """单次操作的 Future 包装，只暴露 等待。"""
    def __init__(自身):#构造未决任务
        """构造未决任务。"""
        自身._future=原生结果()#底层 Future

    def 兑现(自身,值=None):#成功结算
        """成功结算。"""
        if not 自身._future.done():#尚未结算
            自身._future.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):#失败结算
        """失败结算。"""
        if not 自身._future.done():#尚未结算
            自身._future.set_exception(错误)#原样拒绝

    def 等待(自身,超时=None):#阻塞等待
        """阻塞等到结算。"""
        return 自身._future.result(timeout=超时)#取结果或抛错

def 在线程执行(函数):#在工作线程执行
    """在工作线程执行并返回操作任务。"""
    任务=操作任务()#本次任务
    def 执行并结算():#执行函数并结算
        """执行函数并结算。"""
        try:#执行
            任务.兑现(函数())#兑现
        except Exception as 错误:#Future 结算路径上的回调什么都可能抛，契约未定所以收不窄
            任务.拒绝(错误)#拒绝
    工作=threading.Thread(target=执行并结算)#工作线程
    工作.daemon=True#不挡住退出
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
