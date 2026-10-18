'触发检测和菜单归约的类型。实现在同目录的菜单归约，以及客户端里的控制器'
__all__=['触发命中','菜单状态','菜单事件','检测触发形','菜单归约形','精确匹配形']

#字段 trigger / query / quoted / position / span
触发命中=dict#光标下的一个触发词

#字段 open / hit / generation / groups / highlight
菜单状态=dict#一个源一组；就绪且全空会自己关上

#type 为 hit / source-settled / source-failed / move / hover / close
菜单事件=dict#菜单归约事件

检测触发形=object#草稿、光标、守卫到命中或 None
菜单归约形=object#状态加事件到下一状态；空操作返回同一份
精确匹配形=object#在一个源的就绪组里按名字查找
