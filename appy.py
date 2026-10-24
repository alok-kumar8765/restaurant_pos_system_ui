
from pathlib import Path
from datetime import datetime, date
import sqlite3

import pandas as pd
import streamlit as st

# =====================================================
# CONFIGURATION
# =====================================================

DB_PATH = Path(__file__).parent / "restaurant_pos.db"

st.set_page_config(
    page_title="Bistro POS",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================
# MODERN UI DESIGN
# =====================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

.stApp {
    background: #f6f8f5;
    font-family: 'DM Sans', sans-serif;
}

.block-container {
    max-width: 1500px;
    padding-top: 1.8rem;
    padding-bottom: 2rem;
}

h1, h2, h3 {
    font-family: 'Manrope', sans-serif;
    color: #172b22;
    letter-spacing: -0.035em;
}

[data-testid="stSidebar"] {
    background: #14291f;
}

[data-testid="stSidebar"] * {
    color: #f4f8f4;
}

[data-testid="stMetric"] {
    background: white;
    padding: 18px;
    border: 1px solid #e3eae4;
    border-radius: 16px;
    box-shadow: 0 3px 15px #14291f08;
}

[data-testid="stMetricLabel"] {
    color: #718078;
    font-weight: 600;
}

[data-testid="stMetricValue"] {
    color: #176b4d;
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
}

.stButton > button,
.stFormSubmitButton > button,
.stDownloadButton > button {
    border-radius: 10px;
    min-height: 2.5rem;
    font-weight: 700;
    border: 1px solid #dce6df;
}

.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    background: #176b4d;
    color: white;
    border-color: #176b4d;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: white;
    border-radius: 15px;
    border-color: #e3eae4;
}

