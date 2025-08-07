from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
import pandas as pd
import mysql.connector

views = Blueprint('views', __name__)

# MySQL connection
my_db = mysql.connector.connect(
    host="localhost",
    port="3305",
    user="root",
    password="omar2005",
    database="files"
)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    df_html = None
    table_found = False
    table_name = ""
    all_tables = []

    cursor = my_db.cursor()
    cursor.execute("SHOW TABLES")
    all_tables = sorted([row[0] for row in cursor.fetchall()])
    cursor.close()

    if request.method == 'POST':
        table_name = request.form.get("expedition")
        table_name = table_name.strip().replace(" ", "_") if table_name else None

        if table_name:
            cursor = my_db.cursor()
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
            """, (my_db.database, table_name))
            exists = cursor.fetchone()[0] == 1

            if exists:
                table_found = True
                flash(f"Table '{table_name}' found successfuly.", category='success')
                cursor.execute(f"SELECT * FROM `{table_name}`")
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]

                if rows:
                    df = pd.DataFrame(rows, columns=columns)
                    target_col = "result"  

                    if target_col in df.columns:
                        df[target_col] = df[target_col].apply(
                            lambda x: f'<span style="color: blue;">{x}</span>' if pd.notna(x) else x
                        )

                    df_html = df.to_html(classes="table table-bordered table-hover highlight-numbers ", index=False, escape=False)
                else:
                    flash(f"Table '{table_name}' is empty.", category='warning')
            else:
                flash(f"Table '{table_name}' does not exist.", category='error')

            cursor.close()

    return render_template(
        "home.html",
        user=current_user,
        df_html=df_html,
        table=table_found,
        table_name=table_name,
        all_tables=all_tables
    )


# Helper: Create table from DataFrame
def create_table_from_excel(df, mydb, table_name):
    cursor = mydb.cursor()
    
    # Step 1: Create table if not exists
    columns_sql = ', '.join([f"`{col}` VARCHAR(255)" for col in df.columns])
    create_query = f"CREATE TABLE IF NOT EXISTS `{table_name}` ({columns_sql});"
    cursor.execute(create_query)

    # Step 2: Insert data
    placeholders = ', '.join(['%s'] * len(df.columns))
    column_names = ', '.join([f"`{col}`" for col in df.columns])
    insert_query = f"INSERT INTO `{table_name}` ({column_names}) VALUES ({placeholders})"

    for _, row in df.iterrows():
        values = [None if pd.isna(val) else str(val) for val in row]
        cursor.execute(insert_query, values)

    mydb.commit()
    cursor.close()



@views.route('/add', methods=['GET', 'POST'])
@login_required
def upload_excel():
    if request.method == 'POST':
        file1 = request.files.get('file1')
        file2 = request.files.get('file2')

        if file1 and file2:
            # Read table name from cell C4
            table_name_1 = pd.read_excel(file1, header=None).iloc[3, 2]
            table_name_2 = pd.read_excel(file2, header=None).iloc[3, 2]

            if table_name_1 != table_name_2:
                flash('The table names in the two files do not match.', 'error')
                return render_template('add.html', user=current_user)
            
            table_name = str(table_name_1).strip().replace(" ", "_")

            cursor = my_db.cursor()
            cursor.execute("SHOW TABLES LIKE %s", (table_name,))
            if cursor.fetchone():
                flash(f"Table '{table_name}' already exists.", 'error')
                cursor.close()
                return render_template('add.html', user=current_user)
            cursor.close()


            # Read relevant data
            df_company = pd.read_excel(file1, usecols=['N° Lot', 'N° Carton'], header=7)
            df_actual = pd.read_excel(file2, usecols=['N° Lot', 'N° Carton'], header=7)

            df_company['N° Lot'] = df_company['N° Lot'].astype('object')
            df_actual['N° Lot'] = df_actual['N° Lot'].astype('object')

            merge = pd.merge(df_company, df_actual, on='N° Lot', how='outer', suffixes=('_company', '_actual'))

            results = pd.DataFrame(columns=["non_concordance", "exist_sans_declaration", "declaree_nexiste_pas", "result"])

            mismatch = 0
            not_in_company = 0
            not_in_actual = 0

            for _, row in merge.iterrows():
                lot = row['N° Lot']
                cpn = row.get('N° Carton_company')
                act = row.get('N° Carton_actual')

                if pd.isna(cpn) and pd.notna(act):
                    results.loc[len(results)] = [None, None, f"Lot {lot} - Carton {act}", None]
                    not_in_actual += 1
                elif pd.notna(cpn) and pd.isna(act):
                    results.loc[len(results)] = [None, f"Lot {lot} - Carton {cpn}", None, None]
                    not_in_company += 1
                elif cpn != act:
                    results.loc[len(results)] = [f"Lot {lot}: en {act}", None, None, None]
                    mismatch += 1

            summary = f"non-concordance: {mismatch}, exist_sans_declaration: {not_in_company}, declaree_nexiste_pas: {not_in_actual}"
            results.loc[len(results)] = [None, None, None, summary]

            # Clean DataFrame
            for col in results.columns:
                values = results[col].dropna().tolist()
                results[col] = values + [None] * (len(results) - len(values))
            results = results.dropna(how='all')

            # Save Excel
            excel_filename = table_name + ".xlsx"
            results.to_excel(excel_filename, sheet_name="results", index=False)

            # Save to MySQL
            mydb = mysql.connector.connect(
                host="localhost",
                port="3305",
                user="root",
                password="omar2005",
                database="files"
            )
            create_table_from_excel(results, mydb, table_name)

            flash('Files uploaded and compared successfully.', 'success')
            return render_template(
                'home.html',
                results=results.to_html(classes="table table-bordered table-hover", index=False),
                user=current_user
            )
        else:
            flash('Please upload both files.', 'error')

    return render_template('add.html', user=current_user)

