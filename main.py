import sys
import psycopg2
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QComboBox
)

conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вход")
        self.setGeometry(100, 100, 600, 400)

        page_layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        self.id_input = QLineEdit(self)
        self.id_input.setPlaceholderText("ID пользователя")
        page_layout.addWidget(self.id_input)
        page_layout.addLayout(button_layout)

        self.login_button = QPushButton("Войти", self)
        self.login_button.clicked.connect(self.login)
        button_layout.addWidget(self.login_button)

        self.register_button = QPushButton("Зарегистрироваться", self)
        self.register_button.clicked.connect(self.open_registration_window)
        button_layout.addWidget(self.register_button)

        self.setLayout(page_layout)

    def login(self):
        user_id = int(self.id_input.text())
        cursor.execute("SELECT * FROM customer_exists(%s);", (user_id,))
        user = cursor.fetchone()[0]

        if user:
            QMessageBox.information(self, "Успех", "Вход выполнен успешно!")
            self.close()
            self.open_main_window(user_id)
        else:
            QMessageBox.warning(self, "Ошибка", "Пользователь не найден.")

    def open_registration_window(self):
        self.registration_window = RegistrationWindow()
        self.registration_window.show()
        self.close()

    def open_main_window(self, user_id):
        self.main_window = MainWindow(user_id)
        self.main_window.show()
        self.close()


class RegistrationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Регистрация")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.age_input = QLineEdit(self)
        self.age_input.setPlaceholderText("Возраст пользователя")
        layout.addWidget(self.age_input)

        self.gender_combo = QComboBox(self)
        self.gender_combo.addItems(["Male", "Female"])
        layout.addWidget(self.gender_combo)

        self.register_button = QPushButton("Зарегистрироваться")
        self.register_button.clicked.connect(self.register)
        layout.addWidget(self.register_button)

        self.setLayout(layout)

    def register(self):
        age = self.age_input.text()
        gender = self.gender_combo.currentText()

        if age and gender:
            try:
                cursor.execute("SELECT add_customer(%s, %s);", (int(age), gender))
                customer_id = cursor.fetchone()[0]
                conn.commit()
                QMessageBox.information(self, "Успех", f'Регистрация прошла успешно!\nВаш id: {customer_id}')
                self.open_main_window(customer_id)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", str(e))
        else:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля.")

    def open_main_window(self, user_id):
        self.main_window = MainWindow(user_id)
        self.main_window.show()
        self.close()


class MainWindow(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.order_id = None
        self.setGeometry(100, 100, 800, 600)

        page_layout = QHBoxLayout()
        button_layout = QVBoxLayout()

        self.table_widget = QTableWidget()
        page_layout.addWidget(self.table_widget)

        self.catalog_button = QPushButton("Каталог")
        self.catalog_button.clicked.connect(self.show_catalog)
        button_layout.addWidget(self.catalog_button)

        self.cart_button = QPushButton("Корзина")
        self.cart_button.clicked.connect(self.show_cart)
        button_layout.addWidget(self.cart_button)

        self.history_button = QPushButton("История заказов")
        self.history_button.clicked.connect(self.show_history)
        button_layout.addWidget(self.history_button)

        self.add_to_cart_button = QPushButton("Добавить в корзину")
        self.add_to_cart_button.clicked.connect(self.add_to_cart)
        button_layout.addWidget(self.add_to_cart_button)

        self.complete_order_button = QPushButton("Оформить заказ")
        self.complete_order_button.clicked.connect(self.complete_order)
        button_layout.addWidget(self.complete_order_button)

        self.top_products_button = QPushButton("Топ продуктов")
        self.top_products_button.clicked.connect(self.show_top_products)
        button_layout.addWidget(self.top_products_button)

        self.show_catalog()

        page_layout.addLayout(button_layout)
        self.setLayout(page_layout)

    def update_table(self, name):
        self.setWindowTitle(name)
        rows = cursor.fetchall()

        self.table_widget.setRowCount(len(rows))
        self.table_widget.setColumnCount(len(rows[0]))
        self.table_widget.setHorizontalHeaderLabels([desc[0] for desc in cursor.description])

        for i, row in enumerate(rows):
            for j, item in enumerate(row):
                self.table_widget.setItem(i, j, QTableWidgetItem(str(item)))

    def show_catalog(self):
        cursor.execute("SELECT * FROM products;")
        self.update_table("Каталог")

    def show_cart(self):
        if(self.order_id is None):
            QMessageBox.warning(self, "Ошибка", "Продукты не выбраны!")
            return
        cursor.execute(f"SELECT * FROM get_cart({self.order_id});")
        self.update_table("Корзина")

    def show_history(self):
        cursor.execute(f"SELECT * FROM get_customer_orders({self.user_id});")
        self.update_table("История заказов")

    def add_to_cart(self):
        if(self.windowTitle() == "История заказов"):
            QMessageBox.warning(self, "Ошибка", "Продукт не выбран!")
            return
        if(self.order_id is None):
            cursor.execute(f"SELECT add_order({self.user_id});")
            self.order_id = int(cursor.fetchone()[0])
            conn.commit()

        row = self.table_widget.currentRow()
        column = 0
        product_id = self.table_widget.item(row, column).text()
        cursor.execute("CALL add_order_item(%s, %s)", (self.order_id, product_id))
        conn.commit()
        QMessageBox.information(self, "Успех", f'Продукт {product_id} успешно добавлен в корзину!')

    def complete_order(self):
        if (self.order_id is None):
            QMessageBox.warning(self, "Ошибка", "Продукты не выбраны!")
            return
        cursor.execute("CALL complete_order(%s, %s, %s, %s)", (self.order_id, self.user_id, 'Paypal', 'Overnight'))
        conn.commit()
        QMessageBox.information(self, "Успех", 'Заказ успешно оформлен!')
        self.order_id = None

    def show_top_products(self):
        cursor.execute("SELECT * FROM get_top_products(10);")
        self.update_table("Топ продуктов")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    # main_window = MainWindow(1000)
    # main_window.show()
    sys.exit(app.exec())