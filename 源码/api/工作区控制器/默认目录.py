'校验宿主文档目录。不相对当前工作目录解析'
import sys#平台
import ntpath as 窗口路径#win32 路径
import posixpath as 正斜杠路径#posix 路径

__all__=['校验文档目录']


def 校验文档目录(目录,平台=None):
    '目录必须是完全限定路径。win32 上只有盘符或 UNC 根算数，单斜杠根不算'
    if 平台 is None:#未指定
        平台=sys.platform#本机
    路径模块=窗口路径 if 平台=='win32' else 正斜杠路径#按平台
    if 平台=='win32':#分开盘符根和单斜杠根
        驱动,尾=路径模块.splitdrive(目录)#驱动与其余
        if 驱动.startswith('\\\\'):#UNC
            根=驱动 if 驱动.endswith('\\') else 驱动+'\\'#服务器共享根
        elif 驱动!='' and len(尾)>0 and (尾[0]=='\\' or 尾[0]=='/'):#盘符绝对路径
            根=驱动+尾[0]#如 C:\
        elif len(尾)>0 and (尾[0]=='\\' or 尾[0]=='/'):#没有盘符的根
            根=尾[0]#\ 或 /
        else:#相对
            根=''#没有根
    else:#posix
        根='/' if 目录.startswith('/') else ''#绝对根
    if (not 路径模块.isabs(目录)) or (平台=='win32' and (根=='\\' or 根=='/')):#未完全限定
        raise RuntimeError("Documents directory must be fully qualified: '"+目录+"'")#拒绝
    return 路径模块.normpath(目录)#规范化
