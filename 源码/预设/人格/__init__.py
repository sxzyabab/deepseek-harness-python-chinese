"""按智能体一份、可组合的人设行。

`system_prompt` 把全局人设当作自己的配置拥有，并无条件注册该段落——因此本行是仅作用域的。
挂进智能体预设时，它为那一次会话遮蔽部署人设；挂到全局则会与注册表自己的注册碰撞并大声失败。

对齐上游 `@deepseek-ai/dsh-persona`。公开面仅中文名。配置键与诊断英文字面量保持上游。
"""
from ...依赖.schemastery import 路径上节点,字符串字段,布尔字段#配置字段
from ..系统提示词 import 人设段落名,人设顺序#人设槽常量，与注册表同一出处

__all__=['名称','注入','配置','应用','人设段落名','人设顺序']#仅中文公开名

名称='persona'#Cordis插件名（字面量）
注入=['systemPrompt']#依赖系统提示词服务
配置=路径上节点({#人设行配置
    'text':字符串字段(可空=False),#必填人设正文
    'complete':布尔字段(默认值=False),#默认不独占
    'includeRuntimeContext':布尔字段(默认值=True),#默认纳入运行时上下文
})#配置模式结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 应用(上下文,配置值):#注册人设段落
    """为挂载上下文的作用域注册人设段落。无作用域的上下文会与提示词注册表自己的人设注册碰撞并拒绝。"""
    正文=取字段(配置值,'text')#人设正文
    独占=取字段(配置值,'complete')#是否独占
    段选项={'name':人设段落名,'order':人设顺序,'text':正文}#段落贡献
    if 独占:#独占整份提示词
        段选项['complete']=True#带 complete
    def 挂段():#按 effect 注册段落
        """登记人设段落，拆除时撤回。"""
        return 上下文.systemPrompt.段落(段选项)#登记并返回拆除器
    上下文.effect(挂段,'persona.section()')#effect 名
    纳入运行时=取字段(配置值,'includeRuntimeContext')#是否纳入运行时上下文
    if 纳入运行时 is None:#缺省与模式默认一致
        纳入运行时=True#默认纳入
    if not 纳入运行时:#关闭运行时上下文
        上下文.systemPrompt.抑制运行时上下文()#压制动态快照