.hero {
    background: linear-gradient(120deg, #173d2d, #176b4d, #31986b);
    color: white;
    border-radius: 20px;
    padding: 25px 28px;
    margin-bottom: 24px;
}

.hero h1 {
    color: white;
    margin: 0 0 8px 0;
    font-size: 2rem;
}

.hero p {
    color: #d9f0e2;
    margin: 0;
}

.food-emoji {
    font-size: 2rem;
    background: #eef6ef;
    border-radius: 12px;
    padding: 12px;
    display: inline-block;
    margin-bottom: 10px;
}

.muted {
    color: #718078;
    font-size: 0.9rem;
}

hr {
    border-color: #e3eae4;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# DATABASE
# =====================================================

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    with connect_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                category TEXT NOT NULL,
                price REAL NOT NULL CHECK(price >= 0),
                emoji TEXT NOT NULL DEFAULT '🍽️',
                available INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT NOT NULL,
                order_type TEXT NOT NULL,
                subtotal REAL NOT NULL,
                discount REAL NOT NULL,
                tax_rate REAL NOT NULL,
                tax_amount REAL NOT NULL,
                total REAL NOT NULL,
                payment_method TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL
                    REFERENCES orders(id) ON DELETE CASCADE,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                line_total REAL NOT NULL
            );
        """)

        # Insert demonstration data on first run.
        count = conn.execute(
            "SELECT COUNT(*) FROM menu_items"
        ).fetchone()[0]

        if count == 0:
            sample_menu = [
                ("Classic Veg Burger", "Burgers", 129, "🍔", 1),
                ("Cheese Burger", "Burgers", 159, "🍔", 1),
                ("French Fries", "Sides", 99, "🍟", 1),
                ("Margherita Pizza", "Pizza", 229, "🍕", 1),
                ("Farmhouse Pizza", "Pizza", 319, "🍕", 1),
                ("Paneer Wrap", "Wraps", 159, "🌯", 1),
                ("Cold Coffee", "Drinks", 119, "🥤", 1),
                ("Masala Chai", "Drinks", 35, "☕", 1),
                ("Chocolate Brownie", "Desserts", 109, "🍫", 1),
            ]

            conn.executemany("""
                INSERT INTO menu_items
                (name, category, price, emoji, available)
                VALUES (?, ?, ?, ?, ?)
            """, sample_menu)


def read_menu(available_only=False):
    query = "SELECT * FROM menu_items"

    if available_only:
        query += " WHERE available = 1"

    query += " ORDER BY category, name"

    with connect_db() as conn:
        return pd.read_sql_query(query, conn)


def read_orders(start=None, end=None):
    query = "SELECT * FROM orders"
    conditions = []
    params = []

    if start:
        conditions.append("date(created_at) >= date(?)")
        params.append(str(start))

    if end:
        conditions.append("date(created_at) <= date(?)")
        params.append(str(end))

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY id DESC"

    with connect_db() as conn:
        return pd.read_sql_query(
            query, conn, params=params
        )


def read_order_items(order_id):
    with connect_db() as conn:
        return pd.read_sql_query("""
            SELECT
                item_name AS Item,
                quantity AS Quantity,
                unit_price AS Price,
                line_total AS Total
            FROM order_items
            WHERE order_id = ?
        """, conn, params=(int(order_id),))


# =====================================================
# BUSINESS LOGIC
# =====================================================

def money(value):
    return f"₹{float(value):,.2f}"


def save_menu_item(
    name, category, price, emoji, available, item_id=None
):
    if not name.strip() or not category.strip():
        raise ValueError("Name and category are required.")

    with connect_db() as conn:
        if item_id is None:
            conn.execute("""
                INSERT INTO menu_items
                (name, category, price, emoji, available)
                VALUES (?, ?, ?, ?, ?)
            """, (
                name.strip(),
                category.strip(),
                float(price),
                emoji.strip() or "🍽️",
                int(available),
            ))
        else:
            conn.execute("""
                UPDATE menu_items
                SET name=?, category=?, price=?,
                    emoji=?, available=?
                WHERE id=?
            """, (
                name.strip(),
                category.strip(),
                float(price),
                emoji.strip() or "🍽️",
                int(available),
                int(item_id),
            ))


def finish_order(
    customer, order_type, cart, discount, tax_rate, payment
):
    if not cart:
        raise ValueError("The cart is empty.")

    subtotal = round(sum(
        item["price"] * item["quantity"]
        for item in cart.values()
    ), 2)

    discount = min(max(float(discount), 0), subtotal)

    taxable_amount = max(subtotal - discount, 0)

    tax_amount = round(
        taxable_amount * float(tax_rate) / 100, 2
    )

    total = round(taxable_amount + tax_amount, 2)

    customer = customer.strip() or "Walk-in Customer"
    created_at = datetime.now().isoformat(timespec="seconds")

    # The order and its items are saved in one transaction.
    with connect_db() as conn:
        cursor = conn.execute("""
            INSERT INTO orders (
                customer, order_type, subtotal, discount,
                tax_rate, tax_amount, total,
                payment_method, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer, order_type, subtotal, discount,
            float(tax_rate), tax_amount, total,
            payment, created_at,
        ))

        order_id = cursor.lastrowid

        for item in cart.values():
            line_total = round(
                item["price"] * item["quantity"], 2
            )

            conn.execute("""
                INSERT INTO order_items (
                    order_id, item_name, quantity,
                    unit_price, line_total
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                order_id, item["name"], item["quantity"],
                item["price"], line_total,
            ))

    return {
        "id": order_id,
        "customer": customer,
        "order_type": order_type,
        "subtotal": subtotal,
        "discount": discount,
        "tax_rate": float(tax_rate),
        "tax_amount": tax_amount,
        "total": total,
        "payment": payment,
        "created_at": created_at,
        "items": [
            dict(item) for item in cart.values()
        ],
    }


def create_receipt(order):
    lines = [
        "              BISTRO POS",
        "=" * 36,
        f"Receipt: #{order['id']}",
        f"Date: {order['created_at']}",
        f"Customer: {order['customer']}",
        f"Order type: {order['order_type']}",
        "-" * 36,
    ]

    for item in order["items"]:
        lines.append(
            f"{item['name']} x {item['quantity']}"
        )
        lines.append(
            f"  {money(item['price'])} each"
            f"  |  {money(item['price'] * item['quantity'])}"
        )

    lines.extend([
        "-" * 36,
        f"Subtotal: {money(order['subtotal'])}",
        f"Discount: -{money(order['discount'])}",
        f"Tax ({order['tax_rate']:.2f}%): "
        f"{money(order['tax_amount'])}",
        f"TOTAL: {money(order['total'])}",
        f"Payment: {order['payment']}",
        "=" * 36,
        "Thank you! Please visit again.",
    ])

    return "\n".join(lines)


initialize_database()

# =====================================================
# SESSION STATE
# =====================================================

if "cart" not in st.session_state:
    st.session_state.cart = {}

if "last_receipt" not in st.session_state:
    st.session_state.last_receipt = None

if "last_order_id" not in st.session_state:
    st.session_state.last_order_id = None


# =====================================================
# NAVIGATION
# =====================================================

st.sidebar.markdown("""
<div style="font-size:38px">🥬</div>
<h2 style="color:white;margin:0">Bistro POS</h2>
<p style="color:#b8cabe">
Restaurant operations, simplified.
</p>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "WORKSPACE",
    [
        "Overview",
        "New Order",
        "Menu Manager",
        "Sales & Orders",
        "Data & Backup",
    ],
)

