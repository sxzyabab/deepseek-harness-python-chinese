'按需做页面规划，并用当前插件做重复检查'
import os
from ...基础设施.js特性 import PromiseEX as 期约
from ...基础设施.通用工具 import 紧凑json编码
from ...技能.技能 import 捆绑技能排名
from ...内核.智能体循环.中止与并发 import 已中止,若已中止则抛出

__all__=['登记创建技能']

技能文件=os.path.join(os.path.dirname(__file__),'skills','personalized-pages.md')

def 登记创建技能(上下文):
    '登记本实验的技能，不增加系统提示段落'
    候选={
        'name':'personalized-pages',
        'description':'Plan an optional page or small tool when the user asks for a page, tab, panel, tool or interface in this app (even for one-off use), wants something to keep, revisit or update later, will keep changing data in your answer, or wants a live view of this app’s own data (Sessions, tasks, logs, workspace). Load this before reading any files or source; it says how to submit the proposal. Not for requested files or code, ordinary answers, existing-feature questions, quoted wishes or declined offers.',
        'provider':'dsh-personalized-pages',
        'source':'bundled',
        'rank':捆绑技能排名,
        'locator':None,
        'invocation':{'modelInvocable':True,'userInvocable':False},
    }
    def 列出():
        '目录里只有这一条'
        盒=期约()
        盒.解决([候选])
        return 盒
    def 获取(_候选,选项):
        '读随包说明，再附上当前官方插件'
        盒=期约()
        try:
            信号=选项.get('signal') if isinstance(选项,dict) else None
            if 已中止(信号):
                若已中止则抛出(信号)
            文件=open(技能文件,'r',encoding='utf-8')
            try:
                说明=文件.read()
            finally:
                文件.close()
            行=[]
            for 组合包 in 上下文.pluginManager.列出组合包():
                if not 组合包.get('official'):
                    continue
                元=组合包.get('meta') if isinstance(组合包.get('meta'),dict) else {}
                标题=元.get('title') if 元.get('title') is not None else 组合包['name']
                描述=元.get('description')
                if 描述 is None:
                    描述=组合包.get('description') if 组合包.get('description') is not None else ''
                行.append({'name':组合包['name'],'title':标题,'description':描述,'enabled':组合包.get('enabled')})
            if 已中止(信号):
                若已中止则抛出(信号)
            条目={键:值 for 键,值 in 候选.items() if 键 not in ('rank','locator')}
            条目['content']=说明+'\n## Existing capabilities to check against this page plan\n\n'+紧凑json编码(行)
            盒.解决(条目)
        except Exception as 错误:
            盒.拒绝(错误)
        return 盒
    def 构造(_控制=None):
        '借用的同进程提供方'
        return {'name':候选['provider'],'list':列出,'get':获取}
    上下文.skills.登记提供方(构造)
