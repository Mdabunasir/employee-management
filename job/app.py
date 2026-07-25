from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime


app = Flask(__name__)

DB = "employee.db"



# ================= DATABASE =================

def db_connect():
    return sqlite3.connect(DB)



def init_db():

    conn = db_connect()
    cur = conn.cursor()


    cur.execute("""
    CREATE TABLE IF NOT EXISTS Employee(

        ID INTEGER PRIMARY KEY AUTOINCREMENT,

        Company TEXT,

        Join_Date TEXT,

        Address TEXT,

        Per_Hour REAL

    )
    """)



    cur.execute("""
    CREATE TABLE IF NOT EXISTS Posting(

        ID INTEGER PRIMARY KEY AUTOINCREMENT,

        Employee_ID INTEGER,

        Start_Time TEXT,

        End_Time TEXT,

        Hour REAL DEFAULT 0,

        Total_Taka REAL DEFAULT 0,

        Status TEXT

    )
    """)


    conn.commit()
    conn.close()






# ================= HOME =================


@app.route("/")
def index():

    return render_template("index.html")






# ================= NEW ENTRY =================


@app.route("/new_entry")
def new_entry():

    return render_template("newentry.html")





# ================= SAVE EMPLOYEE =================

@app.route("/save_employee",methods=["POST"])
def save_employee():

    company=request.form.get("company")
    join=request.form.get("join_date")
    address=request.form.get("address")
    per=request.form.get("salary_hour")


    if company=="" or join=="" or per=="":
        return "Please fill all data"



    conn=db_connect()
    cur=conn.cursor()



    # Duplicate Company Check

    check=cur.execute("""
    SELECT ID 
    FROM Employee
    WHERE Company=?
    """,
    (company,)
    ).fetchone()



    if check:

        conn.close()

        return """
        <script>
        alert('Company already exists!');
        window.location.href='/new_entry';
        </script>
        """




    cur.execute("""
    INSERT INTO Employee
    (
    Company,
    Join_Date,
    Address,
    Per_Hour
    )

    VALUES(?,?,?,?)

    """,
    (
    company,
    join,
    address,
    float(per)
    ))



    conn.commit()
    conn.close()


    return """
    <script>
    alert('Employee Saved Successfully');
    window.location.href='/new_entry';
    </script>
    """







# ================= POSTING PAGE =================


@app.route("/employee")
def employee():


    conn=db_connect()
    cur=conn.cursor()



    employees=cur.execute("""
    
    SELECT *

    FROM Employee

    ORDER BY ID

    """).fetchall()



    running=cur.execute("""

    SELECT

    Posting.ID,
    Employee.Company,
    Posting.Start_Time


    FROM Posting


    JOIN Employee

    ON Employee.ID=Posting.Employee_ID


    WHERE Posting.Status='Running'


    ORDER BY Posting.ID DESC

    LIMIT 1


    """).fetchone()



    conn.close()



    return render_template(
        "postingwork.html",
        employees=employees,
        running=running,
        now=datetime.now().strftime("%H:%M")
    )










# ================= START WORK =================


@app.route("/post_start",methods=["POST"])
def post_start():


    employee=request.form.get("employee")

    start=request.form.get("startTime")



    if not employee:

        return redirect("/employee")



    conn=db_connect()
    cur=conn.cursor()



    cur.execute("""

    INSERT INTO Posting

    (
    Employee_ID,
    Start_Time,
    Status
    )

    VALUES(?,?,?)

    """,
    (
    employee,
    start,
    "Running"
    ))



    conn.commit()
    conn.close()



    return redirect("/employee")









# ================= END WORK =================


@app.route("/post_end",methods=["POST"])
def post_end():


    end=request.form.get("endTime")



    conn=db_connect()
    cur=conn.cursor()



    data=cur.execute("""

    SELECT *

    FROM Posting

    WHERE Status='Running'

    ORDER BY ID DESC

    LIMIT 1


    """).fetchone()



    if data:



        start=datetime.strptime(
            data[2],
            "%H:%M"
        )


        finish=datetime.strptime(
            end,
            "%H:%M"
        )



        diff=finish-start



        hour=round(
            diff.seconds/3600,
            2
        )



        per=cur.execute("""

        SELECT Per_Hour

        FROM Employee

        WHERE ID=?


        """,
        (data[1],)

        ).fetchone()



        total=0


        if per:

            total=hour*per[0]





        cur.execute("""

        UPDATE Posting

        SET

        End_Time=?,

        Hour=?,

        Total_Taka=?,

        Status='Complete'


        WHERE ID=?


        """,
        (
        end,
        hour,
        total,
        data[0]
        ))





    conn.commit()
    conn.close()



    return redirect("/employee")



@app.route("/report")
def report():

    conn=db_connect()
    cur=conn.cursor()


    data=cur.execute("""

    SELECT

    Employee.ID,
    Employee.Company,
    Employee.Join_Date,
    Employee.Address,
    Employee.Per_Hour,

    Posting.Start_Time,
    Posting.End_Time,
    Posting.Hour,
    Posting.Total_Taka


    FROM Employee


    LEFT JOIN Posting

    ON Employee.ID = Posting.Employee_ID


    ORDER BY Employee.ID DESC


    """).fetchall()



    company=cur.execute("""
    SELECT DISTINCT Company
    FROM Employee
    """).fetchall()



    conn.close()


    return render_template(
        "report.html",
        data=data,
        company=company
    )







# ================= DELETE EMPLOYEE =================

@app.route("/delete_employee/<int:id>")
def delete_employee(id):

    conn = db_connect()
    cur = conn.cursor()


    # আগে Posting delete হবে
    cur.execute("""
    DELETE FROM Posting
    WHERE Employee_ID=?
    """,
    (id,))


    # তারপর Employee delete হবে
    cur.execute("""
    DELETE FROM Employee
    WHERE ID=?
    """,
    (id,))


    conn.commit()
    conn.close()


    return redirect("/")


# ================= EDIT =================

@app.route("/edit_employee/<int:id>")
def edit_employee(id):

    conn=db_connect()
    cur=conn.cursor()


    data=cur.execute("""
    SELECT *
    FROM Employee
    WHERE ID=?
    """,(id,)).fetchone()


    conn.close()


    return render_template(
        "edit.html",
        data=data
    )





@app.route("/update_employee",methods=["POST"])
def update_employee():


    id=request.form["id"]

    company=request.form["company"]

    join=request.form["join_date"]

    address=request.form["address"]

    per=request.form["salary_hour"]



    conn=db_connect()
    cur=conn.cursor()


    cur.execute("""
    UPDATE Employee

    SET

    Company=?,
    Join_Date=?,
    Address=?,
    Per_Hour=?

    WHERE ID=?

    """,
    (
    company,
    join,
    address,
    per,
    id
    ))


    conn.commit()
    conn.close()


    return redirect("/report")





# ================= RUN =================


if __name__=="__main__":


    init_db()


    app.run(debug=True)