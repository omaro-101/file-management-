# file-management-
This project is a web-based file management and data comparison tool built using Flask, Pandas, and MySQL . It allows authenticated users to upload and compare two Excel files — to detect discrepancies in inventory or shipment records.

⚙️ Key Features :
User Authentication – Secure login system using Flask-Login.

Drag & Drop File Upload – Intuitive interface for uploading two Excel files side by side.

Automatic Table Detection – Reads and compares table names from Excel to ensure consistency.

Dynamic Result Display – Displays comparison results in a styled, sortable HTML table.

MySQL Integration – Saves validated results as new tables in the database.

Existing Tables Viewer – Lists all saved tables for quick access and inspection.

🧰 Tech Stack
Backend: Flask, Flask-Login, SQLAlchemy

Frontend: HTML, CSS (Bootstrap), JavaScript

Database: MySQL + SQLAlchemy ORM

Data Handling: Pandas

Authentication: Login & session handling using Flask-Login

🚀 How to Use
1 - Log in

2 - Upload Two Excel Files

  File 1: Received expedition
  
  File 2: Company expedition

3 - Validate: The system checks for:

  Matching table names
  
  Duplicate tables
  
  Missing or mismatched data

4 - Compare: Results are shown in a clear table.

5 - Save: Valid results are saved to the MySQL database.

6 - Access Past Results: Use the left-side panel to view any previously uploaded comparison
