import re#开 body 定位
from ...基础设施.通用工具 import 紧凑json编码
from .主题设置 import 默认偏好,默认字号,默认字号表,默认字体族,字号规格,字体角色,字体族变量,规范化字体族

__all__=['启动主题注入行','注入启动主题']

开体标签=re.compile(r'<body(?:\s[^>]*)?>',re.I|re.ASCII)#定位开 body 标签；空白只吃 ASCII
浅色画布='#fff'
深色画布='#151517'

def 启动主题样式(偏好):#按偏好拼头部样式
    '在任何脚本执行前给文档画布上色的 CSS'
    浅色=':root{color-scheme:light}body{background-color:'+浅色画布+';--dsh-boot-bg:'+浅色画布+'}'#浅色规则
    深色=':root{color-scheme:dark}body{background-color:'+深色画布+';--dsh-boot-bg:'+深色画布+'}'#深色规则
    if 偏好=='light':#强制浅色
        return 浅色
    if 偏好=='dark':#强制深色
        return 深色
    return 浅色+'@media(prefers-color-scheme:dark){'+深色+'}'#系统偏好

def 收齐字号(字号,字号表):
    '单个正文字号补成三角色；显式字号表优先'
    结果=dict(默认字号表)
    if type(字号) is int:
        结果['text']=字号
    if isinstance(字号表,dict):
        for 角色 in 字体角色:
            if 角色 in 字号表 and type(字号表[角色]) is int:
                结果[角色]=字号表[角色]
    return 结果

def 启动主题脚本(偏好,字号=None,字号表=None,字体族=None):#按偏好与字体拼脚本体
    '构造安装调色板、三种字号和非空字体列表的 body 脚本'
    尺寸=收齐字号(字号,字号表)
    族=dict(默认字体族)
    if isinstance(字体族,dict):
        for 角色 in 字体角色:
            if 角色 in 字体族:
                族[角色]=规范化字体族(字体族[角色])
    声明=''
    for 角色 in 字体角色:
        声明+='document.body.style.setProperty('+紧凑json编码(字号规格[角色]['variable'])+', '+紧凑json编码(str(尺寸[角色])+'px')+');'
        if len(族[角色])>0:
            声明+='document.body.style.setProperty('+紧凑json编码(字体族变量(角色))+', '+紧凑json编码(族[角色])+');'
    return (#立即执行，避免污染全局
        '(() => {'#开 IIFE
        +'const preference = '+紧凑json编码(偏好)+';'#嵌入当前内置偏好
        +'const systemDark = preference === \'system\''#偏好为跟随系统
        +' && typeof matchMedia !== \'undefined\''#且存在 matchMedia
        +' && matchMedia(\'(prefers-color-scheme: dark)\').matches;'#且系统为暗色
        +'const dark = preference === \'dark\' || systemDark;'#显式暗色或系统暗色
        +'document.documentElement.dataset.dsThemeSource = preference;'#根节点记下偏好源
        +'document.body.toggleAttribute(\'data-ds-dark-theme\', dark);'#同步 body 暗色属性
        +声明
        +'})()'#内联 IIFE
    )#脚本结束

def 启动主题注入行(偏好=None,字号=None,字号表=None,字体族=None):
    '主题引导行：头部 CSS 先上色，再 body 脚本安装调色板与字体'
    if 偏好 is None:#缺省
        偏好=默认偏好#跟随系统
    if 字号 is None and 字号表 is None:#缺省
        字号=默认字号#默认正文字号
    return [#注入行
        {'kind':'style','text':启动主题样式(偏好)},#头部样式
        {'kind':'script','placement':'body','text':启动主题脚本(偏好,字号,字号表,字体族)},#body 脚本
    ]#行结束

def 注入启动主题(网页,偏好=None,字号=None):#把引导插入 index HTML
    '把样式与脚本立刻插在开 body 标签之后。无 body 的片段接到末尾'
    行表=启动主题注入行(偏好,字号)#注入行
    片段=''#拼 HTML
    for 行 in 行表:#逐行
        if 行['kind']=='style':#样式
            片段+='<style>'+行['text']+'</style>'#样式标签
        else:#脚本
            片段+='<script>'+行['text']+'</script>'#脚本标签
    命中=开体标签.search(网页)#定位开 body 标签
    if 命中 is None:#无 body 则追加到末尾
        return 网页+片段#追加
    位置=命中.end()#开标签之后的插入点
    return 网页[:位置]+片段+网页[位置:]#紧挨开 body 后插入
