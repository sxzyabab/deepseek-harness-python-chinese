'环境移除把共享凭证政策翻译成 OAR 的覆盖接口'
import os
from ...子进程.子进程 import 擦洗父环境

__all__=['环境覆盖']

def 环境覆盖(额外):
    '只留下擦洗移除、变化的代理值和显式设置，保留原生移除'
    已擦洗=擦洗父环境()
    覆盖={}
    for 键 in list(os.environ.keys()):
        if 键 not in 已擦洗:
            覆盖[键]=None
    for 键,值 in 已擦洗.items():
        if os.environ.get(键)!=值:
            覆盖[键]=值
    结果=dict(覆盖)
    结果.update(额外)
    return 结果
