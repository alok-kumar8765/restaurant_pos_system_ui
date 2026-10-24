import sqlite3
from datetime import datetime, date
from pathlib import Path

import pandas as pd
import streamlit as st

# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

DB_PATH = Path(__file__).parent / "restaurant_pos.db"

st.set_page_config(
    page_title="Restaurant POS",
    page_icon="🍽️",
    layout="wide"
)


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS menu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL COLLATE NOCASE,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                available INTEGER NOT NULL DEFAULT 1
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT,
                order_type TEXT,
                subtotal REAL,
                discount REAL,
                tax REAL,
                total REAL,
                payment_method TEXT,
                created_at TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                item_name TEXT,
                quantity INTEGER,
                price REAL,
                total REAL,
                FOREIGN KEY(order_id) REFERENCES orders(id)
            )
        """)

        count = conn.execute(
            "SELECT COUNT(*) FROM menu"
        ).fetchone()[0]

        if count == 0:
            sample_menu = [
                ("Veg Burger", "Burgers", 99),
                ("Cheese Burger", "Burgers", 139),
                ("French Fries", "Sides", 79),
                ("Margherita Pizza", "Pizza", 199),
                ("Farmhouse Pizza", "Pizza", 279),
                ("Veg Sandwich", "Sandwiches", 89),
                ("Cold Coffee", "Drinks", 99),
                ("Masala Tea", "Drinks", 25),
                ("Paneer Wrap", "Wraps", 149),
            ]

            conn.executemany(
                """
                INSERT INTO menu(name, category, price)
                VALUES (?, ?, ?)
                """,
                sample_menu
            )


initialize_database()


def get_menu(available_only=False):
    query = "SELECT * FROM menu"

    if available_only:
        query += " WHERE available = 1"

    query += " ORDER BY category, name"

    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


def format_money(amount):
    return f"₹{amount:,.2f}"


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "cart" not in st.session_state:
    st.session_state.cart = {}

if "last_receipt" not in st.session_state:
    st.session_state.last_receipt = None


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

st.sidebar.title("🍽️ Restaurant POS")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "New Order",
        "Menu Management",
        "Order History",
        "Data Export"
    ]
)


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

if page == "Dashboard":

    st.title("📊 Restaurant Dashboard")

    with get_connection() as conn:
        orders = pd.read_sql_query(
            "SELECT * FROM orders",
            conn
        )

        menu = pd.read_sql_query(
            "SELECT * FROM menu",
            conn
        )

    revenue = (
        orders["total"].sum()
        if not orders.empty else 0
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Revenue",
        format_money(revenue)
    )

    col2.metric(
        "Total Orders",
        len(orders)
    )

    col3.metric(
        "Menu Items",
        len(menu)
    )

    st.divider()

    if not orders.empty:

        st.subheader("Recent Orders")

        st.dataframe(
            orders.sort_values(
                "id", ascending=False
            ).head(10),
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Sales Overview")

        chart_data = orders.copy()

        chart_data["Day"] = pd.to_datetime(
            chart_data["created_at"]
        ).dt.date

        daily_sales = chart_data.groupby(
            "Day"
        )["total"].sum()

        st.line_chart(daily_sales)

    else:
        st.info(
            "No completed orders yet. "
            "Create your first order to see sales data."
        )


# --------------------------------------------------
# NEW ORDER / POS
# --------------------------------------------------

elif page == "New Order":

    st.title("🛒 Point of Sale")

    menu = get_menu(available_only=True)

    if menu.empty:
        st.warning("No available menu items.")

    else:

        menu_col, cart_col = st.columns(
            [1.2, 1]
        )

        # ---------------- MENU ----------------

        with menu_col:

            st.subheader("Digital Menu")

            search = st.text_input(
                "Search food items"
            )

            categories = [
                "All"
            ] + sorted(
                menu["category"].unique().tolist()
            )

            category = st.selectbox(
                "Filter by category",
                categories
            )

            filtered = menu.copy()

            if search:
                filtered = filtered[
                    filtered["name"].str.contains(
                        search,
                        case=False,
                        na=False
                    )
                ]

            if category != "All":
                filtered = filtered[
                    filtered["category"] == category
                ]

            for _, item in filtered.iterrows():

                c1, c2, c3 = st.columns(
                    [3, 1, 1]
                )

                c1.write(f"**{item['name']}**")
                c1.caption(item["category"])

                c2.write(
                    format_money(item["price"])
                )

                if c3.button(
                    "Add",
                    key=f"add_{item['id']}"
                ):

                    key = str(item["id"])

                    if key in st.session_state.cart:
                        st.session_state.cart[key][
                            "quantity"
                        ] += 1

                    else:
                        st.session_state.cart[key] = {
                            "name": item["name"],
                            "price": float(item["price"]),
                            "quantity": 1
                        }

                    st.rerun()

        # ---------------- CART ----------------

        with cart_col:

            st.subheader("Current Order")

            cart = st.session_state.cart

            if not cart:

                st.info("Your cart is empty.")

            else:

                for key in list(cart.keys()):

                    item = cart[key]

                    with st.container(border=True):

                        st.write(
                            f"**{item['name']}**"
                        )

                        qcol, rcol = st.columns(
                            [2, 1]
                        )

                        quantity = qcol.number_input(
                            "Quantity",
                            min_value=1,
                            max_value=99,
                            value=item["quantity"],
                            key=f"qty_{key}"
                        )

                        cart[key]["quantity"] = quantity

                        if rcol.button(
                            "Remove",
                            key=f"remove_{key}"
                        ):
                            del cart[key]
                            st.rerun()

                subtotal = sum(
                    item["price"] * item["quantity"]
                    for item in cart.values()
                )

                st.metric(
                    "Subtotal",
                    format_money(subtotal)
                )

                # ---------------- CHECKOUT ----------------

                with st.form("checkout_form"):

                    customer = st.text_input(
                        "Customer name"
                    )

                    order_type = st.selectbox(
                        "Order type",
                        [
                            "Dine-in",
                            "Takeaway",
                            "Delivery"
                        ]
                    )

                    discount = st.number_input(
                        "Discount (₹)",
                        min_value=0.0,
                        max_value=float(subtotal),
                        value=0.0
                    )

                    tax_rate = st.number_input(
                        "Tax rate (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=0.0,
                        step=0.5
                    )

                    payment = st.selectbox(
                        "Payment method",
                        [
                            "Cash",
                            "UPI",
                            "Card",
                            "Other"
                        ]
                    )

                    taxable = max(
                        subtotal - discount,
                        0
                    )

                    tax_amount = round(
                        taxable * tax_rate / 100,
                        2
                    )

                    total = round(
                        taxable + tax_amount,
                        2
                    )

                    st.write(
                        f"Tax: {format_money(tax_amount)}"
                    )

                    st.subheader(
                        f"Grand Total: {format_money(total)}"
                    )

                    submit = st.form_submit_button(
                        "Complete Order",
                        type="primary",
                        use_container_width=True
                    )

                if submit:

                    try:

                        created_at = datetime.now().isoformat(
                            timespec="seconds"
                        )

                        with get_connection() as conn:

                            cursor = conn.execute(
                                """
                                INSERT INTO orders
                                (
                                    customer,
                                    order_type,
                                    subtotal,
                                    discount,
                                    tax,
                                    total,
                                    payment_method,
                                    created_at
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    customer.strip() or "Walk-in Customer",
                                    order_type,
                                    subtotal,
                                    discount,
                                    tax_amount,
                                    total,
                                    payment,
                                    created_at
                                )
                            )

                            order_id = cursor.lastrowid

                            for item in cart.values():

                                line_total = (
                                    item["price"]
                                    * item["quantity"]
                                )

                                conn.execute(
                                    """
                                    INSERT INTO order_items
                                    (
                                        order_id,
                                        item_name,
                                        quantity,
                                        price,
                                        total
                                    )
                                    VALUES (?, ?, ?, ?, ?)
                                    """,
                                    (
                                        order_id,
                                        item["name"],
                                        item["quantity"],
                                        item["price"],
                                        line_total
                                    )
                                )

                        receipt_lines = [
                            "       RESTAURANT POS",
                            "=" * 32,
                            f"Order: #{order_id}",
                            f"Date: {created_at}",
                            f"Customer: {customer or 'Walk-in Customer'}",
                            f"Type: {order_type}",
                            "-" * 32
                        ]

                        for item in cart.values():

                            line_total = (
                                item["price"]
                                * item["quantity"]
                            )

                            receipt_lines.append(
                                f"{item['name']} x{item['quantity']}"
                            )

                            receipt_lines.append(
                                format_money(line_total)
                            )

                        receipt_lines.extend([
                            "-" * 32,
                            f"Subtotal: {format_money(subtotal)}",
                            f"Discount: {format_money(discount)}",
                            f"Tax: {format_money(tax_amount)}",
                            f"TOTAL: {format_money(total)}",
                            f"Payment: {payment}",
                            "=" * 32,
                            "Thank you! Visit again."
                        ])

                        st.session_state.last_receipt = (
                            "\n".join(receipt_lines)
                        )

                        st.session_state.cart = {}

                        st.success(
                            f"Order #{order_id} saved successfully."
                        )

                        st.rerun()

                    except sqlite3.Error as error:

                        st.error(
                            f"Database error: {error}"
                        )

    # Receipt remains available after checkout reruns.

    if st.session_state.last_receipt:

        st.divider()
        st.subheader("Latest Receipt")

        st.code(
            st.session_state.last_receipt,
            language=None
        )

        st.download_button(
            "Download Receipt",
            data=st.session_state.last_receipt,
            file_name="restaurant_receipt.txt",
            mime="text/plain"
        )


