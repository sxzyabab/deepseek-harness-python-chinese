"""JSONL 耐久会话持久化后端（对齐 upstream session-persistence-jsonl）。"""
import os#路径
from ...依赖.schemastery import 字典字段,字符串字段,布尔字段,数字字段#配置
from ..会话持久化 import (
    会话持久化,默认预备会话缓存大小,默认写批最大延迟毫秒,
    持久化协调器,会话格式不支持错误,持久化错误,
)#基座与协调器
from .格式 import 日志路径,扫描日志,编码段,默认压缩#格式工具
from .zstd编解码 import 压缩zstd帧,解压zstd帧#zstd

名称='session-persistence-jsonl'#Cordis 插件名
注入=['sessions']#依赖
配置=字典字段({
    'root':字符串字段(),#根目录必填
    'packChunks':布尔字段(默认值=True),#打包块
    'compression':字符串字段(默认值='zstd'),#压缩
    'preparedSessionCacheSize':数字字段(默认值=默认预备会话缓存大小),#预备缓存
    'writeBatchMaxDelayMs':数字字段(默认值=默认写批最大延迟毫秒),#写批延迟
})#配置模式
__all__=['名称','注入','配置','jsonl会话持久化']#公开面

class jsonl会话持久化(会话持久化):
    """每会话一个追加 JSONL 文件；协调器拥有写路径。"""
    def __init__(自身,上下文,配置值):#构造
        """按配置登记 JSONL 后端并交给协调器。"""
        super().__init__(上下文)#基类
        if 'root' not in 配置值:#缺根
            raise 持久化错误('session-persistence-jsonl: root is required')#拒绝
        根=配置值['root']#根
        if len(str(根).strip())==0:#空根
            raise 持久化错误('session-persistence-jsonl: root is required')#拒绝
        自身.根=os.path.abspath(str(根))#绝对根
        if 'packChunks' in 配置值:#给了打包
            自身.打包块=配置值['packChunks']#打包
        else:#缺席
            自身.打包块=True#默认打包
        if 'compression' in 配置值:#给了压缩
            自身.压缩=配置值['compression']#压缩
        else:#缺席
            自身.压缩=默认压缩#默认 zstd
        if 'preparedSessionCacheSize' in 配置值:#给了预备缓存
            预备缓存=配置值['preparedSessionCacheSize']#预备缓存
        else:#缺席
            预备缓存=默认预备会话缓存大小#默认
        if 'writeBatchMaxDelayMs' in 配置值:#给了写批延迟
            写批延迟=配置值['writeBatchMaxDelayMs']#写批延迟
        else:#缺席
            写批延迟=默认写批最大延迟毫秒#默认
        自身.协调器=持久化协调器(上下文,自身.造后端(),{
            'preparedSessionCacheSize':预备缓存,#预备缓存
            'writeBatchMaxDelayMs':写批延迟,#写批延迟
        })#协调器

    @property
    def 支持原样子产物(自身):#是否支持原样子产物
        """JSONL 后端暴露原样子产物。"""
        return True#支持

    def 造后端(自身):#协调器后端适配
        """把文件 IO 原语交给协调器。"""
        持有=自身#外层持久化实例
        class 后端:
            """协调器耐久原语。"""
            name='session-persistence-jsonl'#诊断名
            def locate(自身,头):#定位
                """定位产物。"""
                路径=日志路径(持有.根,头)#算路径
                if not os.path.exists(路径):#缺席
                    return None#无产物
                return {'kind':'jsonl','path':路径}#位置
            def loadStored(自身,标识,信号=None):#加载
                """加载已存会话。"""
                路径=日志路径(持有.根,{'id':标识})#路径
                if not os.path.exists(路径):#缺席
                    raise 会话格式不支持错误('session not found: '+str(标识))#拒绝
                with open(路径,'rb') as 文件:#读文件
                    原始=文件.read()#字节
                if 持有.压缩=='zstd':#zstd
                    明文=解压zstd帧(原始)#多帧读尽
                else:#未压缩
                    明文=原始#原样
                return 扫描日志(明文.decode('utf-8'))#解析
            def readStoredRevision(自身,标识,信号=None):#修订
                """读已存修订指纹。"""
                路径=日志路径(持有.根,{'id':标识})#路径
                if not os.path.exists(路径):#缺席
                    return None#无
                状态=os.stat(路径)#stat
                return ':'.join([str(状态.st_dev),str(状态.st_ino),str(状态.st_size),str(状态.st_mtime_ns),str(状态.st_ctime_ns)])#修订
            def loadStoredFrom(自身,标识,起始序号,信号=None):#后缀读
                """从起始序号起读后缀。"""
                已加载=自身.loadStored(标识,信号)#全读
                事件列表=[]#过滤
                for 事件 in 已加载['events']:#逐事件
                    if 事件['seq']>=起始序号:#落在后缀
                        事件列表.append(事件)#收集
                return {'meta':已加载['meta'],'events':事件列表}#返回
            def appendBatch(自身,标识,批次,信号=None):#追加
                """追加一批事件；zstd 时本批压成一帧再 ab 拼接。"""
                路径=日志路径(持有.根,{'id':标识})#路径
                os.makedirs(os.path.dirname(路径),exist_ok=True)#建目录
                段=编码段(批次,持有.打包块)#编码
                载荷=段.encode('utf-8')#UTF-8 字节
                if 持有.压缩=='zstd':#zstd
                    载荷=压缩zstd帧(载荷)#本批一帧
                with open(路径,'ab') as 文件:#追加
                    文件.write(载荷)#写
                return None#无撕裂标记
            def commitRepair(自身,标识,修复,信号=None):#修复
                """提交修复。"""
                raise 持久化错误('jsonl repair not implemented in Python port yet')#待补
            def list(自身,信号=None):#列表
                """列出可解析的会话头；坏文件跳过。"""
                头列表=[]#结果
                for 根,目录列表,文件列表 in os.walk(持有.根):#遍历
                    for 名 in 文件列表:#文件
                        if not 名.endswith('.jsonl') and not 名.endswith('.jsonl.zst'):#过滤
                            continue#跳过
                        try:#解析头
                            检查=自身.loadStored(os.path.basename(根),信号)#按目录名
                            头列表.append(检查['meta'])#收集
                        except Exception:#坏文件形态不定，收不窄
                            continue#跳过
                return 头列表#返回
            def close(自身):#关闭
                """关闭。无状态。"""
                return#无状态
        return 后端()#实例

    def 定位(自身,头):#转发定位
        """转发定位。"""
        return 自身.协调器.backend.locate(头)#转发

    def 创建(自身,头):#转发创建
        """转发创建。"""
        return 自身.协调器.create(头)#转发

    def 追加(自身,标识,事件列表):#转发追加
        """转发追加。"""
        return 自身.协调器.append(标识,事件列表)#转发

    def 加载(自身,标识):#转发加载
        """转发加载。"""
        return 自身.协调器.load(标识)#转发

    def 检查(自身,标识,信号=None):#转发检查
        """转发检查。"""
        return 自身.协调器.inspect(标识,信号)#转发

    def 从序号读(自身,标识,起始序号,信号=None):#转发后缀读
        """转发后缀读。"""
        return 自身.协调器.readFrom(标识,起始序号,信号)#转发

    def 列出(自身,信号=None):#转发列出
        """转发列出。"""
        return 自身.协调器.list(信号)#转发

    def 列出快照(自身,信号=None):#转发列出快照
        """转发列出快照。"""
        return 自身.协调器.listSnapshots(信号)#转发

def 应用(上下文,配置值):#加载
    """加载 JSONL 会话持久化。"""
    jsonl会话持久化(上下文,配置值)#注册

jsonl会话持久化.inject=注入#Cordis 注入
jsonl会话持久化.name=名称#Cordis 插件名
inject=注入#Cordis 槽
name=名称#Cordis 槽
Config=配置#Cordis 配置
apply=应用#Cordis 插件入口
default=jsonl会话持久化#Cordis 默认导出槽
