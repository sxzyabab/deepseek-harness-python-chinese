'Win32 文件夹对话框的纯顺序：DPI、STA、创建、Show、取结果。绑定可替换'
取消HRESULT=0x800704C7#用户关掉对话框
选文件夹=0x20#FOS_PICKFOLDERS
强制文件系统=0x40#FOS_FORCEFILESYSTEM
不改目录=0x8#FOS_NOCHANGEDIR

def 有符号(值):#HRESULT 按 32 位有符号看
    '失败的 HRESULT 小于 0'
    值=值 & 0xFFFFFFFF#32 位
    if 值>=0x80000000:#高位
        return 值-0x100000000#有符号
    return 值#正数

def 检查(结果,何事):#失败就抛
    '成功原样返回'
    if 有符号(结果)<0:#失败
        raise OSError(何事+' failed: HRESULT 0x'+format(结果 & 0xFFFFFFFF,'x'))#带码
    return 结果#成功

def 运行文件夹对话框(绑定,标题,显示中):#在调用线程上跑一次模态对话框
    'Show 之前回调线程号，好让另一线程关掉窗口'
    绑定.设置线程DPI()#尽量要高 DPI
    检查(绑定.初始化套间(),'CoInitializeEx')#STA
    try:#公寓已初始化，每条路径都要反初始化一次
        对话框=绑定.创建文件夹对话框()#COM 对象
        try:#用完释放
            检查(对话框.设置选项(选文件夹 | 强制文件系统 | 不改目录),'SetOptions')#选项
            检查(对话框.设置标题(标题),'SetTitle')#标题
            显示中(绑定.当前线程号())#阻塞前通知
            绑定.按Alt抢前台()#Show 前
            显示结果=对话框.显示()#阻塞到人选完或关掉
            if (显示结果 & 0xFFFFFFFF)==取消HRESULT:#取消
                return None#无路径
            检查(显示结果,'Show')#其它失败
            结果=对话框.结果路径()#路径
            检查(结果['hr'],'GetResult')#取结果失败
            return 结果['path']#选中路径
        finally:#释放对话框
            对话框.释放()#Release
    finally:#反初始化
        绑定.反初始化()#CoUninitialize