# --------------------------------------------------
# MENU MANAGEMENT
# --------------------------------------------------

elif page == "Menu Management":

    st.title("📋 Menu Management")

    st.subheader("Add Menu Item")

    with st.form("add_menu_form"):

        name = st.text_input("Item name")

        category = st.text_input(
            "Category",
            placeholder="Pizza, Drinks, Snacks"
        )

        price = st.number_input(
            "Price (₹)",
            min_value=0.0,
            value=50.0,
            step=5.0
        )

        available = st.checkbox(
            "Available for ordering",
            value=True
        )

        add = st.form_submit_button(
            "Add Item",
            type="primary"
        )

    if add:

        if not name.strip() or not category.strip():

            st.error(
                "Please enter an item name and category."
            )

        else:

            try:

                with get_connection() as conn:

                    conn.execute(
                        """
                        INSERT INTO menu
                        (name, category, price, available)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            name.strip(),
                            category.strip(),
                            price,
                            int(available)
                        )
                    )

                st.success("Menu item added.")
                st.rerun()

            except sqlite3.IntegrityError:

                st.error(
                    "An item with that name already exists."
                )

    st.divider()

    st.subheader("Existing Menu")

    menu = get_menu()

    st.dataframe(
        menu,
        hide_index=True,
        use_container_width=True
    )

    if not menu.empty:

        choices = {
            f"{row['id']} — {row['name']}": row["id"]
            for _, row in menu.iterrows()
        }

        selected = st.selectbox(
            "Select item to edit",
            list(choices.keys())
        )

        item_id = choices[selected]

        item = menu[
            menu["id"] == item_id
        ].iloc[0]

        with st.form("edit_menu_form"):

            edit_name = st.text_input(
                "Item name",
                value=item["name"]
            )

            edit_category = st.text_input(
                "Category",
                value=item["category"]
            )

            edit_price = st.number_input(
                "Price (₹)",
                min_value=0.0,
                value=float(item["price"]),
                step=5.0
            )

            edit_available = st.checkbox(
                "Available for ordering",
                value=bool(item["available"])
            )

            save = st.form_submit_button(
                "Save Changes"
            )

        if save:

            try:

                with get_connection() as conn:

                    conn.execute(
                        """
                        UPDATE menu
                        SET name=?, category=?, price=?, available=?
                        WHERE id=?
                        """,
                        (
                            edit_name.strip(),
                            edit_category.strip(),
                            edit_price,
                            int(edit_available),
                            item_id
                        )
                    )

                st.success("Menu item updated.")
                st.rerun()

            except sqlite3.IntegrityError:

                st.error(
                    "Another item already uses that name."
                )


# --------------------------------------------------
# ORDER HISTORY
# --------------------------------------------------

elif page == "Order History":

    st.title("🧾 Order History")

    with get_connection() as conn:

        orders = pd.read_sql_query(
            """
            SELECT * FROM orders
            ORDER BY id DESC
            """,
            conn
        )

    if orders.empty:

        st.info("No orders have been completed yet.")

    else:

        start = st.date_input(
            "From date",
            value=date.today().replace(day=1)
        )

        end = st.date_input(
            "To date",
            value=date.today()
        )

        orders["order_date"] = pd.to_datetime(
            orders["created_at"]
        ).dt.date

        filtered = orders[
            (orders["order_date"] >= start)
            & (orders["order_date"] <= end)
        ]

        st.metric(
            "Filtered Sales",
            format_money(filtered["total"].sum())
        )

        st.dataframe(
            filtered,
            hide_index=True,
            use_container_width=True
        )

        if not filtered.empty:

            selected_order = st.selectbox(
                "View order items",
                filtered["id"].tolist()
            )

            with get_connection() as conn:

                details = pd.read_sql_query(
                    """
                    SELECT item_name, quantity, price, total
                    FROM order_items
                    WHERE order_id=?
                    """,
                    conn,
                    params=(int(selected_order),)
                )

            st.subheader(
                f"Items in Order #{selected_order}"
            )

            st.dataframe(
                details,
                hide_index=True,
                use_container_width=True
            )

        st.download_button(
            "Export Orders CSV",
            data=filtered.to_csv(index=False),
            file_name="restaurant_orders.csv",
            mime="text/csv"
        )


# --------------------------------------------------
# DATA EXPORT
# --------------------------------------------------

elif page == "Data Export":

    st.title("💾 Data Export & Backup")

    menu = get_menu()

    with get_connection() as conn:

        orders = pd.read_sql_query(
            "SELECT * FROM orders",
            conn
        )

    st.subheader("Export Menu")

    st.download_button(
        "Download Menu CSV",
        data=menu.to_csv(index=False),
        file_name="restaurant_menu.csv",
        mime="text/csv"
    )

    st.subheader("Export Orders")

    st.download_button(
        "Download All Orders CSV",
        data=orders.to_csv(index=False),
        file_name="restaurant_orders.csv",
        mime="text/csv"
    )

    st.subheader("Database Backup")

    if DB_PATH.exists():

        st.download_button(
            "Download SQLite Database",
            data=DB_PATH.read_bytes(),
            file_name="restaurant_pos_backup.db",
            mime="application/octet-stream"
        )

    st.warning(
        "This application stores data locally. "
        "Back up your database regularly."
    )

    st.caption(
        "Payment options are recorded only; no actual UPI or card payment "
        "is processed. Tax defaults to 0%. Confirm the correct tax rate "
        "for your business before using this for real billing."
    )