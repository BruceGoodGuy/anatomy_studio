"""Đổi các cơ Schutte1993Muscle_Deprecated của MoBL-ARMS thành Millard2012EquilibriumMuscle.

Lý do: bộ giải cân bằng cơ–gân của Schutte (lỗi thời trong OpenSim 4) hội tụ sai tuỳ trạng thái
trước đó (vd. delta trước ra l/l_opt = 3.0 ở tư thế chống đẩy, trong khi đúng là 0.77). Millard 2012
là mô hình cơ mà phần chân (Rajagopal) đang dùng → toàn thân cùng một cách tính.
Giữ nguyên: đường cơ (điểm bám, điểm uốn, mặt quấn), lực tối đa, chiều dài sợi tối ưu, chiều dài
gân nghỉ, góc lông chim. Đường cong lực–chiều dài dùng mặc định của Millard.

    python tools/mobl_to_millard.py assets/model/MoBL_ARMS_J.osim assets/model/MoBL_ARMS_millard.osim
"""
import sys
import xml.etree.ElementTree as ET

KEEP = ["GeometryPath", "max_isometric_force", "optimal_fiber_length", "tendon_slack_length", "pennation_angle_at_optimal",
        "appliesForce", "min_control", "max_control"]


def main(src, dst):
    tree = ET.parse(src)
    n = 0
    for parent in tree.getroot().iter():
        for i, el in enumerate(list(parent)):
            if el.tag != "Schutte1993Muscle_Deprecated":
                continue
            new = ET.Element("Millard2012EquilibriumMuscle", el.attrib)
            for k in KEEP:
                c = el.find(k)
                if c is not None:
                    new.append(c)
            ET.SubElement(new, "max_contraction_velocity").text = "10"
            ET.SubElement(new, "fiber_damping").text = "0.1"
            parent.remove(el)
            parent.insert(i, new)
            n += 1
    tree.write(dst, encoding="UTF-8", xml_declaration=True)
    print(f"{n} cơ → Millard2012EquilibriumMuscle: {dst}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
