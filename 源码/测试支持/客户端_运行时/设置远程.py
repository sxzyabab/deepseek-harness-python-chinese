"""bench 插件所注入的 settings Remote 命名空间的测试替身。

对齐上游 `client-runtime/src/settings-remote.ts`。公开面仅中文名。
"""
from .设置作用域 import 间谍函数#spy（与设置作用域共用，无额外文件）

__all__=['脚本化设置远程']#仅中文公开名

def 脚本化设置远程(命名空间们=None,选项=None):#构建脚本化 settings 远程
    """为 bench 构建脚本化 settings Remote 命名空间。"""
    if 命名空间们 is None:#缺省
        命名空间们=[]#空列表
    if 选项 is None:#缺省
        选项={}#空映射
    服务中=[list(命名空间们)]#当前服务的视图（可变盒）
    可写=选项['writable'] if 'writable' in 选项 else True#可写
    有文档=选项['hasDocument'] if 'hasDocument' in 选项 else False#是否有文档
    def 应答(命名空间键):#按键应答
        """成功回显匹配视图，否则拒绝。"""
        视图=next((候选 for 候选 in 服务中[0] if (候选.get('ns') if isinstance(候选,dict) else getattr(候选,'ns',None))==命名空间键),None)#按键查找
        if 视图 is None:#无匹配
            return {'ok':False,'error':{'code':'settings/rejected','message':f'no scripted namespace "{命名空间键}"','details':{'ns':命名空间键}}}#拒绝
        return {'ok':True,'value':视图}#成功应答
    更新=间谍函数(lambda 命名空间键,_补丁,_修订:应答(命名空间键))#update spy
    替换=间谍函数(lambda 命名空间键,_段,_修订:应答(命名空间键))#replace spy
    变更=间谍函数(lambda 命名空间键,_操作,_修订:应答(命名空间键))#mutate spy
    def 发布(下一批):#发布
        """替换服务视图。"""
        服务中[0]=list(下一批)#替换
    return {#返回面
        'settings':{#settings 实现
            'describe':lambda:{'ok':True,'value':{'writable':可写,'hasDocument':有文档,'namespaces':服务中[0]}},#描述
            'update':更新,#转发 update
            'replace':替换,#转发 replace
            'mutate':变更,#转发 mutate
        },#settings 结束
        'update':更新,#暴露 update spy
        'replace':替换,#暴露 replace spy
        'mutate':变更,#暴露 mutate spy
        'publish':发布,#替换服务视图
    }#返回结束

scriptedSettingsRemote=脚本化设置远程#上游名
