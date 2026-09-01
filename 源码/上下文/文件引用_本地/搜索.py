"""工作区文件搜索索引，供 `@file` 补全使用。

对齐上游 `file-reference-local/src/search.ts` 的核心行为。
"""
import os,threading#路径与后台索引
from concurrent.futures import Future as _原生Future#索引任务
from ..文件引用.词法 import 光标处活动令牌,格式化文件提及#再导出词法

默认最大结果数=20#单次查询默认最多候选
默认最大条目数=50000#单工作区索引默认上限
默认排除目录=(#默认跳过的目录基名
    '.git','node_modules','dist','build','out','coverage','target',
    '.next','.nuxt','.turbo','.venv','__pycache__','.pytest_cache','.mypy_cache','.gradle',
)#排除目录结束

__all__=[#仅中文公开名
    '默认最大结果数','默认最大条目数','默认排除目录',
    '工作区文件搜索','光标处活动令牌','格式化文件提及',
]#公开面结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 信号已中止(信号):#对齐 AbortSignal.aborted
    """信号是否已中止。"""
    if 信号 is None:#无信号
        return False#未中止
    if 取字段(信号,'aborted') is True:#英文旗标
        return True#已中止
    if 取字段(信号,'已中止') is True:#中文旗标
        return True#已中止
    return False#未中止

def 规范化查询(查询):#把查询收成可比对的片段
    """统一斜杠并去掉首尾空白。"""
    return str(查询 or '').strip().replace('\\','/')#规范化

def 评分(查询,路径):#简单子串匹配评分
    """查询为空时按路径字典序；否则优先前缀再子串。"""
    小写路径=路径.lower()#小写路径
    小写查询=查询.lower()#小写查询
    if 查询=='':#空查询
        return (0,小写路径)#仅排序
    if 小写路径.startswith(小写查询):#前缀命中
        return (1,len(小写路径))#前缀优先
    位置=小写路径.find(小写查询)#子串位置
    if 位置>=0:#子串命中
        return (2,位置,len(小写路径))#位置越前越好
    return None#未命中

class 工作区文件搜索:#可取消的工作区索引
    """按工作区根目录维护有界路径索引。"""
    def __init__(自身,工作区根,配置=None):#构造索引
        """解析配置并记住根目录。"""
        配置=配置 or {}#默认空配置
        自身.根=os.path.abspath(工作区根)#绝对根
        自身.最大结果=取字段(配置,'maxResults',默认最大结果数)#结果上限
        自身.最大条目=取字段(配置,'maxEntries',默认最大条目数)#索引上限
        排除=取字段(配置,'excludedDirectories',None)#排除目录
        自身.排除=set(排除 if 排除 is not None else 默认排除目录)#排除集合
        自身._代次=0#失效代次
        自身._锁=threading.Lock()#互斥
        自身._条目=None#已建索引
        自身._构建中=None#在途 Future

    def 失效(自身):#使索引过时
        """下一次查询会重建索引。"""
        with 自身._锁:#互斥
            自身._代次+=1# bump 代次
            自身._条目=None#清缓存
            自身._构建中=None#放弃在途

    def 拆除(自身):#释放索引
        """使索引失效，不再构建。"""
        自身.失效()#同失效

    def _遍历(自身,目录,条目们,计数):#深度优先遍历
        """在条目预算内收集文件与目录路径。"""
        if 计数[0]>=自身.最大条目:#已达上限
            return#停止
        try:#列举目录
            名称们=os.listdir(目录)#目录项
        except OSError:#不可读
            return#跳过
        for 名称 in sorted(名称们):#稳定顺序
            if 计数[0]>=自身.最大条目:#预算耗尽
                return#停止
            完整=os.path.join(目录,名称)#完整路径
            相对=os.path.relpath(完整,自身.根).replace('\\','/')#相对路径
            if 名称 in 自身.排除 and os.path.isdir(完整):#排除目录
                continue#跳过
            try:#探测类型
                是目录=os.path.isdir(完整)#是否目录
            except OSError:#不可探测
                continue#跳过
            种类='directory' if 是目录 else 'file'#种类
            条目们.append({'path':相对,'kind':种类})#收录
            计数[0]+=1#计数
            if 是目录:#递归子目录
                自身._遍历(完整,条目们,计数)#深入

    def _确保索引(自身):#懒构建索引
        """首次查询时后台构建；并发查询共享同一 Future。"""
        with 自身._锁:#互斥
            if 自身._条目 is not None:#已有缓存
                return 自身._条目#直接返回
            if 自身._构建中 is not None:#正在构建
                return 自身._构建中#共享 Future
            未来=_原生Future()#新 Future
            自身._构建中=未来#记下在途
            代次=自身._代次#捕获代次
        def 构建():#后台构建体
            """遍历工作区并填充条目。"""
            条目们=[]#收集路径
            计数=[0]#可变计数器
            自身._遍历(自身.根,条目们,计数)#遍历
            with 自身._锁:#写回
                if 代次!=自身._代次:#已失效
                    未来.set_result([])#空索引
                    自身._构建中=None#清在途
                    return#结束
                自身._条目=条目们#缓存
                自身._构建中=None#清在途
                未来.set_result(条目们)#兑现
        threading.Thread(target=构建,daemon=True).start()#后台线程
        return 未来#返回 Future

    def 列举(自身,查询,信号):#列举匹配候选
        """按查询排序并截断到 maxResults。"""
        if 信号已中止(信号):#已取消
            raise Exception('file-reference-local: list cancelled')#取消
        索引未来=自身._确保索引()#确保索引
        索引=索引未来.result() if hasattr(索引未来,'result') else 索引未来#等待索引
        查询串=规范化查询(查询)#规范化查询
        排名=[]#评分结果
        for 候选 in 索引:#扫描索引
            if 信号已中止(信号):#构建后仍要尊重取消
                raise Exception('file-reference-local: list cancelled')#取消
            分=评分(查询串,候选['path'])#评分
            if 分 is None:#未命中
                continue#跳过
            排名.append((分,候选))#记下
        排名.sort(key=lambda 项:项[0])#按分排序
        return [项[1] for 项 in 排名[:自身.最大结果]]#截断返回
