import { useEffect, useMemo, useRef, useState } from "react";
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const API_BASE = "http://localhost:8080";
const WS_BASE = "ws://localhost:8080";

const USERS_KEY = "knownUsers";

function readKnownUsers() {
  try {
    const raw = localStorage.getItem(USERS_KEY);
    const arr = raw ? JSON.parse(raw) : [];
    if (Array.isArray(arr)) return arr.filter((x) => Number.isInteger(x) && x > 0);
    return [];
  } catch {
    return [];
  }
}

function writeKnownUsers(arr) {
  const uniq = Array.from(new Set(arr)).filter((x) => Number.isInteger(x) && x > 0);
  uniq.sort((a, b) => a - b);
  localStorage.setItem(USERS_KEY, JSON.stringify(uniq));
  return uniq;
}

function rememberUser(id) {
  const n = Number(id);
  if (!Number.isInteger(n) || n <= 0) return readKnownUsers();
  return writeKnownUsers([...readKnownUsers(), n]);
}

function Card({ title, children }) {
  return (
    <div
      style={{
        background: "#111827",
        border: "1px solid #1f2937",
        borderRadius: 12,
        padding: 16,
        boxShadow: "0 10px 30px rgba(0,0,0,0.25)",
      }}
    >
      <div style={{ fontSize: 14, color: "#93c5fd", marginBottom: 10, fontWeight: 700 }}>
        {title}
      </div>
      {children}
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label style={{ display: "grid", gap: 6, color: "#e5e7eb", fontSize: 13 }}>
      <span style={{ color: "#9ca3af" }}>{label}</span>
      {children}
    </label>
  );
}

function Input(props) {
  return (
    <input
      {...props}
      style={{
        padding: "10px 12px",
        borderRadius: 10,
        border: "1px solid #374151",
        background: "#0b1220",
        color: "#e5e7eb",
        outline: "none",
      }}
    />
  );
}

function Button({ variant = "primary", ...props }) {
  const bg =
    variant === "primary"
      ? "#2563eb"
      : variant === "green"
      ? "#16a34a"
      : variant === "ghost"
      ? "transparent"
      : "#374151";

  const border = variant === "ghost" ? "1px solid #374151" : "1px solid transparent";

  return (
    <button
      {...props}
      style={{
        padding: "10px 12px",
        borderRadius: 10,
        border,
        background: bg,
        color: "#fff",
        cursor: props.disabled ? "not-allowed" : "pointer",
        opacity: props.disabled ? 0.6 : 1,
        fontWeight: 700,
      }}
    />
  );
}

function Container({ children }) {
  return (
    <div
      style={{
        minHeight: "100vh",
        background:
          "radial-gradient(1200px 600px at 20% 0%, rgba(37,99,235,0.25), transparent), #030712",
        padding: "24px 16px",
        color: "#e5e7eb",
        fontFamily: "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial",
      }}
    >
      <div style={{ maxWidth: 1200, margin: "0 auto" }}>{children}</div>
    </div>
  );
}

function TopNav() {
  const linkStyle = ({ isActive }) => ({
    padding: "8px 12px",
    borderRadius: 10,
    textDecoration: "none",
    color: isActive ? "#ffffff" : "#cbd5e1",
    background: isActive ? "#1d4ed8" : "transparent",
    border: "1px solid #334155",
    fontWeight: 700,
    fontSize: 13,
  });

  return (
    <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 14 }}>
      <div style={{ fontSize: 20, fontWeight: 900 }}>
        SE_4 — Orders UI{" "}
        <span style={{ color: "#9ca3af", fontSize: 13 }}>(payments + orders + WS)</span>
      </div>

      <div style={{ marginLeft: "auto", display: "flex", gap: 10 }}>
        <NavLink to="/" style={linkStyle}>
          Main
        </NavLink>
        <NavLink to="/history" style={linkStyle}>
          History
        </NavLink>
        <NavLink to="/users" style={linkStyle}>
          Users
        </NavLink>
      </div>
    </div>
  );
}