st.sidebar.divider()
st.sidebar.caption("Local restaurant management system")
st.sidebar.caption("Python • Streamlit • Pandas • SQLite")


# =====================================================
# PAGE 1 — DASHBOARD
# =====================================================

if page == "Overview":

    st.markdown("""
    <div class="hero">
        <p>RESTAURANT WORKSPACE</p>
        <h1>Good food. Smooth service.</h1>
        <p>
        Manage orders, maintain your menu,
        and understand your sales at a glance.
        </p>
    </div>
    """, unsafe_allow_html=True)

    orders = read_orders()
    menu = read_menu()

    today = date.today()

    if not orders.empty:
        orders["order_day"] = pd.to_datetime(
            orders["created_at"]
        ).dt.date

        today_orders = orders[
            orders["order_day"] == today
        ]

        today_revenue = float(today_orders["total"].sum())
        lifetime_revenue = float(orders["total"].sum())
    else:
        today_orders = orders
        today_revenue = 0
        lifetime_revenue = 0

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Today's Revenue", money(today_revenue))
    c2.metric("Today's Orders", len(today_orders))
    c3.metric("Lifetime Sales", money(lifetime_revenue))
    c4.metric(
        "Available Items",
        int(menu["available"].sum()) if not menu.empty else 0
    )

    st.write("")

    left, right = st.columns([1.5, 1])

    with left:
        st.subheader("📈 Revenue Trend")

        if orders.empty:
            st.info("Your sales chart will appear after your first order.")
        else:
            chart = orders.copy()
            chart["Day"] = pd.to_datetime(
                chart["created_at"]
            ).dt.date

            daily = chart.groupby("Day")["total"].sum()
            st.line_chart(daily)

    with right:
        st.subheader("⚡ Quick Actions")

        st.caption("Choose a task to get started.")

        if st.button(
            "＋ Start a New Order",
            type="primary",
            use_container_width=True
        ):
            st.session_state.open_pos = True
            st.rerun()

        if st.button(
            "＋ Manage Menu",
            use_container_width=True
        ):
            st.session_state.open_menu = True
            st.rerun()

        st.divider()
        st.subheader("Recent Orders")

        if orders.empty:
            st.caption("No completed orders yet.")
        else:
            recent = orders.head(5)[
                ["id", "customer", "total", "created_at"]
            ].copy()

            recent.columns = [
                "Order", "Customer", "Total", "Date"
            ]

            recent["Total"] = recent["Total"].map(money)

            st.dataframe(
                recent,
                hide_index=True,
                use_container_width=True
            )


# =====================================================
# PAGE 2 — POINT OF SALE
# =====================================================

