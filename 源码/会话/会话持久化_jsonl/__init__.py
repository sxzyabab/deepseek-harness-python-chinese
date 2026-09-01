"""JSONL 耐久会话持久化后端（对齐 upstream session-persistence-jsonl）。"""
import os#路径
from ...依赖 import schemastery#配置
from ..会话持久化 import (
    会话持久化,默认预备会话缓存大小,默认写批最大延迟毫秒,写批延迟上限毫秒,
    持久化协调器,会话格式不支持错误,
)#基座与协调器
from .格式 import 日志路径,扫描日志,编码段,默认压缩#格式工具
from .zstd编解码 import 压缩zstd帧,解压zstd帧#zstd
名称='session-persistence-jsonl'#Cordis 插件名
注入=['sessions']#依赖
配置=schemastery.对象字段({
    'root':schemastery.字符串字段(),#根目录必填
    'packChunks':schemastery.布尔字段(默认值=True),#打包块
    'compression':schemastery.字符串字段(默认值='zstd'),#压缩
    'preparedSessionCacheSize':schemastery.数字字段(默认值=默认预备会话缓存大小),#预备缓存
    'writeBatchMaxDelayMs':schemastery.数字字段(默认值=默认写批最大延迟毫秒),#写批延迟
})#配置模式
__all__=['名称','注入','配置','jsonl会话持久化','默认']#公开面

def 取字段(对象,键,缺省=None):#读字段
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键,缺省)#键
    return getattr(对象,键,缺省)#属性

def 解开(值):#可等待则等待
    等待=getattr(值,'wait',None) or getattr(值,'等待',None)#方法
    if callable(等待):#可等待
        return 等待()#等待
    return 值#同步

class jsonl会话持久化(会话持久化):#JSONL 后端
    """每会话一个追加 JSONL 文件；协调器拥有写路径。"""
    inject=['sessions']#注入
    name='session-persistence-jsonl'#诊断名
    @property#原样子产物
    def 支持原样子产物(自身):return True#支持
    supportsRawArtifacts=property(lambda 自身:True)#Cordis 槽
    def __init__(自身,上下文,配置值):#构造
        super().__init__(上下文)#基类
        根=配置值.get('root')#根
        if 根 is None or len(str(根).strip())==0:#空根
            raise Exception('session-persistence-jsonl: root is required')#拒绝
        自身._根=os.path.abspath(str(根))#绝对根
        自身._打包块=配置值.get('packChunks',True)#打包
        自身._压缩=配置值.get('compression','zstd')#压缩
        自身._协调器=持久化协调器(上下文,自身._后端(),{
            'preparedSessionCacheSize':配置值.get('preparedSessionCacheSize',默认预备会话缓存大小),
            'writeBatchMaxDelayMs':配置值.get('writeBatchMaxDelayMs',默认写批最大延迟毫秒),
        })#协调器

    def _后端(自身):#协调器后端适配
        """把文件 IO 原语交给协调器。"""
        class 后端:#内联后端
            name='session-persistence-jsonl'#名
            def locate(适配,头):#定位
                路径=日志路径(自身._根,头)#算路径
                return None if not os.path.exists(路径) else {'kind':'jsonl','path':路径}#位置
            def loadStored(适配,标识,信号=None):#加载
                路径=日志路径(自身._根,{'id':标识})#路径
                if not os.path.exists(路径):#缺席
                    raise 会话格式不支持错误('session not found: '+str(标识))#拒绝
                明文=解压zstd帧(open(路径,'rb').read()) if 自身._压缩=='zstd' else open(路径,'rb').read()#读
                return 扫描日志(明文.decode('utf-8'))#解析
            def readStoredRevision(适配,标识,信号=None):#修订
                路径=日志路径(自身._根,{'id':标识})#路径
                if not os.path.exists(路径):#缺席
                    return None#无
                状态=os.stat(路径)#stat
                return ':'.join([str(状态.st_dev),str(状态.st_ino),str(状态.st_size),str(状态.st_mtime_ns),str(状态.st_ctime_ns)])#修订
            def loadStoredFrom(适配,标识,起始序号,信号=None):#后缀读
                已加载=适配.loadStored(标识,信号)#全读
                事件们=[事件 for 事件 in 已加载['events'] if 取字段(事件,'seq')>=起始序号]#过滤
                return {'meta':已加载['meta'],'events':事件们}#返回
            def appendBatch(适配,标识,批次,信号=None):#追加
                路径=日志路径(自身._根,{'id':标识})#路径
                os.makedirs(os.path.dirname(路径),exist_ok=True)#建目录
                段=编码段(批次,自身._打包块)#编码
                载荷=段.encode('utf-8')#字节
                if 自身._压缩=='zstd':#zstd
                    载荷=压缩zstd帧(载荷)#压缩
                with open(路径,'ab') as 文件:#追加
                    文件.write(载荷)#写
                return None#无撕裂标记
            def commitRepair(适配,标识,修复,信号=None):#修复
                raise Exception('jsonl repair not implemented in Python port yet')#待补
            def list(适配,信号=None):#列表
                头们=[]#结果
                for 根,目录们,文件们 in os.walk(自身._根):#遍历
                    for 名 in 文件们:#文件
                        if not 名.endswith('.jsonl') and not 名.endswith('.jsonl.zst'):#过滤
                            continue#跳过
                        try:#解析头
                            检查=适配.loadStored(os.path.basename(根),信号)#按目录名
                            头们.append(检查['meta'])#收集
                        except Exception:#坏文件
                            continue#跳过
                return 头们#返回
            def close(适配):#关闭
                return#无状态
        return 后端()#实例

    def 定位(自身,头):return 自身._协调器.backend.locate(头)#转发
    def 创建(自身,头):return 自身._协调器.create(头)#转发
    def 追加(自身,标识,事件们):return 自身._协调器.append(标识,事件们)#转发
    def 加载(自身,标识):return 自身._协调器.load(标识)#转发
    def 检查(自身,标识,信号=None):return 自身._协调器.inspect(标识,信号)#转发
    def 从序号读(自身,标识,起始序号,信号=None):return 自身._协调器.readFrom(标识,起始序号,信号)#转发
    def 列出(自身,信号=None):return 自身._协调器.list(信号)#转发
    def 列出快照(自身,信号=None):return 自身._协调器.listSnapshots(信号)#转发

def 应用(上下文,配置值):#加载
    jsonl会话持久化(上下文,配置值)#注册

apply=应用#Cordis 插件入口
default=jsonl会话持久化#默认类
默认=jsonl会话持久化#中文默认