function MainPage() {
  const [userId, setUserId] = useState(1);

  // payments
  const [topupAmount, setTopupAmount] = useState(1000);
  const [balance, setBalance] = useState(null);

  const [orderAmount, setOrderAmount] = useState(100);
  const [desc, setDesc] = useState("test");
  const [orderId, setOrderId] = useState(null);
  const [status, setStatus] = useState("-");
  const wsRef = useRef(null);

  const canCreateOrder = useMemo(() => userId > 0 && orderAmount > 0, [userId, orderAmount]);

  async function createAccount() {
    try {
      rememberUser(userId);

      const res = await fetch(`${API_BASE}/payments/accounts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: Number(userId) }),
      });

      if (res.status === 409) {
        toast.info("Счёт уже существует");
        await refreshBalance(true);
        return;
      }
      if (!res.ok) throw new Error(await res.text());

      const data = await res.json();
      setBalance(data.balance);
      toast.success(`Счёт создан. Баланс: ${data.balance}`);
    } catch (e) {
      toast.error(String(e.message || e));
    }
  }

  async function topUp() {
    try {
      rememberUser(userId);

      const res = await fetch(`${API_BASE}/payments/accounts/topup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: Number(userId), amount: Number(topupAmount) }),
      });

      if (!res.ok) throw new Error(await res.text());

      const data = await res.json();
      setBalance(data.balance);
      toast.success(`Пополнение успешно. Баланс: ${data.balance}`);
    } catch (e) {
      toast.error(String(e.message || e));
    }
  }

  async function refreshBalance(showToast = false) {
    try {
      rememberUser(userId);

      const res = await fetch(`${API_BASE}/payments/accounts/${Number(userId)}/balance`);
      if (!res.ok) throw new Error(await res.text());

      const data = await res.json();
      setBalance(data.balance);
      if (showToast) toast.info(`Баланс: ${data.balance}`);
    } catch (e) {
      toast.error(String(e.message || e));
    }
  }

  async function createOrder() {
    try {
      rememberUser(userId);

      setStatus("NEW");
      setOrderId(null);

      const res = await fetch(`${API_BASE}/orders/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: Number(userId),
          amount: Number(orderAmount),
          description: desc,
        }),
      });

      if (!res.ok) throw new Error(await res.text());

      const data = await res.json();
      const id = data.order_id;

      setOrderId(id);
      setStatus(data.status ?? "NEW");
      toast.info(`Заказ #${id} создан. Ждём оплату…`);

      subscribeWs(id);
    } catch (e) {
      toast.error(String(e.message || e));
    }
  }

  function subscribeWs(id) {
    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch {}
      wsRef.current = null;
    }

    const ws = new WebSocket(`${WS_BASE}/ws/orders/${id}`);
    wsRef.current = ws;

    ws.onopen = () => toast.success(`WS подключен к заказу #${id}`);

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        setStatus(msg.status);
        toast.info(`Статус заказа #${msg.order_id}: ${msg.status}`);
        // по желанию: обновим баланс без тоста
        refreshBalance(false);
      } catch {
        toast.info(`WS: ${ev.data}`);
      }
    };

    ws.onerror = () => toast.error("WS error");
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, alignItems: "start" }}>
      <Card title="Настройки пользователя">
        <Field label="user_id">
          <Input type="number" value={userId} onChange={(e) => setUserId(Number(e.target.value))} />
        </Field>

        <div style={{ height: 10 }} />

        <div style={{ display: "flex", gap: 10, alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ color: "#9ca3af", fontSize: 13 }}>
            Текущий баланс: <b style={{ color: "#e5e7eb" }}>{balance ?? "-"}</b>
          </div>
          <Button variant="ghost" onClick={() => refreshBalance(true)}>
            Обновить баланс
          </Button>
        </div>
      </Card>

      <Card title="Payments">
        <div style={{ display: "grid", gap: 10 }}>
          <Button variant="green" onClick={createAccount}>
            Создать счёт
          </Button>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 140px", gap: 10 }}>
            <Field label="topup amount">
              <Input
                type="number"
                value={topupAmount}
                onChange={(e) => setTopupAmount(Number(e.target.value))}
              />
            </Field>
            <div style={{ alignSelf: "end" }}>
              <Button onClick={topUp}>Пополнить</Button>
            </div>
          </div>

          <div style={{ color: "#9ca3af", fontSize: 12 }}>
            Подсказка: создай счёт → пополни → создай заказ → дождись push по WS.
          </div>
        </div>
      </Card>

      <div style={{ gridColumn: "1 / -1" }}>
        <Card title="Orders">
          <div style={{ display: "grid", gridTemplateColumns: "160px 1fr 160px", gap: 10 }}>
            <Field label="amount">
              <Input
                type="number"
                value={orderAmount}
                onChange={(e) => setOrderAmount(Number(e.target.value))}
              />
            </Field>

            <Field label="description">
              <Input value={desc} onChange={(e) => setDesc(e.target.value)} />
            </Field>

            <div style={{ alignSelf: "end" }}>
              <Button onClick={createOrder} disabled={!canCreateOrder}>
                Создать заказ
              </Button>
            </div>
          </div>

          <div style={{ height: 12 }} />

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
            <div style={{ padding: 12, border: "1px solid #1f2937", borderRadius: 12 }}>
              <div style={{ color: "#9ca3af", fontSize: 12 }}>order_id</div>
              <div style={{ fontWeight: 800, fontSize: 18 }}>{orderId ?? "-"}</div>
            </div>

            <div style={{ padding: 12, border: "1px solid #1f2937", borderRadius: 12 }}>
              <div style={{ color: "#9ca3af", fontSize: 12 }}>status</div>
              <div style={{ fontWeight: 800, fontSize: 18 }}>{status}</div>
            </div>

            <div style={{ padding: 12, border: "1px solid #1f2937", borderRadius: 12 }}>
              <div style={{ color: "#9ca3af", fontSize: 12 }}>WS</div>
              <div style={{ fontWeight: 700 }}>{orderId ? `Подписан на #${orderId}` : "—"}</div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

