"""计划域的纯类型：`plan` 投影键声明的唯一归属处，不引入本包宿主侧值导入（cordis 服务、dsh-tools、dsh-agent）。两处命名空间投影为它服务——`./类型` 给宿主消费方，`./客户端` 给客户端聚合——内容零重复。"""
from typing import TypedDict#结构类型

__all__=['计划投影字段','计划投影']#公开面

计划投影字段=('active','pending')#线上值：已记录模式与是否有未决选择

class 计划投影(TypedDict):#plan 投影的线上值
    active:bool#已提交状态
    pending:bool#是否有未决选择
