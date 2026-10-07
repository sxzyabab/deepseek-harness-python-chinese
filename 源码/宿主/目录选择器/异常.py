'目录选择缝的带码失败，供浏览原语抛出'
class 目录选择器错误(OSError):#工作区控制器按 OSError 接住后再读 code/path
    '关闭的业务码：directory-unreadable、directory-exists、directory-create-failed'
    def __init__(自身,码,路径,消息):#码、绝对路径、给人看的说明
        '记下业务码与路径'
        super().__init__(消息)#消息
        自身.code=码#业务码
        自身.path=路径#绝对路径
        自身.name='DirectoryPickerError'#错误名
