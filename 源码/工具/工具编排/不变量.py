from __future__ import annotations as 注解

from typing import NoReturn as 无返回

from ...模型后端.llm.品牌 import 调用标识 as 工具调用标识

def 断言有效工具调用标识(标识:工具调用标识)->None:
    "断言工具调用标识有效。"
    if not 是有效工具调用标识(标识):
        抛无效工具调用标识(标识)

def 断言有效工具名(名称:str)->None:
    "断言工具名有效。"
    if not 是有效工具名(名称):
        抛无效工具名(名称)

def 是有效工具调用标识(标识:工具调用标识)->bool:
    "工具调用标识是否有效。"
    return bool(标识) and all(字.isalnum() or 字 in "-_" for 字 in 标识)

def 是有效工具名(名称:str)->bool:
    "工具名是否有效。"
    return bool(名称) and all(字.isalnum() or 字 in "-_" for 字 in 名称)

def 抛无效工具调用标识(标识:工具调用标识)->无返回:
    "抛出无效工具调用标识错误。"
    raise ValueError(f"无效工具调用标识:{标识!r}")

def 抛无效工具名(名称:str)->无返回:
    "抛出无效工具名错误。"
    raise ValueError(f"无效工具名:{名称!r}")
