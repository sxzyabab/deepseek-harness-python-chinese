'本包异常。目录浏览失败与跨文件的错误名判定放在这里'

class 目录浏览错误(Exception):
    '宿主目录业务失败。name 保持 DirectoryBrowseError，插件包不共享异常类身份'
    def __init__(自身,rpc错误):
        'rpc错误为宿主目录失败，带 code 与 message'
        自身.rpcError=rpc错误#宿主失败
        if isinstance(rpc错误,dict):#字典失败
            码=rpc错误.get('code','')#码
            文=rpc错误.get('message','')#说明
        else:#对象失败
            码=getattr(rpc错误,'code','')#码
            文=getattr(rpc错误,'message','')#说明
        super().__init__('directory browse failed: '+str(码)+': '+str(文))#上游原文
        自身.name='DirectoryBrowseError'#类名判定用

def 错误名(错误):
    '插件包按 name 认异常，没有 name 时用类型名'
    if not isinstance(错误,BaseException):#不是异常
        return ''#无名
    名=getattr(错误,'name',None)#显式名
    if isinstance(名,str) and 名!='':#有
        return 名#用它
    return type(错误).__name__#类型名

def 远程码(错误):
    '读 rpcError.code。字典和对象两种都认'
    远程=getattr(错误,'rpcError',None)#远程失败
    if isinstance(远程,dict):#字典
        return 远程.get('code')#码
    return getattr(远程,'code',None)#对象码