elif page == "New Order":

    st.markdown("""
    <div class="hero">
        <p>POINT OF SALE</p>
        <h1>Build an order.</h1>
        <p>Explore the menu, add items, and complete checkout.</p>
    </div>
    """, unsafe_allow_html=True)

    menu = read_menu(available_only=True)

    if menu.empty:
        st.warning("No available items. Add items in Menu Manager.")
    else:
        menu_col, cart_col = st.columns([1.35, 1])

        with menu_col:
            st.subheader("🍕 Explore the Menu")

            search_col, category_col = st.columns([1.3, 1])

            search = search_col.text_input(
                "Search",
                placeholder="Search dishes...",
                label_visibility="collapsed",
            )

            categories = ["All Categories"] + sorted(
                menu["category"].unique().tolist()
            )

            category = category_col.selectbox(
                "Category",
                categories,
                label_visibility="collapsed",
            )

            shown = menu.copy()

            if search.strip():
                shown = shown[
                    shown["name"].str.contains(
                        search.strip(),
                        case=False,
                        na=False
                    )
                ]

            if category != "All Categories":
                shown = shown[
                    shown["category"] == category
                ]

            if shown.empty:
                st.info("No matching items found.")

            cards = st.columns(2)

            for index, (_, item) in enumerate(shown.iterrows()):
                with cards[index % 2]:
                    with st.container(border=True):
                        st.markdown(
                            f"<div class='food-emoji'>{item['emoji']}</div>",
                            unsafe_allow_html=True
                        )

                        st.markdown(f"**{item['name']}**")
                        st.caption(item["category"])

                        st.markdown(
                            f"### {money(item['price'])}"
                        )

                        if st.button(
                            "＋ Add to Order",
                            key=f"add_{item['id']}",
                            use_container_width=True
                        ):
                            key = str(int(item["id"]))

                            if key in st.session_state.cart:
                                st.session_state.cart[key]["quantity"] += 1
                            else:
                                st.session_state.cart[key] = {
                                    "id": int(item["id"]),
                                    "name": item["name"],
                                    "price": float(item["price"]),
                                    "quantity": 1,
                                }

                            st.rerun()

        with cart_col:
            st.subheader("🛍️ Your Order")

            cart = st.session_state.cart

            if not cart:
                st.info("Your basket is empty. Add an item to begin.")
            else:
                for key in list(cart.keys()):
                    item = cart[key]

                    with st.container(border=True):
                        st.markdown(f"**{item['name']}**")
                        st.caption(
                            f"{money(item['price'])} per item"
                        )

                        qcol, rcol = st.columns([2, 1])

                        quantity = qcol.number_input(
                            "Quantity",
                            min_value=1,
                            max_value=99,
                            value=int(item["quantity"]),
                            key=f"qty_{key}",
                        )

                        st.session_state.cart[key]["quantity"] = int(quantity)

                        if rcol.button(
                            "Remove",
                            key=f"remove_{key}"
                        ):
                            del st.session_state.cart[key]
                            st.rerun()

                        st.write(
                            f"Line total: "
                            f"**{money(item['price'] * quantity)}**"
                        )

                subtotal = sum(
                    item["price"] * item["quantity"]
                    for item in st.session_state.cart.values()
                )

                st.metric("Subtotal", money(subtotal))

                with st.form("checkout_form"):

                    customer = st.text_input(
                        "Customer Name",
                        placeholder="Walk-in Customer"
                    )

                    order_type = st.selectbox(
                        "Order Type",
                        ["Dine-in", "Takeaway", "Delivery"]
                    )

                    discount = st.number_input(
                        "Discount (₹)",
                        min_value=0.0,
                        max_value=float(subtotal),
                        value=0.0,
                        step=10.0,
                    )

                    tax_rate = st.number_input(
                        "Tax Rate (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=0.0,
                        step=0.5,
                    )

                    payment = st.selectbox(
                        "Payment Method",
                        ["Cash", "UPI", "Card", "Other"]
                    )

                    taxable = max(subtotal - discount, 0)

                    tax_preview = round(
                        taxable * tax_rate / 100, 2
                    )

                    total_preview = taxable + tax_preview

                    st.write(f"Tax: {money(tax_preview)}")
                    st.subheader(f"Grand Total: {money(total_preview)}")

                    submitted = st.form_submit_button(
                        "Complete Order",
                        type="primary",
                        use_container_width=True,
                    )

                if submitted:
                    try:
                        order = finish_order(
                            customer,
                            order_type,
                            st.session_state.cart,
                            discount,
                            tax_rate,
                            payment,
                        )

                        st.session_state.last_receipt = create_receipt(order)
                        st.session_state.last_order_id = order["id"]
                        st.session_state.cart = {}

                        st.success(
                            f"Order #{order['id']} saved successfully."
                        )
                        st.rerun()

                    except (ValueError, sqlite3.Error) as exc:
                        st.error(f"Could not complete order: {exc}")

    if st.session_state.last_receipt:
        st.divider()

        st.subheader(
            f"Latest Receipt — #{st.session_state.last_order_id}"
        )

        st.code(st.session_state.last_receipt, language=None)

        st.download_button(
            "⬇ Download Receipt",
            data=st.session_state.last_receipt.encode("utf-8"),
            file_name=f"receipt_{st.session_state.last_order_id}.txt",
            mime="text/plain",
        )


