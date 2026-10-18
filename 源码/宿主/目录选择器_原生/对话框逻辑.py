'Win32 文件夹对话框的纯顺序：DPI、STA、创建、Show、取结果。绑定可替换'
from .异常 import 目录选择器原生错误#失败

取消HRESULT=0x800704C7-0x100000000#用户关掉对话框，与 JS 的 0x800704c7|0 相同
选文件夹=0x20#FOS_PICKFOLDERS
强制文件系统=0x40#FOS_FORCEFILESYSTEM
不改目录=0x8#FOS_NOCHANGEDIR


def 检查(结果,何事):
    'HRESULT 失败就抛，成功原样返回'
    if 结果<0:#失败
        码=format(结果 & 0xFFFFFFFF,'x')#无符号十六进制
        raise 目录选择器原生错误(何事+' failed: HRESULT 0x'+码)#带码
    return 结果#成功


def 运行文件夹对话框(绑定,标题,显示中):
    '在调用线程上跑一次模态对话框。Show 之前把线程号交给显示中'
    绑定.设置线程DPI()#尽量要高 DPI
    检查(绑定.初始化套间(),'CoInitializeEx')#STA
    try:#公寓已初始化，每条路径都要反初始化一次
        对话框=绑定.创建文件夹对话框()#COM 对象
        try:#用完释放
            选项=选文件夹 | 强制文件系统 | 不改目录#文件夹、文件系统、不改工作目录
            检查(对话框.设置选项(选项),'SetOptions')#选项
            检查(对话框.设置标题(标题),'SetTitle')#标题
            显示中(绑定.当前线程号())#阻塞前通知
            绑定.按Alt抢前台()#Show 前
            显示结果=对话框.显示()#阻塞到人选完或关掉
            if 显示结果==取消HRESULT:#取消
                return None#无路径
            检查(显示结果,'Show')#其它失败
            结果=对话框.结果路径()#路径
            检查(结果['hr'],'GetResult')#取结果失败
            return 结果['path']#选中路径
        finally:#释放对话框
            对话框.释放()#Release
    finally:#反初始化
        绑定.反初始化()#CoUninitialize
