import mysql.connector
global cnx
global isInserted

#Create a connection to the database
cnx = mysql.connector.connect(
    host="localhost", 
    user="root", 
    password="root", 
    database="quizo"
)

def get_all_details():
    cursor = cnx.cursor()

    query = ("SELECT * FROM quizo.sign_up")
    cursor.execute(query)

    rows = cursor.fetchall()

    for row in rows:
        print(row)
    cursor.close()
    return

def insert_signup(email, username, password):
    try:
        #Create a cursor object
        cursor = cnx.cursor()

        query = "INSERT INTO quizo.sign_up (email, username, password) VALUES (%s, %s, %s)"
        # query2 = "INSERT INTO quizo.login_credentials () VALUES ()"
        
        cursor.execute(query, (email, username, password))
        cnx.commit()
        cursor.close()
        print("Sign-Up data credentials inserted successfully!")
        return 1

    except mysql.connector.Error as err:
        print("Error inserting the order item:", err)
        #Rollback changes if necessary
        cnx.rollback()
        return -1
    
    except Exception as e:
        print(f"An error occurred: {e}")
        #Rollback changes if necessary
        cnx.rollback()
        return -1
    return None

def search_login_credentials(email, password):
    #Create a cursor object
    cursor = cnx.cursor()

    query = ("SELECT email,password FROM quizo.sign_up where email=%s and password=%s")
    cursor.execute(query, (email, password))
    rows = cursor.fetchall()
    cursor.close()
    if rows:
        print("Data found")
        return True
    else:
        print("No data found.")
    return False


if __name__ == "__main__":
    print(get_all_details())
    # print(search_login_credentials('kumar1166@gmail.com', 'Kris@2223'))
    # insert_signup('kumar1166@gmail.com', 'kris6', 'Kris@2223')
    # print(get_all_details())