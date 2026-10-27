// Lõi hiển thị dùng chung cho trang viewer (blog) và Anatomy Studio.
// Trang viewer.html được đóng gói thành MỘT file: pipeline/build.py chèn nguyên file này vào
// (bỏ các chữ "export"). Studio nạp trực tiếp /web/anatomy-core.js. Hai nơi vì thế luôn
// biến dạng và tô màu cơ giống hệt nhau.
import * as THREE from "three";

export const b64 = (s) => { const bin = atob(s); const u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i); return u.buffer; };
export const readIdx = (str, nv) => (nv < 65535 ? new Uint16Array(b64(str)) : new Uint32Array(b64(str)));

// ---------------------------------------------------------------- mức kéo giãn
// Định nghĩa giống hệt pipeline/stretch.py. l = l/l_opt hiện tại, l0 = lúc bắt đầu.
//   a = l/l0 − 1 (dài thêm), b = max(0, l − max(1, l0)) (vượt cả lúc bắt đầu lẫn chiều dài tối ưu)
//   a ≤ 0: S = a (ngắn lại)      a > 0: S = min(a/0.25, 1) + b/0.4  (dài ra → bị kéo giãn khi S > 1)
export const STRETCH_SPAN = 0.4, STRETCH_GROW = 0.25;
export function stretchIndex(l, l0) {
  const a = l / l0 - 1;
  if (!(a > 0)) return a;
  return Math.min(a / STRETCH_GROW, 1) + Math.max(0, l - Math.max(1, l0)) / STRETCH_SPAN;
}
export const SLACK = 0.5;   // dưới mức này sợi cơ thực tế đã chùng (gân không còn căng)

// Bảng màu đọc từ biến CSS của trang: --short --optimal --lengthen --long --longest
export function makePalette(css) {
  const C = {};
  const read = () => { for (const k of ["short", "optimal", "lengthen", "long", "longest"]) C[k] = new THREE.Color(css("--" + k) || "#888"); };
  read();
  const clamp = THREE.MathUtils.clamp;
  return {
    read,
    // chế độ "Kéo giãn": theo S
    stretch(S, out = new THREE.Color()) {
      if (S <= 0) return out.copy(C.optimal).lerp(C.short, clamp(-S / 0.3, 0, 1));
      if (S <= 1) return out.copy(C.optimal).lerp(C.lengthen, S);
      if (S <= 1.5) return out.copy(C.lengthen).lerp(C.long, (S - 1) / 0.5);
      return out.copy(C.long).lerp(C.longest, clamp((S - 1.5) / 0.5, 0, 1));
    },
    // chế độ "l/l_opt": độ dài tuyệt đối
    length(v, out = new THREE.Color()) {
      if (v <= 1) return out.copy(C.short).lerp(C.optimal, clamp((v - 0.6) / 0.4, 0, 1));
      if (v <= 1.25) return out.copy(C.optimal).lerp(C.long, (v - 1) / 0.25);
      return out.copy(C.long).lerp(C.longest, clamp((v - 1.25) / 0.25, 0, 1));
    },
  };
}

// ---------------------------------------------------------------- xương OpenSim
// bones: osim.bones.json. Trả về { nodes: [Group theo thứ tự bodies], idx: {tên: i} }
export function buildBones(scene, bones, bodies, material) {
  const idx = Object.fromEntries(bodies.map((b, i) => [b, i]));
  const nodes = bodies.map((name) => { const g = new THREE.Group(); g.name = name; scene.add(g); return g; });
  for (const bd of bones.bodies) {
    const node = nodes[idx[bd.body]]; if (!node) continue;
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(b64(bd.v)), 3));
    g.setIndex(new THREE.BufferAttribute(readIdx(bd.idx, bd.nv), 1));
    g.computeVertexNormals();
    const mesh = new THREE.Mesh(g, material); mesh.renderOrder = 2; node.add(mesh);
  }
  return { nodes, idx };
}
// xf: mảng [x y z qx qy qz qw] theo body
export function setPose(nodes, xf, bodies) {
  bodies.forEach((b, i) => { const n = nodes[i]; if (!n) return; const o = i * 7; n.position.set(xf[o], xf[o + 1], xf[o + 2]); n.quaternion.set(xf[o + 3], xf[o + 4], xf[o + 5], xf[o + 6]); n.updateMatrix(); });
}

