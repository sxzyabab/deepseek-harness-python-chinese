from nicegui import ui as 界面

__all__=['样式表']

样式表='''
.日程标记根.mark,
.日程标记根 .mark {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 20px;
  color: var(--dsw-alias-label-tertiary);
}
.日程标记根 .visuallyHidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}
.日程标记根.tasks,
.日程标记根 .tasks {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.日程标记根 .task {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  min-width: 0;
}
.日程标记根 .taskIcon {
  flex: none;
  display: inline-flex;
  align-items: center;
  height: 16px;
  color: #CFD3D6;
}
.日程标记根 .taskBody {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.日程标记根 .taskName {
  font-size: 12px;
  line-height: 16px;
  color: #FFFFFF;
  overflow-wrap: break-word;
}
.日程标记根 .taskTiming {
  font-size: 12px;
  line-height: 16px;
  color: #CFD3D6;
}
.日程标记根 .taskRelative {
  color: #ADB2B8;
  overflow-wrap: anywhere;
}
.日程标记根 .omitted {
  font-size: 12px;
  line-height: 16px;
  color: #ADB2B8;
}
'''
界面.add_css(样式表,shared=True)
