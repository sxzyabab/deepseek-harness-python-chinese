"""捆绑的 Office 工作流与文件系统资源，用于文档编写与结构检查。"""
import os,re,yaml#路径、frontmatter 与 YAML
from ...依赖.schemastery import 字符串字段#配置字段
from ..技能 import 捆绑技能排名#打包技能标准排名

__all__=['名称','注入','配置','应用','默认']#仅中文公开名；Cordis 槽英文别名不入表

#常量
名称='skill-office'#Cordis插件名（字面量不译）
注入=['skills']#依赖 skills 服务
配置={'assetRoot':字符串字段(最小长度=1)}#可选外部资源根；给出时至少一字
技能名列表=('office-docx','office-pptx','office-xlsx')#三个随包 Office 技能名
前栏模式=re.compile(r'^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)')#YAML frontmatter
默认资源根=os.path.abspath(os.path.join(os.path.dirname(__file__),'资源'))#随包资源目录

#工具
class 办公技能错误(Exception):
    """本包异常基类。"""

def 解析技能(原文,路径):
    """拆 frontmatter 与正文；缺描述则抛错。"""
    匹配=前栏模式.match(原文)#匹配开头 YAML 块
    if 匹配 is None:#缺 frontmatter
        raise 办公技能错误('skill-office: '+路径+' has no YAML frontmatter')#缺 frontmatter
    元数据=yaml.safe_load(匹配.group(1))#解析元数据
    描述=None#待取
    if isinstance(元数据,dict) and 'description' in 元数据:#有 description 键
        描述=元数据['description']#取描述
    if not isinstance(描述,str) or len(描述)==0:#描述必填非空
        raise 办公技能错误('skill-office: '+路径+' has no description')#缺描述
    return {'description':描述,'content':原文[匹配.end():].strip()}#正文去掉 frontmatter 后裁空白

#
def 应用(上下文,配置值=None):
    """向技能注册表登记 Office 技能，资源可供脚本解释器读取。"""
    if 配置值 is None:#省略配置
        配置值={}#空配置
    资源根=配置值['assetRoot'] if 'assetRoot' in 配置值 else 默认资源根#默认随包资源
    if not os.path.isabs(资源根):#必须绝对路径
        raise 办公技能错误('skill-office: assetRoot must be an absolute directory')#拒绝相对路径
    检查器=os.path.join(资源根,'scripts','check_office.py')#共享检查器路径
    if not os.path.isfile(检查器):#共享检查器必须存在
        raise 办公技能错误('skill-office: assets must contain scripts/check_office.py')#缺检查器则激活失败
    候选列表=[]#目录候选
    for 技能名 in 技能名列表:#为每个技能建目录候选
        目录=os.path.join(资源根,技能名)#该技能资源目录
        路径=os.path.join(目录,'SKILL.md')#技能正文路径
        with open(路径,'r',encoding='utf-8') as 文件:#同步读
            原文=文件.read()#技能 Markdown
        描述=解析技能(原文,路径)['description']#取描述
        候选列表.append({#目录候选
            'name':技能名,#技能名
            'description':描述,#描述
            'invocation':{'modelInvocable':True,'userInvocable':True},#模型与用户均可调用
            'provider':'dsh-office',#提供方
            'source':'bundled',#随包来源
            'rank':捆绑技能排名,#捆绑排名
            'resourceBase':{'kind':'directory','path':目录},#资源基址
            'locator':路径,#定位器
        })#候选结束
    def 列出(选项=None):
        """返回三候选目录。"""
        return 候选列表#固定三候选
    def 获取(候选,选项=None):
        """按定位器加载正文，拼出完整定义。"""
        if 选项 is None:#省略选项
            选项={}#空
        定位器=候选['locator']#正文路径
        with open(定位器,'r',encoding='utf-8') as 文件:#读 UTF-8
            原文=文件.read()#全文
        正文=解析技能(原文,定位器)['content']#去掉 frontmatter 的正文
        摘要={键:候选[键] for 键 in 候选 if 键!='rank' and 键!='locator'}#去掉 rank 与 locator
        摘要['content']=正文#拼完整定义
        return 摘要#定义
    提供方={#不可变捆绑提供方
        'name':'dsh-office',#提供方名
        'list':列出,#列目录
        'get':获取,#加载正文
    }#提供方结束
    def 构造(_控制=None):
        """返回本提供方。"""
        return 提供方#不可变提供方
    上下文.skills.登记提供方(构造)#挂到技能注册表

name=名称#Cordis插件名槽
inject=注入#Cordis依赖声明槽
Config=配置#Cordis配置模式槽
apply=应用#Cordis插件入口槽
默认=应用#中文默认导出
default=应用#Cordis默认导出槽
