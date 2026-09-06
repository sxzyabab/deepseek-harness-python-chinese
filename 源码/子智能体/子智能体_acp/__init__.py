"""进程外 ACP 子智能体后端（对齐 upstream subagent-acp）。"""
from ...依赖.schemastery import 字典字段,字符串字段,列表字段,数字字段#配置
from ..子智能体.错误 import 子智能体错误#缝内失败
from .运行 import 启动acp跑,默认处置eof宽限毫秒,默认处置宽限毫秒#运行

名称='subagent-acp'#Cordis 插件名
注入=['subagents','subprocess']#依赖
配置=字典字段({
    'providerName':字符串字段(默认值='acp'),
    'command':字符串字段(),#可执行文件必填
    'args':列表字段(字符串字段(),默认值=[]),
    'cwd':字符串字段(),
    'permission':字符串字段(默认值='reject'),
    'env':字典字段[字符串字段(),字符串字段()](默认值={}),
    'disposeEofGraceMs':数字字段(默认值=默认处置eof宽限毫秒),
    'disposeGraceMs':数字字段(默认值=默认处置宽限毫秒),
})#配置

__all__=['名称','注入','配置','应用']#公开面

class acp提供方:
    """进程外 ACP 子体；不广告父侧启动能力。"""
    def __init__(自身,名,规格):
        """记下提供方名、能力与运行规格。规格为 dict。"""
        自身.名称=名#名
        自身.能力={}#无启动能力
        自身.继承父上下文=False#契约
        自身._规格=规格#运行规格

    def 启动(自身,请求):
        """启动 ACP 一次性跑。请求为 dict。"""
        return 启动acp跑(请求,自身._规格)#进程外跑

def 应用(上下文,配置值):
    """加载 ACP 提供方。配置为 dict。"""
    命令=str(配置值['command'] if 'command' in 配置值 else '').strip()#命令
    if len(命令)==0:#无命令
        raise 子智能体错误('subagent-acp: command is required','INVALID_CONFIG')#拒绝
    名=配置值['providerName'] if 'providerName' in 配置值 else 'acp'#名
    规格={#运行规格
        'command':配置值['command'],#命令
        'args':配置值['args'] if 'args' in 配置值 else [],#参数
        'cwd':配置值['cwd'] if 'cwd' in 配置值 else None,#工作目录
        'permission':配置值['permission'] if 'permission' in 配置值 else 'reject',#权限
        'env':配置值['env'] if 'env' in 配置值 else {},#环境
        'disposeEofGraceMs':配置值['disposeEofGraceMs'] if 'disposeEofGraceMs' in 配置值 else 默认处置eof宽限毫秒,#EOF 宽限
        'disposeGraceMs':配置值['disposeGraceMs'] if 'disposeGraceMs' in 配置值 else 默认处置宽限毫秒,#处置宽限
        'subprocess':上下文.subprocess,#子进程缝
    }#规格结束
    上下文.subagents.登记提供方(acp提供方(名,规格))#登记

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=应用#框架槽
