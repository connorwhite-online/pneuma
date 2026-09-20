#!/usr/bin/env bash
# Regenerate everything from tools/design.py.  Needs KiCad 10 (for pcbnew/kicad-cli) and a
# Python with cadquery+matplotlib (for the enclosure assembly/plots): set KICAD_APP / CQ_PY.
set -euo pipefail
cd "$(dirname "$0")"
KICAD_APP=${KICAD_APP:-/Applications/KiCad/KiCad.app}
[ -d "$KICAD_APP" ] || KICAD_APP=/Volumes/KiCad/KiCad/KiCad.app
KPY="$KICAD_APP/Contents/Frameworks/Python.framework/Versions/Current/bin/python3"
KCLI="$KICAD_APP/Contents/MacOS/kicad-cli"
export KICAD_SHARE="$KICAD_APP/Contents/SharedSupport"
export KICAD10_3DMODEL_DIR="$KICAD_SHARE/3dmodels"
CQ_PY=${CQ_PY:-python3}
mkdir -p ../out
"$KPY" lib_gen.py
"$KPY" gen_sch.py
"$KPY" gen_pcb.py
"$KPY" export_interface.py 2>/dev/null | grep wrote
python3 bom.py
for b in pneuma-main pneuma-pwr; do
  "$KCLI" sch erc "../$b/$b.kicad_sch" -o "../out/$b-erc.rpt" --severity-error >/dev/null || true
  "$KCLI" pcb drc "../$b/$b.kicad_pcb" -o "../out/$b-drc.rpt" --severity-error >/dev/null || true
  "$KCLI" pcb export step "../$b/$b.kicad_pcb" -o "../out/$b.step" --subst-models --force >/dev/null 2>&1 || true
  "$KCLI" sch export pdf "../$b/$b.kicad_sch" -o "../out/$b-schematic.pdf" >/dev/null 2>&1 || true
  grep -E "ERC messages|Errors" "../out/$b-erc.rpt" | head -1 | sed "s/^/$b ERC: /"
  grep -E "Found [0-9]+ DRC" "../out/$b-drc.rpt" | sed "s/^/$b DRC(errors): /"
done
"$CQ_PY" assemble_L.py 2>/dev/null | head -1
"$CQ_PY" spreader_dxf.py
"$CQ_PY" plot_layout.py
