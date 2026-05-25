# -*- coding: utf-8 -*-
"""
Created on Mon Apr  6 20:35:58 2026

@author: 86173
"""

import numpy as np
from matplotlib import pyplot as plt
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams['axes.unicode_minus'] = False

# ==================== 第一部分：最短实验类 ====================
class ShortestExperiment:
    def __init__(self, A, B, C, D, L, x0=None):
        self.A = np.asarray(A, dtype=float)
        self.B = np.asarray(B, dtype=float)
        self.C = np.asarray(C, dtype=float)
        self.D = np.asarray(D, dtype=float)
        self.n = self.A.shape[0]
        self.m = self.B.shape[1]
        self.p = self.C.shape[0]

        print(f"系统维度: n={self.n}, m={self.m}, p={self.p}")

        assert self.A.shape == (self.n, self.n), "A 维度错误"
        assert self.B.shape == (self.n, self.m), "B 维度错误"
        assert self.C.shape == (self.p, self.n), "C 维度错误"
        assert self.D.shape == (self.p, self.m), "D 维度错误"

        self.L = L
        self.x = np.zeros((self.n, 1)) if x0 is None else np.asarray(x0).reshape(self.n, 1)
        self.u_list = []
        self.y_list = []
        self.target_rank = self.L * self.m + self.n

    def _step(self, u):
        u = np.asarray(u, dtype=float).reshape(self.m, 1)
        y = self.C @ self.x + self.D @ u
        y_flat = y.flatten()
        if y_flat.size != self.p:
            raise ValueError(f"输出维度错误: 期望 {self.p}, 得到 {y_flat.size}")
        self.u_list.append(u.flatten())
        self.y_list.append(y_flat)
        self.x = self.A @ self.x + self.B @ u

    def _build_hankel(self):
        t = len(self.u_list)
        if t < self.L:
            return None, None, t
        cols = t - self.L + 1
        H_y = np.zeros((self.L * self.p, cols))
        H_u = np.zeros((self.L * self.m, cols))
        for col in range(cols):
            for row in range(self.L):
                idx = col + row
                y_vec = self.y_list[idx]
                u_vec = self.u_list[idx]
                for i in range(self.p):
                    H_y[row*self.p + i, col] = y_vec[i]
                for j in range(self.m):
                    H_u[row*self.m + j, col] = u_vec[j]
        H = np.vstack((H_y, H_u))
        if self.L > 0 and self.p > 0:
            G_y = H_y[:-self.p, :]
        else:
            G_y = np.empty((0, cols))
        G = np.vstack((G_y, H_u)) if G_y.size > 0 else H_u
        return H, G, t

    def _rank(self, M, tol=1e-10):
        if M.size == 0:
            return 0
        s = np.linalg.svd(M, compute_uv=False)
        return np.sum(s > tol)

    def _check_condition(self, H, G, t):
        if self.L - 1 >= 0:
            cols_prev = t - (self.L - 1) + 1
            if cols_prev <= 0:
                rank_H_prev = 0
            else:
                H_y_prev = np.zeros(((self.L - 1) * self.p, cols_prev))
                H_u_prev = np.zeros(((self.L - 1) * self.m, cols_prev))
                for col in range(cols_prev):
                    for row in range(self.L - 1):
                        idx = col + row
                        y_vec = self.y_list[idx]
                        u_vec = self.u_list[idx]
                        for i in range(self.p):
                            H_y_prev[row*self.p + i, col] = y_vec[i]
                        for j in range(self.m):
                            H_u_prev[row*self.m + j, col] = u_vec[j]
                H_prev = np.vstack((H_y_prev, H_u_prev))
                rank_H_prev = self._rank(H_prev)
        else:
            rank_H_prev = 0
        rank_G = self._rank(G)
        return rank_G < self.m + rank_H_prev

    def generate(self, max_attempts=100):
        if self.m == 1:
            u0 = np.array([[1.0]], dtype=float)
        else:
            u0 = np.eye(self.m, dtype=float)
        for i in range(self.m):
            self._step(u0[:, i])
        print(f"初始数据长度: {len(self.u_list)}")
        while True:
            H, G, t = self._build_hankel()
            if H is None:
                self._step(np.random.randn(self.m))
                continue
            rank_H = self._rank(H)
            print(f"t={t}, rank(H)={rank_H}, target={self.target_rank}")
            if rank_H >= self.target_rank:
                print("实验完成")
                y_out = np.vstack(self.y_list)
                return np.array(self.u_list), y_out
            if self._check_condition(H, G, t):
                success = False
                for attempt in range(max_attempts):
                    u_try = np.random.randn(self.m)
                    x_save = self.x.copy()
                    u_save = self.u_list.copy()
                    y_save = self.y_list.copy()
                    y_try = self.C @ x_save + self.D @ u_try.reshape(self.m, 1)
                    y_try_flat = y_try.flatten()
                    u_save.append(u_try.flatten())
                    y_save.append(y_try_flat)
                    t_temp = len(u_save)
                    if t_temp < self.L:
                        success = True
                        break
                    cols_temp = t_temp - self.L + 1
                    H_y_temp = np.zeros((self.L * self.p, cols_temp))
                    H_u_temp = np.zeros((self.L * self.m, cols_temp))
                    for col in range(cols_temp):
                        for row in range(self.L):
                            idx = col + row
                            y_vec = y_save[idx]
                            u_vec = u_save[idx]
                            for i in range(self.p):
                                H_y_temp[row*self.p + i, col] = y_vec[i]
                            for j in range(self.m):
                                H_u_temp[row*self.m + j, col] = u_vec[j]
                    H_temp = np.vstack((H_y_temp, H_u_temp))
                    rank_temp = self._rank(H_temp)
                    if rank_temp > rank_H:
                        success = True
                        self._step(u_try)
                        break
                if not success:
                    print("多次尝试未增秩，强制应用")
                    self._step(u_try)
            else:
                self._step(np.random.randn(self.m))
        return np.array(self.u_list), np.array(self.y_list)

