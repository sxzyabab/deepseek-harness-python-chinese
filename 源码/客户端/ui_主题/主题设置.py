import re#字体名清洗
from ...依赖.schemastery import 枚举字段,整数字段,字符串字段#配置字段
from .异常 import 主题错误#本包异常

__all__=[
    '主题偏好表',
    '主题设置命名空间',
    '主题偏好字段',
    '字号字段',
    '默认偏好',
    '字号最小',
    '字号最大',
    '默认字号',
    '主题设置模式',
    '是否主题偏好',
    '主题错误',
    '字体角色',
    '字号规格',
    '字体族字段',
    '默认字号表',
    '默认字体族',
    '是否字号',
    '规范化字体族',
    '字体族变量',
]

主题偏好表=('light','dark','system')#内置偏好：浅色、深色或跟随系统
主题设置命名空间='ui-theme'#主题插件拥有的设置命名空间
主题偏好字段='preference'#所选内置主题偏好字段名
字号字段='fontSize'#会话内容字号字段名
默认偏好='system'#默认跟随系统
字号最小=12#接受的最小内容字号（px）
字号最大=17#接受的最大内容字号（px）
默认字号=14#无覆盖时的内容字号（px）

字体角色=('text','code','terminal')#正文、代码、侧栏终端
字号规格={#各角色的设置字段、CSS 变量与整数 px 范围
    'text':{'field':字号字段,'variable':'--dsh-content-font-size','min':字号最小,'max':字号最大,'default':默认字号},
    'code':{'field':'codeFontSize','variable':'--dsh-code-font-size','min':10,'max':16,'default':11},
    'terminal':{'field':'terminalFontSize','variable':'--dsh-terminal-font-size','min':10,'max':20,'default':13},
}
字体族字段={'text':'textFontFamily','code':'codeFontFamily','terminal':'terminalFontFamily'}#各角色字体列表字段
默认字号表={角色:字号规格[角色]['default'] for 角色 in 字体角色}#无覆盖时的字号
默认字体族={角色:'' for 角色 in 字体角色}#空串表示用内置字体栈
通用字体族={#CSS 通用族与系统族，保持不加重引号
    'serif','sans-serif','monospace','cursive','fantasy','system-ui','ui-serif','ui-sans-serif',
    'ui-monospace','ui-rounded','emoji','math','fangsong','-apple-system','blinkmacsystemfont',
}
去掉字体名杂质=re.compile('["\'\\\\<>\x00-\x1f\x7f]')#引号、反斜杠、尖括号与控制字符

主题设置模式={#持久主题设置 schema
    主题偏好字段:枚举字段(*主题偏好表,默认值=默认偏好),#preference：浅色、深色或跟随系统，默认跟随系统
    字号字段:整数字段(最小=字号最小,最大=字号最大,默认值=默认字号),#fontSize：整数 px
    字号规格['code']['field']:整数字段(最小=字号规格['code']['min'],最大=字号规格['code']['max'],默认值=字号规格['code']['default']),
    字号规格['terminal']['field']:整数字段(最小=字号规格['terminal']['min'],最大=字号规格['terminal']['max'],默认值=字号规格['terminal']['default']),
    字体族字段['text']:字符串字段(默认值=''),
    字体族字段['code']:字符串字段(默认值=''),
    字体族字段['terminal']:字符串字段(默认值=''),
}#结束主题设置模式

def 是否主题偏好(值):#收窄成可持久化偏好
    '把一条传输或注册表值收窄成可持久化的偏好'
    return 值 in 主题偏好表#内置列表含该值则为偏好

def 是否字号(角色,像素):
    '该角色范围内的整数 px 才接受'
    if 角色 not in 字号规格 or type(像素) is bool or type(像素) is not int:
        return False
    规格=字号规格[角色]
    return 像素>=规格['min'] and 像素<=规格['max']

def 字体族变量(角色):
    '该角色的字体列表写到这个 CSS 变量，排在内置栈前面'
    return '--dsh-font-family-'+角色

def 规范化字体族(值):
    '逗号分隔；去掉引号与控制字符；非通用族加重引号。没有名字时返回空串'
    if not isinstance(值,str):
        return ''
    名表=[]
    for 名 in 值.split(','):
        名=去掉字体名杂质.sub('',名)
        名=re.sub(r'\s+',' ',名).strip()
        if 名=='':
            continue
        if 名.lower() in 通用字体族:
            名表.append(名)
        else:
            名表.append('"'+名+'"')
    return ', '.join(名表)