# =====================================================
# PAGE 3 — MENU MANAGEMENT
# =====================================================

elif page == "Menu Manager":

    st.markdown("""
    <div class="hero">
        <p>MENU CATALOGUE</p>
        <h1>Keep the menu fresh.</h1>
        <p>Manage dishes, prices, categories, and availability.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("＋ Add New Menu Item", expanded=True):

        with st.form("add_menu_form"):
            c1, c2 = st.columns(2)

            name = c1.text_input("Item Name")
            category = c2.text_input("Category")

            c3, c4 = st.columns(2)

            price = c3.number_input(
                "Price (₹)",
                min_value=0.0,
                value=99.0,
                step=5.0,
            )

            emoji = c4.text_input("Emoji", value="🍽️")

            available = st.checkbox(
                "Available for ordering",
                value=True
            )

            add = st.form_submit_button(
                "Save Menu Item",
                type="primary"
            )

        if add:
            try:
                save_menu_item(
                    name, category, price, emoji, available
                )
                st.success(f"{name} added to the menu.")
                st.rerun()

            except ValueError as exc:
                st.error(str(exc))

            except sqlite3.IntegrityError:
                st.error("An item with that name already exists.")

    menu = read_menu()

    st.subheader("Existing Menu")

    if menu.empty:
        st.info("No menu items yet.")
    else:
        display = menu.copy()

        display["available"] = display["available"].map({
            1: "Available",
            0: "Hidden",
        })

        st.dataframe(
            display,
            hide_index=True,
            use_container_width=True,
        )

        choices = {
            f"{row.id} — {row.name}": int(row.id)
            for row in menu.itertuples()
        }

        selected = st.selectbox(
            "Select an item to edit",
            list(choices.keys()),
        )

        item_id = choices[selected]

        item = menu[menu["id"] == item_id].iloc[0]

        with st.form("edit_menu_form"):
            edit_name = st.text_input(
                "Item Name",
                value=str(item["name"])
            )

            edit_category = st.text_input(
                "Category",
                value=str(item["category"])
            )

            edit_price = st.number_input(
                "Price (₹)",
                min_value=0.0,
                value=float(item["price"]),
                step=5.0,
            )

            edit_emoji = st.text_input(
                "Emoji",
                value=str(item["emoji"]),
            )

            edit_available = st.checkbox(
                "Available for ordering",
                value=bool(item["available"]),
            )

            save = st.form_submit_button(
                "Update Menu Item",
                type="primary",
            )

        if save:
            try:
                save_menu_item(
                    edit_name,
                    edit_category,
                    edit_price,
                    edit_emoji,
                    edit_available,
                    item_id,
                )

                st.success("Menu item updated.")
                st.rerun()

            except ValueError as exc:
                st.error(str(exc))

            except sqlite3.IntegrityError:
                st.error("Another item already uses that name.")


# =====================================================
# PAGE 4 — SALES AND ORDERS
# =====================================================

elif page == "Sales & Orders":

    st.markdown("""
    <div class="hero">
        <p>BUSINESS INTELLIGENCE</p>
        <h1>Sales & Order History</h1>
        <p>Track revenue, review transactions, and export reports.</p>
    </div>
    """, unsafe_allow_html=True)

    today = date.today()

    c1, c2 = st.columns(2)

    start = c1.date_input(
        "Start Date",
        value=today.replace(day=1)
    )

    end = c2.date_input(
        "End Date",
        value=today
    )

    if start > end:
        st.error("Start date must be on or before end date.")
    else:
        orders = read_orders(start, end)

        if orders.empty:
            st.info("No orders found for the selected dates.")
        else:
            revenue = float(orders["total"].sum())

            a, b, c, d = st.columns(4)

            a.metric("Revenue", money(revenue))
            b.metric("Orders", len(orders))
            c.metric("Average Order", money(revenue / len(orders)))
            d.metric("Discounts", money(orders["discount"].sum()))

            st.subheader("Daily Revenue")

            chart = orders.copy()

            chart["Day"] = pd.to_datetime(
                chart["created_at"]
            ).dt.date

            daily = chart.groupby("Day")["total"].sum()

            st.bar_chart(daily)

            st.subheader("Transactions")

            display = orders[
                [
                    "id", "created_at", "customer",
                    "order_type", "payment_method", "total"
                ]
            ].copy()

            display.columns = [
                "Order #", "Date/Time", "Customer",
                "Order Type", "Payment", "Total"
            ]

            st.dataframe(
                display,
                hide_index=True,
                use_container_width=True,
            )

            order_id = st.selectbox(
                "Inspect Order",
                orders["id"].astype(int).tolist(),
            )

            st.subheader(f"Items in Order #{order_id}")

            st.dataframe(
                read_order_items(order_id),
                hide_index=True,
                use_container_width=True,
            )

            st.download_button(
                "Export Orders CSV",
                data=orders.to_csv(index=False).encode("utf-8"),
                file_name="restaurant_sales.csv",
                mime="text/csv",
            )


# =====================================================
# PAGE 5 — DATA EXPORT AND BACKUP
# =====================================================

elif page == "Data & Backup":

    st.markdown("""
    <div class="hero">
        <p>DATA MANAGEMENT</p>
        <h1>Your data, in your control.</h1>
        <p>Export your reports and download database backups.</p>
    </div>
    """, unsafe_allow_html=True)

    menu = read_menu()
    orders = read_orders()

    a, b, c = st.columns(3)

    a.metric("Menu Items", len(menu))
    b.metric("Saved Orders", len(orders))

    lifetime_sales = (
        orders["total"].sum()
        if not orders.empty else 0
    )

    c.metric("Lifetime Revenue", money(lifetime_sales))

    st.subheader("Export Menu")

    st.download_button(
        "Download Menu CSV",
        data=menu.to_csv(index=False).encode("utf-8"),
        file_name="restaurant_menu.csv",
        mime="text/csv",
    )

    st.subheader("Export Orders")

    st.download_button(
        "Download Orders CSV",
        data=orders.to_csv(index=False).encode("utf-8"),
        file_name="restaurant_orders.csv",
        mime="text/csv",
    )

    st.subheader("Database Backup")

    if DB_PATH.exists():
        st.download_button(
            "Download SQLite Backup",
            data=DB_PATH.read_bytes(),
            file_name=f"restaurant_backup_{date.today()}.db",
            mime="application/octet-stream",
        )

    st.warning(
        "This is a local V1 application. Back up your database regularly. "
        "Payment methods are recorded for reporting; the application does "
        "not process actual UPI or card payments."
    )

    st.caption(
        "Tax defaults to 0%. Confirm the correct tax treatment for your "
        "restaurant before using this application for live billing."
    )
