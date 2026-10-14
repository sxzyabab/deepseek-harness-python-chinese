'把检查器文档里匹配到的按键转发到父级 iframe，不替换父窗口的命令仲裁'
import json
from nicegui import ui as 界面

__all__=['绑定检查器键盘']

def 安装脚本(元素标识,绑定):
    '在 iframe 文档上安装一次 keydown；绑定含 code 与 modifiers'
    载荷=json.dumps(绑定,ensure_ascii=False)
    return f'''
(function(){{
  const frame=document.getElementById({json.dumps(元素标识)});
  if(!frame) return;
  const binding={载荷};
  if(frame.__dshInspectorRelease) frame.__dshInspectorRelease();
  const attach=()=>{{
    const doc=frame.contentDocument;
    if(!doc) return;
    if(frame.__dshInspectorKey) doc.removeEventListener("keydown", frame.__dshInspectorKey);
    const keydown=(event)=>{{
      if(event.defaultPrevented||event.isComposing||(event.getModifierState&&event.getModifierState("AltGraph"))) return;
      if(!binding||binding.secondCode!=null||binding.code!==event.code) return;
      const flags=[event.ctrlKey,event.altKey,event.shiftKey,event.metaKey];
      const names=["control","alt","shift","meta"];
      const modifiers=binding.modifiers||[];
      for(let i=0;i<4;i++) if(modifiers.includes(names[i])!==flags[i]) return;
      const forwarded=new KeyboardEvent("keydown",{{
        key:event.key,code:event.code,ctrlKey:event.ctrlKey,altKey:event.altKey,
        shiftKey:event.shiftKey,metaKey:event.metaKey,repeat:event.repeat,
        bubbles:true,cancelable:true,composed:true
      }});
      if(!frame.dispatchEvent(forwarded)) event.preventDefault();
    }};
    doc.addEventListener("keydown",keydown);
    frame.__dshInspectorKey=keydown;
  }};
  frame.__dshInspectorRelease=()=>{{
    frame.removeEventListener("load", attach);
    const doc=frame.contentDocument;
    if(doc && frame.__dshInspectorKey) doc.removeEventListener("keydown", frame.__dshInspectorKey);
  }};
  frame.addEventListener("load",attach);
  attach();
}})();
'''

def 页面标识(框):
    'NiceGUI 元素在文档里的 id'
    if hasattr(框,'html_id'):
        return 框.html_id
    标识=getattr(框,'id',None)
    if isinstance(标识,int):
        return 'c'+str(标识)
    if isinstance(标识,str) and 标识!='':
        return 标识
    return None

def 绑定检查器键盘(框,读绑定):
    '按当前有效绑定安装转发，并返回拆除函数'
    def 释放():
        '拆掉文档监听'
        return None
    标识=页面标识(框)
    绑定=读绑定()
    if 标识 is None or not isinstance(绑定,dict) or not 绑定.get('code'):
        return 释放
    界面.run_javascript(安装脚本(标识,绑定))
    def 拆掉():
        '去掉 load 与 keydown'
        界面.run_javascript(
            f'document.getElementById({json.dumps(标识)})?.__dshInspectorRelease?.()'
        )
    return 拆掉
