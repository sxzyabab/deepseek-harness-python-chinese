'配置档装载操作共用的可本地化拒绝'

__all__=['装载失败','非法安装规格错误','注册表错误','安装已取消错误']

class 装载失败(Exception):
    '预期的装载拒绝；呈现交给调用方词典'
    def __init__(自身,码):
        '记下可本地化拒绝码；消息原样为码字符串'
        super().__init__(码)
        自身.code=码

class 非法安装规格错误(Exception):
    'pnpm 与注册表都不会接受的规格；reason 给人读'
    def __init__(自身,规格,理由):
        '记下修剪后的规格与一句拒绝理由'
        super().__init__('plugin-manager: '+理由+': '+规格)
        自身.name='InvalidInstallSpecError'
        自身.spec=规格
        自身.reason=理由

class 注册表错误(Exception):
    '插件装载注册表解析失败'

class 安装已取消错误(Exception):
    '调用方停止安装；文件已恢复后抛出'
    def __init__(自身):
        '固定消息'
        super().__init__('安装已取消')
        自身.name='InstallCancelledError'#错误名
