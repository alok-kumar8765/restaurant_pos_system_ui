# 🍽️ Restaurant POS System
=========================

A simple, user-friendly Restaurant Point of Sale (POS) System built with **Python, Streamlit, SQLite, and Pandas** to manage restaurant orders, menu items, billing, sales reports, and data exports through an interactive web interface.

!Python !Streamlit !SQLite !Pandas !License !Status

📌 Table of Contents
--------------------

*   About the Project
    
*   Project Objectives
    
*   Features
    
*   Technology Stack
    
*   Project Structure
    
*   System Requirements
    
*   Installation Guide
    
*   How to Run the Application
    
*   How to Use
    
*   Database Design
    
*   Use Cases
    
*   Advantages and Disadvantages
    
*   Current Limitations
    
*   Future Improvements
    
*   Troubleshooting
    
*   Security and Data Management
    
*   Contributing
    
*   License
    
*   Acknowledgements
    
*   Author
    

## 📖 About the Project
--------------------

The **Restaurant POS System** is a lightweight restaurant management application designed to simplify everyday billing and order management tasks.

Traditional manual billing can be time-consuming and may lead to calculation errors, inconsistent records, and difficulties tracking sales. This project provides a centralized interface where restaurant staff can manage menu items, create customer orders, calculate bills, save transactions, and review sales history.

The application uses **Streamlit** to provide an interactive web interface, **SQLite** to store data locally, and **Pandas** to retrieve and analyze tabular data.

It is suitable for learning Python application development, database integration, dashboard creation, and basic restaurant management workflows.

### 🎯 Project Objectives

*   Simplify restaurant order creation and billing.
    
*   Maintain a structured digital menu.
    
*   Automatically calculate subtotals, discounts, taxes, and final totals.
    
*   Store completed orders and their individual items in a database.
    
*   Provide a dashboard for monitoring sales and order activity.
    
*   Allow users to export records and download database backups.
    
*   Demonstrate the practical use of Python, SQL, and Streamlit.
    

## ✨ Features
----------

### 📊 1. Restaurant Dashboard

*   View total revenue from recorded orders.
    
*   Monitor the total number of completed orders.
    
*   View the total number of menu items.
    
*   Display the ten most recent orders.
    
*   Visualize daily sales using a line chart.
    
*   Show an informative message when no orders exist.
    

### 🛒 2. Point of Sale (POS)

*   Browse available menu items.
    
*   Search for food items by name.
    
*   Filter menu items by category.
    
*   Add products to the shopping cart.
    
*   Increase item quantities.
    
*   Remove items from the cart.
    
*   Calculate the order subtotal automatically.
    
*   Enter customer information.
    
*   Choose an order type:
    
    *   Dine-in
        
    *   Takeaway
        
    *   Delivery
        
*   Apply a fixed monetary discount.
    
*   Configure a tax percentage.
    
*   Select a payment method:
    
    *   Cash
        
    *   UPI
        
    *   Card
        
    *   Other
        
*   Calculate the final payable amount.
    
*   Save completed orders to the database.
    
*   Generate a text-based receipt.
    
*   Download the latest receipt.
    

### 📋 3. Menu Management

*   Add new menu items.
    
*   Specify item names, categories, and prices.
    
*   Mark items as available or unavailable.
    
*   View the complete menu.
    
*   Edit existing menu items.
    
*   Update prices and categories.
    
*   Prevent duplicate menu item names, regardless of letter case.
    

### 🧾 4. Order History

*   View previously completed orders.
    
*   Filter orders by a date range.
    
*   Calculate total sales for the selected period.
    
*   View individual items associated with an order.
    
*   Export filtered order records as a CSV file.
    

### 💾 5. Data Export and Backup

*   Download menu data in CSV format.
    
*   Export all recorded orders to CSV.
    
*   Download a copy of the SQLite database.
    
*   Keep a local backup of restaurant records.
    

### 🗄️ 6. Local Database

*   Automatically create the database and required tables.
    
*   Store menu items, orders, and order details.
    
*   Insert sample menu items when the menu is initially empty.
    
*   Persist data between application restarts as long as the database file is retained.
    

🧰 Technology Stack
-------------------

TechnologyPurposePythonApplication logic and calculationsStreamlitInteractive web interfaceSQLiteLocal relational databasePandasData retrieval, filtering, and analysissqlite3Python interface for SQLitedatetimeOrder timestamps and date filteringpathlibDatabase file path management

### Main Python Libraries

*   **Streamlit:** Creates the dashboard, navigation, forms, tables, and interactive controls.
    
*   **Pandas:** Processes database records and prepares data for display and export.
    
*   **SQLite:** Stores menu items, completed orders, and order line items in a local database.
    

## 📁 Project Structure
--------------------

The project can be organized as follows:

