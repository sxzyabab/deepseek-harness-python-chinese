"""JSONL 持久化后端的 Zstandard 帧原语（对齐 upstream zstd.ts 公开面）。"""
from io import BytesIO#字节流
import zstandard as zstd#zstd

ZSTD魔数=0xFD2FB528#Zstandard 帧魔数（小端）

def 压缩zstd帧(明文):#压缩一帧
    """压缩一条可独立解码且带校验和的 Zstandard 帧。"""
    if isinstance(明文,str):#文本
        明文=明文.encode('utf-8')#转字节
    压缩器=zstd.ZstdCompressor(write_checksum=True)#带校验和
    return 压缩器.compress(明文)#单帧

def 解压zstd帧(载荷):#解压一帧或拼接帧
    """解压完整帧并校验；多帧拼接时读尽全部明文。"""
    解压器=zstd.ZstdDecompressor()#解压器
    with 解压器.stream_reader(BytesIO(载荷)) as 阅读器:#多帧阅读器
        return 阅读器.read()#全部明文

def 扫描zstd帧(缓冲,最大帧数=None):#结构扫描帧
    """在不解压的情况下定位完整帧；EOF 落在末帧内则返回撕裂起点。"""
    if isinstance(缓冲,memoryview):#memoryview
        缓冲=bytes(缓冲)#转字节
    帧列表=[]#完整帧
    偏移=0#游标
    上限=浮点无穷 if 最大帧数 is None else 最大帧数#上限
    while 偏移<len(缓冲):#未扫完
        起点=偏移#本帧起点
        if len(缓冲)-偏移<4:#魔数不足
            return {'frames':帧列表,'tornStart':起点}#撕裂
        魔数=int.from_bytes(缓冲[偏移:偏移+4],'little')#读魔数
        if 魔数!=ZSTD魔数:#非法
            raise Error(f'corrupt Zstandard session log: invalid frame magic at byte {偏移}')#拒绝
        偏移+=4#跳过魔数
        if 偏移==len(缓冲):#描述符不足
            return {'frames':帧列表,'tornStart':起点}#撕裂
        描述符=缓冲[偏移]#帧头描述符
        偏移+=1#跳过描述符
        if (描述符&0x18)!=0:#保留位
            raise Error(f'corrupt Zstandard session log: reserved frame-header bit at byte {偏移-1}')#拒绝
        内容大小标志=描述符>>6#内容大小标志
        单段=(描述符&0x20)!=0#单段
        有校验和=(描述符&0x04)!=0#校验和
        字典标志=描述符&0x03#字典标志
        字典字节=4 if 字典标志==3 else 字典标志#字典字节数
        内容大小字节=(1 if 单段 else 0) if 内容大小标志==0 else (1<<内容大小标志)#内容大小字节
        剩余头=(0 if 单段 else 1)+字典字节+内容大小字节#剩余头
        if len(缓冲)-偏移<剩余头:#头不足
            return {'frames':帧列表,'tornStart':起点}#撕裂
        偏移+=剩余头#跳过剩余头
        while True:#扫描块
            if len(缓冲)-偏移<3:#块头不足
                return {'frames':帧列表,'tornStart':起点}#撕裂
            块头=int.from_bytes(缓冲[偏移:偏移+3],'little')#三字节块头
            偏移+=3#跳过块头
            末块=(块头&1)!=0#末块
            块类型=(块头>>1)&0x03#块类型
            块大小=块头>>3#块大小
            if 块类型==0x03:#保留块类型
                raise Error(f'corrupt Zstandard session log: reserved block type at byte {偏移-3}')#拒绝
            载荷字节=1 if 块类型==0x01 else 块大小#载荷字节
            if len(缓冲)-偏移<载荷字节:#载荷不足
                return {'frames':帧列表,'tornStart':起点}#撕裂
            偏移+=载荷字节#跳过载荷
            if 末块:#末块
                break#结束块循环
        if 有校验和:#校验和
            if len(缓冲)-偏移<4:#不足
                return {'frames':帧列表,'tornStart':起点}#撕裂
            偏移+=4#跳过
        帧列表.append({'start':起点,'end':偏移})#记录完整帧
        if len(帧列表)>=上限:#达上限
            return {'frames':帧列表}#返回
    return {'frames':帧列表}#全部完整

def 解压zstd前缀(输入):#解压不完整前缀
    """从不完整末帧的可用字节恢复明文；调用方须先确立撕裂边界。"""
    if isinstance(输入,str):#文本
        输入=输入.encode('utf-8')#转字节
    解压器=zstd.ZstdDecompressor()#解压器
    块列表=[]#已产明文
    try:#流式读
        with 解压器.stream_reader(BytesIO(输入)) as 阅读器:#阅读器
            while True:#直到 EOF 或损坏停
                try:#读一块
                    块=阅读器.read(65536)#块
                except zstd.ZstdError:#不完整帧/校验未完成
                    break#保留已产明文
                if not 块:#EOF
                    break#结束
                块列表.append(块)#收集
    except zstd.ZstdError:#开流即失败
        return b''.join(块列表)#可能为空
    return b''.join(块列表)#拼接

class Error(Exception):#zstd 辅助错误
    """Zstandard 帧原语抛出的 Error 风格异常。"""

浮点无穷=float('inf')#正无穷（帧上限缺省）

class 公开zstd帧解码器:#公开一次性 API 多帧适配器
    """只用公开一次性解压做成的同步多帧解码器（不对齐 Node 私有 decoder）。"""
    def __init__(自身):#构造
        """初始化生命周期。"""
        自身._已启动=False#是否已开始
        自身._已关闭=False#是否已关闭

    def 解码(自身,源,帧列表):#按序解压
        """按源顺序解码并校验完整帧；产出缓冲在推进前有效。"""
        if 自身._已启动:#禁止二次启动
            raise Error('Zstandard frame decoder was already started')#拒绝
        if 自身._已关闭:#已关闭
            raise Error('cannot start a closed Zstandard frame decoder')#拒绝
        自身._已启动=True#标记
        try:#解压每帧
            for 帧 in 帧列表:#遍历
                起点=帧['start']#起点
                终点=帧['end']#终点
                try:#一次性解压
                    明文=解压zstd帧(源[起点:终点])#解压该帧
                except Exception as 错误:#校验失败
                    raise Error(f'corrupt Zstandard session log: frame at byte {起点} failed validation') from 错误#包装
                yield 明文#交出
        finally:#无论成败
            自身.关闭()#释放

    def 关闭(自身):#关闭
        """释放资源；重复调用无害。"""
        自身._已关闭=True#标记

def 创建zstd帧解码器():#创建帧解码器
    """返回公开 API 帧解码器（Python 无 Node 私有 decoder）。"""
    return 公开zstd帧解码器()#公开实现

__all__=[#公开面
    '压缩zstd帧','解压zstd帧','扫描zstd帧','解压zstd前缀',
    '创建zstd帧解码器','公开zstd帧解码器','ZSTD魔数','Error',
]#公开面结束
