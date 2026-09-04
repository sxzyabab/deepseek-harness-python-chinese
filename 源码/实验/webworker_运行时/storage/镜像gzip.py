"""镜像字节信封。打包器写出一个装 ustar 归档的 gzip 成员，
worker 用平台自带解压器 inflate，再让 tar 读取器见到字节——
`storage/tar.ts` 保持纯 ustar 读取器，内无编解码器。

对齐上游 `webworker-runtime/src/storage/image-gzip.ts`。公开面仅中文名。
"""
import gzip#gzip解压

__all__=['流式解压镜像','解压镜像']#仅中文公开名

gzip魔术=(0x1f,0x8b)#gzip成员识别字节（RFC 1952 §2.3.1）
引用字节数=8#拒绝正文时引用的字节数

def 十六进制预览(字节们):#十六进制预览
    """前若干字节的十六进制预览。"""
    return ' '.join(f'{字节:02x}' for 字节 in 字节们[:引用字节数])#空格分隔

def 拒绝正文(来源,已读):#构造拒绝错误
    """构造非 gzip 成员正文的拒绝错误。"""
    读描述='an empty body' if len(已读)==0 else 十六进制预览(已读)#可读已读
    return Exception(#拒绝文案
        f'webworker image: {来源} is not the gzip-compressed tar this deployment serves as its image '
        f'(expected a member starting 1f 8b, read {读描述}); '
        'a host that answered with a Content-Encoding the transport already decoded, or a build that wrote '
        'the archive uncompressed, arrives exactly this way'
    )#错误结束

def 要求gzip成员(来源,块流):#校验并透传gzip头
    """拒绝非 gzip 成员正文的透传；跨块持有头直至可判定。

    参数:
        来源: 镜像 URL，或字节如何到达；拒绝时点名。
        块流: 产出字节块的可迭代。
    产出:
        校验通过后的正文块。
    """
    头=b''#已缓冲头
    已判定=False#是否已判定
    for 块 in 块流:#逐块
        if 已判定:#已判定则透传
            yield 块#转发
            continue#下一块
        头=头+块#合并缓冲
        if len(头)<len(gzip魔术):#仍不够判定
            continue#等待更多
        if any(头[位置]!=字节 for 位置,字节 in enumerate(gzip魔术)):#魔术不匹配
            raise 拒绝正文(来源,头)#拒绝
        已判定=True#标记已判定
        yield 头#放出完整头起缓冲
        头=b''#清空
    if not 已判定:#太短仍未判定
        raise 拒绝正文(来源,头)#拒绝

def 流式解压镜像(正文流,来源):#流式解压
    """边到达边 inflate 打包的 VFS 镜像。

    参数:
        正文流: 镜像正文块可迭代，直接来自 fetch 或包住字节。
        来源: 镜像 URL，或字节如何到达；拒绝时点名。
    返回:
        镜像携带的 ustar 归档。
    """
    已校验=b''.join(要求gzip成员(来源,正文流))#先校验魔术并收齐
    return gzip.decompress(已校验)#gzip解压

def 解压镜像(字节们,来源):#缓冲解压入口
    """inflate 驻于内存的打包 VFS 镜像。

    字节变成正文，使两个入口跑同一条流：一条解压路径、一次拒绝，
    不论镜像来自网络还是调用方缓冲。

    参数:
        字节们: 镜像字节。
    返回:
        镜像携带的 ustar 归档。
    """
    if 字节们 is None or len(字节们)==0:#无正文
        raise Exception(f'webworker image: {来源} produced no readable body')#无正文
    return 流式解压镜像([bytes(字节们)],来源)#走同一路径
