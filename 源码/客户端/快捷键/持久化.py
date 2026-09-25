"""序列化偏好事务；存储所有者只发布已接受写入或读取诊断。"""
import json#文档序列化
from threading import Lock as 锁#单写串行
from uuid import uuid4 as 生成uuid4#修订身份
from .配置文档 import 编辑快捷键文档,有效快捷键,解析快捷键文档#文档事务

__all__=[#仅中文公开名
    '初始快捷键配置','快捷键持久化',
]#公开面结束

生成修订=生成uuid4#随机修订

def 初始快捷键配置():
    """异步适配器启动用的禁用初始快照（本侧同步调用）。"""
    return {#初始快照
        'revision':str(生成修订()),#修订
        'sequence':0,#序号
        'document':{'schemaVersion':1,'profiles':{}},#空文档
        'status':'loading',#加载中
        'error':None,#无错
        'usingDefaults':True,#用默认
    }#快照结束

class 快捷键持久化:
    """localStorage 与 Electron 原子文件适配器共享的单写协调器。"""
    def __init__(自身,存储,运行时,平台,写前重读,发布):
        """记下存储适配器与发布回调。"""
        自身.存储=存储#读写面
        自身.运行时=运行时#壳
        自身.平台=平台#设备
        自身.写前重读=写前重读#写前是否重读
        自身.发布=发布#快照发布
        自身.快照=初始快捷键配置()#当前已接受
        自身.原文=None#上次原始串；未读为未定义语义用对象哨兵
        自身.原文已读=False#是否已成功读过
        自身.定义表=None#产品目录
        自身.活跃=True#是否仍接受
        自身.队锁=锁()#串行

    def 设定定义(自身,定义表):
        """安装或撤销产品目录，并失效其上一寿命的草稿。"""
        自身.定义表=定义表#目录
        自身.接受(dict(自身.快照))#换修订并发布

    def 拆除(自身):
        """停止接受编辑或发布迟到的完成。"""
        自身.活跃=False#停

    def 读当前(自身):
        """读当前文件；失败保留上次已接受文档并禁用普通写入。"""
        with 自身.队锁:#串行
            return 自身.读取()#读

    def 编辑(自身,编辑,修订):
        """比较草稿 revision、校验完整候选，再持久化后发布。"""
        with 自身.队锁:#串行
            if 自身.写前重读:#写前重读
                自身.读取()#刷新
            def 结果(状态):
                """带当前快照的分类结果。"""
                return {'status':状态,'snapshot':自身.快照}#结果
            if not 自身.活跃 or 自身.定义表 is None or 自身.快照['status']=='loading':#未就绪
                return 结果('not-ready')#未就绪
            if 修订!=自身.快照['revision']:#过期
                return 结果('stale')#陈旧
            if 自身.快照['status']=='unreadable':#不可读
                return 结果('unreadable')#不可读
            类型=编辑['type']#编辑类型
            if 类型 in ('set','reset'):#单条须可编辑
                命中=False#是否可编辑命令
                for 行 in 自身.定义表:#逐定义
                    if 行['id']==编辑['id'] and 行.get('fixed') is None:#可编辑
                        命中=True#命中
                        break#止
                if not 命中:#无此命令
                    return 结果('not-ready')#未就绪
            文档=编辑快捷键文档(自身.快照['document'],编辑,自身.运行时,自身.平台)#候选
            行表=有效快捷键(自身.定义表,文档,自身.运行时,自身.平台)#有效行
            非法=None#问题行
            for 行 in 行表:#找非法
                if 类型=='reset-all' or 行['id']==编辑.get('id'):#相关行
                    if 行['issue'] is not None or len(行['conflicts'])>0:#有问题
                        非法=行#记下
                        break#止
            #显式编辑不得静默禁用另一命令的默认绑定
            挤出=None#被挤命令
            if 类型=='set':#设置
                for 行 in 行表:#找含本 id 的冲突
                    if 编辑['id'] in 行['conflicts']:#被本编辑挤
                        挤出=行#记下
                        break#止
            if 非法 is not None or 挤出 is not None:#冲突
                出={**结果('conflict')}#冲突结果
                if 非法 is not None and 非法['issue'] is not None:#有 issue
                    出['issue']=非法['issue']#附带
                if 非法 is not None and len(非法['conflicts'])>0:#冲突列表
                    出['conflicts']=list(非法['conflicts'])#用非法行
                elif 挤出 is not None:#挤出
                    出['conflicts']=[挤出['id']]#被挤 id
                else:#空
                    出['conflicts']=[]#空
                return 出#冲突
            try:#持久化
                原文=json.dumps(文档,ensure_ascii=False,indent=2)+'\n'#美化 JSON
                自身.存储.write(原文)#写入
                自身.原文=原文#记下
                自身.原文已读=True#已有原文
                下一={**自身.快照,'document':文档,'status':'ready','error':None,'usingDefaults':False}#就绪
                自身.接受(下一)#发布
                return 结果('saved')#已存
            except Exception:#写入失败时适配器保留上一份完整文档
                return 结果('write-failed')#写失败

    def 接受(自身,快照):
        """换修订、推进序号并发布。"""
        自身.快照={#新快照
            **快照,
            'sequence':自身.快照['sequence']+1,#推进
            'revision':str(生成修订()),#新修订
        }#快照结束
        if not 自身.活跃:#已拆
            return#不发布
        try:#订阅者
            自身.发布(自身.快照)#发布
        except Exception as 错误:#订阅失败
            print('快捷键配置订阅者失败:',错误)#诊断

    def 读取(自身):
        """读存储；失败保留上次已接受文档。"""
        try:#读原文
            原文=自身.存储.read()#可读 None
        except Exception:#读失败
            if 自身.快照['error']!='read':#尚未记读错
                自身.接受({**自身.快照,'status':'unreadable','error':'read'})#诊断
            return 自身.快照#当前
        if 自身.原文已读 and 原文==自身.原文 and 自身.快照['error']!='read':#未变
            return 自身.快照#复用
        自身.原文=原文#记下
        自身.原文已读=True#已读
        文档=解析快捷键文档(原文)#解码
        if isinstance(文档,str):#分类失败
            自身.接受({**自身.快照,'status':'unreadable','error':文档})#诊断
        else:#已接受文档
            自身.接受({**自身.快照,'document':文档,'status':'ready','error':None,'usingDefaults':原文 is None})#就绪
        return 自身.快照#当前
