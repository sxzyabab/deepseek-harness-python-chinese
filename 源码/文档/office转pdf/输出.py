"""只读取私有任务目录内有界、普通的 PDF。"""
import os,re,stat#路径打开、PDF 头尾校验、文件类型
from ...工具.超时 import 若已中止则抛出#中止入口
from .异常 import office转pdf错误#分类失败

__all__=['读取pdf']#仅中文公开名

#常量
pdf头模式=re.compile(rb'^%PDF-\d\.\d',re.ASCII)#PDF 魔数

def 读取pdf(路径,上限,信号):
    """拒绝缺失、链接形、超限、截断与非 PDF 输出；返回独立于临时文件的完整字节。"""
    若已中止则抛出(信号)#入口检查
    条目=os.lstat(路径)#不跟随链接
    if not stat.S_ISREG(条目.st_mode):#非普通文件
        raise office转pdf错误('invalid-output','The converter output is not a regular file.')#拒绝
    句柄=os.open(路径,os.O_RDONLY|os.O_NOFOLLOW)#只读且不跟随
    try:
        信息=os.fstat(句柄)#再检
        if not stat.S_ISREG(信息.st_mode):#非普通文件
            raise office转pdf错误('invalid-output','The converter output is not a regular file.')#拒绝
        if 信息.st_size>上限:#已知过大
            raise office转pdf错误('output-too-large','The converted PDF exceeds maxOutputBytes.')#拒绝
        缓冲=bytearray(信息.st_size+1)#多一字节探测
        已读=0#累计
        while 已读<len(缓冲):#循环读
            若已中止则抛出(信号)#读中检查
            片=os.read(句柄,len(缓冲)-已读)#一块
            if len(片)==0:#EOF
                break#结束
            缓冲[已读:已读+len(片)]=片#写入
            已读+=len(片)#推进
        若已中止则抛出(信号)#读后检查
        if 已读>上限:#超限
            raise office转pdf错误('output-too-large','The converted PDF exceeds maxOutputBytes.')#拒绝
        pdf=bytes(缓冲[:已读])#定长
        尾=pdf[-1024:] if 已读>=1024 else pdf#尾窗
        if 已读!=信息.st_size or pdf头模式.match(pdf[:8]) is None or not 尾.decode('ascii','replace').rstrip().endswith('%%EOF'):#不完整
            raise office转pdf错误('invalid-output','The converter did not produce a complete PDF.')#拒绝
        return pdf#完整 PDF
    finally:
        os.close(句柄)#关闭
