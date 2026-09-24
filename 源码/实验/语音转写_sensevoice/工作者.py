import json,os,sys
from .配置 import 应用配置
from .模型推断 import 创建转写器
from .进程服务器 import 启动识别服务器

def 主入口():
    """私有子进程入口；Host 拥有终止，stdout 只报就绪。"""
    原始=json.loads(sys.argv[1])
    路径={'model':原始['model'],'tokens':原始['tokens'],'vad':原始['vad']}
    配置={**应用配置(原始),**路径}
    令牌=os.environ['DSH_SPEECH_TOKEN']
    if len(令牌)!=64:
        raise RuntimeError('invalid speech token')
    del os.environ['DSH_SPEECH_TOKEN']
    服务=启动识别服务器(令牌,配置['maxAudioBytes'],创建转写器(配置))
    sys.stdout.write(json.dumps({'port':服务['port']})+'\n')
    sys.stdout.flush()
    服务['server'].serve_forever()

if __name__=='__main__':
    主入口()