// ---------------------------------------------------------------- biến dạng cơ (dual quaternion)
// Mỗi đỉnh cơ mang trọng số của các xương (chậu, đùi, cẳng chân, thân), lấy từ một trường điều hoà
// dựng sẵn (pipeline/zbind.py). Đỉnh di chuyển bằng cách trộn chuyển động cứng của các xương bằng dual
// quaternion. Mọi cơ dùng chung một trường liên tục nên không rách, cơ kề nhau đi cùng nhau.
// Bên trái dùng chính trọng số đó trên mesh đối xứng, với xương bên trái.
// <dqs>
export function skinDQ(rest, cur, out, o) {
  // dual quaternion của S = X_cur · X_rest⁻¹  (x y z qx qy qz qw)
  let rx = rest[3], ry = rest[4], rz = rest[5], rw = rest[6];
  let n = Math.hypot(rx, ry, rz, rw); rx /= n; ry /= n; rz /= n; rw /= n;
  let cx = cur[3], cy = cur[4], cz = cur[5], cw = cur[6];
  n = Math.hypot(cx, cy, cz, cw); cx /= n; cy /= n; cz /= n; cw /= n;
  const ax = -rx, ay = -ry, az = -rz, aw = rw;                    // conj(rest)
  const qx = cw * ax + cx * aw + cy * az - cz * ay, qy = cw * ay - cx * az + cy * aw + cz * ax;
  const qz = cw * az + cx * ay - cy * ax + cz * aw, qw = cw * aw - cx * ax - cy * ay - cz * az;
  // t = cur.p - q0 · rest.p
  const px = rest[0], py = rest[1], pz = rest[2];
  const tx0 = 2 * (qy * pz - qz * py), ty0 = 2 * (qz * px - qx * pz), tz0 = 2 * (qx * py - qy * px);
  const rpx = px + qw * tx0 + (qy * tz0 - qz * ty0), rpy = py + qw * ty0 + (qz * tx0 - qx * tz0), rpz = pz + qw * tz0 + (qx * ty0 - qy * tx0);
  const tx = cur[0] - rpx, ty = cur[1] - rpy, tz = cur[2] - rpz;
  out[o] = qx; out[o + 1] = qy; out[o + 2] = qz; out[o + 3] = qw;
  // qe = 0.5 · (t, 0) · q0
  out[o + 4] = 0.5 * (tx * qw + ty * qz - tz * qy);
  out[o + 5] = 0.5 * (-tx * qz + ty * qw + tz * qx);
  out[o + 6] = 0.5 * (tx * qy - ty * qx + tz * qw);
  out[o + 7] = 0.5 * (-tx * qx - ty * qy - tz * qz);
}
export function dqsDeform(V, K, W, dq, out, mirror) {
  const nv = V.length / 3, zs = mirror ? -1 : 1;
  for (let v = 0; v < nv; v++) {
    let b0x = 0, b0y = 0, b0z = 0, b0w = 0, bex = 0, bey = 0, bez = 0, bew = 0;
    // quaternion của mọi xương đưa về cùng bán cầu với xương có trọng số lớn nhất của đỉnh
    let r = 0;
    for (let k = 1; k < K; k++) if (W[v * K + k] > W[v * K + r]) r = k;
    const ro = r * 8;
    for (let k = 0; k < K; k++) {
      let w = W[v * K + k]; if (w === 0) continue;
      const o = k * 8;
      if (dq[o] * dq[ro] + dq[o + 1] * dq[ro + 1] + dq[o + 2] * dq[ro + 2] + dq[o + 3] * dq[ro + 3] < 0) w = -w;
      b0x += w * dq[o]; b0y += w * dq[o + 1]; b0z += w * dq[o + 2]; b0w += w * dq[o + 3];
      bex += w * dq[o + 4]; bey += w * dq[o + 5]; bez += w * dq[o + 6]; bew += w * dq[o + 7];
    }
    const n = Math.hypot(b0x, b0y, b0z, b0w);
    b0x /= n; b0y /= n; b0z /= n; b0w /= n; bex /= n; bey /= n; bez /= n; bew /= n;
    const px = V[v * 3], py = V[v * 3 + 1], pz = zs * V[v * 3 + 2];
    const tx0 = 2 * (b0y * pz - b0z * py), ty0 = 2 * (b0z * px - b0x * pz), tz0 = 2 * (b0x * py - b0y * px);
    const rx = px + b0w * tx0 + (b0y * tz0 - b0z * ty0), ry = py + b0w * ty0 + (b0z * tx0 - b0x * tz0), rz = pz + b0w * tz0 + (b0x * ty0 - b0y * tx0);
    // t = 2 (w0·ve − we·v0 + v0 × ve)
    const tx = 2 * (b0w * bex - bew * b0x + (b0y * bez - b0z * bey));
    const ty = 2 * (b0w * bey - bew * b0y + (b0z * bex - b0x * bez));
    const tz = 2 * (b0w * bez - bew * b0z + (b0x * bey - b0y * bex));
    out[v * 3] = rx + tx; out[v * 3 + 1] = ry + ty; out[v * 3 + 2] = rz + tz;
  }
}
// </dqs>

