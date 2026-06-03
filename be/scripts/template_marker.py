"""
Template Marker - Click chuột để lấy tọa độ value_zone từ ảnh form chuẩn.

Cách dùng:
    py scripts/template_marker.py <ảnh_form_chuẩn> [advance_payment_slip]

Quy trình:
    1. Cửa sổ OpenCV mở ảnh form chuẩn.
    2. Với MỖI field theo thứ tự script in ra (vd info.don_vi):
         - Click TL (top-left) của value_zone -> chấm xanh.
         - Click BR (bottom-right)            -> hộp đỏ + ghi tọa độ.
    3. Phím tắt:
         u       — undo điểm/box vừa click
         s       — bỏ qua field hiện tại (giữ nguyên tọa độ cũ)
         r       — reset toàn bộ (làm lại từ đầu)
         Enter   — chấp nhận khi đủ box (sẽ ghi file)
         Esc/q   — thoát không ghi
         f       — bật/tắt full-screen
    4. Sau khi xong, script ghi đè value_zone (header/info/footer) và
       x_range/region (line_items) vào template JSON.

Lưu ý:
    - Tọa độ trong template là TƯƠNG ĐỐI (0..1) so với kích thước ảnh.
    - Với line_items, ta yêu cầu click "region" (vùng tổng) trước, rồi
      click x_range của từng cột (chỉ x — y dùng từ region).
    - Backup template cũ tự động: <stem>.bak.json.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import cv2

# UTF-8 stdout cho Windows console
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

WIN = "Template Marker — TL rồi BR; u=undo, s=skip, r=reset, Enter=save, Esc=quit"


def _list_simple_fields(tpl: dict):
    """Sinh list (path, spec) cho các field có value_zone (header/info/footer)."""
    out = []
    for key, spec in tpl.get("header", {}).items():
        out.append((f"header.{key}", spec, "value_zone"))
    for key, spec in tpl.get("info", {}).items():
        out.append((f"info.{key}", spec, "value_zone"))
    for key, spec in tpl.get("footer", {}).items():
        out.append((f"footer.{key}", spec, "value_zone"))
    return out


class Marker:
    def __init__(self, image_path: str, tpl_path: Path):
        self.image_path = image_path
        self.tpl_path = tpl_path
        self.template = json.loads(tpl_path.read_text(encoding="utf-8"))
        self.img_orig = cv2.imread(image_path)
        if self.img_orig is None:
            raise SystemExit(f"❌ Không đọc được ảnh: {image_path}")
        self.h, self.w = self.img_orig.shape[:2]
        self.scale = self._fit_scale()
        self.fullscreen = False
        self.points: list[tuple[int, int]] = []   # 2 điểm tạm thời (TL, BR) cho field hiện tại
        self.boxes: dict[str, list[float]] = {}   # path -> [x0,y0,x1,y1] tương đối
        self.fields = self._build_field_queue()
        self.idx = 0

    # ── chuẩn bị queue field cần click ──────────────
    def _build_field_queue(self) -> list[tuple[str, str]]:
        """Trả [(path, hint)]; line_items: 1 dòng region + N cột x_range."""
        q: list[tuple[str, str]] = []
        for path, _spec, _kind in _list_simple_fields(self.template):
            q.append((path, "TL → BR (góc trên-trái → góc dưới-phải)"))
        li = self.template.get("line_items")
        if li:
            q.append(("line_items.region", "TL → BR cho TOÀN bảng line items"))
            for col_key in li.get("columns", {}).keys():
                q.append((f"line_items.x_range.{col_key}", "TL → BR (chỉ x được dùng)"))
        return q

    def _fit_scale(self) -> float:
        """Co ảnh về khung 1280×900 nếu lớn hơn để vừa màn hình."""
        max_w, max_h = 1280, 900
        s = min(max_w / self.w, max_h / self.h, 1.0)
        return s

    def _disp(self) -> "any":
        """Sinh ảnh hiển thị (đã resize + vẽ lại các box đã ghi + điểm tạm)."""
        if self.scale < 1.0:
            disp = cv2.resize(self.img_orig, None, fx=self.scale, fy=self.scale, interpolation=cv2.INTER_AREA)
        else:
            disp = self.img_orig.copy()

        # Box đã ghi
        for path, rel in self.boxes.items():
            x0 = int(rel[0] * self.w * self.scale)
            y0 = int(rel[1] * self.h * self.scale)
            x1 = int(rel[2] * self.w * self.scale)
            y1 = int(rel[3] * self.h * self.scale)
            cv2.rectangle(disp, (x0, y0), (x1, y1), (0, 200, 0), 2)
            cv2.putText(disp, path, (x0 + 2, max(y0 - 4, 12)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 150, 0), 1, cv2.LINE_AA)

        # Điểm tạm thời (TL nếu chỉ có 1)
        for p in self.points:
            cv2.circle(disp, p, 5, (0, 255, 0), -1)
        if len(self.points) == 2:
            cv2.rectangle(disp, self.points[0], self.points[1], (0, 0, 255), 2)

        # Hướng dẫn field hiện tại
        if self.idx < len(self.fields):
            path, hint = self.fields[self.idx]
            text = f"[{self.idx+1}/{len(self.fields)}] {path}  —  {hint}"
            cv2.putText(disp, text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 200), 2, cv2.LINE_AA)
        else:
            cv2.putText(disp, "ĐỦ — bấm Enter để LƯU, Esc để bỏ.", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 100, 0), 2, cv2.LINE_AA)
        return disp

    def _on_mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and self.idx < len(self.fields):
            self.points.append((x, y))
            if len(self.points) == 2:
                # Convert từ pixel hiển thị → tọa độ tương đối
                (a, b), (c, d) = self.points
                x0, y0 = sorted([a, c])[0], sorted([b, d])[0]
                x1, y1 = sorted([a, c])[1], sorted([b, d])[1]
                rel = [
                    x0 / (self.w * self.scale),
                    y0 / (self.h * self.scale),
                    x1 / (self.w * self.scale),
                    y1 / (self.h * self.scale),
                ]
                rel = [round(v, 4) for v in rel]
                path, _ = self.fields[self.idx]
                self.boxes[path] = rel
                self.points = []
                self.idx += 1
                print(f"  ✓ {path}: {rel}")

    def _undo(self) -> None:
        if self.points:
            self.points.pop()
            return
        if self.idx > 0:
            self.idx -= 1
            path, _ = self.fields[self.idx]
            self.boxes.pop(path, None)
            print(f"  ↩ undo {path}")

    def _reset(self) -> None:
        self.points.clear()
        self.boxes.clear()
        self.idx = 0
        print("  ↺ reset")

    def _toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        prop = cv2.WINDOW_FULLSCREEN if self.fullscreen else cv2.WINDOW_NORMAL
        cv2.setWindowProperty(WIN, cv2.WND_PROP_FULLSCREEN, prop)

    def _save(self) -> None:
        """Ghi tọa độ vào template JSON. Backup file cũ."""
        bak = self.tpl_path.with_suffix(".bak.json")
        shutil.copy2(self.tpl_path, bak)
        print(f"📦 Backup template cũ: {bak.name}")

        for path, rel in self.boxes.items():
            head, _, key = path.partition(".")
            if path.startswith("header.") or path.startswith("info.") or path.startswith("footer."):
                self.template[head][key]["value_zone"] = rel
            elif path == "line_items.region":
                self.template["line_items"]["region"] = rel
            elif path.startswith("line_items.x_range."):
                col_key = path.split(".", 2)[2]
                self.template["line_items"]["columns"][col_key]["x_range"] = [rel[0], rel[2]]

        self.tpl_path.write_text(
            json.dumps(self.template, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"✅ Đã ghi: {self.tpl_path}")

    def run(self) -> None:
        cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WIN, int(self.w * self.scale) + 20, int(self.h * self.scale) + 20)
        cv2.setMouseCallback(WIN, self._on_mouse)

        print("\nFields cần click (theo thứ tự):")
        for i, (path, hint) in enumerate(self.fields):
            print(f"  {i+1:2d}. {path:38s} — {hint}")
        print()

        while True:
            cv2.imshow(WIN, self._disp())
            key = cv2.waitKey(20) & 0xFF
            if key == 27 or key == ord("q"):
                print("✗ Hủy, không lưu.")
                break
            if key == 13:  # Enter
                if not self.boxes:
                    print("⚠ Chưa click box nào.")
                    continue
                self._save()
                break
            if key == ord("u"):
                self._undo()
            elif key == ord("s") and self.idx < len(self.fields):
                path, _ = self.fields[self.idx]
                print(f"  ⤳ skip {path}")
                self.idx += 1
                self.points.clear()
            elif key == ord("r"):
                self._reset()
            elif key == ord("f"):
                self._toggle_fullscreen()

        cv2.destroyAllWindows()


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    image_path = sys.argv[1]
    doc_type = sys.argv[2] if len(sys.argv) > 2 else "advance_payment_slip"
    tpl_path = Path(__file__).resolve().parent.parent / "app" / "templates" / f"{doc_type}.json"
    if not tpl_path.exists():
        print(f"❌ Template không tồn tại: {tpl_path}")
        return 1

    Marker(image_path, tpl_path).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
