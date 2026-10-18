import json
from ...依赖.schemastery import 枚举字段,字符串字段
from .主题设置 import (
    主题偏好表,默认偏好,字号规格,字号模式,字体角色,字体族变量,规范化字体族,
)
from . import (
    异常,
    主题设置,
    客户端,
)

__all__=['应用','配置','异常','主题设置','客户端']

def 读易失(字段):
    '易失单元格读 get；普通值原样返回'
    if isinstance(字段,(dict,list,str,bytes,bytearray,bool,int,float)) or 字段 is None:
        return 字段
    取值=getattr(字段,'get',None)
    if callable(取值):
        return 取值()
    return 字段

def 易失(字段):
    '标记该字段运行中可更新'
    字段.meta={'volatile':True}
    return 字段

配置={
    'preference':易失(枚举字段(*主题偏好表,默认值=默认偏好)),
    'fontSize':易失(字号模式(字号规格['text'])),
    'codeFontSize':易失(字号模式(字号规格['code'])),
    'terminalFontSize':易失(字号模式(字号规格['terminal'])),
    'textFontFamily':易失(字符串字段(默认值='')),
    'codeFontFamily':易失(字符串字段(默认值='')),
    'terminalFontFamily':易失(字符串字段(默认值='')),
}

def 应用(上下文,配置对象):
    '关掉设置自动呈现，并把当前调色板、字号和字体注入 index'
    def 接线(子上下文):
        '有 settings 时关掉自动呈现'
        def 挂():
            'auto:false 绑到本纤程'
            return 子上下文.settings.configure({'auto':False},上下文.纤程)
        子上下文.副作用(挂)
    上下文.依赖启动(['settings'],接线)
    def 注入索引(表):
        '把启动主题行推到注入表最前'
        偏好=读易失(配置对象['preference'])
        字号表={
            'text':读易失(配置对象['fontSize']),
            'code':读易失(配置对象['codeFontSize']),
            'terminal':读易失(配置对象['terminalFontSize']),
        }
        字体族表={
            'text':读易失(配置对象['textFontFamily']),
            'code':读易失(配置对象['codeFontFamily']),
            'terminal':读易失(配置对象['terminalFontFamily']),
        }
        浅色画布='#fff'
        深色画布='#151517'
        浅色=':root{color-scheme:light}body{background-color:'+浅色画布+';--dsh-boot-bg:'+浅色画布+'}'
        深色=':root{color-scheme:dark}body{background-color:'+深色画布+';--dsh-boot-bg:'+深色画布+'}'
        if 偏好=='light':
            样式文本=浅色
        elif 偏好=='dark':
            样式文本=深色
        else:
            样式文本=浅色+'@media(prefers-color-scheme:dark){'+深色+'}'
        尺寸段=''
        字体段=''
        for 角色 in 字体角色:
            尺寸段+=(
                '\n  document.body.style.setProperty('
                +json.dumps(字号规格[角色]['variable'])+', '
                +json.dumps(str(字号表[角色])+'px')+')'
            )
            列表=规范化字体族(字体族表[角色])
            if 列表!='':
                字体段+=(
                    '\n  document.body.style.setProperty('
                    +json.dumps(字体族变量(角色))+', '
                    +json.dumps(列表)+')'
                )
        脚本体=(
            '(() => {\n'
            '  const preference = '+json.dumps(偏好)+'\n'
            "  const systemDark = preference === 'system'\n"
            "    && typeof matchMedia !== 'undefined'\n"
            "    && matchMedia('(prefers-color-scheme: dark)').matches\n"
            "  const dark = preference === 'dark' || systemDark\n"
            '  document.documentElement.dataset.dsThemeSource = preference\n'
            "  document.body.toggleAttribute('data-ds-dark-theme', dark)"
            +尺寸段+字体段+'\n'
            '})()'
        )
        表.extend([
            {'kind':'style','text':样式文本},
            {'kind':'script','placement':'body','text':脚本体},
        ])
    上下文.监听('webserver/index-inject',注入索引,{'前置':True})

apply=应用
Config=配置
