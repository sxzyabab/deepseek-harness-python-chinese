from ...依赖.schemastery import 字典字段,字符串字段,数字字段#配置
from ..子智能体 import 无启动能力,断言可用工作目录#无能力广告与目录校验
from .运行 import 启动codex运行,默认处置宽限毫秒#运行
from . import (
    异常,
)

名称='subagent-codex'#Cordis 插件名
依赖=['subagents','subprocess']#依赖
配置=字典字段(字典结构={
    'providerName':字符串字段(默认值='codex'),
    'permissionMode':字符串字段(默认值='never'),
    'disposeGraceMs':数字字段(默认值=默认处置宽限毫秒),
})#配置

__all__=['名称','依赖','配置','应用']#公开面

class codex提供方:
    '进程外 Codex 子体；不广告父侧启动能力'
    def __init__(自身,名,规格):
        '记下提供方名、能力与运行规格。规格为 dict'
        自身.名称=名#名
        自身.能力=dict(无启动能力)#五项启动能力全关
        自身.继承父上下文=False#契约
        自身._规格=规格#规格

    def 启动(自身,请求):
        '启动 Codex 一次性跑。工作目录来自服务解析后的 request.cwd'
        规格=dict(自身._规格)#拷贝
        规格['cwd']=断言可用工作目录('subagent-codex','child cwd',请求['cwd'])#绝对可进入目录
        return 启动codex运行(请求,规格)#跑

def 应用(上下文,配置值):
    '加载 Codex 提供方。配置为 dict'
    名=配置值['providerName'] if 'providerName' in 配置值 else 'codex'#名
    规格={#运行规格
        'permissionMode':配置值['permissionMode'] if 'permissionMode' in 配置值 else 'never',#权限模式
        'disposeGraceMs':配置值['disposeGraceMs'] if 'disposeGraceMs' in 配置值 else 默认处置宽限毫秒,#处置宽限
        'subprocess':上下文.subprocess,#子进程缝
    }#规格结束
    上下文.subagents.登记提供方(codex提供方(名,规格))#登记

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=应用#框架槽