# ==================== 第二部分：数据驱动 ILC 类 ====================
class DataDrivenILC:
    def __init__(self, u_exp, y_exp, n, N, L, Q=1.0, R=0.1):
        self.u_exp = np.asarray(u_exp, dtype=float)
        self.y_exp = np.asarray(y_exp, dtype=float)
        if self.y_exp.ndim == 1:
            self.y_exp = self.y_exp.reshape(-1, 1)

        self.t_len = self.u_exp.shape[0]
        self.m = self.u_exp.shape[1]
        self.p = self.y_exp.shape[1]
        self.n = n
        self.N = N
        self.L = L

        print(f"ILC 参数: N={self.N}, n={self.n}, m={self.m}, p={self.p}")
        print(f"数据形状: u_exp {self.u_exp.shape}, y_exp {self.y_exp.shape}")

        if self.N < self.n:
            raise ValueError(f"控制时域 N={self.N} 必须 ≥ 系统阶次 n={self.n}")
        if self.t_len < self.N:
            raise ValueError(f"实验数据长度 {self.t_len} < 控制时域 {self.N}")

        # 权重矩阵
        self.R_mat = R * np.eye(self.L * self.m, dtype=float)
        self.Q_mat = Q * np.eye((self.N) * self.p, dtype=float)
        self.S = np.block([[self.R_mat, np.zeros((self.L*self.m, (self.N)*self.p))],
                           [np.zeros(((self.N)*self.p, self.L*self.m)), self.Q_mat]])

        self._build_data_matrices()
        self._compute_W0()
        self._compute_gain()

    def _build_data_matrices(self):
        M = self.t_len - self.L + 1
        H_u = np.zeros((self.L * self.m, M))
        H_y = np.zeros((self.L * self.p, M))
        for col in range(M):
            for row in range(self.L):
                idx = col + row
                H_u[row*self.m:(row+1)*self.m, col] = self.u_exp[idx]
                H_y[row*self.p:(row+1)*self.p, col] = self.y_exp[idx]

        self.U_p = H_u[:self.n*self.m, :]
        self.Y_p = H_y[:self.n*self.p, :]
        self.U_f = H_u[self.n*self.m:, :]
        self.Y_f = H_y[self.n*self.p:, :]
        self.H_Lu = H_u
        print(f"数据矩阵构造完成: 窗口数={M}, U_p形状={self.U_p.shape}, U_f形状={self.U_f.shape}")

    def _compute_W0(self):
        M = self.H_Lu.shape[1]
        A_eq = np.vstack([self.U_p, self.Y_p, self.U_f])   
        b = np.vstack([np.zeros((self.n*self.m, M)),
                       np.zeros((self.n*self.p, M)),
                       self.H_Lu[self.n*self.m:, :]])      
        G = np.linalg.pinv(A_eq) @ b
        Y0 = self.Y_f @ G
        self.W0 = np.vstack([self.H_Lu, Y0])             
        print(f"W0 形状: {self.W0.shape}")

    def _compute_gain(self):
        W0T_S_W0 = self.W0.T @ self.S @ self.W0
        pinv = np.linalg.pinv(W0T_S_W0, rcond=1e-10)
        # I0 = [I; 0]  (N*m + (N-n)*p) x (N*m)
        I0 = np.vstack([np.eye(self.L * self.m),
                        np.zeros(((self.N) * self.p, self.L * self.m))])
        K = I0.T @ self.W0 @ pinv @ self.W0.T @ self.S   # (N*m, N*m + (N-n)*p)
        # 取未来输入和未来误差部分
        self.K = K[self.n*self.m:, self.N*self.m:]      
    

    def run(self, system, r, u0=None, max_iter=100, tol=1e-5):
        expected_len = L * self.p
        if len(r) != expected_len:
            raise ValueError(f"期望轨迹长度 {len(r)} 应为 {expected_len}")

        if u0 is None:
            u = np.zeros(L * self.m, dtype=float)
        else:
            u = u0.copy().astype(float)

        errors = []
        u_hist = [u.copy()]

        for k in range(max_iter):
            y = system(u)
            if len(y) != expected_len:
                raise ValueError(f"系统输出长度 {len(y)} 应为 {expected_len}")
            e = r - y
            err_norm = np.linalg.norm(e)
            errors.append(err_norm)
            print(f"Iter {k}: error norm = {err_norm:.6f}")

            if err_norm < tol:
                print("收敛，停止迭代")
                break

            delta_u_f = self.K @ e
            # 只更新未来输入（后 (N-n)*m 个元素）
            u[self.n * self.m :] = u[self.n * self.m :] + delta_u_f
            u_hist.append(u.copy())

        return u_hist, errors

