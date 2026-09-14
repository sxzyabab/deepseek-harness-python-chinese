from ...依赖.schemastery import 字符串字段,布尔字段#配置字段
from ...内核.系统提示词 import 人设段落名,人设顺序#人设槽常量，与注册表同一出处

名称='persona'#Cordis插件名（字面量）
注入=['systemPrompt']#依赖系统提示词服务
配置={#人设行配置
    'text':字符串字段(可空=False),#必填人设正文
    'complete':布尔字段(默认值=False),#默认不独占
    'includeRuntimeContext':布尔字段(默认值=True),#默认纳入运行时上下文
}#配置模式结束

def 应用(上下文,配置值):
    """为挂载上下文的作用域注册人设段落。无作用域的上下文会与提示词注册表自己的人设注册碰撞并拒绝。配置值是 dict。"""
    正文=配置值['text']#人设正文，配置必填
    独占=配置值['complete'] if 'complete' in 配置值 else False#缺键则不独占
    段选项={'name':人设段落名,'order':人设顺序,'text':正文}#段落贡献
    if 独占 is True:#独占整份提示词
        段选项['complete']=True#带 complete
    def 挂段():
        """登记人设段落，拆除时撤回。"""
        return 上下文.systemPrompt.段落(段选项)#登记并返回拆除器
    上下文.副作用(挂段,'persona.section()')#副作用名
    纳入运行时=True if 'includeRuntimeContext' not in 配置值 else 配置值['includeRuntimeContext']#缺键则纳入
    if 纳入运行时 is False:#关闭运行时上下文
        上下文.systemPrompt.抑制运行时上下文()#压制动态快照

__all__=['名称','注入','配置','应用','人设段落名','人设顺序']#仅中文公开名
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明
Config=配置#Cordis 配置模式
apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出
