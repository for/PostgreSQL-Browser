import sys
import psycopg2
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QListWidget, QMessageBox, QInputDialog

class PostgreSQLGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.conn = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("PostgreSQL Database Manager")
        self.setGeometry(300, 300, 600, 500)

        mainLayout = QVBoxLayout()

        # Connection settings
        connectionLayout = QHBoxLayout()
        self.hostEdit = QLineEdit("localhost")
        self.portEdit = QLineEdit("5432")
        self.usernameEdit = QLineEdit("postgres")
        self.passwordEdit = QLineEdit()
        self.passwordEdit.setEchoMode(QLineEdit.EchoMode.Password)

        connectionLayout.addWidget(QLabel("Host:"))
        connectionLayout.addWidget(self.hostEdit)
        connectionLayout.addWidget(QLabel("Port:"))
        connectionLayout.addWidget(self.portEdit)
        connectionLayout.addWidget(QLabel("Username:"))
        connectionLayout.addWidget(self.usernameEdit)
        connectionLayout.addWidget(QLabel("Password:"))
        connectionLayout.addWidget(self.passwordEdit)

        # Buttons
        self.connectButton = QPushButton("Connect & List Databases")
        self.connectButton.clicked.connect(self.listDatabases)
        self.createDbButton = QPushButton("Create New Database")
        self.createDbButton.clicked.connect(self.createDatabase)
        self.deleteDbButton = QPushButton("Delete Database")
        self.deleteDbButton.clicked.connect(self.deleteDatabase)
        self.showDbButton = QPushButton("Show Database Contents")
        self.showDbButton.clicked.connect(self.showDatabaseContents)

        # Database List
        self.dbList = QListWidget()

        # Output text area
        self.outputTextEdit = QTextEdit()
        self.outputTextEdit.setReadOnly(True)

        # Add widgets to layout
        mainLayout.addLayout(connectionLayout)
        mainLayout.addWidget(self.connectButton)
        mainLayout.addWidget(self.createDbButton)
        mainLayout.addWidget(self.deleteDbButton)
        mainLayout.addWidget(self.showDbButton)
        mainLayout.addWidget(QLabel("Databases:"))
        mainLayout.addWidget(self.dbList)
        mainLayout.addWidget(self.outputTextEdit)

        self.setLayout(mainLayout)

    def connectToDatabase(self, dbname='postgres'):
        try:
            if self.conn:
                self.conn.close()
            self.conn = psycopg2.connect(
                host=self.hostEdit.text(),
                port=int(self.portEdit.text()),
                user=self.usernameEdit.text(),
                password=self.passwordEdit.text(),
                dbname=dbname
            )
            self.outputTextEdit.append(f"Connected to {dbname} successfully.")
            return True
        except psycopg2.Error as e:
            self.outputTextEdit.append(f"Error connecting to database: {e}")
            return False

    def listDatabases(self):
        if self.connectToDatabase():
            self.outputTextEdit.append("Listing databases...")
            cur = self.conn.cursor()
            cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
            databases = cur.fetchall()
            self.dbList.clear()
            for db in databases:
                self.dbList.addItem(db[0])
            cur.close()

    def createDatabase(self):
        dbname, ok = QInputDialog.getText(self, 'Create Database', 'Enter database name:')
        if ok and dbname:
            try:
                # Ensure we are connected to the default database to create a new one
                if self.connectToDatabase():
                    # Set the connection to autocommit mode
                    self.conn.autocommit = True

                    cur = self.conn.cursor()
                    cur.execute(f"CREATE DATABASE \"{dbname}\"")
                    cur.close()

                    # Optionally, you can turn autocommit off after creating the database
                    # if you plan to execute other commands that should be run in a transaction.
                    # self.conn.autocommit = False

                    self.outputTextEdit.append(f"Database {dbname} created successfully.")
                    self.listDatabases()  # Refresh the database list
            except psycopg2.Error as e:
                self.outputTextEdit.append(f"Error creating database: {e}")

    def deleteDatabase(self):
        selected_db = self.dbList.currentItem()
        if selected_db:
            dbname = selected_db.text()
            reply = QMessageBox.question(self, 'Delete Database', f"Are you sure you want to delete database '{dbname}'?", 
                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                             QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    # Ensure we are connected to the default database to delete another one
                    if self.connectToDatabase():
                        # Set the connection to autocommit mode
                        self.conn.autocommit = True

                        cur = self.conn.cursor()
                        cur.execute(f"DROP DATABASE IF EXISTS \"{dbname}\"")
                        cur.close()

                        self.outputTextEdit.append(f"Database {dbname} deleted successfully.")
                        self.listDatabases()  # Refresh the database list
                        self.dbList.takeItem(self.dbList.row(selected_db))  # Remove the item from the list
                except psycopg2.Error as e:
                    self.outputTextEdit.append(f"Error deleting database: {e}")
            else:
                self.outputTextEdit.append(f"Deletion of database '{dbname}' cancelled.")
        else:
            self.outputTextEdit.append("No database selected.")

    def showDatabaseContents(self):
        selected_db = self.dbList.currentItem()
        if selected_db:
            dbname = selected_db.text()
            try:
                if self.connectToDatabase(dbname):
                    cur = self.conn.cursor()
                    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
                    tables = cur.fetchall()
                    self.outputTextEdit.append(f"Tables in database {dbname}:")
                    for table in tables:
                        self.outputTextEdit.append(f"- {table[0]}")
                        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table[0]}'")
                        columns = cur.fetchall()
                        self.outputTextEdit.append(f"  Columns:")
                        for column in columns:
                            self.outputTextEdit.append(f"    - {column[0]}")
                        cur.execute(f"SELECT * FROM {table[0]}")
                        rows = cur.fetchall()
                        self.outputTextEdit.append(f"  Rows:")
                        for row in rows:
                            self.outputTextEdit.append(f"    - {row}")
                    cur.close()
            except psycopg2.Error as e:
                self.outputTextEdit.append(f"Error showing database contents: {e}")
        else:
            self.outputTextEdit.append("No database selected.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = PostgreSQLGUI()
    gui.show()
    sys.exit(app.exec())