function HistoryPage() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const didInit = useRef(false);

  async function loadOrders(showToast = true) {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/orders/orders`);
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setOrders(data);

      if (showToast) toast.info(`Загружено заказов: ${data.length}`, { toastId: "orders_loaded" });
    } catch (e) {
      toast.error(String(e.message || e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (didInit.current) return;
    didInit.current = true;
    loadOrders(false);
  }, []);

  return (
    <Card title="История заказов">
      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <Button variant="ghost" onClick={() => loadOrders(true)} disabled={loading}>
          {loading ? "Загрузка..." : "Обновить"}
        </Button>

        <div style={{ color: "#9ca3af", fontSize: 13 }}>
          Показываем: order_id, user_id, amount, status (description не трогаем — backend не меняем)
        </div>
      </div>

      <div style={{ height: 12 }} />

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ color: "#9ca3af", textAlign: "left" }}>
              <th style={{ padding: "8px 6px" }}>ID</th>
              <th style={{ padding: "8px 6px" }}>User</th>
              <th style={{ padding: "8px 6px" }}>Amount</th>
              <th style={{ padding: "8px 6px" }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.order_id} style={{ borderTop: "1px solid #1f2937" }}>
                <td style={{ padding: "8px 6px" }}>{o.order_id}</td>
                <td style={{ padding: "8px 6px" }}>{o.user_id}</td>
                <td style={{ padding: "8px 6px" }}>{o.amount}</td>
                <td style={{ padding: "8px 6px", fontWeight: 800 }}>{o.status}</td>
              </tr>
            ))}

            {orders.length === 0 && (
              <tr>
                <td colSpan={4} style={{ padding: 12, color: "#9ca3af" }}>
                  Нет заказов. Создай заказ на вкладке Main.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function UsersPage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);

  async function loadUsers() {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/payments/accounts`);
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setRows(data);
      toast.info(`Загружено пользователей: ${data.length}`, { toastId: "users_loaded" });
    } catch (e) {
      toast.error(String(e.message || e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUsers();
  }, []);

  return (
    <Card title="Users (все аккаунты из Payments)">
      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <Button variant="ghost" onClick={loadUsers} disabled={loading}>
          {loading ? "Загрузка..." : "Обновить"}
        </Button>
        <div style={{ color: "#9ca3af", fontSize: 13 }}>
          Данные берём из Payments: GET /accounts
        </div>
      </div>

      <div style={{ height: 12 }} />

      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
        <thead>
          <tr style={{ color: "#9ca3af", textAlign: "left" }}>
            <th style={{ padding: "8px 6px" }}>user_id</th>
            <th style={{ padding: "8px 6px" }}>balance</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.user_id} style={{ borderTop: "1px solid #1f2937" }}>
              <td style={{ padding: "8px 6px" }}>{r.user_id}</td>
              <td style={{ padding: "8px 6px", fontWeight: 800 }}>{r.balance}</td>
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={2} style={{ padding: 12, color: "#9ca3af" }}>
                Аккаунтов пока нет. Создай на вкладке Main.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </Card>
  );
}


export default function App() {
  return (
    <BrowserRouter>
      <Container>
        <TopNav />
        <Routes>
          <Route path="/" element={<MainPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/users" element={<UsersPage />} />
        </Routes>
        <ToastContainer position="bottom-right" />
      </Container>
    </BrowserRouter>
  );
}