```
restaurant-pos/  │  ├── app.py                    # Main Streamlit application  ├── restaurant_pos.db         # SQLite database (created automatically)  ├── requirements.txt           # Python dependencies  ├── README.md                  # Project documentation  ├── .gitignore                 # Files excluded from Git  │  └── LICENSE                    # Project license (optional)
```

**Important:** The database file is generated automatically when the application initializes. It does not need to exist before the first run.

The requirements.txt, .gitignore, and LICENSE files are recommended project files; they are not created by the supplied application code.

## 💻 System Requirements
----------------------

Before installing the application, ensure you have:

*   Python 3.10 or newer recommended.
    
*   Pip, the Python package installer.
    
*   A modern web browser.
    
*   A terminal or command prompt.
    
*   Git (optional, for cloning the repository).
    

Supported environments include Windows, macOS, and Linux, provided Python and the required dependencies are installed.

⚙️ Installation Guide
---------------------

Follow these steps to set up the project on your computer.

### Step 1: Clone the Repository

Replace the example repository URL with your actual GitHub repository URL.

```py
git clone https://github.com/alok-kaushal8765/resturant_system_ui.git
```

Navigate to the project directory:

```py
cd resturant_system_ui
```

Alternatively, download the project as a ZIP file from GitHub and extract it.

### Step 2: Create a Virtual Environment

A virtual environment keeps the project's dependencies separate from other Python applications.

**Windows:**


```py
python -m venv venv  venv\Scripts\activate
```

If you use PowerShell and activation is blocked, you may need to adjust your local execution policy or activate the environment through Command Prompt instead.

**macOS / Linux:**

```py
python3 -m venv venv  source venv/bin/activate
```

### Step 3: Create requirements.txt

Create a file named requirements.txt in the project root and add:

```
streamlit  pandas
```

These are the external Python packages imported by the application. The sqlite3, datetime, and pathlib modules are included with Python.

For reproducible installations, you can pin the package versions after testing the application in your environment.

### Step 4: Install Dependencies

With your virtual environment activated, run:

```

python -m pip install --upgrade pip  pip install -r requirements.txt
```

Wait for the installation to finish.

### Step 5: Verify the Project Files

Ensure that the main Python file is named app.py, or remember the actual filename if you used a different name.

Your project directory should contain at least:

```

 app.py  requirements.txt
```

The database will be created automatically when the application runs.

🚀 How to Run the Application
-----------------------------

Start the Streamlit application from the project directory:

```

 streamlit run app.py
```

Streamlit will start a local web server and usually open the application in your default browser.

If it does not open automatically, visit:

```

http://localhost:8501
```

To stop the application, press Ctrl + C in the terminal where Streamlit is running.

### First-Time Startup

When the application starts for the first time, it:

1.  Creates restaurant\_pos.db in the same directory as app.py.
    
2.  Creates the menu, orders, and order\_items tables.
    
3.  Inserts sample menu items if the menu table is empty.
    
4.  Displays the dashboard.
    

You can then start adding menu items or creating orders.

🖥️ How to Use
--------------

### 1\. Dashboard

Select **Dashboard** from the sidebar.

Here you can:

*   Review total recorded revenue.
    
*   Check the number of orders.
    
*   See the number of menu items.
    
*   Review recent transactions.
    
*   Analyze daily sales activity.
    

The dashboard updates when completed orders are saved.

### 2\. Manage the Menu

Select **Menu Management**.

To add an item:

1.  Enter the item name.
    
2.  Enter its category.
    
3.  Set the price in Indian rupees (₹).
    
4.  Choose whether the item is available for ordering.
    
5.  Click **Add Item**.
    

To edit an item:

1.  Select the item from the existing menu.
    
2.  Update its details.
    
3.  Click **Save Changes**.
    

Unavailable items remain in the database but are excluded from the new-order menu.

### 3\. Create a New Order

Select **New Order**.

1.  Search for an item or select a category.
    
2.  Click **Add** beside each item you want to order.
    
3.  Adjust quantities in the current order panel.
    
4.  Remove unwanted items if necessary.
    
5.  Review the subtotal.
    
6.  Enter the customer name, or leave it blank for a walk-in customer.
    
7.  Select the order type.
    
8.  Enter a discount if applicable.
    
9.  Set the tax rate.
    
10.  Select the payment method.
    
11.  Review the displayed tax and grand total.
    
12.  Click **Complete Order**.
    

After successful checkout, the order and its line items are saved to SQLite. The application displays a receipt that you can download.

**Billing formula:**

```

Subtotal = Sum of (Item Price × Quantity)  Taxable Amount = Max(Subtotal − Discount, 0)  Tax = Taxable Amount × Tax Rate / 100  Grand Total = Taxable Amount + Tax
```

The tax rate defaults to 0%, so configure the appropriate rate before using the application for actual billing.

### 4\. Review Order History

Select **Order History**.

1.  Choose the start date.
    
2.  Choose the end date.
    
3.  Review the filtered orders and total sales.
    
4.  Select an order to view its
