from . import DeepSeek模型标签,文案
from .DeepSeek模型标签 import DeepSeek模型标签 as 标签组件
from .文案 import 中文,俄文,德文,日文,法文,英文,西班牙文,葡萄牙文

__all__=['DeepSeek模型标签','文案','名称','依赖','应用']

名称='ui-deepseek-model-label-1017'
命名空间='deepseek-model-label-1017'
依赖=['slots','locale']

def 应用(上下文,配置=None):
    '在模型标签槽还挂着的时候，给对得上的官方 Flash 加上角标'
    def 登记词典():
        '挂上各语言文案。看得见的字走中文表'
        return 上下文.locale.register(命名空间,{
            'zh':中文,'en':英文,'ja':日文,'es':西班牙文,'fr':法文,'de':德文,'ru':俄文,'pt':葡萄牙文,
        })
    上下文.副作用(登记词典,'deepseek-model-label-1017: dictionaries')
    def 挂标签():
        '登记到输入框模型名槽'
        return 上下文.slots.register({
            'name':'conversation.input.model.label',
            'locale':命名空间,
        },标签组件)
    上下文.slots.inject('conversation.input.model.label',挂标签)

inject=依赖
name=名称
apply=应用
default=应用