// ---------------------------------------------------------------- cơ Z-Anatomy
// zan: zanat_binding.json. bodyNodes/bodyIdx: xương OpenSim. muscleOf(id) → đối tượng cơ của trang (hoặc null).
// mirror: bài đối xứng (chỉ có dữ liệu cơ bên phải; bên trái dùng chung số liệu).
export class ZAnatomy {
  constructor(scene, zan, bodyNodes, bodyIdx, muscleOf, mirror) {
    this.meshes = []; this.mapped = new Set(); this.sides = {}; this.K = zan.skinBodies.length;
    // độ đậm: cơ bình thường / cơ bị làm mờ / xương (chế độ chụp ảnh chỉnh được)
    this.style = { on: 1, dim: 0.12 };
    const K = this.K;
    const flipIndex = (idx) => { const o = idx.slice(); for (let i = 0; i < o.length; i += 3) { o[i + 1] = idx[i + 2]; o[i + 2] = idx[i + 1]; } return o; };
    this.boneMat = new THREE.MeshStandardMaterial({ color: 0xe9e2d3, emissive: 0x2a2620, roughness: 0.7, transparent: true, opacity: 0.55, depthWrite: false });
    for (const bn of zan.bones) {
      const v = new Float32Array(b64(bn.v)), idx = readIdx(bn.idx, bn.nv);
      const targets = [[bn.body, false]];
      if (/_r$/.test(bn.body)) targets.push([bn.body.replace(/_r$/, "_l"), true]);
      for (const [body, mir] of targets) {
        const node = bodyNodes[bodyIdx[body]]; if (!node) continue;
        if (bn.replace !== false) node.children.forEach((c) => { if (c.isMesh && !c.userData.zbone) c.visible = false; });
        const g = new THREE.BufferGeometry();
        g.setAttribute("position", new THREE.BufferAttribute(mir ? v.map((x, i) => (i % 3 === 2 ? -x : x)) : v, 3));
        g.setIndex(new THREE.BufferAttribute(mir ? flipIndex(idx) : idx, 1));
        g.computeVertexNormals();
        const mesh = new THREE.Mesh(g, this.boneMat); mesh.renderOrder = 2; mesh.userData.zbone = true; node.add(mesh);
      }
    }
    for (const s of ["R", "L"]) {
      const names = zan.skinBodies.map((n) => (s === "L" ? n.replace(/_r$/, "_l") : n));
      this.sides[s] = {
        nodes: names.map((n) => bodyNodes[bodyIdx[n]]),
        rest: names.map((n) => zan.rest[n]),
        dq: new Float64Array(K * 8),
        lines: zan.lines.map((ln) => muscleOf(mirror || s === "R" ? ln.id : ln.id.replace(/_r$/, "_l"))),
        val: new Float32Array(zan.lines.length),
      };
      for (const m of this.sides[s].lines) if (m) this.mapped.add(m);
    }
    for (const zm of zan.muscles) {
      const nv = zm.nv, idx = readIdx(zm.idx, nv);
      const V = Float32Array.from(new Int16Array(b64(zm.v)), (x) => x / 1e4);
      const W = Float32Array.from(new Uint16Array(b64(zm.bw)), (x) => x / 65535);
      for (let v = 0; v < nv; v++) { let t = 0; for (let k = 0; k < K; k++) t += W[v * K + k]; for (let k = 0; k < K; k++) W[v * K + k] /= t; }
      const rec = { name: zm.name, nv, V, W, l: new Uint8Array(b64(zm.l)), w: new Float32Array(b64(zm.w)), sides: {} };
      for (const s of ["R", "L"]) {
        const g = new THREE.BufferGeometry();
        g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(nv * 3), 3));
        g.setAttribute("color", new THREE.BufferAttribute(new Float32Array(nv * 3), 3));
        g.setIndex(new THREE.BufferAttribute(s === "L" ? flipIndex(idx) : idx, 1));
        // DoubleSide: ở nếp khớp gập sâu, một tam giác rất nhỏ có thể quay mặt sau ra ngoài; vẽ cả hai mặt
        // để không bao giờ lộ "lỗ thủng".
        const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.52, emissive: 0x161210, transparent: true, side: THREE.DoubleSide });
        const mesh = new THREE.Mesh(g, mat);
        mesh.frustumCulled = false; mesh.renderOrder = 1; mesh.userData.zrec = rec; mesh.userData.side = s; mesh.userData.zb = this;
        scene.add(mesh);
        rec.sides[s] = { g, mat, mesh, muscles: [...new Set(zm.lines.map((l) => this.sides[s].lines[l]).filter(Boolean))] };
      }
      this.meshes.push(rec);
    }
    this._cur = new Float64Array(7);
  }
  // valueOf(m) → số dùng để tô (S hoặc l/l_opt); colourOf(value, out) → THREE.Color
  updateSide(s, valueOf) {
    const S = this.sides[s], c = this._cur;
    S.nodes.forEach((node, k) => {
      c[0] = node.position.x; c[1] = node.position.y; c[2] = node.position.z;
      c[3] = node.quaternion.x; c[4] = node.quaternion.y; c[5] = node.quaternion.z; c[6] = node.quaternion.w;
      skinDQ(S.rest[k], c, S.dq, k * 8);
    });
    S.lines.forEach((m, i) => { S.val[i] = m ? valueOf(m) : NaN; });
  }
  deform(rec, s, colourOf, neutral) {
    const S = this.sides[s], g = rec.sides[s].g;
    dqsDeform(rec.V, this.K, rec.W, S.dq, g.attributes.position.array, s === "L");
    const colArr = g.attributes.color.array, { l, w, nv } = rec, col = this._col || (this._col = new THREE.Color());
    for (let v = 0; v < nv; v++) {
      const a = S.val[l[v * 2]], b = S.val[l[v * 2 + 1]];
      const x = Number.isNaN(a) ? b : Number.isNaN(b) ? a : w[v] * a + (1 - w[v]) * b;
      if (Number.isNaN(x)) col.copy(neutral); else colourOf(x, col);
      colArr[v * 3] = col.r; colArr[v * 3 + 1] = col.g; colArr[v * 3 + 2] = col.b;
    }
    g.attributes.position.needsUpdate = true; g.attributes.color.needsUpdate = true; g.computeVertexNormals();
  }
  // look(muscles) → "hide" | "dim" | "on" | "picked"
  update(valueOf, colourOf, look, neutral) {
    for (const s of ["R", "L"]) this.updateSide(s, (m) => valueOf(m, s));
    for (const rec of this.meshes) for (const s of ["R", "L"]) {
      const { mesh, mat, muscles } = rec.sides[s];
      const L = look(muscles, s);
      mesh.visible = L !== "hide"; if (L === "hide") continue;
      this.deform(rec, s, colourOf, neutral);
      mat.opacity = L === "dim" ? this.style.dim : this.style.on; mat.depthWrite = mat.opacity > 0.95;
      if (mat.opacity <= 0.001) { mesh.visible = false; continue; }
      mat.emissive.setHex(L === "picked" ? 0x3a2a1c : 0x161210);
    }
  }
  setBoneOpacity(a) { this.boneMat.opacity = a; this.boneMat.visible = a > 0.001; }
  // điểm neo (trọng tâm phần mesh thuộc từng cơ) để gắn nhãn tên cơ trên ảnh — toạ độ thế giới
  anchors() {
    const acc = new Map();
    for (const rec of this.meshes) for (const s of ["R", "L"]) {
      const { mesh, g } = rec.sides[s]; if (!mesh.visible) continue;
      const P = g.attributes.position.array, lines = this.sides[s].lines;
      for (let v = 0; v < rec.nv; v++) {
        const m = lines[rec.l[v * 2 + (rec.w[v] >= 0.5 ? 0 : 1)]]; if (!m) continue;
        let a = acc.get(m); if (!a) acc.set(m, (a = { x: 0, y: 0, z: 0, n: 0, side: s }));
        a.x += P[v * 3]; a.y += P[v * 3 + 1]; a.z += P[v * 3 + 2]; a.n++;
      }
    }
    for (const a of acc.values()) { a.x /= a.n; a.y /= a.n; a.z /= a.n; }
    return acc;
  }
  hide() { for (const rec of this.meshes) for (const s of ["R", "L"]) rec.sides[s].mesh.visible = false; }
  pickables() { return this.meshes.flatMap((rec) => Object.values(rec.sides).map((x) => x.mesh)).filter((m) => m.visible && m.material.opacity > 0.5); }
  // cơ (đối tượng trang) tại một giao điểm tia
  muscleAt(hit) {
    const rec = hit.object.userData.zrec, s = hit.object.userData.side, vtx = hit.face.a;
    return this.sides[s].lines[rec.l[vtx * 2 + (rec.w[vtx] >= 0.5 ? 0 : 1)]] || null;
  }
}
