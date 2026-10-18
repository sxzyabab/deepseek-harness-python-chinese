import re
from ...依赖.schemastery import 枚举字段,整数字段,字符串字段

__all__=[
    '主题偏好表','主题设置命名空间','主题偏好字段','字号字段','默认偏好',
    '字号最小','字号最大','默认字号','字体角色','字号规格','字体族字段',
    '默认字号表','默认字体族','字体族变量','字号模式','主题设置模式',
    '是否字号','规范化字体族',
]

主题偏好表=('light','dark','system')
主题设置命名空间='ui-theme'
主题偏好字段='preference'
字号字段='fontSize'
默认偏好='system'
字号最小=10
字号最大=22
默认字号=14
字体角色=('text','code','terminal')
字号规格={
    'text':{'field':字号字段,'variable':'--dsh-content-font-size','min':字号最小,'max':字号最大,'default':默认字号},
    'code':{'field':'codeFontSize','variable':'--dsh-code-font-size','min':10,'max':16,'default':11},
    'terminal':{'field':'terminalFontSize','variable':'--dsh-terminal-font-size','min':10,'max':20,'default':13},
}
字体族字段={
    'text':'textFontFamily',
    'code':'codeFontFamily',
    'terminal':'terminalFontFamily',
}
默认字号表={
    'text':字号规格['text']['default'],
    'code':字号规格['code']['default'],
    'terminal':字号规格['terminal']['default'],
}
默认字体族={'text':'','code':'','terminal':''}
通用字体族={
    'serif','sans-serif','monospace','cursive','fantasy','system-ui','ui-serif','ui-sans-serif',
    'ui-monospace','ui-rounded','emoji','math','fangsong','-apple-system','blinkmacsystemfont',
}
去掉字体名杂质=re.compile('["\'\\\\<>\x00-\x1f\x7f]')

def 字体族变量(角色):
    '该角色的字体列表写到这个 CSS 变量，排在内置栈前面'
    return '--dsh-font-family-'+角色

def 字号模式(规格):
    '该角色字号的整数 px 模式'
    return 整数字段(最小=规格['min'],最大=规格['max'],默认值=规格['default'])

主题设置模式={
    主题偏好字段:枚举字段(*主题偏好表,默认值=默认偏好),
    字号字段:字号模式(字号规格['text']),
    字号规格['code']['field']:字号模式(字号规格['code']),
    字号规格['terminal']['field']:字号模式(字号规格['terminal']),
    字体族字段['text']:字符串字段(默认值=''),
    字体族字段['code']:字符串字段(默认值=''),
    字体族字段['terminal']:字符串字段(默认值=''),
}

def 是否字号(角色,像素):
    '该角色范围内的整数 px 才接受'
    if isinstance(像素,bool) or not isinstance(像素,int):
        return False
    规格=字号规格[角色]
    return 像素>=规格['min'] and 像素<=规格['max']

def 规范化字体族(值):
    '逗号分隔；去掉引号与控制字符；非通用族加重引号。没有名字时返回空串'
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
