"""生产与回放校验共用的、形如 ISO 的时钟上下文时间戳格式化。"""
import os#读取进程TZ
from datetime import datetime as 日期时间#纪元与字段拆分
from types import SimpleNamespace as 简易命名空间#对齐resolvedOptions对象
from zoneinfo import ZoneInfo as 区时#IANA时区

时间戳分段=('day','hour','minute','month','second','timeZoneName','year')#Intl分段名联合，仅作文档对齐

class 时间戳错误(Exception):
    """时间戳包的异常基类。"""

def 解析进程时区名():#省略显式时区时解析进程回退时区
    """对齐 Node 省略 timeZone 时的进程时区解析，优先 TZ，其次本地 ZoneInfo.key。"""
    if 'TZ' in os.environ:#有TZ
        环境时区=os.environ['TZ']#进程TZ
        if isinstance(环境时区,str) and len(环境时区)>0:#非空
            return 区时(环境时区).key#经ZoneInfo规范名
    本地=日期时间.now(tz=区时('UTC')).astimezone()#UTC此刻转到本地
    信息=本地.tzinfo#本地tzinfo
    if hasattr(信息,'key'):#ZoneInfo才有key
        键=信息.key#IANA键
        if isinstance(键,str) and len(键)>0:#已是IANA
            return 键#进程时区名
    raise 时间戳错误('time-context: failed to resolve the system time zone')#无法解析系统时区

def 创建时间戳格式化器(时区=None):#创建时钟读数格式化器
    """创建持久时钟读数所用的精确格式化器。显式展示时区，或 None 表示进程回退时区。"""
    if 时区 is None:#进程默认
        时区名=解析进程时区名()#解析进程时区
    else:#显式时区
        时区名=区时(时区).key#非法则抛出，交给调用方包装
    return 时间戳格式化器(时区名)#带稳定数字本地字段与长数字偏移的格式化器

def 格式化时间戳(此刻,格式化器,时区):#格式化纪元毫秒为持久时间戳
    """把纪元毫秒格式化为带偏移与 IANA 时区的、形如 ISO 的时间戳。"""
    时刻=日期时间.fromtimestamp(此刻/1000,tz=格式化器.时区对象)#按格式化器时区拆字段；此刻是纪元毫秒 int
    年=str(时刻.year).zfill(4)#四位年
    月=str(时刻.month).zfill(2)#两位月
    日=str(时刻.day).zfill(2)#两位日
    时=str(时刻.hour).zfill(2)#两位时，24小时制
    分=str(时刻.minute).zfill(2)#两位分
    秒=str(时刻.second).zfill(2)#两位秒
    偏移量=时刻.utcoffset()#该时刻偏移
    if 偏移量 is None:#无偏移
        偏移秒=0#零
    else:#有偏移
        偏移秒=int(偏移量.total_seconds())#整秒偏移
    if 偏移秒>=0:#非负
        符号='+'#正号
    else:#负
        符号='-'#负号
    绝对值=abs(偏移秒)#绝对值
    偏移时=绝对值//3600#偏移小时
    偏移分=(绝对值%3600)//60#偏移分钟
    偏移=符号+str(偏移时).zfill(2)+':'+str(偏移分).zfill(2)#长数字偏移
    return 年+'-'+月+'-'+日+'T'+时+':'+分+':'+秒+偏移+'['+时区+']'#ISO形时间戳加时区括号

class 时间戳格式化器:#持久时钟读数格式化器
    """带稳定数字本地字段与长数字偏移的格式化器，对齐 Intl.DateTimeFormat 的本包用法。"""
    def __init__(自身,时区名):#按规范时区名构造
        """按规范 IANA 时区名构造。"""
        自身.时区名=时区名#括号与解析共用的规范名
        自身.时区对象=区时(时区名)#ZoneInfo实例

    def 解析选项(自身):#对齐resolvedOptions
        """给出规范时区名。"""
        return 简易命名空间(timeZone=自身.时区名)#对象属性timeZone
