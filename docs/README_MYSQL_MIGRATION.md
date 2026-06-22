# 🗄️ Database Migration Guide: SQLite to MySQL

This guide provides step-by-step instructions to migrate the Enterprise College Management System (CMS) database from **SQLite** to **MySQL**. It covers installing dependencies, setting up the MySQL database, updating the application configuration, and migrating your existing data.

---

## Step 1: Install MySQL Server

If you do not have MySQL installed on your system:
1. Download the **MySQL Installer for Windows** from the [official website](https://dev.mysql.com/downloads/installer/).
2. Run the installer and choose the **Server Only** or **Developer Default** setup.
3. During setup, configure your root password (e.g., `root123`) and keep the default port (`3306`).
4. Ensure the MySQL service is running (you can check this in the Windows `Services` app).

---

## Step 2: Create the MySQL Database & User

Open your command prompt or terminal and log into the MySQL CLI using the root user:

```bash
mysql -u root -p
```
*(Enter the root password you configured during installation when prompted)*

Run the following SQL commands one by one to create a dedicated database and user for the CMS application:

```sql
-- 1. Create the database with robust encoding
CREATE DATABASE cms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. Create a specific user for the application (Change 'secure_password' to your preference)
CREATE USER 'cms_user'@'localhost' IDENTIFIED BY 'secure_password';

-- 3. Grant the user full permissions on the cms_db
GRANT ALL PRIVILEGES ON cms_db.* TO 'cms_user'@'localhost';

-- 4. Apply the privileges
FLUSH PRIVILEGES;

-- 5. Exit the MySQL prompt
EXIT;
```

---

## Step 3: Install Required Python Packages

Your Python application needs a driver to connect to MySQL. We will use `PyMySQL`, which is a pure-Python MySQL client, and `sqlite3-to-mysql`, a tool to transfer your existing data.

1. Open your terminal in the project directory (`C:\CMS`).
2. Activate your virtual environment:
   ```cmd
   venv\Scripts\activate
   ```
3. Install the packages:
   ```cmd
   pip install PyMySQL sqlite3-to-mysql
   ```
4. Update your `requirements.txt` to save the new dependency:
   ```cmd
   pip freeze > requirements.txt
   ```

---

## Step 4: Migrate Existing Data (Optional but Recommended)

If you want to keep all your existing users, courses, departments, etc., from the SQLite `cms.db`, you need to migrate the data before running the app. 

Run the following CLI command from your project root (ensure your virtual environment is still activated):

```cmd
sqlite3mysql -f ./cms.db -d cms_db -u cms_user -p secure_password -h localhost
```

**Note:** 
- `-f ./cms.db` points to your existing SQLite database.
- `-d cms_db` is the MySQL database you just created.
- Replace `secure_password` with the password you set in Step 2.

This tool will automatically read your SQLite tables, convert the schema, and insert the rows into your new MySQL database.

---

## Step 5: Update the Application Configuration

You must tell SQLAlchemy to connect to the new MySQL database instead of the old SQLite file.

1. Open the `.env` file in the root of your project (`C:\CMS\.env`).
   *(If you don't have a `.env` file, look for the configuration file where `DATABASE_URL` is defined, likely `C:\CMS\app\core\config.py`)*

2. Locate the line that looks like this:
   ```text
   DATABASE_URL="mysql+pymysql://cms_user:secure_password@127.0.0.1:3306/cms_db"
   ```

3. Change it to the MySQL connection string format:
   ```text
   DATABASE_URL="mysql+pymysql://cms_user:secure_password@localhost:3306/cms_db"
   ```
   *(Ensure you replace `secure_password` with your actual database user password)*

---

## Step 6: Run and Verify

Start your application just like before:

```cmd
python run.py
```

### Verification Checklist:
1. Check the console output for the SQLAlchemy startup logs. It should say `Engine(mysql+pymysql://...)` instead of `Engine(sqlite://...)`.
2. Open your browser and navigate to `http://localhost:8000`.
3. Log in with your existing admin credentials.
4. Verify that the Courses, Departments, Subjects, Students, and Teachers modules are loading your data correctly.

---

## Troubleshooting

- **"ModuleNotFoundError: No module named 'pymysql'"**: Ensure you have activated the virtual environment and successfully ran `pip install PyMySQL`.
- **"Access denied for user"**: Double-check the username and password in the `.env` file matches exactly what you created in Step 2.
- **Data Transfer Errors**: If `sqlite3mysql` throws errors regarding foreign keys, you can add the `--ignore-duplicate-keys` flag or manually delete the `cms.db` and simply let SQLAlchemy create fresh, empty tables in MySQL upon running `python run.py`.
