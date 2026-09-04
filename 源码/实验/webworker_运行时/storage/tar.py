"""未压缩 ustar 归档：VFS 镜像格式。一次 fetch 交付整棵树，
读取器交出指向已拉取缓冲的子数组视图，故挂载不拷贝，
worker 内也不跑 inflate。

对齐上游 `webworker-runtime/src/storage/tar.ts`。公开面仅中文名。
"""
import math#块对齐ceil

__all__=['打包tar','解析tar']#仅中文公开名

块大小=512#ustar块大小

def 写八进制(头,偏移,长度,值):#写八进制字段
    """写八进制字段：零填充数字并以 NUL 结尾。"""
    文本=format(值,'o').zfill(长度-1)#零填充八进制
    字节=文本.encode('utf-8')#编码
    头[偏移:偏移+len(字节)]=字节#写入

def 拆名字(名称):#拆name/prefix
    """把条目名拆成 ustar 的 name 与 prefix 字段。

    参数:
        名称: 完整条目名。
    返回:
        两个字段；名字直接放得下时 prefix 为空。
    """
    if len(名称.encode('utf-8'))<=100:#短名直放
        return {'name':名称,'prefix':''}#短名
    for 索引 in range(len(名称)-1,0,-1):#自右找斜杠
        if 名称[索引]!='/':#非斜杠跳过
            continue#处理下一段
        前缀=名称[:索引]#前缀段
        剩余=名称[索引+1:]#name段
        if len(剩余.encode('utf-8'))<=100 and len(前缀.encode('utf-8'))<=155:#两端皆合
            return {'name':剩余,'prefix':前缀}#返回拆分
    raise Exception(f'vfs tar: entry name does not fit the ustar name+prefix split: {名称}')#无法拆分

def 打包tar(文件们):#打包ustar
    """把条目打成一份未压缩 ustar 归档。

    条目保持给定顺序；以斜杠结尾的名字成为目录项。
    内容原样写入——压缩属于 HTTP 传输，不属于归档。

    参数:
        文件们: 条目名到内容字节。
    返回:
        归档字节。
    """
    块们=[]#块收集
    for 条目名,内容 in 文件们.items():#逐条目
        是目录=条目名.endswith('/')#是否目录名
        大小=0 if 是目录 else len(内容)#内容大小
        拆分=拆名字(条目名)#拆字段
        头=bytearray(块大小)#头块
        名字节=拆分['name'].encode('utf-8')#name字节
        头[0:len(名字节)]=名字节#写name
        写八进制(头,100,8,0o755 if 是目录 else 0o644)#mode
        写八进制(头,108,8,0)#uid
        写八进制(头,116,8,0)#gid
        写八进制(头,124,12,大小)#size
        写八进制(头,136,12,0)#mtime
        头[148:156]=b' '*8#校验和空格占位
        头[156]=0x35 if 是目录 else 0x30#typeflag
        头[257:262]=b'ustar'#魔术
        头[263:265]=b'00'#版本
        前缀字节=拆分['prefix'].encode('utf-8')#prefix字节
        头[345:345+len(前缀字节)]=前缀字节#prefix
        校验=sum(头)#累加校验
        校验文本=format(校验,'o').zfill(6).encode('utf-8')#写校验
        头[148:148+len(校验文本)]=校验文本#校验字段
        头[154]=0#NUL
        头[155]=0x20#空格
        块们.append(bytes(头))#推头
        if 大小>0:#有内容
            数据=内容 if isinstance(内容,(bytes,bytearray)) else bytes(内容)#规范字节
            块们.append(数据)#推数据
            填充=大小%块大小#块对齐剩余
            if 填充!=0:#需填零
                块们.append(bytes(块大小-填充))#填零
    块们.append(bytes(块大小*2))#双空块收尾
    return b''.join(块们)#返回归档

def 读字段(头,偏移,长度):#读NUL字段
    """返回一个头字段中的 NUL 终止字符串。"""
    终点=偏移#扫描终点
    while 终点<偏移+长度 and 头[终点]!=0:#遇NUL停
        终点+=1#推进
    return bytes(头[偏移:终点]).decode('utf-8')#解码

def 解析tar(归档):#解析ustar
    """解析未压缩 ustar 归档。

    文件字节是指向 `归档` 的子数组视图，非拷贝；调用方自担别名。
    写出子集之外的条目种类（链接、PAX 扩展）大声失败而非跳过。

    参数:
        归档: 归档字节。
    返回:
        按归档顺序的条目。
    """
    条目们=[]#条目列表
    偏移=0#游标
    总长=len(归档)#归档长度
    while 偏移+块大小<=总长:#还有整块
        头=归档[偏移:偏移+块大小]#取头
        if all(字节==0 for 字节 in 头):#空块结束
            break#结束
        短名=读字段(头,0,100)#短名
        前缀=读字段(头,345,155)#前缀
        名称=短名 if 前缀=='' else f'{前缀}/{短名}'#拼全名
        大小文本=读字段(头,124,12).strip() or '0'#八进制大小文本
        大小=int(大小文本,8)#八进制大小
        权限文本=读字段(头,100,8).strip() or '0'#权限文本
        权限=int(权限文本,8)&0o777#权限掩码
        类型标志=头[156]#类型标志
        是目录=类型标志==0x35 or 名称.endswith('/')#是否目录
        if 类型标志 not in (0x30,0,0x35):#不支持类型
            raise Exception(f'vfs tar: unsupported entry type {chr(类型标志 or 0)} for "{名称}"')#拒绝
        数据起点=偏移+块大小#数据起点
        条目们.append({'name':名称,'bytes':归档[数据起点:数据起点+大小],'directory':是目录,'mode':权限})#推条目
        偏移=数据起点+math.ceil(大小/块大小)*块大小#跳到下一块对齐
    return 条目们#返回条目
