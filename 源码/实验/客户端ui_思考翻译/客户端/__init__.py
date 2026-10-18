'展开思考的可选翻译'
from ....类型化远程调用.协议 import 严格编解码,调用描述符,远程贡献#客户端挂载用的描述符
from . import 挂载#Remote 和槽位
from . import 文案#中英文案表
from . import 翻译#展开区控制器
from . import 偏好表单#暂存表单
from . import 思考正文#展开区界面
from . import 思考设置#插件页界面

__all__=['挂载','文案','翻译','偏好表单','思考正文','思考设置','依赖','应用']

包名='@deepseek-ai/dsh-experimental-client-ui-cot-translation'#生成物上的包名
服务名='cotTranslation'#宿主服务键
命名='cotTranslation'#Remote 命名空间
前缀=包名+'#'+命名+'/'#描述符标识前缀


def 严格(符号):
    '严格编解码。注册表还要 create，这一路不另做结构校验'
    编解码=严格编解码(符号)#模式与类型符号
    def 创建():
        '原样交回透传模式'
        return 编解码['schema']#透传
    编解码['create']=创建#注册表要这个工厂
    return 编解码


远程贡献值=远程贡献(包名,[
    调用描述符(
        前缀+'limits',服务名,命名,'limits',
        [],
        严格('CotTranslationSnapshot'),
        {'file':'src/index.ts','line':47,'column':3},
        取消={'parameter':'signal'},
    ),#不发送文本的限额
    调用描述符(
        前缀+'translate',服务名,命名,'translate',
        [{
            'name':'request',
            'wire':'request',
            'source':'json',
            'codec':严格('TranslationRequest'),
        }],
        严格('string'),
        {'file':'src/index.ts','line':64,'column':3},
        取消={'parameter':'signal'},
    ),#一段展示文本
])#src 里没有生成的 remote 文件，描述符按两个 Remote 方法补上

依赖=挂载.依赖#客户端要等的服务
inject=依赖#框架槽


def 应用(上下文,配置值=None):
    '挂上实验思考展示和它的 Remote。返回卸除函数'
    return 挂载.挂载思考翻译(上下文,远程贡献值)#先 Remote，再界面


apply=应用#客户端入口
default=应用#客户端默认导出
