"""随包 dsh-badge 技能提供方。对齐上游 `@deepseek-ai/dsh-skill-badge`（packages/skill/skill-badge）。"""
import os#资源路径解析
from ...依赖 import cordis#外部依赖胶水
from ..技能 import 捆绑技能排名#打包技能标准排名（与 dsh-skill 同源常量）

__all__=['名称','注入','提供方名','应用','默认']#仅中文公开名；Cordis 槽英文别名不入表

名称='skill-badge'#Cordis插件名（字面量不译）
注入=['skills']#依赖技能注册表
name=名称#Cordis插件名槽
inject=注入#Cordis依赖声明槽
提供方名='dsh-badge'#在 ctx.skills 上的提供方名（字面量不译）
资源目录=os.path.abspath(os.path.join(os.path.dirname(__file__),'资源'))#随包 assets 目录；上游 dsh-badge.png 未随译，缺图不造
技能正文路径=os.path.join(资源目录,'dsh-badge.md')#技能正文路径
资源基址={'kind':'directory','path':资源目录}#随包资源目录基址
调用策略={'modelInvocable':True,'userInvocable':True}#模型与用户均可调用
描述='Add the official “powered by dsh” badge to documents, pull requests, merge requests, and other content produced with DeepSeek Harness. Use whenever creating a pull request or merge request. Also use when the user asks for a dsh badge, powered-by-dsh attribution, or a reusable dsh badge asset or snippet.'#面向模型的描述（字面量不译）
候选={#目录唯一候选
    'name':'dsh-badge',#技能名
    'description':描述,#描述
    'invocation':调用策略,#调用策略
    'provider':提供方名,#提供方
    'source':'bundled',#随包来源
    'resourceBase':资源基址,#资源基址
    'rank':捆绑技能排名,#捆绑排名
    'locator':技能正文路径,#正文定位
}#目录候选结束

def 列出(options=None):#目录只有这一条；options 由注册表传入，本包忽略
    """返回随包候选列表（立刻兑现）。形参 options 与 skill 注册表 list(options) 调用兼容。"""
    return 已兑现([候选])#单元素目录

def 获取(_候选,options=None):#读随包正文；options 由注册表传入，本包忽略
    """加载随包技能正文，拼出完整定义。形参 options 与 skill 注册表 get(candidate, options) 调用兼容。"""
    with open(技能正文路径,'r',encoding='utf-8') as 文件:#读 UTF-8 正文
        正文=文件.read()#技能 Markdown 正文
    return 已兑现({#完整定义（不含 locator/rank）
        'name':候选['name'],#技能名
        'description':候选['description'],#描述
        'invocation':候选['invocation'],#调用策略
        'provider':候选['provider'],#提供方
        'source':候选['source'],#来源
        'resourceBase':资源基址,#资源基址
        'content':正文,#正文
    })#兑现结束

提供方={#不可变技能提供方
    'name':提供方名,#提供方名
    'list':列出,#列目录
    'get':获取,#加载正文
}#技能提供方结束

def 应用(上下文):#登记随包提供方
    """把随包 dsh-badge 提供方登记到 ctx.skills；无配置项。"""
    def 构造(_控制=None):#注册表要的同步工厂
        """返回本提供方（忽略控制面；本包无失效逻辑）。"""
        return 提供方#不可变提供方
    上下文.skills.登记提供方(构造)#挂到技能注册表

apply=应用#Cordis插件入口槽
default=应用#默认导出槽
默认=应用#中文默认导出
