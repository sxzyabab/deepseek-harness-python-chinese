from ..node.未实现失败 import 运行时错误
import math

__all__=['打包tar','解析tar']

块大小=512

def 写八进制(头,偏移,长度,值):
    """写八进制字段：零填充数字并以 NUL 结尾。"""
    文本=format(值,'o').zfill(长度-1)
    字节=文本.encode('utf-8')
    头[偏移:偏移+len(字节)]=字节

def 拆名字(名称):
    """把条目名拆成 ustar 的 name 与 prefix 字段。

    参数:
        名称: 完整条目名。
    返回:
        两个字段；名字直接放得下时 prefix 为空。
    """
    if len(名称.encode('utf-8'))<=100:
        return {'name':名称,'prefix':''}
    for 索引 in range(len(名称)-1,0,-1):
        if 名称[索引]!='/':
            continue
        前缀=名称[:索引]
        剩余=名称[索引+1:]
        if len(剩余.encode('utf-8'))<=100 and len(前缀.encode('utf-8'))<=155:
            return {'name':剩余,'prefix':前缀}
    raise 运行时错误(f'vfs tar: entry name does not fit the ustar name+prefix split: {名称}')

def 打包tar(文件表):
    """把条目打成一份未压缩 ustar 归档。

    条目保持给定顺序；以斜杠结尾的名字成为目录项。
    内容原样写入——压缩属于 HTTP 传输，不属于归档。

    参数:
        文件表: 条目名到内容字节。
    返回:
        归档字节。
    """
    块列表=[]
    for 条目名,内容 in 文件表.items():
        是目录=条目名.endswith('/')
        大小=0 if 是目录 else len(内容)
        拆分=拆名字(条目名)
        头=bytearray(块大小)
        名字节=拆分['name'].encode('utf-8')
        头[0:len(名字节)]=名字节
        写八进制(头,100,8,0o755 if 是目录 else 0o644)#mode
        写八进制(头,108,8,0)#uid
        写八进制(头,116,8,0)#gid
        写八进制(头,124,12,大小)#size
        写八进制(头,136,12,0)#mtime
        头[148:156]=b' '*8#校验和空格占位
        头[156]=0x35 if 是目录 else 0x30#typeflag
        头[257:262]=b'ustar'
        头[263:265]=b'00'
        前缀字节=拆分['prefix'].encode('utf-8')
        头[345:345+len(前缀字节)]=前缀字节
        校验=sum(头)
        校验文本=format(校验,'o').zfill(6).encode('utf-8')
        头[148:148+len(校验文本)]=校验文本
        头[154]=0
        头[155]=0x20
        块列表.append(bytes(头))
        if 大小>0:
            数据=内容 if isinstance(内容,(bytes,bytearray)) else bytes(内容)
            块列表.append(数据)
            填充=大小%块大小
            if 填充!=0:
                块列表.append(bytes(块大小-填充))
    块列表.append(bytes(块大小*2))
    return b''.join(块列表)

def 读字段(头,偏移,长度):
    """返回一个头字段中的 NUL 终止字符串。"""
    终点=偏移
    while 终点<偏移+长度 and 头[终点]!=0:
        终点+=1
    return bytes(头[偏移:终点]).decode('utf-8')

def 解析tar(归档):
    """解析未压缩 ustar 归档。

    文件字节是指向 `归档` 的子数组视图，非拷贝；调用方自担别名。
    写出子集之外的条目种类（链接、PAX 扩展）大声失败而非跳过。

    参数:
        归档: 归档字节。
    返回:
        按归档顺序的条目。
    """
    条目列表=[]
    偏移=0
    总长=len(归档)
    while 偏移+块大小<=总长:
        头=归档[偏移:偏移+块大小]
        if all(字节==0 for 字节 in 头):
            break
        短名=读字段(头,0,100)
        前缀=读字段(头,345,155)
        名称=短名 if 前缀=='' else f'{前缀}/{短名}'
        大小文本=读字段(头,124,12).strip() or '0'
        大小=int(大小文本,8)
        权限文本=读字段(头,100,8).strip() or '0'
        权限=int(权限文本,8)&0o777
        类型标志=头[156]
        是目录=类型标志==0x35 or 名称.endswith('/')
        if 类型标志 not in (0x30,0,0x35):
            raise 运行时错误(f'vfs tar: unsupported entry type {chr(0 if 类型标志 is None else 类型标志)} for "{名称}"')#??0，类型标志 0 合法
        数据起点=偏移+块大小
        条目列表.append({'name':名称,'bytes':归档[数据起点:数据起点+大小],'directory':是目录,'mode':权限})
        偏移=数据起点+math.ceil(大小/块大小)*块大小
    return 条目列表
