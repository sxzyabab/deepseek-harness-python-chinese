from uuid import UUID
from dataclasses import dataclass as 数据类

class deepseek网页端:
    def __init__(self,cookie:str):
        self.cookie=cookie

    def 生成对话记录导出链接(self)->str:
        ...

        return '成功执行'

        return '生成未结束'

        return f'{url}'

    def 获取对话记录(self,uuid:UUID|str)->dict:
        ...


@数据类
class 对话:
    uuid:UUID
    所属用户:deepseek网页端
    ...


    def 获取对话内容(self)->dict:
        ...