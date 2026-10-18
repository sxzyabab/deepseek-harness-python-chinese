'把生成的 Typert 制品写进各个包自己的 lib。同一批制品再写一遍，盘上字节不变'
import os

__all__=[
    '写包制品','写工作区制品',
]

远程客户端文件=(
    'typert.remote-client.js',
    'typert.remote-client.d.ts',
    'typert.remote-client.d.ts.map',
)

def 写文本(路径,正文):
    '按原文写入。换行保持 LF，失败时原样抛文件系统错误'
    文件=open(路径,'w',encoding='utf-8',newline='\n')
    try:
        文件.write(正文)
    finally:
        文件.close()

def 删除文件(路径):
    '文件不存在则跳过。其余删除失败原样抛出'
    if not os.path.lexists(路径):
        return
    os.remove(路径)

def 有宿主面(制品列表):
    '这一包的制品里有没有 host 面'
    for 制品 in 制品列表:
        if 制品['face']=='host':
            return True
    return False

def 写包制品(包目录,制品列表):
    '写到包目录下的 lib：每个制品一份 typert.<face>。带远程方法时再写三份 remote-client。宿主面没有远程方法时删掉上次留下的远程客户端文件。逐个写，中途失败时这个包可能只换了一部分'
    输出=os.path.join(包目录,'lib')
    os.makedirs(输出,exist_ok=True)
    已写远程=False
    for 制品 in 制品列表:
        面=制品['face']
        写文本(os.path.join(输出,'typert.'+面+'.js'),制品['js'])
        写文本(os.path.join(输出,'typert.'+面+'.d.ts'),制品['dts'])
        if 'remote' in 制品 and 制品['remote'] is not None:
            已写远程=True
            远程=制品['remote']
            写文本(os.path.join(输出,'typert.remote-client.js'),远程['js'])
            写文本(os.path.join(输出,'typert.remote-client.d.ts'),远程['dts'])
            写文本(os.path.join(输出,'typert.remote-client.d.ts.map'),远程['dtsMap'])
    if not 已写远程 and 有宿主面(制品列表):
        for 文件名 in 远程客户端文件:
            删除文件(os.path.join(输出,文件名))

def 写工作区制品(根,制品列表):
    '按制品顺序把每一件写进它自己的包。某一件写失败就停；前面的包留下新文件，后面的包仍是上次的文件'
    for 制品 in 制品列表:
        写包制品(os.path.join(根,制品['packageRoot']),[制品])
