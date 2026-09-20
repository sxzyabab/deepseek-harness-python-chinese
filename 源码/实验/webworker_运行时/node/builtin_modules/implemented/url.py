from urllib.parse import unquote as 百分号解码

__all__=[
    'fileURLToPath','pathToFileURL','resolve','URL','URLSearchParams','__esModule','default',
]

def 文件url转路径(地址):
    """`file:` URL 的文件系统路径。"""
    解析结果=globals()['URL'](地址) if isinstance(地址,str) else 地址
    if 解析结果.protocol!='file:':
        raise TypeError(f'The URL must be of scheme file (received {解析结果.protocol})')
    return 百分号解码(解析结果.pathname)

def 路径转文件url(路径):
    """文件系统路径的 `file:` URL。"""
    转义=路径.replace('%','%25').replace('\\','%5C').replace('\n','%0A').replace('\r','%0D').replace('\t','%09')
    地址=globals()['URL']('file:///')
    地址.pathname=转义 if 转义.startswith('/') else f'/{转义}'
    return 地址

def 解析(说明符,基址):
    """由说明符及其基址得到绝对 URL。"""
    return str(globals()['URL'](说明符,基址))

fileURLToPath=文件url转路径
pathToFileURL=路径转文件url
resolve=解析
URL=globals()['URL'] if 'URL' in globals() else None
URLSearchParams=globals()['URLSearchParams'] if 'URLSearchParams' in globals() else None
__esModule=True
default={
    'fileURLToPath':文件url转路径,'pathToFileURL':路径转文件url,'resolve':解析,
    'URL':URL,'URLSearchParams':URLSearchParams,
}
