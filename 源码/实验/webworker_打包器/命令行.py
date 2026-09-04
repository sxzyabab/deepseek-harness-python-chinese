"""从本仓库打包 Preview 部署：组合并降级基础镜像，再写入每个具名 fixture overlay 及其清单。

用法: dsh-pack-vfs-image --out <file> [--profile web] [--root /dsh]
      node --import tsx/esm src/bin.ts --out ../../apps/web/dist/preview/vfs-image.tar.gz

对齐上游 `webworker-packer/src/bin.ts`。公开面仅中文名。
"""
import json,os,sys#文件系统与进程
from ..webworker_运行时 import (#预览夹具清单面
    预览夹具清单文件,#清单叶名
    预览夹具清单版本,#清单版本
)#运行时结束
from .打包 import 打包虚拟文件系统镜像,打包虚拟文件系统叠加#打包入口
from .仓库 import (#仓库辅助
    组合配置档,配置树列表,描述打包,索引工作区包,预览夹具列表,#仓库函数
)#仓库结束

__all__=[#仅中文公开名
    '主',
]#公开面结束

def 读标志(名,缺省=None):#读一对--flag value
    """读一对 `--flag value`。

    对齐上游 `flag`。
    """
    位置=None#找位置
    标志='--'+名#完整标志
    for 下标,参数 in enumerate(sys.argv):#扫argv
        if 参数==标志:#命中
            位置=下标#记下
            break#停止
    if 位置 is None:#缺席
        if 缺省 is not None:return 缺省#默认
        raise Exception('dsh-pack-vfs-image: --'+名+' is required')#必填
    if 位置+1>=len(sys.argv) or sys.argv[位置+1].startswith('--'):#缺值
        raise Exception('dsh-pack-vfs-image: --'+名+' needs a value')#缺值
    return sys.argv[位置+1]#取值

def 主():#命令行入口
    """从本仓库打包 Preview 部署。"""
    仓库根=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','..','..'))#仓库根
    配置档=读标志('profile','web')#profile名
    输出=读标志('out')#输出路径
    输出文件=输出 if os.path.isabs(输出) else os.path.abspath(os.path.join(os.getcwd(),输出))#绝对输出
    结果=打包虚拟文件系统镜像({#打基础镜像
        'config':组合配置档(仓库根,配置档),#组合配置
        'profile':配置档,#配置档名
        'root':读标志('root','/dsh'),#虚拟根
        'workspaces':索引工作区包(仓库根),#包索引
        'resolveFrom':仓库根,#解析起点
        'configTrees':配置树列表(仓库根),#配置树
    })#打包结束
    if len(结果['missing'])>0:#缺依赖
        raise Exception('vfs image: '+str(len(结果['missing']))+' dependencies did not resolve; the image would be incomplete')#缺依赖
    os.makedirs(os.path.dirname(输出文件),exist_ok=True)#确保目录
    open(输出文件,'wb').write(结果['image'])#写镜像
    夹具定义=预览夹具列表(仓库根)#fixture定义
    夹具目录=os.path.join(os.path.dirname(输出文件),'fixtures')#fixture目录
    os.makedirs(夹具目录,exist_ok=True)#确保夹具目录
    夹具行们=[]#报告行
    夹具们=[]#清单条目
    for 夹具 in 夹具定义:#每个夹具
        已打=打包虚拟文件系统叠加(夹具['trees'])#打overlay
        文件='fixtures/'+夹具['id']+'.tar.gz'#相对路径
        open(os.path.join(os.path.dirname(输出文件),文件),'wb').write(已打['image'])#写overlay
        夹具行们.append('  fixture overlay     '+夹具['id']+' ('+str(len(已打['image']))+' B compressed)')#报告行
        夹具们.append({#清单条目
            'id':夹具['id'],#标识
            'label':夹具['label'],#标签
            'description':夹具['description'],#描述
            'overlays':[文件],#overlay列表
        })#条目结束
    清单={#预览夹具清单
        'version':预览夹具清单版本,#清单版本
        'defaultFixture':(夹具们[0]['id'] if len(夹具们)>0 else None),#默认fixture
        'fixtures':夹具们,#条目
    }#清单结束
    open(os.path.join(os.path.dirname(输出文件),预览夹具清单文件),'w',encoding='utf-8').write(#写清单
        json.dumps(清单,indent=2,ensure_ascii=False)+'\n',#JSON正文
    )#写完
    sys.stdout.write('\n'.join(描述打包(结果,仓库根,输出文件)+夹具行们+['']))#报告

if __name__=='__main__':#直接运行
    主()#入口
