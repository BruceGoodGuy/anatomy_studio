"""Đường dẫn dự án, nạp mô hình OpenSim và đặt tư thế theo tên toạ độ (độ)."""
import math
import os

import numpy as np
import opensim as osim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
MODEL_PATH = os.path.join(ASSETS, "model", "RajagopalLaiUhlrich2023.osim")
GEOMETRY_DIR = os.path.join(ASSETS, "model", "Geometry")
EXERCISES_DIR = os.path.join(ROOT, "exercises")
OUTPUT_DIR = os.path.join(ROOT, "output")
WEB_DIR = os.path.join(ROOT, "web")

osim.Logger.setLevelString("error")
osim.ModelVisualizer.addDirToGeometrySearchPaths(GEOMETRY_DIR)

TRANSLATIONS = {"pelvis_tx", "pelvis_ty", "pelvis_tz"}


def load_model(rigid_tendons=False):
    model = osim.Model(MODEL_PATH)
    if rigid_tendons:
        # Gân cứng: chiều dài sợi cơ suy ra thuần tuý từ hình học — điều duy nhất mà
        # phân tích chỉ có chuyển động (không có dữ liệu lực) báo cáo được trung thực.
        muscles = model.updMuscles()
        for i in range(muscles.getSize()):
            muscles.get(i).set_ignore_tendon_compliance(True)
            muscles.get(i).set_ignore_activation_dynamics(True)
    state = model.initSystem()
    return model, state


class Poser:
    """Đặt giá trị toạ độ (độ / mét) và đọc vị trí, hướng, khối tâm."""

    def __init__(self, model, state):
        self.model, self.state = model, state
        self.coords = model.getCoordinateSet()
        self.names = [self.coords.get(i).getName() for i in range(self.coords.getSize())]
        self.coupled = {}
        cons = model.getConstraintSet()
        for i in range(cons.getSize()):
            c = osim.CoordinateCouplerConstraint.safeDownCast(cons.get(i))
            if c is not None:
                self.coupled[c.getDependentCoordinateName()] = (c.getIndependentCoordinateNames().get(0), c.getFunction())

    def set(self, values, reset=False):
        s = self.state
        if reset:
            for n in self.names:
                c = self.coords.get(n)
                c.setValue(s, c.getDefaultValue(), False)
        for name, v in values.items():
            self.coords.get(name).setValue(s, v if name in TRANSLATIONS else math.radians(v), False)
        for dep, (indep, f) in self.coupled.items():
            self.coords.get(dep).setValue(s, f.calcValue(osim.Vector(1, self.coords.get(indep).getValue(s))), False)
        self.model.realizePosition(s)

    def values(self):
        out = {}
        for n in self.names:
            v = self.coords.get(n).getValue(self.state)
            out[n] = v if n in TRANSLATIONS else math.degrees(v)
        return out

    def body_pos(self, body, station=(0, 0, 0)):
        p = self.model.getBodySet().get(body).findStationLocationInGround(self.state, osim.Vec3(*station))
        return np.array([p.get(i) for i in range(3)])

    def body_R(self, body):
        R = self.model.getBodySet().get(body).getTransformInGround(self.state).R()
        return np.array([[R.get(i, j) for j in range(3)] for i in range(3)])

    def com(self):
        c = self.model.calcMassCenterPosition(self.state)
        return np.array([c.get(i) for i in range(3)])

    def body_xforms(self, bodies):
        """[x y z qx qy qz qw] cho mỗi body."""
        out = []
        for b in bodies:
            X = self.model.getBodySet().get(b).getTransformInGround(self.state)
            p, q = X.p(), X.R().convertRotationToQuaternion()
            out.append([p.get(0), p.get(1), p.get(2), q.get(1), q.get(2), q.get(3), q.get(0)])
        return out


def body_names(model):
    return [model.getBodySet().get(i).getName() for i in range(model.getNumBodies())]


def slugify(name):
    import unicodedata
    s = unicodedata.normalize("NFKD", name.replace("đ", "d").replace("Đ", "D"))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    out = "".join(c if c.isalnum() else "-" for c in s)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-") or "bai-tap"
