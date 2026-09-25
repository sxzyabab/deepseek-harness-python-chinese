"""命令贡献与不可变目录值。

区域：'page' | 'editable' | 'terminal'
上下文 dict：可选 source、region、modal、target
解析结果：status in ('handled','blocked','pass')；handled 含 run 可调用；blocked 含 reason
命令 dict：id、label()、aliases、defaults、regions、modals、resolve(上下文)
目录行 dict：id、label、aliases、keys、aria、binding、modified、conflicts、issue
手势 dict：code、可选 secondCode、control、alt、shift、meta、repeat、composing、defaultPrevented
固定输入：type=='keydown' 含 gesture、context、consume；或 type=='reset'
固定命令 dict：id、label()、keys、bindings、group
固定目录行 dict：id、label、keys、bindings、group
快捷键服务面：runtime、platform、catalog、config、fixedCatalog、stopSequenceMs、
  registerFixed、observeFixedInput、describeBinding、edit、recording、closeWindow、register
"""

__all__=[]#纯约定模块，无运行时导出
