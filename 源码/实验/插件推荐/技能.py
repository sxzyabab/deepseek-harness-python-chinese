'按需提供的官方插件目录，只服务明确的产品用途'
import os
from ...基础设施.js特性 import PromiseEX as 期约
from ...基础设施.通用工具 import 紧凑json编码
from ...技能.技能 import 捆绑技能排名
from ...内核.智能体循环.中止与并发 import 已中止,若已中止则抛出

__all__=['可推荐','登记官方插件技能']

技能文件=os.path.join(os.path.dirname(__file__),'skills','official-plugins.md')

def 可推荐(组合包):
    '只收随安装提供的可选插件。不接受任意安装目标'
    return bool(组合包.get('official') and 组合包.get('optional') and 组合包.get('availability')!='missing'
        and 组合包.get('readOnlyReason') is None and 组合包.get('error') is None)

def 目录文本(组合包列表):
    '技能列出的可推荐插件：名字、标题、说明和是否已选'
    行=[]
    for 组合包 in 组合包列表:
        if not 可推荐(组合包):
            continue
        元=组合包.get('meta') if isinstance(组合包.get('meta'),dict) else {}
        标题=元.get('title') if 元.get('title') is not None else 组合包['name']
        说明=元.get('description')
        if 说明 is None:
            说明=组合包.get('description') if 组合包.get('description') is not None else ''
        行.append({'name':组合包['name'],'title':标题,'description':说明,'enabled':组合包.get('enabled')})
    return 紧凑json编码(行)

def 登记官方插件技能(上下文):
    '登记本实验的技能，不增加模型工具，也不增加系统提示段落'
    候选={
        'name':'official-plugins',
        'description':'Check DSH’s optional plugins when the user asks how to do or use something in this app, whether it can, or says a capability is missing or should change: tools, input, thinking or title display, session search, terminals, worktrees, agent teams, desktop control, automation, access, approvals, badges or signatures, plugins or plugin sources. Not a request to develop DSH, even in its own repository: load before reading files or source. Not for ordinary tasks, quoted wishes or declined offers.',
        'invocation':{'modelInvocable':True,'userInvocable':False},
        'provider':'dsh-official-plugins',
        'source':'bundled',
        'rank':捆绑技能排名,
        'locator':None,
    }
    def 列出():
        '目录里只有这一条'
        盒=期约()
        盒.解决([候选])
        return 盒
    def 获取(_候选,选项):
        '读随包说明，再附上当前可推荐目录'
        盒=期约()
        try:
            信号=选项.get('signal') if isinstance(选项,dict) else None
            if 已中止(信号):
                若已中止则抛出(信号)
            文件=open(技能文件,'r',encoding='utf-8')
            try:
                政策=文件.read()
            finally:
                文件.close()
            目录=目录文本(上下文.pluginManager.列出组合包())
            if 已中止(信号):
                若已中止则抛出(信号)
            条目={键:值 for 键,值 in 候选.items() if 键 not in ('rank','locator')}
            条目['content']=政策+'\n## Official plugins\n\n'+目录
            盒.解决(条目)
        except Exception as 错误:
            盒.拒绝(错误)
        return 盒
    def 构造(_控制=None):
        '借用的同进程提供方'
        return {'name':候选['provider'],'list':列出,'get':获取}
    上下文.skills.登记提供方(构造)