# ==================== 第三部分：主程序 ====================
if __name__ == "__main__":
    # 系统定义（最小实现）
    n, m, p = 2, 1, 1
    A = np.array([[0.183, 0.045], [-0.172, -0.166]], dtype=float)
    B = np.array([[-0.45], [0.526]], dtype=float)
    C = np.array([[0.81, -0.67]], dtype=float)
    D = np.array([[0]], dtype=float)

    print("A 形状:", A.shape)
    print("B 形状:", B.shape)
    print("C 形状:", C.shape)
    print("D 形状:", D.shape)

    # 1. 运行最短实验，生成离线数据
    L = 261
    exp = ShortestExperiment(A, B, C, D, L)
    u_exp, y_exp = exp.generate()
    print(f"最短实验数据长度: {len(u_exp)}, y_exp形状: {y_exp.shape}")

    # 2. 设定 ILC 参数
    N = L - n 
    t = np.linspace(0, 2 * np.pi, L, dtype=float)
    # ------------------------------------------------------------------
    # 轨迹一：衰减正弦波
    #r_full = (0.98**t) * np.sin(5*t) * 0.5
    #
    # 轨迹二：组合衰减正余弦波（当前使用）
    # r_2(t) = 0,                                  t = 0, 1
    # r_2(t) = 0.5*(0.98)^t*sin(3t)+0.2*(0.96)^t*cos(7t), t = 2,...,260
    # ------------------------------------------------------------------
    r_full = (0.98**t) * np.sin(3*t) * 0.5 + (0.96**t) * np.cos(7*t) * 0.2
    # 期望轨迹
    r = np.zeros(L * p)
    r[n:] = r_full[n:]      # 只跟踪后 N 步
   
    print(f"期望轨迹长度: {len(r)}")

    # 3. 初始化数据驱动 ILC
    ilc = DataDrivenILC(u_exp, y_exp, n, N, L, Q=1.0, R=0.1)

    # 4. 定义系统仿真函数
    def simulate(u_vec):
        u_vec = u_vec.reshape(-1, m).astype(float)
        steps = u_vec.shape[0]
        x = np.zeros((n, 1), dtype=float)
        y_list = []
        for t_idx in range(steps):
            u_t = u_vec[t_idx, :].reshape(m, 1)
            y_t = C @ x + D @ u_t
            y_list.append(y_t.flatten())
            x = A @ x + B @ u_t
        return np.hstack(y_list).astype(float)

    # 5. 运行 ILC
    u_hist, errors = ilc.run(simulate, r, max_iter=100, tol=1e-5)

    # 6. 绘图
    plt.figure()
    plt.semilogy(errors)
    plt.xlabel("迭代次数")
    plt.ylabel("跟着误差范数")
    plt.title("迭代学习控制收敛性")
    plt.grid(True)

    final_u = u_hist[-1]
    final_y = simulate(final_u)
    plt.figure()
    plt.plot(r, label="期望轨迹")
    plt.plot(final_y, label="实际输出")
    plt.xlabel("长度")
    plt.ylabel("数值")
    plt.legend()
    plt.title("实际输出跟踪期望轨迹效果")
    plt.grid(True)
    plt.show()