from __future__ import annotations
import math
from .models import EnergySnapshot, PriDecision

def clamp(v,lo,hi): return max(lo,min(hi,v))
def score(import_w,export_w,weight_import,weight_export):
    return max(import_w,0.0)*weight_import+max(export_w,0.0)*weight_export

def house_target_level(house_w,step_w,weight_import=1.0,weight_export=1.0):
    """Diagnostic seulement."""
    if step_w<=0:return 100,0.0,0.0
    h=max(float(house_w),0.0)
    t=0 if h<=0 else int(clamp(math.ceil(h/step_w)*10,0,100))
    return t,0.0,0.0

def decide_zero(snapshot:EnergySnapshot,current_level:int,settings:dict[str,object])->PriDecision:
    export_limit=max(float(settings.get("pri_export_acceptable_w",150.0)),0.0)
    import_limit=max(float(settings.get("pri_import_acceptable_w",200.0)),0.0)
    diag,_,_=house_target_level(snapshot.house_w,float(settings.get("pri_step_w",400.0)))
    if snapshot.export_w>export_limit:
        target=max(current_level-10,0)
        return PriDecision("descente" if target<current_level else "maintien",current_level,target,
            f"Export {snapshot.export_w:.0f} W > {export_limit:.0f} W : PRI {current_level}% -> {target}%.",
            snapshot.export_w,0.0,diag)
    if snapshot.import_w>import_limit:
        target=min(current_level+10,100)
        return PriDecision("remontee" if target>current_level else "maintien",current_level,target,
            f"Import {snapshot.import_w:.0f} W > {import_limit:.0f} W : PRI {current_level}% -> {target}%.",
            snapshot.import_w,0.0,diag)
    return PriDecision("maintien",current_level,current_level,
        f"Zone neutre réseau : export={snapshot.export_w:.0f} W, import={snapshot.import_w:.0f} W : maintien {current_level}%.",
        0.0,0.0,diag)

def decide_dynamic(snapshot:EnergySnapshot,current_level:int,settings:dict[str,object],injection_price:float|None,boiler_absorbing:bool)->PriDecision:
    return decide_zero(snapshot,current_level,settings)
